"""Turntable check sheet of a GLB model: 6 angles, textured on top, untextured clay below.

    blender -b -P tools/pipeline/turntable.py -- MODEL.glb SHEET.png [turn=DEG]

Clay shows the shape alone (holes, blobs, fused limbs, extra parts); textured shows whether
the texture sits right. The angles: front, front-right, right, back, left, front-left (the
model's front faces -Y in Blender after a glTF import; Pixal3D models face +Y, so model.py passes
turn=180). Prints the mesh stats too.
"""
import math, os, sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
TURN = next((float(x[5:]) for x in argv[2:] if x.startswith('turn=')), 0.0)
TILE = 400
ANGLES = [0, 45, 90, 180, 270, 315]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
biggest = max(len(o.data.vertices) for o in meshes)
for o in [o for o in meshes if len(o.data.vertices) < biggest * 0.02]:   # helpers, e.g. Tripo's hidden Icosphere
    bpy.data.objects.remove(o)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
verts = sum(len(o.data.vertices) for o in meshes)
faces = sum(len(o.data.polygons) for o in meshes)
deps = bpy.context.evaluated_depsgraph_get()   # posed / skinned vertices, not the rig's bounds
pts = []
for o in meshes:
    ev = o.evaluated_get(deps)
    pts += [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
    ev.to_mesh_clear()
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center, size = (lo + hi) / 2, hi - lo
print(f'MESH objects={len(meshes)} verts={verts} faces={faces} size x={size.x:.3f} y={size.y:.3f} z={size.z:.3f}')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = scene.render.resolution_y = TILE
scene.render.film_transparent = False
world = bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.36, 0.32, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.6

cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'
cam_data.ortho_scale = max(size.x, size.y, size.z) * 1.15
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
sun_data = bpy.data.lights.new('sun', 'SUN'); sun_data.energy = 3.0
sun = bpy.data.objects.new('sun', sun_data); scene.collection.objects.link(sun)

clay = bpy.data.materials.new('clay')
clay.use_nodes = True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.72, 0.68, 1)
originals = {o.name: [s.material for s in o.material_slots] for o in meshes}

def shoot(angle, path):
    a = math.radians(angle + TURN)
    d = max(size) * 3
    # front faces -Y: the camera starts at -Y and orbits counter-clockwise seen from above
    cam.location = center + Vector((d * math.sin(a), -d * math.cos(a), 0))
    cam.rotation_euler = (math.radians(90), 0, a)
    sun.rotation_euler = (math.radians(50), 0, a + math.radians(30))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

tmp = os.path.splitext(out)[0] + '_tiles'
os.makedirs(tmp, exist_ok=True)
tiles = []
for row, mode in enumerate(('tex', 'clay')):
    for o in meshes:
        for i, s in enumerate(o.material_slots):
            s.material = clay if mode == 'clay' else originals[o.name][i]
    for col, ang in enumerate(ANGLES):
        p = os.path.join(tmp, f'{mode}_{ang:03d}.png')
        shoot(ang, p)
        tiles.append((row, col, p))

sheet = bpy.data.images.new('sheet', TILE * len(ANGLES), TILE * 2, alpha=False)
px = [0.0] * (TILE * len(ANGLES) * TILE * 2 * 4)
for row, col, p in tiles:
    im = bpy.data.images.load(p)
    src_px = list(im.pixels)
    y0 = (1 - row) * TILE   # Blender images start at the bottom row
    for y in range(TILE):
        a = (y * TILE) * 4
        b = ((y0 + y) * TILE * len(ANGLES) + col * TILE) * 4
        px[b:b + TILE * 4] = src_px[a:a + TILE * 4]
sheet.pixels = px
sheet.filepath_raw = out
sheet.file_format = 'PNG'
sheet.save()
print('SHEET', out)
