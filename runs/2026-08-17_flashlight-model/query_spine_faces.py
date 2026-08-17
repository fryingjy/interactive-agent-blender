"""Read-only: identify the long thin near-axis 'spine' faces created by
revolve_closed_profile's implicit wraparound closing edge, and the two
small near-axis boundary rings at the tail/front tips."""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "blender_ops"))

import persistent_ids  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
blend_path = argv[0]
name = argv[1]

bpy.ops.wm.open_mainfile(filepath=blend_path)
obj = bpy.data.objects[name]
me = obj.data

id_maps = persistent_ids.get_id_maps(name)
face_id_to_index = id_maps["faces"]["index_to_id"]

spine_face_ids = []
for poly in me.polygons:
    radii = [(me.vertices[v].co.x ** 2 + me.vertices[v].co.y ** 2) ** 0.5 for v in poly.vertices]
    if all(r < 0.5 for r in radii):
        aid = face_id_to_index.get(poly.index)
        if aid:
            spine_face_ids.append(aid)

print(json.dumps({"spine_face_count": len(spine_face_ids), "spine_face_ids": spine_face_ids}))
