"""Reduce a generated model to a rig- and render-friendly face count, keeping its texture.

    blender -b -P tools/pipeline/decimate.py -- IN.glb OUT.glb [faces=30000]

Pixal3D gives ~700k faces; the Tripo models we animated had ~20k. Collapse decimation keeps the
UVs, so the baked texture still fits.
"""
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
target = next((int(x[6:]) for x in argv[2:] if x.startswith('faces=')), 30000)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
total = sum(len(o.data.polygons) for o in meshes)
for o in meshes:
    m = o.modifiers.new('decimate', 'DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.ratio = min(1.0, target / total)
    m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)
print('DECIMATED', total, '->', sum(len(o.data.polygons) for o in meshes))
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB')
