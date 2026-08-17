"""Live proof for generic connected front-to-rear profile loft construction."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from blender_ops.modeler_server import ModelerServer
from blender_ops.state_probe import mesh_health


def main() -> None:
    output = ROOT / "runs" / "2026-08-16_profile-loft-lab"
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    front = [(-1.4, -1.0), (1.4, -1.0), (1.2, 0.4), (0.7, 1.0), (-1.1, 1.0)]
    rear = [(-1.25, -1.0), (1.25, -1.0), (1.05, 0.15), (0.5, 0.72), (-0.9, 0.72)]
    server = ModelerServer()
    result = server.cmd_create_profile_loft("Measured_Profile_Loft", front, rear, 0.8)
    obj = bpy.data.objects[result["name"]]
    health = mesh_health(obj.name)
    report = {
        "record_type": "PROFILE_LOFT_RUNTIME_LAB",
        "claim_boundary": "Proves generic connected profile-loft construction only; it does not establish an asset's reference likeness or final topology quality.",
        "front_profile": front,
        "rear_profile": rear,
        "result": result,
        "mesh_health": health,
        "checks": {
            "single_mesh": len([item for item in bpy.data.objects if item.type == "MESH"]) == 1,
            "manifold": health["non_manifold_edges"] == 0,
            "all_bridge_walls_quad": sum(len(face.vertices) == 4 for face in obj.data.polygons) == len(front),
            "cap_ngons_explicit": result["cap_topology"] == "NGON" and health["ngons"] == 2,
            "persistent_ids": all(name in obj.data.attributes for name in ("agent_vertex_id", "agent_edge_id", "agent_face_id")),
        },
    }
    report["pass"] = all(report["checks"].values())
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "profile_loft_lab.blend"))
    print("PROFILE_LOFT_LAB:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
