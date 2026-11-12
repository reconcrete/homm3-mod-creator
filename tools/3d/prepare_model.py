"""Import a generated GLB, simplify it, stand it on the ground and save a .blend.

Also renders orthographic side / top / front views (transparent PNGs) and writes the
view parameters to views.json so a grid can be drawn over them.

Run: blender -b -P tools/3d/prepare_model.py -- MODEL.glb WORKDIR [target_faces]
"""
import json
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
model, work = argv[0], argv[1]
target_faces = int(argv[2]) if len(argv) > 2 else 60000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=model)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print("MESHES", [(o.name, len(o.data.polygons)) for o in meshes])
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "Body"
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in list(bpy.context.scene.objects):
    if o != body:
        bpy.data.objects.remove(o)

# Exported models are cut along texture seams; weld them so the surface is connected
# (UVs live on face corners, so the texture is unaffected).
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=1e-5)
bpy.ops.object.mode_set(mode="OBJECT")

faces = len(body.data.polygons)
if faces > target_faces:
    mod = body.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = target_faces / faces
    bpy.ops.object.modifier_apply(modifier=mod.name)

# Scale to 2 units long on its longest axis, centre on X/Y, feet on Z=0.
corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
lo = Vector((min(c[i] for c in corners) for i in range(3)))
hi = Vector((max(c[i] for c in corners) for i in range(3)))
scale = 2.0 / max(hi - lo)
body.scale = (scale,) * 3
body.location = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)) * scale
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.shade_smooth()

corners = [Vector(c) for c in body.bound_box]
lo = Vector((min(c[i] for c in corners) for i in range(3)))
hi = Vector((max(c[i] for c in corners) for i in range(3)))
print("FACES", len(body.data.polygons), "BOUNDS", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
print("MATERIALS", [m.name for m in body.data.materials])

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 1000
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-40))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.6
scene.collection.objects.link(cam)
scene.camera = cam
centre = (lo + hi) / 2
views = {
    "side_pos_x": ((centre.x + 10, centre.y, centre.z), (90, 0, 90)),    # looking along -X
    "side_neg_x": ((centre.x - 10, centre.y, centre.z), (90, 0, -90)),   # looking along +X
    "front_neg_y": ((centre.x, centre.y - 10, centre.z), (90, 0, 0)),    # looking along +Y
    "back_pos_y": ((centre.x, centre.y + 10, centre.z), (90, 0, 180)),   # looking along -Y
    "top": ((centre.x, centre.y, centre.z + 10), (0, 0, 0)),             # looking down
}
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = f"{work}/view_{name}.png"
    bpy.ops.render.render(write_still=True)

json.dump({"centre": list(centre), "ortho_scale": cam.data.ortho_scale, "lo": list(lo), "hi": list(hi)},
          open(f"{work}/views.json", "w"))
bpy.ops.wm.save_as_mainfile(filepath=f"{work}/prepared.blend")
print("SAVED")
