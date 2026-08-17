"""Live verification for one connected all-quad shell with an integrated opening."""

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


def grid(y):
    xs, zs = (-1.5, -0.5, 0.5, 1.5), (-1.0, -0.2, 0.6, 1.0)
    return [[[x, y, z] for x in xs] for z in zs]


def main() -> None:
    output = ROOT / "runs" / "2026-08-16_quad-shell-grid-lab"
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    server = ModelerServer()
    # Bottom-center omitted cell leaves an integrated U opening.
    cells = [[True, False, True], [True, True, True], [True, True, True]]
    result = server.cmd_create_quad_shell_grid("Quad_Opening_Shell", grid(-0.4), grid(0.4), cells)
    obj = bpy.data.objects[result["name"]]
    health = mesh_health(obj.name)
    boundary_edges = 0
    for row, values in enumerate(cells):
        for column, active in enumerate(values):
            if not active:
                continue
            for neighbor_row, neighbor_column in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
                if (
                    neighbor_row < 0 or neighbor_row >= len(cells)
                    or neighbor_column < 0 or neighbor_column >= len(values)
                    or not cells[neighbor_row][neighbor_column]
                ):
                    boundary_edges += 1
    report = {
        "record_type": "QUAD_SHELL_GRID_RUNTIME_LAB",
        "claim_boundary": "Proves generic all-quad connected-shell construction with an opening; it does not prove visual reference fidelity.",
        "result": result,
        "mesh_health": health,
        "checks": {
            "single_mesh": len([item for item in bpy.data.objects if item.type == "MESH"]) == 1,
            "manifold": health["non_manifold_edges"] == 0,
            "all_base_faces_quads": health["ngons"] == 0,
            "opening_preserved": len(obj.data.polygons) == 2 * result["active_cell_count"] + boundary_edges,
            "persistent_ids": all(name in obj.data.attributes for name in ("agent_vertex_id", "agent_edge_id", "agent_face_id")),
        },
    }
    report["pass"] = all(report["checks"].values())
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "quad_shell_grid_lab.blend"))
    print("QUAD_SHELL_GRID_LAB:" + json.dumps(report))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
