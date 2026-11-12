"""Build the armature from rig.json, skin the mesh, pose each animation frame, render.

Run: blender -b WORK/prepared.blend -P tools/3d/animate_render.py -- WORK [action ...]
Frames go to WORK/frames/<action>/<nn>.png (transparent, Heroes 3 battle camera:
creature facing right, seen from slightly above and slightly from the front).
The rigged scene is saved as WORK/rigged.blend.
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
work = argv[0]
wanted = argv[1:] or ["idle", "walk", "attack", "hit", "death"]

rig = json.load(open(f"{work}/rig.json"))["bones"]
skin = np.load(f"{work}/rig.npz")
body = bpy.data.objects["Body"]
scene = bpy.context.scene

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new("Rig")
arm = bpy.data.objects.new("Rig", arm_data)
scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for b in rig:
    eb = arm_data.edit_bones.new(b["name"])
    eb.head, eb.tail = Vector(b["head"]), Vector(b["tail"])
    eb.roll = 0.0
for b in rig:
    if b["parent"] is not None:
        arm_data.edit_bones[b["name"]].parent = arm_data.edit_bones[rig[b["parent"]]["name"]]
bpy.ops.object.mode_set(mode="OBJECT")

groups = [body.vertex_groups.new(name=b["name"]) for b in rig]
idx, wts = skin["bone_idx"], skin["bone_w"]
for v in range(len(idx)):
    for k in range(4):
        if wts[v, k] > 0.01:
            groups[idx[v, k]].add([v], float(wts[v, k]), "REPLACE")
mod = body.modifiers.new("Armature", "ARMATURE")
mod.object = arm
body.parent = arm

rest = {b["name"]: arm_data.bones[b["name"]].matrix_local.to_quaternion() for b in rig}
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def world_rot(name, *axis_angles):
    """Rotate a bone about world axes (degrees), whatever the bone's own orientation."""
    q = Quaternion()
    for axis, deg in axis_angles:
        q = Quaternion(axis, math.radians(deg)) @ q
    r = rest[name]
    arm.pose.bones[name].rotation_quaternion = r.inverted() @ q @ r


def root_move(dx=0.0, dy=0.0, dz=0.0):
    arm.pose.bones["Root"].location = rest["Root"].inverted() @ Vector((dx, dy, dz))


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def bump(t, start, peak, end):
    if t <= start or t >= end:
        return 0.0
    return ease((t - start) / (peak - start)) if t < peak else ease((end - t) / (end - peak))


# Four-beat walk: each paw is on the ground 60% of the cycle, then lifts and reaches.
LEG_OFFSET = {"leg_rl": 0.0, "leg_fl": 0.25, "leg_rr": 0.5, "leg_fr": 0.75}
STANCE = 0.6


def leg_cycle(p):
    """Returns (swing, lift): swing -1 (reaching forward) .. +1 (pushed back); lift 0..1."""
    p %= 1.0
    if p < STANCE:
        return -1 + 2 * (p / STANCE), 0.0
    q = (p - STANCE) / (1 - STANCE)
    return 1 - 2 * ease(q), math.sin(math.pi * q)


chain_phase = {}
for b in rig:
    chain_phase.setdefault(b["chain"], (len(chain_phase) * 2.399) % (2 * math.pi))


def pose(action, t):
    """t runs 0..1 over the action."""
    w = 2 * math.pi * t
    for pb in arm.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()

    sway, droop = 1.0, 0.0
    root_rot, head_pitch = [], 0.0
    dx = dz = 0.0
    leg_amp = 0.0
    paw = 0.0
    jaw_open = 0.0

    if action == "idle":
        dz = 0.008 * math.sin(w)
        head_pitch = 2.5 * math.sin(w)
    elif action == "walk":
        dz = 0.012 * math.cos(2 * w)
        root_rot = [(Y, 1.5 * math.sin(2 * w)), (X, 2.0 * math.sin(w))]
        head_pitch = -2.5 * math.sin(2 * w + 0.6)
        leg_amp = 1.0
        sway = 1.3
    elif action == "attack":
        wind = bump(t, 0.0, 0.25, 0.4)
        strike = bump(t, 0.3, 0.5, 0.9)
        dx = -0.07 * wind + 0.26 * strike
        dz = 0.03 * wind - 0.05 * strike
        root_rot = [(Y, 8 * wind - 10 * strike)]
        head_pitch = -10 * wind + 26 * strike
        paw = strike
        jaw_open = bump(t, 0.1, 0.38, 0.62)
        sway = 1.0 + 1.5 * strike
    elif action == "hit":
        k = bump(t, 0.0, 0.3, 1.0)
        dx = -0.12 * k
        dz = 0.02 * k
        root_rot = [(Y, -9 * k)]
        head_pitch = -16 * k
        jaw_open = 0.6 * k
        sway = 1.0 + 2.0 * k
    elif action == "death":
        k = ease(t / 0.8)
        dx = -0.08 * k
        dz = -0.30 * k
        root_rot = [(Y, -6 * k), (X, 86 * k)]
        head_pitch = 20 * k
        jaw_open = 0.5 * k
        sway = 1.0 - k
        droop = k

    root_move(dx, 0.0, dz)
    if root_rot:
        world_rot("Root", *root_rot)

    for b in rig:
        name, part, d = b["name"], b["part"], b["depth"]
        if part == "tail":
            ph = chain_phase[b["chain"]]
            a = 3.2 * sway * math.sin(w - 0.55 * d + ph)
            c = 1.6 * sway * math.sin(w - 0.55 * d + ph + 1.3)
            world_rot(name, (X, a), (Y, c - 4.5 * droop))
        elif part == "head" and d == 0:
            world_rot(name, (Y, head_pitch))

    if "jaw" in rest:
        world_rot("jaw", (Y, 24 * jaw_open))

    for part in LEG_OFFSET:
        pose_leg(part, t, leg_amp, paw, droop, 0.0)
    if leg_amp:
        # The leg's bend is solved, not keyed: bisect the bend until the paw sits at the
        # height the gait wants (ground while planted, a smooth arc while stepping).
        for part in LEG_OFFSET:
            _, lift = leg_cycle(t + LEG_OFFSET[part])
            target = paw_rest[part] + 0.05 * lift
            lo, hi = -12.0, 60.0
            for _ in range(9):
                mid_bend = (lo + hi) / 2
                pose_leg(part, t, leg_amp, paw, droop, mid_bend)
                if paw_height(part) < target:
                    lo = mid_bend
                else:
                    hi = mid_bend
            pose_leg(part, t, leg_amp, paw, droop, (lo + hi) / 2)


def pose_leg(part, t, leg_amp, paw, droop, bend):
    """bend > 0 folds the leg (elbow / knee and wrist / hock), which raises the paw."""
    front = part in ("leg_fl", "leg_fr")
    for b in LEG_BONES[part]:
        d, n = b["depth"], b["chain_len"]
        mid, low = round(0.4 * (n - 1)), round(0.75 * (n - 1))
        ang = 0.0
        if leg_amp:
            swing, _ = leg_cycle(t + LEG_OFFSET[part])
            if d == 0:
                ang = 12 * swing
            if d == low:
                ang += -8 * swing
        if d == 0:
            ang += bend * (-0.3 if front else 0.35)
        if d == mid or d == mid + 1:
            ang += bend * (0.5 if front else -0.5)
        if d == low:
            ang += bend * (-0.55 if front else 0.75)
        if paw and part == "leg_fr":
            if d == 0:
                ang += -34 * paw
            elif d == mid:
                ang += 22 * paw
        if droop and d == 0:
            ang += 12 * droop
        world_rot(b["name"], (Y, ang))


def paw_height(part):
    """Lowest point of the paw in the current pose."""
    bpy.context.view_layer.update()
    mesh = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    return float(co.reshape(-1, 3)[PAWS[part], 2].min())


LEG_BONES = {part: [b for b in rig if b["part"] == part] for part in LEG_OFFSET}
PAWS = {part: skin[f"paw_{part}"] for part in LEG_OFFSET}
paw_rest = {part: paw_height(part) for part in LEG_OFFSET}
print("PAW REST", {k: round(v, 3) for k, v in paw_rest.items()})

# ---------------------------------------------------------------- look and camera
for mat in body.data.materials:
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Metallic"].default_value = 0.0
                node.inputs["Roughness"].default_value = 0.75

for obj in list(scene.objects):
    if obj.type in {"LIGHT", "CAMERA"}:
        bpy.data.objects.remove(obj)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.9


def add_sun(name, energy, direction):
    sun = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
    sun.data.energy = energy
    sun.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(sun)


add_sun("Key", 3.2, (0.55, 0.6, -0.75))     # from the upper left of the picture, in front
add_sun("Fill", 0.9, (-0.6, 0.5, -0.3))

target = Vector((0.0, 0.0, 0.62))
azimuth, elevation = math.radians(14), math.radians(17)
direction = Vector((math.sin(azimuth), -math.cos(azimuth), math.tan(elevation))).normalized()
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 3.3
cam.location = target + direction * 12
cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "BLENDER_EEVEE"
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 900, 800
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"

FRAMES = {"idle": 8, "walk": 12, "attack": 8, "hit": 6, "death": 8}
for action in wanted:
    count = FRAMES[action]
    os.makedirs(f"{work}/frames/{action}", exist_ok=True)
    for f in range(count):
        looping = action in ("idle", "walk")
        pose(action, f / count if looping else f / (count - 1))
        bpy.context.view_layer.update()
        scene.render.filepath = f"{work}/frames/{action}/{f:02d}.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERED", action, count)

pose("idle", 0.0)
bpy.ops.wm.save_as_mainfile(filepath=f"{work}/rigged.blend")
print("DONE")
