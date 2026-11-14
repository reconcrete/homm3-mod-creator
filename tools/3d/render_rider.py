"""Adventure-map frames of a hero on a mount from one unrigged GLB (rider and mount in one mesh).

    blender -b -P tools/3d/render_rider.py -- MODEL.glb OUTDIR [height=48] [elev=25] [cloud=1]

Writes OUTDIR/g<group>/<frame>.png at 4x (384x256, the 96x64 hero picture of the original game) and
OUTDIR/meta.json. Groups as in the original hero DEFs: 0-4 standing, 5-9 moving, each for the
directions up, up-right, right, down-right, down (VCMI mirrors the left ones). Standing frames
breathe (8 frames of 180 ms), moving frames are one hop (8 frames of 50 ms, highest at frame 3 like
the flag's bob). The model's feet sit on (48, 54) of the 1x picture. meta.json gives, per group and
frame, the 1x pixel of the rider's chest (where riders.py ends the flag pole that it draws) and the
mesh's screen box. No ground shadow: the animation json asks VCMI to generate its map shadow.
"""
import json, math, os, sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = argv[0], argv[1]
opt = dict(a.split('=') for a in argv[2:])
HEIGHT_PX = float(opt.get('height', 48))     # rider's head to the mount's feet, 1x pixels (the knight: about 45)
ELEV = math.radians(float(opt.get('elev', 25)))
S = 4                                         # supersampling
W, H = 96 * S, 64 * S
FEET = (48, 54)                               # room below for toes nearer the camera; riders.py moves each direction down onto row 63
YAW = [180, 135, 90, 45, 0]                   # up, up-right, right, down-right, down; glTF front is -Y
# one hop: height in 1x pixels, vertical squash, pitch (degrees, negative = nose up)
HOP = [(0, 0.93, 0), (2, 1.04, -7), (4, 1.04, -5), (5, 1.02, -1), (4, 1.0, 3), (2, 1.0, 6), (0, 0.98, 3), (0, 0.92, 0)]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
biggest = max(len(o.data.vertices) for o in meshes)
for o in [o for o in meshes if len(o.data.vertices) < biggest * 0.02]:
    bpy.data.objects.remove(o)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']


def sand_cloud(meshes):
    """A lumpy flat cloud of sand under the rider's feet (Pixal3D drops a fuzzy sand cloud as background)."""
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(deps)
        pts += [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
        ev.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    h = hi.z - lo.z
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1,
                                          location=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z - h * 0.05))
    cloud = bpy.context.active_object
    cloud.scale = (h * 0.5, h * 0.42, h * 0.12)
    tex = bpy.data.textures.new('lumps', 'CLOUDS')
    tex.noise_scale = 0.35
    mod = cloud.modifiers.new('lumps', 'DISPLACE')
    mod.texture, mod.strength, mod.texture_coords = tex, 0.35, 'LOCAL'
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_apply(modifier='lumps')
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new('sand')
    mat.use_nodes = True
    nt = mat.node_tree
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 18
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.22, 0.12, 0.03, 1)   # linear colours: these read as golden sand
    ramp.color_ramp.elements[1].color = (0.72, 0.46, 0.13, 1)
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    bsdf = nt.nodes['Principled BSDF']
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0
    cloud.data.materials.append(mat)
    return cloud


if opt.get('cloud'):
    meshes.append(sand_cloud(meshes))
for o in bpy.context.scene.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
model = bpy.context.view_layer.objects.active
model.parent = None
model.rotation_mode = 'XYZ'   # the glTF importer leaves quaternions, which ignore rotation_euler
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# feet on z=0, centred on the origin, so scaling and turning keep the feet in place
vs = [v.co.copy() for v in model.data.vertices]
lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
for v in model.data.vertices:
    v.co -= shift
height = hi.z - lo.z
# the rider's chest: the middle of the vertices in the top fifth, a little lower
top = [v.co for v in model.data.vertices if v.co.z > height * 0.8]
chest = Vector((sum(p.x for p in top) / len(top), sum(p.y for p in top) / len(top), height * 0.72))

scene = bpy.context.scene
world = bpy.data.worlds.new('World'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[1].default_value = 1.2
for name, energy, direction in (('Key', 4.2, (0.5, 0.45, -0.75)), ('Fill', 1.3, (-0.6, -0.4, -0.4))):
    sun = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN'))
    sun.data.energy = energy
    sun.rotation_euler = Vector(direction).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(sun)
for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs['Metallic'].default_value = 0.0
                node.inputs['Roughness'].default_value = max(0.6, node.inputs['Roughness'].default_value)

# camera from the south, looking down ELEV; scale so the model stands HEIGHT_PX tall (seen from the front)
d = Vector((0, math.cos(ELEV), -math.sin(ELEV)))     # view direction
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
cam.data.type = 'ORTHO'
cam.location = -d * 20
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
depth = hi.y - lo.y
seen = height * math.cos(ELEV) + depth * math.sin(ELEV) * 0.5
ppu = HEIGHT_PX * S / seen                            # render pixels per scene unit
cam.data.ortho_scale = W / ppu
cam.data.shift_x = 0
cam.data.shift_y = (FEET[1] * S - H / 2) / W           # origin (the feet) lands on FEET
scene.render.engine = 'BLENDER_EEVEE'
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'   # AgX (the default) greys the colours out at this size
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
bpy.context.view_layer.update()


def screen(p):
    c = world_to_camera_view(scene, cam, p)
    return [round(c.x * W / S, 1), round((1 - c.y) * H / S, 1)]


meta = {'chest': {}, 'box': {}}
for group in range(10):
    yaw = math.radians(YAW[group % 5])
    os.makedirs(f'{out}/g{group}', exist_ok=True)
    for f in range(8):
        if group < 5:                                  # breathing
            b = math.sin(2 * math.pi * f / 8)
            z, sz, pitch = 0, 1 + 0.03 * b, 0
        else:
            z, sz, pitch = HOP[f]
        sxy = 1 / math.sqrt(sz)
        model.location = (0, 0, z * S / ppu)
        model.scale = (sxy, sxy, sz)
        model.rotation_euler = (math.radians(pitch), 0, yaw)
        bpy.context.view_layer.update()
        scene.render.filepath = f'{out}/g{group}/{f}.png'
        bpy.ops.render.render(write_still=True)
        meta['chest'][f'{group}:{f}'] = screen(model.matrix_world @ chest)
        pts = [screen(model.matrix_world @ Vector(c)) for c in
               [(x, y, zz) for x in (lo.x - shift.x, hi.x - shift.x) for y in (lo.y - shift.y, hi.y - shift.y) for zz in (0, height)]]
        meta['box'][f'{group}:{f}'] = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
json.dump(meta, open(f'{out}/meta.json', 'w'), indent=1)
print('RENDERED', out)
