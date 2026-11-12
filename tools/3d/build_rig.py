#!/usr/bin/env python3
"""Turn the mesh skeleton into a rig description: bones, body-part groups, skin weights.

Usage: build_rig.py WORK
Reads WORK/skeleton.json, skeleton.npz, mesh.npz. Writes WORK/rig.json (bones) and
WORK/rig.npz (per-vertex bone indices and weights, up to 4 per vertex).

Body parts are assigned by where a joint sits (quadruped facing +X):
  leg_fl / leg_fr / leg_rl / leg_rr, head, tail, torso.
"""
import json
import sys

import numpy as np
import scipy.sparse as sp

work = sys.argv[1]
skel = json.load(open(f"{work}/skeleton.json"))
nodes = skel["nodes"]
arr = np.load(f"{work}/skeleton.npz")
node_of = arr["node_of"].copy()
mesh = np.load(f"{work}/mesh.npz")
V, E = mesh["verts"], mesh["edges"]

children = {}
for nd in nodes:
    children.setdefault(nd["parent"], []).append(nd["id"])

# Fold tiny leaf joints (claw tips, fur spikes) into their parents.
alive = {nd["id"] for nd in nodes}
merged_into = {}
changed = True
while changed:
    changed = False
    for nd in nodes:
        i = nd["id"]
        if i not in alive or nd["parent"] is None:
            continue
        kids = [k for k in children.get(i, []) if k in alive]
        if not kids and nd["count"] < 30:
            alive.discard(i)
            merged_into[i] = nd["parent"]
            nodes[nd["parent"]]["count"] += nd["count"]
            changed = True


def resolve(i):
    while i in merged_into:
        i = merged_into[i]
    return i


def part_of(c):
    x, y, z = c
    if z < 0.42 and x > -0.25:
        if x > 0.4:
            return "leg_fl" if y > 0 else "leg_fr"
        if x < 0.32:
            return "leg_rl" if y > 0 else "leg_rr"
    if x > 0.55 and z >= 0.42:
        return "head"
    if x < 0.36 and (z > 0.75 or x < -0.22):
        return "tail"
    return "torso"


roots = [nd["id"] for nd in nodes if nd["parent"] is None and nd["id"] in alive]
root_pos = np.average([nodes[r]["centroid"] for r in roots], axis=0, weights=[nodes[r]["count"] for r in roots])

bones = [{"name": "Root", "parent": None, "head": (root_pos - np.array([0.12, 0, 0])).tolist(),
          "tail": root_pos.tolist(), "part": "root", "depth": 0, "chain": 0}]
bone_of_node = {}
order = sorted(alive, key=lambda i: nodes[i]["level"])
for i in order:
    nd = nodes[i]
    if nd["parent"] is None:
        bone_of_node[i] = 0
        continue
    parent_bone = bone_of_node[resolve(nd["parent"])]
    head = bones[parent_bone]["tail"]
    tail = nd["centroid"]
    if np.linalg.norm(np.subtract(tail, head)) < 0.012:
        bone_of_node[i] = parent_bone
        continue
    part = part_of(tail)
    pb = bones[parent_bone]
    same = pb["part"] == part
    bones.append({"name": f"{part}_{len(bones):03d}", "parent": parent_bone, "head": head, "tail": tail,
                  "part": part, "depth": pb["depth"] + 1 if same else 0,
                  "chain": pb["chain"] if same else len(bones)})
    bone_of_node[i] = len(bones) - 1

vert_bone = np.array([bone_of_node[resolve(int(i))] if i >= 0 else 0 for i in node_of])

# Legs get their own chains from shoulder / hip down to the paw, sliced by height. The
# surface-distance rings only separate a leg from the body below the elbow, which leaves
# the shoulders and haunches rigid.
LEG_TOP, LEG_BAND = 0.56, 0.08
tail_vert = np.array([bones[b]["part"] == "tail" for b in vert_bone])
side = np.abs(V[:, 1]) > 0.12
low = V[:, 2] < LEG_TOP
regions = {
    "leg_fl": (V[:, 0] > 0.40) & side & low & (V[:, 1] > 0),
    "leg_fr": (V[:, 0] > 0.40) & side & low & (V[:, 1] < 0),
    "leg_rl": (V[:, 0] > -0.25) & (V[:, 0] < 0.33) & side & low & (V[:, 1] > 0) & ~tail_vert,
    "leg_rr": (V[:, 0] > -0.25) & (V[:, 0] < 0.33) & side & low & (V[:, 1] < 0) & ~tail_vert,
}
# Whatever the ring skeleton already called a leg belongs to the leg too (the inner side
# of a leg fails the "side" test above and would otherwise stay glued to the body).
old_part = np.array([bones[b]["part"] for b in vert_bone])
for part in regions:
    span = (V[:, 0] > 0.40) & (V[:, 0] < 0.80) if part in ("leg_fl", "leg_fr") else (V[:, 0] > -0.25) & (V[:, 0] < 0.33)
    regions[part] = (regions[part] | ((old_part == part) & span)) & low
for bn in bones:
    if bn["part"].startswith("leg_"):
        bn["part"] = "unused"
# Lower jaw: one bone hinged at the mouth corner, so the creature can snap.
jaw = np.nonzero((V[:, 0] > 0.775) & (V[:, 2] < 0.405) & (np.abs(V[:, 1]) < 0.13) & (V[:, 2] > 0.3))[0]
if len(jaw) > 30:
    owner = int(np.bincount(vert_bone[jaw]).argmax())
    tip = V[jaw][V[jaw][:, 0] > np.percentile(V[jaw][:, 0], 80)].mean(axis=0)
    bones.append({"name": "jaw", "parent": owner, "head": [0.775, 0.0, 0.43], "tail": tip.tolist(),
                  "part": "jaw", "depth": 0, "chain": len(bones)})
    vert_bone[jaw] = len(bones) - 1
    print("jaw vertices", len(jaw))

paws = {}
for part, mask in regions.items():
    band = np.floor((LEG_TOP - V[:, 2]) / LEG_BAND).astype(int)
    joints, members = [], []
    for k in range(int(LEG_TOP / LEG_BAND) + 1):
        sel = np.nonzero(mask & (band == k))[0]
        if len(sel) >= 10:
            joints.append(V[sel].mean(axis=0))
            members.append(sel)
    first = len(bones)
    count = len(joints) - 1
    for k in range(count):
        bones.append({"name": f"{part}_{k}", "parent": 0 if k == 0 else len(bones) - 1,
                      "head": joints[k].tolist(), "tail": joints[k + 1].tolist(),
                      "part": part, "depth": k, "chain": first, "chain_len": count})
    # The top slice stays with the body (it is flank and chest); the leg starts below it.
    for k, sel in enumerate(members):
        if k >= 1:
            vert_bone[sel] = first + min(k - 1, count - 1)
    paws[part] = members[-1]

# Smooth the hard assignment over the surface so joints bend instead of tearing.
n, b = len(V), len(bones)
W = sp.csr_matrix((np.ones(n), (np.arange(n), vert_bone)), shape=(n, b))
A = sp.coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
deg = np.asarray(A.sum(axis=1)).ravel()
A = sp.diags(1.0 / np.maximum(deg, 1)) @ A
for _ in range(10):
    W = (0.5 * W + 0.5 * (A @ W)).tocsr()
W = W.toarray()
top = np.argsort(-W, axis=1)[:, :4]
weights = np.take_along_axis(W, top, axis=1)
weights /= weights.sum(axis=1, keepdims=True)

json.dump({"bones": bones}, open(f"{work}/rig.json", "w"))
np.savez(f"{work}/rig.npz", bone_idx=top, bone_w=weights, **{f"paw_{k}": v for k, v in paws.items()})
parts = {}
for bn in bones:
    parts[bn["part"]] = parts.get(bn["part"], 0) + 1
print(len(bones), "bones", parts)
print("chains:", {p: len({bn["chain"] for bn in bones if bn["part"] == p}) for p in parts})
