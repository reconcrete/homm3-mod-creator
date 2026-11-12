"""Visual check of a rigged humanoid: skeleton, skin-weight heatmaps and test poses.

    blender -b -P tools/pipeline/rigcheck.py -- RIGGED.glb OUT_PREFIX [front=+y]

Writes OUT_PREFIX-skeleton.png (joints and bones over a see-through model, front and side),
OUT_PREFIX-weights.png (one heatmap per main bone: blue 0 to red 1) and OUT_PREFIX-poses.png
(rest, arms up, lunge, twist; textured three-quarter view above, clay side view below).
Look for: joints inside the body at the real elbows, knees, hips and shoulders; each heatmap
confined to its own limb (no bleeding into the torso or the other leg); poses that bend
without tearing, collapsing or dragging cloth and props along wrongly.

Bones are recognised by the skeleton's structure, not by name (SkinTokens names them
bone_N): the root is the hips, the chain going up is the spine to the head, the two lateral
branches off the chest are the arms, the two chains going down are the legs. The mapping is
printed as MAP lines.
"""
import math, os, sys

import bpy
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, prefix = argv[0], argv[1]
front_arg = next((x[6:] for x in argv[2:] if x.startswith('front=')), '+y')
FRONT = {'+y': Vector((0, 1, 0)), '-y': Vector((0, -1, 0))}[front_arg]
TILE = int(next((x[5:] for x in argv[2:] if x.startswith('tile=')), 400))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
biggest = max(len(o.data.vertices) for o in meshes)
for o in [o for o in meshes if len(o.data.vertices) < biggest * 0.02]:
    bpy.data.objects.remove(o)
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')

# ---------------------------------------------------------------- which bone is which

W = arm.matrix_world
def head(b):
    return W @ b.head_local

def chain(b, pick):
    out = [b]
    while b.children:
        b = pick(b.children)
        out.append(b)
    return out

def extremity(b):   # the descendant furthest from b's head
    best, d = b, 0
    stack = [b]
    while stack:
        c = stack.pop()
        dd = (head(c) - head(b)).length
        if dd > d:
            best, d = c, dd
        stack += list(c.children)
    return head(best)

def top(b):   # the highest joint in b's branch
    z, stack = head(b).z, [b]
    while stack:
        c = stack.pop()
        z = max(z, head(c).z)
        stack += list(c.children)
    return z

bones = arm.data.bones
root = next(b for b in bones if b.parent is None)
ups = [c for c in root.children if top(c) > head(root).z]
downs = [c for c in root.children if top(c) <= head(root).z]
assert len(ups) == 1 and len(downs) == 2, f'not a humanoid layout: {len(ups)} up, {len(downs)} down from {root.name}'
spine = [root]
b = ups[0]
while True:
    spine.append(b)
    kids = list(b.children)
    if not kids:
        break
    up = max(kids, key=top)
    side = [c for c in kids if c is not up and abs(extremity(c).x - head(b).x) > 0.1 * (extremity(c) - head(b)).length]
    if len(side) == 2:
        chest, arms_start = b, side
        neck_head = chain(up, lambda cs: max(cs, key=top))
        spine += neck_head
        break
    b = up
MAP = {'hips': root, 'chest': chest, 'head': spine[-1], 'neck': neck_head[0] if len(neck_head) > 1 else spine[-1]}
MAP['spine'] = spine[len(spine) // 2 - 1] if len(spine) > 4 else chest
for side_name, start in zip(('a', 'b'), sorted(arms_start, key=lambda c: extremity(c).x)):
    ch = chain(start, lambda cs: max(cs, key=lambda c: (extremity(c) - head(c)).length))
    # collarbone, upper arm, forearm, hand (a collarbone is short compared with the upper arm)
    if len(ch) >= 4 and (head(ch[1]) - head(ch[0])).length < 0.6 * (head(ch[2]) - head(ch[1])).length:
        MAP[f'collar_{side_name}'], ch = ch[0], ch[1:]
    MAP[f'upperarm_{side_name}'], MAP[f'forearm_{side_name}'], MAP[f'hand_{side_name}'] = ch[0], ch[1], ch[2]
for side_name, start in zip(('a', 'b'), sorted(downs, key=lambda c: extremity(c).x)):
    ch = chain(start, lambda cs: min(cs, key=lambda c: extremity(c).z))
    MAP[f'thigh_{side_name}'], MAP[f'shin_{side_name}'], MAP[f'foot_{side_name}'] = ch[0], ch[1], ch[2]
for k, v in MAP.items():
    print('MAP', k, v.name)

# ---------------------------------------------------------------- scene

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = scene.render.resolution_y = TILE
world = bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.36, 0.32, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.6
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
sun_data = bpy.data.lights.new('sun', 'SUN'); sun_data.energy = 3.0
sun = bpy.data.objects.new('sun', sun_data); scene.collection.objects.link(sun)

def bounds():
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps)
    pts = [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
    ev.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

REST_LO, REST_HI = bounds()
SIZE = max(REST_HI - REST_LO) * 1.25
CENTER = (REST_LO + REST_HI) / 2

def shoot(angle, path, center=None):
    """angle 0 = the model's front, 90 = its right-hand side as seen from the front's left..."""
    c = center or CENTER
    base = math.atan2(FRONT.x, FRONT.y)
    a = base + math.radians(angle)
    d = SIZE * 3
    cam_data.ortho_scale = SIZE
    cam.location = c + Vector((d * math.sin(a), d * math.cos(a), 0))
    cam.rotation_euler = (math.radians(90), 0, math.pi - a)
    sun.rotation_euler = (math.radians(50), 0, math.pi - a + 0.5)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

def sheet(tiles, cols, path):
    rows = (len(tiles) + cols - 1) // cols
    img = bpy.data.images.new('sheet', TILE * cols, TILE * rows, alpha=False)
    px = [0.2] * (TILE * cols * TILE * rows * 4)
    for i, p in enumerate(tiles):
        r, c = divmod(i, cols)
        src_px = list(bpy.data.images.load(p).pixels)
        y0 = (rows - 1 - r) * TILE
        for y in range(TILE):
            a = y * TILE * 4
            b = ((y0 + y) * TILE * cols + c * TILE) * 4
            px[b:b + TILE * 4] = src_px[a:a + TILE * 4]
    img.pixels = px
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    print('SHEET', path)

tmp = prefix + '_tiles'
os.makedirs(tmp, exist_ok=True)
original = [s.material for s in body.material_slots]

def material(name, color, alpha=1.0, emit=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Alpha'].default_value = alpha
    if emit:
        bsdf.inputs['Emission Color'].default_value = color
        bsdf.inputs['Emission Strength'].default_value = 2.0
    if alpha < 1:
        m.surface_render_method = 'BLENDED'
    return m

def set_body(mat):
    for i, s in enumerate(body.material_slots):
        s.material = mat if mat else original[i]

# ---------------------------------------------------------------- 1. skeleton

ghost = material('ghost', (0.8, 0.78, 0.74, 1), alpha=0.25)
joint_mat = material('joint', (1.0, 0.85, 0.1, 1), emit=True)
bone_mat = material('bone', (0.1, 0.8, 1.0, 1), emit=True)
helpers = []
r = SIZE * 0.008
for b in bones:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 1.6, location=head(b), segments=12, ring_count=8)
    s = bpy.context.object; s.data.materials.append(joint_mat); s.show_in_front = True; helpers.append(s)
    for c in b.children:
        p, q = head(b), head(c)
        v = q - p
        if v.length < 1e-6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.6, depth=v.length, location=(p + q) / 2, vertices=8)
        cyl = bpy.context.object
        cyl.rotation_mode = 'QUATERNION'
        cyl.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(v)
        cyl.data.materials.append(bone_mat); helpers.append(cyl)
set_body(ghost)
tiles = []
for ang in (0, 90):
    p = os.path.join(tmp, f'skel_{ang}.png'); shoot(ang, p); tiles.append(p)
sheet(tiles, 2, prefix + '-skeleton.png')
for h in helpers:
    bpy.data.objects.remove(h)

# ---------------------------------------------------------------- 2. weights

heat = bpy.data.materials.new('heat'); heat.use_nodes = True
nt = heat.node_tree
attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'w'
emit = nt.nodes.new('ShaderNodeEmission')
nt.links.new(attr.outputs['Color'], emit.inputs['Color'])
nt.links.new(emit.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
col = body.data.color_attributes.new('w', 'FLOAT_COLOR', 'POINT')

def ramp(w):   # blue -> green -> red
    return (min(1, 2 * w) if w > 0.5 else 0, min(1, 2 * w) if w <= 0.5 else 2 - 2 * w, max(0, 1 - 2 * w), 1)

set_body(heat)
shown = [k for k in ('head', 'chest', 'upperarm_a', 'forearm_a', 'hand_a', 'thigh_a', 'shin_a', 'thigh_b') if k in MAP]
tiles = []
for k in shown:
    g = body.vertex_groups.get(MAP[k].name)
    for v in body.data.vertices:
        w = next((x.weight for x in v.groups if g is not None and x.group == g.index), 0.0)
        col.data[v.index].color = ramp(w)
    p = os.path.join(tmp, f'w_{k}.png'); shoot(0, p); tiles.append(p)
sheet(tiles, 4, prefix + '-weights.png')

# ---------------------------------------------------------------- 3. poses

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
P = arm.pose.bones

def rotate(name, axis, deg):
    """Rotate a mapped bone about a world axis through its joint."""
    pb = P[MAP[name].name]
    bpy.context.view_layer.update()
    mw = W @ pb.matrix
    pivot = mw.to_translation()
    R = Matrix.Translation(pivot) @ Quaternion(axis, math.radians(deg)).to_matrix().to_4x4() @ Matrix.Translation(-pivot)
    pb.matrix = W.inverted() @ (R @ mw)
    bpy.context.view_layer.update()

def aim(name, child_name, direction):
    """Swing a mapped bone so its child's joint lies along a world direction."""
    bpy.context.view_layer.update()
    pb, cb = P[MAP[name].name], P[MAP[child_name].name]
    a, b = (W @ pb.matrix).to_translation(), (W @ cb.matrix).to_translation()
    q = (b - a).rotation_difference(Vector(direction).normalized())
    axis, ang = q.to_axis_angle()
    rotate(name, axis, math.degrees(ang))

def reset():
    for pb in P:
        pb.matrix_basis = Matrix()
    bpy.context.view_layer.update()

side = Vector((1, 0, 0))
up = Vector((0, 0, 1))
F = FRONT
def out(s):   # lateral direction of side a / b (a is the -x side)
    return -side if s == 'a' else side

poses = {
    'rest': lambda: None,
    'arms up': lambda: [aim(f'upperarm_{s}', f'forearm_{s}', out(s) * 0.5 + up * 0.85) for s in 'ab']
                       + [aim(f'forearm_{s}', f'hand_{s}', out(s) * 0.2 + up * 0.5 + F * 0.8) for s in 'ab'],
    'lunge': lambda: [aim('thigh_a', 'shin_a', F * 0.75 - up * 0.65), aim('shin_a', 'foot_a', -F * 0.15 - up),
                      aim('thigh_b', 'shin_b', -F * 0.35 - up), aim('shin_b', 'foot_b', -F * 0.75 - up * 0.65)],
    'twist': lambda: [rotate('chest', up, 35), rotate('head', up, 40), rotate('spine', side, 15)],
}
set_body(None)
tiles_top, tiles_bottom = [], []
for name, pose in poses.items():
    reset()
    pose()
    bpy.context.view_layer.update()
    lo, hi = bounds()
    c = (lo + hi) / 2
    p = os.path.join(tmp, f'pose_{name}_tex.png'); shoot(-35, p, c); tiles_top.append(p)
    set_body(material('clay', (0.75, 0.72, 0.68, 1)))
    p = os.path.join(tmp, f'pose_{name}_clay.png'); shoot(90, p, c); tiles_bottom.append(p)
    set_body(None)
sheet(tiles_top + tiles_bottom, len(poses), prefix + '-poses.png')
