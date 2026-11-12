"""Move the animations of a rigged GLB (e.g. a Tripo export, Mixamo skeleton) onto another
humanoid rig (e.g. SkinTokens), and save the result as a GLB that tools/3d/render_export.py
renders like any Tripo export.

    blender -b -P tools/pipeline/retarget.py -- SOURCE.glb TARGET.glb OUT.glb [target_front=+y]

Each mapped bone gets the source bone's world-space rotation away from its rest pose, applied
to its own rest pose; the hips also move like the source's, scaled by hip height. Both rigs
should rest in a similar pose (our A-poses). Bones the source lacks (fingers, extras) stay at
rest. The target is turned to face -Y first, like the Tripo exports, if target_front=+y
(Pixal3D models). Clip names stay the source's.
"""
import math, os, sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import humanoid  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
src_path, dst_path, out_path = argv[:3]
target_front = next((x[13:] for x in argv[3:] if x.startswith('target_front=')), '+y')

bpy.ops.wm.read_factory_settings(use_empty=True)

def import_glb(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.context.scene.objects if o not in before]
    for o in [o for o in new if o.type == 'MESH' and not any(m.type == 'ARMATURE' for m in o.modifiers)]:
        new.remove(o)
        bpy.data.objects.remove(o)   # the importer's Icosphere bone shape
    return next(o for o in new if o.type == 'ARMATURE'), [o for o in new if o.type == 'MESH']

src, _src_meshes = import_glb(src_path)
actions = [a for a in bpy.data.actions]
dst, dst_meshes = import_glb(dst_path)
for a in [a for a in bpy.data.actions if a not in actions]:
    bpy.data.actions.remove(a)
for m in _src_meshes:
    bpy.data.objects.remove(m)

if target_front == '+y':   # turn the target to face -Y like the source: rotate bones and vertices
    R = Matrix.Rotation(math.pi, 4, 'Z')
    dst.data.transform(R)
    for m in dst_meshes:
        m.data.transform(R)
    bpy.context.view_layer.update()

def toes_y(arm, M):
    return sum((arm.matrix_world @ M[k].head_local).y for k in ('toe_a', 'toe_b') if k in M)

for m in dst_meshes:   # faster: the meshes don't need deforming while we bake
    for mod in m.modifiers:
        if mod.type == 'ARMATURE':
            mod.show_viewport = False

S_map, D_map = humanoid.map_mixamo(src), humanoid.map_bones(dst)
if (toes_y(src, S_map) < 0) != (toes_y(dst, D_map) < 0):
    sys.exit(f'source and target face different ways (toes y {toes_y(src, S_map):.3f} / {toes_y(dst, D_map):.3f}): fix target_front')
PAIRS = humanoid.pairs(S_map, D_map)
for s, d in PAIRS:
    print('PAIR', s, '->', d)
order = {b.name: i for i, b in enumerate(sorted(dst.data.bones, key=lambda b: len(b.parent_recursive)))}
PAIRS.sort(key=lambda p: order[p[1]])

Ws, Wd = src.matrix_world, dst.matrix_world
rest_s = {s: (Ws @ src.data.bones[s].matrix_local) for s, _ in PAIRS}
rest_d = {d: (Wd @ dst.data.bones[d].matrix_local) for _, d in PAIRS}
hips_s, hips_d = S_map['hips'].name, D_map['hips'].name
def floor(arm, M):
    feet = [M[k] for k in ('foot_a', 'foot_b', 'toe_a', 'toe_b') if k in M]
    return min((arm.matrix_world @ b.head_local).z for b in feet)
scale = (rest_d[hips_d].translation.z - floor(dst, D_map)) / (rest_s[hips_s].translation.z - floor(src, S_map))
print('HIP SCALE', round(scale, 3))

scene = bpy.context.scene
dst.animation_data_create()
for pb in dst.pose.bones:
    pb.rotation_mode = 'QUATERNION'

def set_action(arm, act):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    if act is not None and hasattr(ad, 'action_slot') and act.slots:
        ad.action_slot = act.slots[0]

for act in actions:
    set_action(src, act)
    new = bpy.data.actions.new(act.name)
    set_action(dst, new)
    start, end = (int(round(x)) for x in act.frame_range)
    for f in range(start, end + 1):
        scene.frame_set(f)
        for pb in dst.pose.bones:
            pb.matrix_basis = Matrix()
        bpy.context.view_layer.update()
        for s, d in PAIRS:
            ms = Ws @ src.pose.bones[s].matrix
            delta = ms.to_quaternion() @ rest_s[s].to_quaternion().inverted()
            rot = (delta @ rest_d[d].to_quaternion()).to_matrix().to_4x4()
            pb = dst.pose.bones[d]
            if d == hips_d:
                pos = rest_d[d].translation + (ms.translation - rest_s[s].translation) * scale
            else:
                pos = (Wd @ pb.matrix).translation
            pb.matrix = Wd.inverted() @ (Matrix.Translation(pos) @ rot)
            bpy.context.view_layer.update()
        for s, d in PAIRS:
            pb = dst.pose.bones[d]
            pb.keyframe_insert('rotation_quaternion', frame=f)
            if d == hips_d:
                pb.keyframe_insert('location', frame=f)
    print('CLIP', act.name, start, end)

set_action(dst, None)
for m in dst_meshes:
    for mod in m.modifiers:
        if mod.type == 'ARMATURE':
            mod.show_viewport = True
bpy.data.objects.remove(src)
names = {}
for a in actions:
    names[a.name + '.001'] = a.name
    bpy.data.actions.remove(a)
for a in bpy.data.actions:   # the copies got '.001'; give them the source names back
    a.name = names.get(a.name, a.name)
for o in bpy.context.scene.objects:
    o.select_set(o in [dst] + dst_meshes)
bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB', use_selection=True,
                          export_animation_mode='ACTIONS', export_force_sampling=True)
print('WROTE', out_path, [a.name for a in bpy.data.actions])
