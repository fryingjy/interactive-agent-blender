"""Fresh-process verifier for the saved Connect Vertex Path lab scene."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bmesh
import bpy


def topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    remaining = set(bm.verts)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
    result = {
        "verts": len(bm.verts), "edges": len(bm.edges), "faces": len(bm.faces),
        "face_sizes": sorted(len(face.verts) for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "loose_vertices": sum(not vertex.link_edges for vertex in bm.verts),
        "loose_edges": sum(not edge.link_faces for edge in bm.edges),
        "components": components,
    }
    bm.free()
    return result


def persistent_ids(obj):
    result = {}
    for kind, attribute_name in (
        ("verts", "agent_vertex_id"),
        ("edges", "agent_edge_id"),
        ("faces", "agent_face_id"),
    ):
        attribute = obj.data.attributes.get(attribute_name)
        values = [int(item.value) for item in attribute.data] if attribute else []
        result[kind] = {
            "count": len(values),
            "positive": bool(values) and all(value > 0 for value in values),
            "unique": len(values) == len(set(values)),
        }
    return result


def check(name, expected):
    obj = bpy.data.objects.get(name)
    assert obj is not None, f"missing object {name}"
    measured = topology(obj)
    for key, value in expected.items():
        assert measured[key] == value, f"{name} {key}: expected {value}, got {measured[key]}"
    ids = persistent_ids(obj)
    assert all(domain["positive"] and domain["unique"] for domain in ids.values()), ids
    return {"object": name, "topology": measured, "persistent_ids": ids}


def main():
    separator = sys.argv.index("--") if "--" in sys.argv else len(sys.argv)
    args = sys.argv[separator + 1:]
    output = Path(args[0]) if args else Path(bpy.data.filepath).with_name("connect_vertex_path_fresh_verification.json")
    checks = []
    checks.append(check("Connect_Hex_AllQuad", {
        "verts": 6, "edges": 7, "faces": 2, "face_sizes": [4, 4], "ngons": 0,
        "degenerate_faces": 0, "loose_vertices": 0, "loose_edges": 0, "components": 1,
    }))
    checks.append(check("Connect_ThreeFace_Strip", {
        "verts": 10, "edges": 15, "faces": 6, "face_sizes": [3, 3, 4, 4, 4, 4], "ngons": 0,
        "degenerate_faces": 0, "loose_vertices": 0, "loose_edges": 0, "components": 1,
    }))
    checks.append(check("Connect_Live_EditMode", {
        "verts": 6, "edges": 7, "faces": 2, "face_sizes": [4, 4], "ngons": 0,
        "degenerate_faces": 0, "loose_vertices": 0, "loose_edges": 0, "components": 1,
    }))
    checks.append(check("Reject_AlreadyConnected", {
        "verts": 4, "edges": 4, "faces": 1, "face_sizes": [4], "ngons": 0,
        "degenerate_faces": 0, "loose_vertices": 0, "loose_edges": 0, "components": 1,
    }))
    checks.append(check("Reject_Disconnected", {
        "verts": 8, "edges": 8, "faces": 2, "face_sizes": [4, 4], "ngons": 0,
        "degenerate_faces": 0, "loose_vertices": 0, "loose_edges": 0, "components": 2,
    }))
    report = {
        "verification": "fresh_process_connect_vertex_path",
        "blend": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "checks": checks,
        "passed": len(checks),
        "total": 5,
        "pass": len(checks) == 5,
    }
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CONNECT_VERTEX_PATH_FRESH_VERIFY:" + json.dumps(report))


if __name__ == "__main__":
    main()
