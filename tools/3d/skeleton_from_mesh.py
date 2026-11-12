#!/usr/bin/env python3
"""Compute a skeleton from a mesh by level sets of surface distance (a Reeb graph).

Distances are measured along the surface outward from a seed region (the torso barrel).
Vertices are grouped into bands of equal distance; each connected piece of a band is a
ring around one limb, and its centroid becomes a joint. Linking rings of neighbouring
bands gives a tree: legs, head, ears and every tail come out as chains.

Usage: skeleton_from_mesh.py WORK X_MIN X_MAX Z_MAX [step]
  seed = vertices with X_MIN <= x <= X_MAX and z <= Z_MAX (the body between the leg pairs)
Writes WORK/skeleton.json (nodes: id, parent, level, centroid, count) and
WORK/skeleton.npz (node id per vertex, surface distance per vertex).
"""
import json
import sys

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components, dijkstra

work = sys.argv[1]
x_min, x_max, z_max = map(float, sys.argv[2:5])
step = float(sys.argv[5]) if len(sys.argv) > 5 else 0.07

data = np.load(f"{work}/mesh.npz")
V, E = data["verts"], data["edges"]
n = len(V)
length = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
graph = sp.coo_matrix((np.r_[length, length], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()

seed = np.nonzero((V[:, 0] >= x_min) & (V[:, 0] <= x_max) & (V[:, 2] <= z_max))[0]
dist = dijkstra(graph, indices=seed, min_only=True)
level = np.floor(dist / step).astype(int)
level[np.isinf(dist)] = -1

node_of = np.full(n, -1)
nodes = []
same = level[E[:, 0]] == level[E[:, 1]]
within = sp.coo_matrix((np.ones(same.sum()), (E[same, 0], E[same, 1])), shape=(n, n))
_, comp = connected_components(within, directed=False)
for lv in range(level.max() + 1):
    idx = np.nonzero(level == lv)[0]
    for c in np.unique(comp[idx]):
        members = idx[comp[idx] == c]
        node_of[members] = len(nodes)
        nodes.append({"id": len(nodes), "level": lv, "centroid": V[members].mean(axis=0).tolist(), "count": int(len(members))})

# Parent = the node one band closer to the seed that shares the most mesh edges.
a, b = node_of[E[:, 0]], node_of[E[:, 1]]
links = {}
for u, v in zip(a, b):
    if u < 0 or v < 0 or u == v:
        continue
    lu, lv = nodes[u]["level"], nodes[v]["level"]
    if abs(lu - lv) == 1:
        child, parent = (u, v) if lu > lv else (v, u)
        links.setdefault(int(child), {}).setdefault(int(parent), 0)
        links[int(child)][int(parent)] += 1
for node in nodes:
    cand = links.get(node["id"])
    node["parent"] = max(cand, key=cand.get) if cand else None

json.dump({"step": step, "nodes": nodes}, open(f"{work}/skeleton.json", "w"))
np.savez(f"{work}/skeleton.npz", node_of=node_of, dist=dist)
children = {}
for node in nodes:
    children.setdefault(node["parent"], []).append(node["id"])
leaves = [nd for nd in nodes if nd["id"] not in children]
print(f"{len(nodes)} nodes, {len(leaves)} branch tips, seed {len(seed)} vertices, max level {level.max()}")
for leaf in sorted(leaves, key=lambda nd: -nd["level"]):
    if leaf["count"] >= 15:
        print("tip", leaf["id"], "level", leaf["level"], "at", [round(c, 2) for c in leaf["centroid"]], "verts", leaf["count"])
