"""Shared Blender setup for rendering Heroes 3 battle frames from a rigged GLB.

load(path) imports the GLB and returns its armature; place() scales the creature to HEIGHT
and stands it on z=0 facing right; stage() adds the light and the battle camera (creature
seen slightly from above and the front, 900x800 transparent PNG).
"""
import math

import bpy
from mathutils import Vector

HEIGHT = 1.6
FACING = math.radians(90)   # glTF front (-Y in Blender) turned to +X: facing right on screen


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    # The importer adds an Icosphere as the bone display shape; only skinned meshes are the creature.
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and not any(m.type == "ARMATURE" for m in o.modifiers):
            bpy.data.objects.remove(o)
    return next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")


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


def place(arm, yaw=0.0):
    """Parent everything to a holder, measured in the rest pose: HEIGHT tall, feet on z=0.
    yaw (degrees) turns a model that stands a little off its front axis."""
    roots = [o for o in bpy.context.scene.objects if o.parent is None]
    holder = bpy.data.objects.new("Holder", None)
    bpy.context.scene.collection.objects.link(holder)
    for o in roots:
        o.parent = holder
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    holder.rotation_euler.z = FACING + math.radians(yaw)
    bpy.context.view_layer.update()
    lo, hi = mesh_bounds()
    scale = HEIGHT / (hi.z - lo.z)
    centre = (lo + hi) / 2
    holder.scale = (scale,) * 3
    holder.location = Vector((-centre.x * scale, -centre.y * scale, -lo.z * scale))
    bpy.context.view_layer.update()
    print("SCALE", round(scale, 4))
    return holder


def stage(ortho=3.3):
    """ortho: the camera's view height in scene units (the creature is HEIGHT tall)."""
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
    cam.data.ortho_scale = ortho
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
