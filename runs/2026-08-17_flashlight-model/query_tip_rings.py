"""Read-only: identify the tail-tip and front-tip near-axis ring edges
(both endpoints near-axis AND at the same z), distinct from the long
opposite-z 'spine' edges."""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender_ops"))
import persistent_ids  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
blend_path = argv[0]
name = argv[1]

bpy.ops.wm.open_mainfile(filepath=blend_path)
obj = bpy.data.objects[name]
me = obj.data

id_maps = persistent_ids.get_id_maps(name)
edge_id_to_index = id_maps["edges"]["index_to_id"]

tail_ring = []
front_ring = []
for edge in me.edges:
    v1, v2 = edge.vertices
    c1, c2 = me.vertices[v1].co, me.vertices[v2].co
    r1 = (c1.x ** 2 + c1.y ** 2) ** 0.5
    r2 = (c2.x ** 2 + c2.y ** 2) ** 0.5
    if r1 < 0.5 and r2 < 0.5 and abs(c1.z - c2.z) < 0.01:
        aid = edge_id_to_index.get(edge.index)
        if aid:
            if abs(c1.z) < 1.0:
                tail_ring.append(aid)
            else:
                front_ring.append(aid)

print(json.dumps({
    "tail_ring_count": len(tail_ring), "tail_ring_ids": tail_ring,
    "front_ring_count": len(front_ring), "front_ring_ids": front_ring,
}))
