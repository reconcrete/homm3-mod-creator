"""Write the prepared model's vertices and edges to mesh.npz.

Run: blender -b WORK/prepared.blend -P tools/3d/export_mesh.py -- WORK
"""
import sys

import bpy
import numpy as np

work = sys.argv[sys.argv.index("--") + 1]
mesh = bpy.data.objects["Body"].data
verts = np.zeros(len(mesh.vertices) * 3)
mesh.vertices.foreach_get("co", verts)
edges = np.zeros(len(mesh.edges) * 2, dtype=np.int64)
mesh.edges.foreach_get("vertices", edges)
np.savez(f"{work}/mesh.npz", verts=verts.reshape(-1, 3), edges=edges.reshape(-1, 2))
print("EXPORTED", len(mesh.vertices), len(mesh.edges))
