"""Animate a non-humanoid Tripo rig (Studio's "Other" rigging) by script and render battle frames.

Tripo rigs anything, but its preset and AI motions are human motions, which wreck a scorpion or
a dog. This keeps Tripo's skeleton and skin weights and poses the bones procedurally: each
creature below lists its bone chains (legs, tail, pincers, spine, head) and the clips are built
from eased rotations of those chains, in the creature's own space (up +Z, front F).

Run: blender -b -P tools/3d/animate_rig.py -- RIGGED.glb OUT CREATURE [clip ...]
     clips: idle walk attack hit defend death (default: all)
Frames go to OUT/<clip>/NN.png (900x800 RGBA), with the camera from battle_scene.py.
"""
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import battle_scene  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, creature = argv[0], argv[1], argv[2]
FRAMES = {"idle": 8, "walk": 12, "attack": 8, "hit": 6, "defend": 6, "death": 8}
wanted = argv[3:] or list(FRAMES)
LOOPING = {"idle", "walk"}


def bones(*nums):
    return [f"bone_{n}" for n in nums]


CREATURES = {
    # Desert Scorpion: tail of nine segments, two pincers (the -X pincer has a second, duplicate
    # chain), seven leg chains (the -X front leg has no bones of its own).
    "desert-scorpion": {
        "kind": "scorpion",
        "root": "tripo::Root",
        "tail": bones(2, 3, 4, 5, 6, 7, 8, 9, 10),
        "pincers": [bones(34, 35, 36, 37, 38), bones(56, 57, 58, 59, 60), bones(40, 41, 42, 43, 44)],
        "legs": [bones(12, 13, 14, 15), bones(17, 18, 19, 20), bones(46, 47, 48, 49), bones(51, 52, 53, 54),
                 bones(22, 23, 24, 25), bones(27, 28, 29, 30, 31), bones(62, 63, 64, 65)],
    },
    # Ninja Hound (second Tripo rig): the spine runs hip to neck; the hind legs end above the paws.
    "ninja-hound": {
        "kind": "quadruped",
        "root": "tripo::Root",
        "spine": [f"tripo::0_Right_Limb_{i}" for i in range(4)],
        "head": ["tripo::Head_0", "tripo::Head_1", "tripo::Head_2"],
        "tail": ["bone_22"] + [f"tripo::Tail_{i}" for i in range(4)],
        "front": [bones(10, 11, 12, 13, 14, 15), ["tripo::Spine_0"] + bones(17, 18, 19, 20, 21)],
        "hind": [["bone_27", "tripo::0_Left_Limb_0", "tripo::0_Left_Limb_1"],
                 [f"tripo::1_Left_Limb_{i}" for i in range(3)]],
    },
    # Poison Scorpion (batch 3, second Studio rig; the first gave the claws leg weights and
    # crumpled them): faces -Y. 0_Right_Limb_0 is the body hub (it parents the rear leg chains),
    # so the tail starts at Limb_1. Pincers bone_42-47 (+X) and bone_54-58 (-X).
    "poison-scorpion": {
        "kind": "scorpion",
        "root": "tripo::Root",
        "tail": [f"tripo::0_Right_Limb_{i}" for i in range(1, 10)],
        "pincers": [bones(42, 43, 44, 45, 46, 47), bones(54, 55, 56, 57, 58)],
        "legs": [bones(11, 12, 13, 14, 15, 16), bones(17, 18, 19, 20, 21, 22), bones(48, 49, 50, 51, 52),
                 bones(23, 24, 25, 26, 27, 28), bones(29, 30, 31, 32, 33, 34), bones(36, 37, 38), bones(39, 40, 41)],
    },
    # Ninken Pack Leader (batch 3): faces -X. The right front leg hangs from Spine_3, which also
    # parents the neck flesh (Spine_4); "counter" keeps the neck still when that leg swings.
    "ninken-pack-leader": {
        "kind": "quadruped",
        "root": "tripo::Root",
        "spine": [f"tripo::Spine_{i}" for i in range(3)],
        "head": ["tripo::Head_0", "tripo::Head_1"],
        "tail": ["bone_33"] + [f"tripo::Tail_{i}" for i in range(5)],
        "front": [["bone_6"] + [f"tripo::0_Left_Limb_{i}" for i in range(4)],
                  ["tripo::Spine_3"] + [f"tripo::0_Right_Limb_{i}" for i in range(4)]],
        "hind": [[f"tripo::1_Left_Limb_{i}" for i in range(5)],
                 ["bone_25"] + [f"tripo::1_Right_Limb_{i}" for i in range(4)]],
        "counter": {"tripo::Spine_3": ["tripo::Spine_4"]},
    },
    # Great Water Dragon (batch 3): faces +X. Tail_0 is the hub: the coil runs from it to the tail
    # tip (bone_48-55), the neck rises from it through Tail_1-5 and Head_0-2 to the skull (Head_3).
    # No separate jaw bone; the crest and whiskers are five backward chains.
    "great-water-dragon": {
        "kind": "serpent",
        "ortho": 4.2,       # its death roll throws the head forward, out of the default frame
        "root": "tripo::Root",
        "front": (1, 0, 0),
        "necks": [[f"tripo::Tail_{i}" for i in range(1, 6)] + ["tripo::Head_0", "tripo::Head_1", "tripo::Head_2"]],
        "head": ["tripo::Head_3"],
        "jaw": [],
        "horns": [[f"tripo::Head_{i}" for i in range(6, 11)], bones(14, 15, 16, 17), bones(18, 19, 20, 21, 22, 23, 24),
                  bones(30, 31, 32, 33, 34), bones(35, 36, 37)],
        "body": bones(48, 49, 50, 51, 52, 53, 54, 55),
    },
    # Water Dragon: a limbless water serpent facing +X. The neck has two parallel chains (both
    # carry weights, so they move together); the body is the long tail chain.
    "water-dragon": {
        "kind": "serpent",
        "root": "tripo::Root",
        "front": (1, 0, 0),
        "necks": [bones(1, 2, 3, 4, 5), bones(33, 34, 35, 36, 37, 38)],
        "head": ["tripo::Head_0", "bone_39"],
        "jaw": ["tripo::Head_3", "bone_41"],
        "horns": [bones(9, 10, 11, 12), bones(13, 14, 15, 16), bones(44, 45)],
        "body": [f"tripo::Tail_{i}" for i in range(11)],
    },
}
cfg = CREATURES[creature]

arm = battle_scene.load(src)
rest = {b.name: b.matrix_local.to_quaternion() for b in arm.data.bones}
head = {b.name: b.head_local.copy() for b in arm.data.bones}
tip = {b.name: b.tail_local.copy() for b in arm.data.bones}
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
if "front" in cfg and not isinstance(cfg["front"][0], list):   # quadrupeds use "front" for their front legs
    F = Vector(cfg["front"]).normalized()
elif "spine" in cfg:   # the model can stand a little turned: take its front from the spine
    F = tip[cfg["spine"][-1]] - head[cfg["spine"][0]]
    F.z = 0
    F.normalize()
else:
    F = -Y
L = F.cross(Z).normalized()     # + about L: nose up, legs swing forward
yaw = math.degrees(math.atan2(-1, 0) - math.atan2(F.y, F.x))

battle_scene.place(arm, yaw)
battle_scene.stage(ortho=cfg.get("ortho", 3.3))   # "ortho": a wider camera for a creature that would leave the frame
scene = bpy.context.scene


def rot(name, *axis_angles):
    """Rotate a bone about creature-space axes (degrees), on top of what it already has."""
    q = Quaternion()
    for axis, deg in axis_angles:
        q = Quaternion(axis, math.radians(deg)) @ q
    r = rest[name]
    pb = arm.pose.bones[name]
    pb.rotation_quaternion = pb.rotation_quaternion @ (r.inverted() @ q @ r)


def move_root(v):
    arm.pose.bones[cfg["root"]].location = rest[cfg["root"]].inverted() @ v


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def bump(t, start, peak, end):
    """0 outside start..end, eases up to 1 at peak and back down."""
    if t <= start or t >= end:
        return 0.0
    return ease((t - start) / (peak - start)) if t < peak else ease((end - t) / (end - peak))


def outward(chain):
    """Horizontal direction from the body to the chain's tip."""
    v = tip[chain[-1]] - head[chain[0]]
    v.z = 0
    return v.normalized()


def lift_axis(chain):
    """Rotating a chain's first bone about this axis by a positive angle raises its tip."""
    return outward(chain).cross(Z).normalized()


def step(p):
    """A leg's gait at phase p: (swing -1 back .. +1 forward, lift 0..1). Planted half the cycle."""
    p %= 1.0
    if p < 0.5:
        return 1 - 4 * p, 0.0
    q = (p - 0.5) / 0.5
    return -1 + 2 * ease(q), math.sin(math.pi * q)


def reset():
    for pb in arm.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()


# ---------------------------------------------------------------- scorpion

if cfg["kind"] == "scorpion":
    # Legs in two alternating sets (front to back, alternating per side), like a real scorpion.
    by_side = {s: sorted([c for c in cfg["legs"] if (head[c[0]].x > 0) == s], key=lambda c: head[c[0]].y)
               for s in (True, False)}
    leg_phase = {c[0]: 0.5 * ((i + (0 if s else 1)) % 2) for s, side in by_side.items() for i, c in enumerate(side)}


def pose_scorpion(clip, t):
    w = 2 * math.pi * t
    reset()
    body = Vector()
    body_rot = []
    tail_base = 0.0         # + swings the whole tail forward over the back, - lays it back
    tail_tip = 0.0          # + curls the end of the tail further, - straightens it
    tail_sway = 1.0
    tail_fall = 0.0         # + drops the tail over to the camera's side (death)
    pinch = 0.0             # + opens the pincers outward
    pincer_raise = 0.0      # + lifts the pincers
    pincer_in = 0.0         # + swings the pincers toward the middle
    leg_amp = 0.0
    leg_fold = 0.0          # + curls every leg under the body (death)

    if clip == "idle":
        body.z = 0.004 * math.sin(w)
        tail_base = 1.5 * math.sin(w)
        tail_tip = 2.0 * math.sin(w + 0.8)
        pinch = 4 * math.sin(w + 1.0)
    elif clip == "walk":
        body.z = 0.006 * math.cos(2 * w)
        body_rot = [(Z, 2.0 * math.sin(w))]
        tail_base = 1.5 * math.sin(2 * w)
        pinch = 3 * math.sin(2 * w)
        leg_amp = 1.0
    elif clip == "attack":
        wind = bump(t, 0.0, 0.3, 0.45)
        strike = bump(t, 0.35, 0.55, 1.0)
        body.y = 0.03 * wind - 0.06 * strike
        tail_base = -7 * wind + 13 * strike
        tail_tip = 5 * wind - 9 * strike
        pinch = 10 * bump(t, 0.1, 0.35, 0.6) - 6 * strike
        pincer_raise = 8 * wind
    elif clip == "hit":
        k = bump(t, 0.0, 0.3, 1.0)
        body.y = 0.06 * k
        body.z = 0.01 * k
        body_rot = [(X, -6 * k)]
        tail_base = -8 * k
        tail_tip = -3 * k
        tail_sway = 1.0 + 2 * k
        pincer_raise = 14 * k
        pinch = 8 * k
    elif clip == "defend":
        k = bump(t, 0.0, 0.4, 1.0)
        body.y = 0.03 * k
        body.z = -0.02 * k
        pincer_raise = 24 * k
        pincer_in = 18 * k
        pinch = -6 * k
        tail_base = 4 * k
    elif clip == "death":
        k = ease(t / 0.85)
        body.z = -0.08 * k
        body_rot = [(Y, 14 * k), (X, 5 * k)]
        tail_base = -30 * k
        tail_tip = -14 * k
        tail_fall = 30 * k
        tail_sway = 1.0 - k
        pincer_raise = -12 * k
        pinch = 12 * k
        leg_fold = k

    move_root(body)
    if body_rot:
        rot(cfg["root"], *body_rot)

    n = len(cfg["tail"])
    for d, name in enumerate(cfg["tail"]):
        sway = tail_sway * 2.5 * math.sin(w - 0.6 * d)
        curl = tail_base if d < 3 else (tail_tip if d >= n - 4 else 0.0)
        rot(name, (X, curl + 0.4 * sway), (Z, 0.6 * sway + (tail_fall if d == 0 else 0.0)))

    for chain in cfg["pincers"]:
        side = 1 if head[chain[0]].x > 0 else -1
        rot(chain[0], (lift_axis(chain), pincer_raise), (Z, side * (pinch - pincer_in)))
        if len(chain) > 3:
            rot(chain[-2], (Z, side * 0.6 * pinch))

    for chain in cfg["legs"]:
        axis = lift_axis(chain)
        swing, lift = step(t + leg_phase[chain[0]]) if leg_amp else (0.0, 0.0)
        side = 1 if head[chain[0]].x > 0 else -1
        rot(chain[0], (Z, -side * 16 * swing * leg_amp), (axis, 22 * lift + 30 * leg_fold))
        for name in chain[1:]:
            rot(name, (axis, -18 * leg_fold))


# ---------------------------------------------------------------- quadruped

if cfg["kind"] == "quadruped":
    centre = sum((head[b] for b in cfg["spine"]), Vector()) / len(cfg["spine"])

    def side_of(chain):
        return "l" if (head[chain[0]] - centre).dot(L) > 0 else "r"

    # Four-beat walk: left hind, left front, right hind, right front.
    gait = {"hl": 0.0, "fl": 0.25, "hr": 0.5, "fr": 0.75}
    leg_phase = {}
    for end, chains in (("f", cfg["front"]), ("h", cfg["hind"])):
        for c in chains:
            leg_phase[c[0]] = gait[end + side_of(c)]


def pose_quadruped(clip, t):
    w = 2 * math.pi * t
    reset()
    body = Vector()
    pitch = 0.0         # + nose up (whole body)
    roll = 0.0          # whole body about its length (death)
    head_pitch = 0.0    # + head up
    tail_wag = 0.0      # side to side, degrees
    tail_lift = 0.0     # + tail up
    front_reach = 0.0   # + front legs forward
    hind_reach = 0.0    # + hind legs forward
    leg_amp = 0.0
    limp = 0.0          # legs and head go slack (death)

    if clip == "idle":
        body.z = 0.004 * math.sin(w)
        head_pitch = 3 * math.sin(w + 0.5)
        tail_wag = 9 * math.sin(2 * w)
    elif clip == "walk":
        body.z = 0.008 * math.cos(2 * w)
        head_pitch = -3 * math.cos(2 * w)
        tail_wag = 8 * math.sin(w)
        leg_amp = 1.0
    elif clip == "attack":      # a lunging bite
        wind = bump(t, 0.0, 0.3, 0.45)
        strike = bump(t, 0.35, 0.55, 1.0)
        body += F * (-0.05 * wind + 0.08 * strike)
        body.z += -0.025 * wind - 0.02 * strike
        pitch = 4 * wind - 9 * strike
        head_pitch = 12 * wind - 16 * strike
        front_reach = -8 * wind + 28 * strike
        hind_reach = 6 * wind - 18 * strike
        tail_lift = 10 * wind
        tail_wag = 6 * math.sin(3 * w)
    elif clip == "hit":
        k = bump(t, 0.0, 0.3, 1.0)
        body += F * (-0.08 * k)
        body.z += 0.01 * k
        pitch = 8 * k
        head_pitch = 14 * k
        front_reach = 12 * k
        hind_reach = -6 * k
        tail_lift = -14 * k
    elif clip == "defend":
        k = bump(t, 0.0, 0.4, 1.0)
        body += F * (-0.04 * k)
        body.z -= 0.045 * k
        pitch = -4 * k
        head_pitch = -10 * k
        front_reach = 12 * k
        hind_reach = 8 * k
        tail_lift = -12 * k
    elif clip == "death":
        k = ease(t / 0.85)
        roll = -82 * k
        body.z += 0.03 * k
        head_pitch = -10 * k
        tail_lift = -10 * k
        limp = k

    move_root(body)
    rot(cfg["root"], (L, pitch), (F, roll))

    for d, name in enumerate(cfg["head"]):
        rot(name, (L, head_pitch / len(cfg["head"]) + (-6 * limp if d == 0 else 0.0)))

    for d, name in enumerate(cfg["tail"]):
        rot(name, (Z, tail_wag * (0.6 + 0.2 * d)), (L, (tail_lift if d < 2 else 0.0) - 6 * limp))

    for end, chains, reach in (("f", cfg["front"], front_reach), ("h", cfg["hind"], hind_reach)):
        for chain in chains:
            swing, lift = step(t + leg_phase[chain[0]]) if leg_amp else (0.0, 0.0)
            angle = 18 * swing * leg_amp + reach + 10 * limp
            rot(chain[0], (L, angle))
            for child in cfg.get("counter", {}).get(chain[0], []):   # body flesh parented to a shoulder stays put
                rot(child, (L, -angle))
            knee = chain[min(2, len(chain) - 1)]
            rot(knee, (L, -38 * lift - 12 * limp))


# ---------------------------------------------------------------- serpent

def pose_serpent(clip, t):
    w = 2 * math.pi * t
    reset()
    body = Vector()
    wave = 3.0          # amplitude of the travelling wave along the body, degrees per bone
    wave_speed = 1.0    # cycles of the wave per clip
    neck = 0.0          # + rears the neck back, - throws it forward
    head = 0.0          # + nose up
    jaw = 0.0           # 0 closed .. 1 wide open
    sag = 0.0           # 0 .. 1: the whole body slumps to the ground (death)
    horn = 1.0          # horn sway
    topple = 0.0        # degrees the whole body rolls onto its side (death)

    if clip == "idle":
        body.z = 0.006 * math.sin(w)
        neck = 3 * math.sin(w)
        head = -2 * math.sin(w + 0.7)
        jaw = 0.15 + 0.1 * math.sin(w)
    elif clip == "walk":            # swimming through the air: a stronger wave, a bob
        wave, wave_speed = 7.0, 1.0
        body.z = 0.02 * math.sin(2 * w)
        neck = 4 * math.sin(w + 1.0)
        head = -4 * math.sin(w + 1.6)
        jaw = 0.1
        horn = 1.6
    elif clip == "attack":          # rear back, then a lunging bite
        wind = bump(t, 0.0, 0.3, 0.45)
        strike = bump(t, 0.35, 0.55, 1.0)
        body += F * (-0.04 * wind + 0.12 * strike)
        neck = 16 * wind - 26 * strike
        head = 10 * wind - 14 * strike
        jaw = 0.2 + 0.8 * bump(t, 0.2, 0.42, 0.62)
        wave = 3 + 4 * strike
        horn = 2.0
    elif clip == "hit":
        k = bump(t, 0.0, 0.3, 1.0)
        body += F * (-0.07 * k)
        neck = 14 * k
        head = 18 * k
        jaw = 0.2 + 0.6 * k
        wave = 3 + 5 * k
        horn = 2.5
    elif clip == "defend":          # coils up: neck drawn back and low, head tucked
        k = bump(t, 0.0, 0.4, 1.0)
        body += F * (-0.03 * k)
        body.z -= 0.02 * k
        neck = 20 * k
        head = -16 * k
        wave = 3 + 2 * k
    elif clip == "death":           # the water body slumps to the ground
        k = ease(t / 0.85)
        sag = k
        neck = -10 * k
        head = -18 * k
        jaw = 0.2 + 0.5 * k
        wave = 3 * (1 - k)
        horn = 1 - k
        body.z -= 0.04 * k
        topple = 80 * k             # rolls over onto its side: the arch ends lying on the ground

    move_root(body)
    if topple:
        rot(cfg["root"], (F, -topple))
    n = len(cfg["body"])
    for i, name in enumerate(cfg["body"]):
        a = wave * math.sin(wave_speed * w - 0.7 * i)
        # sag: the raised part of the coil (later bones) falls toward the ground
        rot(name, (L, a - 9 * sag * (i / n)), (Z, 0.5 * a))
    for chain in cfg["necks"]:
        m = len(chain)
        for i, name in enumerate(chain):
            share = 0.6 + 0.8 * i / max(1, m - 1)       # bends more toward the head
            rot(name, (L, (neck * share - 40 * sag) / m * 1.6), (Z, 1.5 * math.sin(w - 0.5 * i) / m))
    for name in cfg["head"]:
        rot(name, (L, head))
    for name in cfg["jaw"]:
        rot(name, (L, -26 * jaw))
    for chain in cfg["horns"]:
        for i, name in enumerate(chain):
            rot(name, (L, horn * 4 * math.sin(w - 0.8 * i)))


pose = {"scorpion": pose_scorpion, "quadruped": pose_quadruped, "serpent": pose_serpent}[cfg["kind"]]

for clip in wanted:
    count = FRAMES[clip]
    folder = os.path.join(out, clip)
    os.makedirs(folder, exist_ok=True)
    for f in range(count):
        pose(clip, f / count if clip in LOOPING else f / (count - 1))
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(folder, f"{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", clip, count)
print("DONE")
