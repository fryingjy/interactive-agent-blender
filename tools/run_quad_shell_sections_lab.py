"""Live verification for an all-quad shell with a controlled depth rollover."""

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


def grid(y, top_offset=0.0):
    xs, zs = (-1.5, -0.5, 0.5, 1.5), (-1.0, -0.2, 0.6, 1.0)
    return [[[x, y, z + (top_offset if row >= 2 else 0.0)] for x in xs] for row, z in enumerate(zs)]


def main() -> None:
    output = ROOT / "runs" / "2026-08-16_quad-shell-sections-lab"
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    cells = [[True, False, True], [True, True, True], [True, True, True]]
    result = ModelerServer().cmd_create_quad_shell_sections(
        "Sectioned_Quad_Opening_Shell", [grid(-0.5), grid(0.0, 0.35), grid(0.5)], cells
    )
    obj = bpy.data.objects[result["name"]]
    health = mesh_health(obj.name)
    report = {
        "record_type": "QUAD_SHELL_SECTIONS_RUNTIME_LAB",
        "claim_boundary": "Proves generic all-quad multi-section construction; it does not prove a target matches a reference.",
        "result": result,
        "mesh_health": health,
        "checks": {
            "single_mesh": len([item for item in bpy.data.objects if item.type == "MESH"]) == 1,
            "manifold": health["non_manifold_edges"] == 0,
            "all_base_faces_quads": health["ngons"] == 0,
            "no_loose_vertices": health["loose_verts"] == 0,
            "persistent_ids": all(name in obj.data.attributes for name in ("agent_vertex_id", "agent_edge_id", "agent_face_id")),
            "intermediate_section_changed_top_height": max(v.co.z for v in obj.data.vertices) > 1.0,
        },
    }
    report["pass"] = all(report["checks"].values())
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "quad_shell_sections_lab.blend"))
    print("QUAD_SHELL_SECTIONS_LAB:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
