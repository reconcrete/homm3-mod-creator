"""Recognise the parts of a humanoid skeleton by structure (Blender), whatever the bones are called.

map_bones(arm) -> {'hips', 'spine': [bones from hips up to the chest], 'chest', 'neck', 'head',
                   'collar_a', 'upperarm_a', 'forearm_a', 'hand_a', 'thigh_a', 'shin_a', 'foot_a',
                   'toe_a', ... the same for _b}: bpy Bone objects. Side a has the smaller x
(world space). SkinTokens names its bones bone_N, so names can't be used; Mixamo rigs have
names too (MIXAMO below), which the structure agrees with.
"""
from mathutils import Vector

MIXAMO = {'hips': 'Hips', 'neck': 'Neck', 'head': 'Head', 'spine': ['Spine', 'Spine1', 'Spine2'],
          'collar': 'Shoulder', 'upperarm': 'Arm', 'forearm': 'ForeArm', 'hand': 'Hand',
          'thigh': 'UpLeg', 'shin': 'Leg', 'foot': 'Foot', 'toe': 'ToeBase'}

def map_bones(arm):
    W = arm.matrix_world

    def head(b):
        return W @ b.head_local

    def top(b):   # the highest joint in b's branch
        z, stack = head(b).z, [b]
        while stack:
            c = stack.pop()
            z = max(z, head(c).z)
            stack += list(c.children)
        return z

    def extremity(b):   # the joint in b's branch furthest from b
        best, d, stack = b, 0, [b]
        while stack:
            c = stack.pop()
            dd = (head(c) - head(b)).length
            if dd > d:
                best, d = c, dd
            stack += list(c.children)
        return head(best)

    def chain(b, pick):
        out = [b]
        while b.children:
            b = pick(b.children)
            out.append(b)
        return out

    bones = arm.data.bones
    root = next(b for b in bones if b.parent is None)
    ups = [c for c in root.children if top(c) > head(root).z]
    downs = [c for c in root.children if top(c) <= head(root).z]
    if len(ups) != 1 or len(downs) != 2:
        raise ValueError(f'not a humanoid layout: {len(ups)} up, {len(downs)} down from {root.name}')
    spine, b = [], ups[0]
    while True:
        spine.append(b)
        kids = list(b.children)
        if not kids:
            raise ValueError('no arms found off the spine')
        up = max(kids, key=top)
        side = [c for c in kids if c is not up and abs(extremity(c).x - head(b).x) > 0.1 * (extremity(c) - head(b)).length]
        if len(side) == 2:
            neck_head = chain(up, lambda cs: max(cs, key=top))
            break
        b = up
    M = {'hips': root, 'spine': spine, 'chest': spine[-1], 'neck': neck_head[0], 'head': neck_head[-1] if len(neck_head) > 1 else neck_head[0]}
    if len(neck_head) > 2:   # the head is the last bone with real length; a short end bone is the head top
        M['head'] = neck_head[1]
    for s, start in zip('ab', sorted(side, key=lambda c: extremity(c).x)):
        ch = chain(start, lambda cs: max(cs, key=lambda c: (extremity(c) - head(c)).length))
        if len(ch) >= 4 and (head(ch[1]) - head(ch[0])).length < 0.6 * (head(ch[2]) - head(ch[1])).length:
            M[f'collar_{s}'], ch = ch[0], ch[1:]
        M[f'upperarm_{s}'], M[f'forearm_{s}'], M[f'hand_{s}'] = ch[0], ch[1], ch[2]
    for s, start in zip('ab', sorted(downs, key=lambda c: extremity(c).x)):
        ch = chain(start, lambda cs: min(cs, key=lambda c: extremity(c).z))
        M[f'thigh_{s}'], M[f'shin_{s}'], M[f'foot_{s}'] = ch[0], ch[1], ch[2]
        if len(ch) > 3:
            M[f'toe_{s}'] = ch[3]
    return M

def map_mixamo(arm, prefix='mixamorig:'):
    """The same parts by Mixamo names; side a/b by world x like map_bones."""
    B = arm.data.bones
    get = lambda n: B.get(prefix + n)
    M = {'hips': get('Hips'), 'spine': [get(n) for n in MIXAMO['spine'] if get(n)], 'neck': get('Neck'), 'head': get('Head')}
    M['chest'] = M['spine'][-1]
    lx = (arm.matrix_world @ get('LeftArm').head_local).x
    sides = {'a': 'Left', 'b': 'Right'} if lx < 0 else {'a': 'Right', 'b': 'Left'}
    for s, lr in sides.items():
        for part in ('collar', 'upperarm', 'forearm', 'hand', 'thigh', 'shin', 'foot', 'toe'):
            b = get(lr + MIXAMO[part])
            if b:
                M[f'{part}_{s}'] = b
    return M

def pairs(src_map, dst_map):
    """(source bone name, target bone name, part) for every part both skeletons have; spines are
    matched by position along the chain."""
    out = []
    for k, v in src_map.items():
        if k == 'spine':
            d = dst_map['spine']
            for i, sb in enumerate(v):
                j = round(i * (len(d) - 1) / max(1, len(v) - 1))
                out.append((sb.name, d[j].name, 'spine'))
        elif k != 'chest' and k in dst_map:
            out.append((v.name, dst_map[k].name, k))
    return out

def leg_bones(arm, M, side):
    """Every bone of one leg: thigh and all its descendants."""
    t = M[f'thigh_{side}']
    return {t.name} | {b.name for b in t.children_recursive}

def separate_legs(arm, mesh, M):
    """Below the knees, take each vertex's weights off the other leg's bones (auto-riggers bleed
    them between feet that stand close together, so one foot drags the other) and renormalise."""
    W = arm.matrix_world
    knee_z = max((W @ M[f'shin_{s}'].head_local).z for s in 'ab')
    mid_x = (W @ M['hips'].head_local).x
    bones = {s: leg_bones(arm, M, s) for s in 'ab'}
    side_x = {s: (W @ M[f'foot_{s}'].head_local).x for s in 'ab'}
    names = {g.index: g.name for g in mesh.vertex_groups}
    changed = 0
    for v in mesh.data.vertices:
        p = mesh.matrix_world @ v.co
        if p.z > knee_z:
            continue
        own = min('ab', key=lambda s: abs(p.x - side_x[s]))
        other = 'b' if own == 'a' else 'a'
        drop = [g for g in v.groups if names.get(g.group) in bones[other] and g.weight > 0]
        if not drop:
            continue
        keep = sum(g.weight for g in v.groups) - sum(g.weight for g in drop)
        for g in drop:
            mesh.vertex_groups[g.group].remove([v.index])
        if keep > 1e-6:
            for g in v.groups:
                g.weight /= keep
        changed += 1
    return changed
