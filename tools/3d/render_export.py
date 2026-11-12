"""Render a Tripo Studio export (one GLB: mesh + skin + several animations) into battle frames.

Camera, light and placement come from battle_scene.py (creature faces right, seen slightly
from above and the front; scaled from the rest pose so every clip lines up).

Run: blender -b -P tools/3d/render_export.py -- EXPORT.glb OUT [turn=DEG] [rigid=BONE] clip=frames[:anim] ...
     turn   degrees to turn the creature toward the camera (humanoids read better in a
            three-quarter view, like the original Heroes 3 soldiers; default 0 = profile)
     ortho  the camera's view height (default 3.3); raise it when a weapon leaves the frame
     rigid  a bone whose descendants' skin weights move onto it: rigid=mixamorig:RightHand
            makes a fist, so a held weapon (often skinned to a finger) follows the wrist
     clip   the frame folder name (walk, idle, attack, ...)
     frames how many frames to render (looping clips skip the last frame)
     anim   the animation's name (or its start) inside the GLB, when it differs from clip; @A-B (seconds)
            renders only that stretch of a long clip
Frames go to OUT/<clip>/NN.png (900x800 RGBA). Without clip arguments it lists the animations.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import battle_scene  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
LOOPING = {"idle", "walk", "run", "mouseover"}

arm = battle_scene.load(src)
actions = {a.name: a for a in bpy.data.actions}
print("ACTIONS", {n: tuple(a.frame_range) for n, a in actions.items()})
if len(argv) < 3:
    sys.exit(0)


def set_action(act):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    if act is not None and hasattr(ad, "action_slot") and act.slots:
        ad.action_slot = act.slots[0]


specs = [a for a in argv[2:] if not a.startswith(("turn=", "rigid=", "ortho="))]
for a in argv[2:]:
    if a.startswith("rigid="):
        bone = arm.data.bones[a[6:]]
        names = {b.name for b in bone.children_recursive}
        for mesh in (o for o in bpy.context.scene.objects if o.type == "MESH"):
            groups = {g.index: g.name for g in mesh.vertex_groups}
            target = mesh.vertex_groups.get(bone.name) or mesh.vertex_groups.new(name=bone.name)
            for v in mesh.data.vertices:
                moved = sum(g.weight for g in v.groups if groups.get(g.group) in names)
                if moved:
                    target.add([v.index], moved, "ADD")
                    for name in names & {groups[g.group] for g in v.groups if g.group in groups}:
                        mesh.vertex_groups[name].remove([v.index])
        print("RIGID", bone.name, len(names), "bones merged")
turn = next((float(a[5:]) for a in argv[2:] if a.startswith("turn=")), 0.0)
battle_scene.place(arm, -turn)
battle_scene.stage(next((float(a[6:]) for a in argv[2:] if a.startswith("ortho=")), 3.3))
scene = bpy.context.scene

for spec in specs:
    clip, _, rest = spec.partition("=")
    count, _, anim = rest.partition(":")
    anim, _, window = anim.partition("@")
    count, anim = int(count), anim or clip
    act = actions.get(anim) or next((a for n, a in actions.items()
                                     if n.lower().endswith(anim.lower()) or n.lower().startswith(anim.lower())), None)
    if act is None:
        print("MISSING", anim)
        continue
    set_action(act)
    start, end = act.frame_range
    if window:   # a stretch of a long clip, in seconds: idle=8:idle@0-2
        fps = scene.render.fps / scene.render.fps_base
        a, b = (float(x) for x in window.split("-"))
        start, end = start + a * fps, min(end, start + b * fps)
    folder = os.path.join(out, clip)
    os.makedirs(folder, exist_ok=True)
    for f in range(count):
        t = f / count if clip in LOOPING else f / max(1, count - 1)
        scene.frame_set(int(round(start + t * (end - start))))
        scene.render.filepath = os.path.join(folder, f"{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", clip, count, "from", act.name, start, end)
print("DONE")
