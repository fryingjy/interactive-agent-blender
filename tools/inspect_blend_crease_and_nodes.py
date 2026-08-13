"""Follow-up read-only inspection: edge crease value distribution per object,
and the actual node contents of any Geometry Nodes modifier (e.g. "Auto
Smooth"), for docs/BLEND_FILE_STUDY_PROTOCOL.md's INSPECT step. Never saves.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def crease_distribution(obj):
    me = obj.data
    attr = me.attributes.get("crease_edge")
    if attr is None:
        return {"present": False}
    values = [item.value for item in attr.data]
    nonzero = [v for v in values if v > 1e-6]
    buckets = {}
    for v in nonzero:
        key = round(v, 2)
        buckets[key] = buckets.get(key, 0) + 1
    return {
        "present": True,
        "total_edges": len(values),
        "nonzero_edges": len(nonzero),
        "value_histogram": buckets,
    }


def node_group_summary(node_group):
    if node_group is None:
        return None
    nodes = []
    for n in node_group.nodes:
        entry = {"name": n.name, "type": n.type, "bl_idname": n.bl_idname}
        if n.type == "GROUP" and n.node_tree:
            entry["sub_group"] = n.node_tree.name
        inputs = {}
        for inp in n.inputs:
            if not inp.is_linked and hasattr(inp, "default_value"):
                try:
                    val = inp.default_value
                    inputs[inp.name] = list(val) if hasattr(val, "__len__") else val
                except Exception:
                    pass
        if inputs:
            entry["unlinked_input_defaults"] = inputs
        nodes.append(entry)
    return {"name": node_group.name, "node_count": len(nodes), "nodes": nodes}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    blend_path, out_path = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    report = {"blend_path": str(blend_path), "objects": {}, "node_groups": {}}
    seen_groups = set()
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        report["objects"][obj.name] = {"crease": crease_distribution(obj)}
        for m in obj.modifiers:
            if m.type == "NODES" and m.node_group and m.node_group.name not in seen_groups:
                seen_groups.add(m.node_group.name)
                report["node_groups"][m.node_group.name] = node_group_summary(m.node_group)

    out_path.write_text(json.dumps(report, indent=2))
    print("RESULT_PATH:" + str(out_path))
    print(json.dumps(report, indent=2)[:4000])


if __name__ == "__main__":
    main()
