"""Render Tripo's animated GLBs (anim-<name>.glb) into Heroes 3 battle frames.

Same camera and light as animate_render.py (creature faces right, seen slightly from above
and the front). Every clip gets the same scale and placement, taken from rigged.glb's rest
pose, so the frames line up across actions: height 1.6 units, feet on z=0.

Run: blender -b -P tools/3d/render_clips.py -- WORK [name=frames ...]
     default: idle=8 walk=12 slash=8 hurt=6 fall=8
Frames go to WORK/frames/<name>/NN.png (900x800 RGBA).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
work = argv[0]
plan = dict(a.split("=") for a in argv[1:]) or {"idle": 8, "walk": 12, "slash": 8, "hurt": 6, "fall": 8}
LOOPING = {"idle", "walk", "run"}
HEIGHT = 1.6
FACING = math.radians(90)   # glTF front (-Y in Blender) turned to +X: facing right on screen


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    holder = bpy.data.objects.new("Holder", None)
    bpy.context.scene.collection.objects.link(holder)
    for o in roots:
        o.parent = holder
    return holder


def mesh_bounds():
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            ev = o.evaluated_get(deps)
            pts += [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
            ev.to_mesh_clear()
    lo = Vector((min(p[i] for p in pts) for i in range(3)))
    hi = Vector((max(p[i] for p in pts) for i in range(3)))
    return lo, hi


# Scale and placement from the rest pose.
holder = load(os.path.join(work, "rigged.glb"))
holder.rotation_euler.z = FACING
bpy.context.view_layer.update()
lo, hi = mesh_bounds()
scale = HEIGHT / (hi.z - lo.z)
centre = (lo + hi) / 2
offset = Vector((-centre.x * scale, -centre.y * scale, -lo.z * scale))
print("SCALE", round(scale, 4), "BOUNDS", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))


def setup_scene():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    for name, energy, direction in (("Key", 3.2, (0.55, 0.6, -0.75)), ("Fill", 0.9, (-0.6, 0.5, -0.3))):
        sun = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        sun.data.energy = energy
        sun.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(sun)
    target = Vector((0.0, 0.0, HEIGHT * 0.45))
    az, el = math.radians(14), math.radians(17)
    d = Vector((math.sin(az), -math.cos(az), math.tan(el))).normalized()
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 3.3
    cam.location = target + d * 12
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = 900, 800
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    node.inputs["Metallic"].default_value = 0.0
                    node.inputs["Roughness"].default_value = max(0.6, node.inputs["Roughness"].default_value)


for name, count in plan.items():
    path = os.path.join(work, f"anim-{name}.glb")
    if not os.path.exists(path):
        print("MISSING", path)
        continue
    count = int(count)
    holder = load(path)
    holder.rotation_euler.z = FACING
    holder.scale = (scale,) * 3
    holder.location = offset
    setup_scene()
    actions = [o.animation_data.action for o in bpy.context.scene.objects if o.animation_data and o.animation_data.action]
    if not actions:
        print("NO ACTION in", path)
        continue
    start, end = actions[0].frame_range
    out = os.path.join(work, "frames", name)
    os.makedirs(out, exist_ok=True)
    for f in range(count):
        t = f / count if name in LOOPING else f / max(1, count - 1)
        bpy.context.scene.frame_set(int(round(start + t * (end - start))))
        bpy.context.scene.render.filepath = os.path.join(out, f"{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", name, count, "from frames", start, end)
print("DONE")
