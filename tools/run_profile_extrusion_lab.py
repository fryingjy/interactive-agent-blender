"""Live Blender proof for the generic connected profile-extrusion operation.

This fixture intentionally uses an abstract measured trapezoid rather than a
product silhouette. It proves construction/editability only; it is not a
reference-likeness benchmark or an asset builder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "blender_ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from modeler_server import ModelerServer
from state_probe import mesh_health


def main() -> None:
    output = ROOT / "runs" / "2026-08-16_profile-extrusion-lab"
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    server = ModelerServer()
    profile = [(-1.4, -0.9), (1.4, -0.9), (1.2, 0.25), (0.8, 0.9), (-1.05, 0.9)]
    result = server.cmd_create_profile_extrusion("Measured_Profile_Cage", profile, 0.6)
    obj = bpy.data.objects["Measured_Profile_Cage"]
    health = mesh_health(obj.name)
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}
    for edge in obj.data.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    visited = set()
    pending = [next(iter(adjacency))]
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(adjacency[current] - visited)
    report = {
        "record_type": "PROFILE_EXTRUSION_RUNTIME_LAB",
        "claim_boundary": "Proves a generic connected profile cage can be created and inspected through the typed server; it does not prove artistic reference fidelity.",
        "profile": profile,
        "result": result,
        "mesh_health": health,
        "checks": {
            "one_mesh_object": len([item for item in bpy.data.objects if item.type == "MESH"]) == 1,
            "connected": len(visited) == len(adjacency),
            "manifold": health["non_manifold_edges"] == 0,
            "side_faces_are_quads": sum(len(poly.vertices) == 4 for poly in obj.data.polygons) == len(profile),
            "persistent_ids_assigned": all(
                attr in obj.data.attributes
                for attr in ("agent_vertex_id", "agent_edge_id", "agent_face_id")
            ),
            "caps_explicitly_recorded_as_ngons": result["cap_topology"] == "NGON",
        },
    }
    report["pass"] = all(report["checks"].values())
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "profile_extrusion_lab.blend"))
    print("PROFILE_EXTRUSION_LAB:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
