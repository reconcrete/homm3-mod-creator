"""Blender: dump a rigged GLB's bones and a vertex sample to JSON for plot_bones.py.
Run: blender -b -P tools/3d/bone_map.py -- RIGGED.glb OUT.json"""
import bpy, sys, json
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
out = {'v': [], 'b': {}}
for o in bpy.data.objects:
    if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers):
        for i, v in enumerate(o.data.vertices):
            if i % 7 == 0:
                w = o.matrix_world @ v.co; out['v'].append([w.x, w.y, w.z])
for b in arm.data.bones:
    h, t = arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local
    out['b'][b.name] = [[h.x, h.y, h.z], [t.x, t.y, t.z]]
json.dump(out, open(a[1], 'w'))
