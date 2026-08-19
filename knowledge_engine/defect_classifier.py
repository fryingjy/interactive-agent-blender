"""Turn raw observed geometry into semantic defect tickets the knowledge base can key on.

Why this module exists (2026-08-19 audit finding):

`blender_ops.evaluated_probe.evaluated_defect_regions` reports *statistical* anomalies --
`area_outlier` and `high_angle` -- and honestly documents that it cannot distinguish a real
defect from healthy curvature. Skills, meanwhile, declared `planner_hint.trigger_ticket_types`
in an *intent* vocabulary (`multi_edge_corner_bevel`, `local_feature_extrusion_on_coarse_surface`).
Those two vocabularies are disjoint, so no skill could ever fire from observation. The recorded
runtime-validation evidence had bridged the gap only by hand-authoring a ticket whose type string
was copied out of the skill's own trigger list -- i.e. the test supplied the answer it then
asserted. `tools/audit_observation_to_skill_gap.py` reproduces that failure.

The fix is not to make the statistical probe smarter. It is to classify geometry into *named,
structural defect conditions* that are true or false by construction rather than by threshold --
things a modeler would name out loud ("there's a triangle at that corner") and that a skill can
therefore be keyed to repair.

Design rules, kept deliberately strict:

- A ticket is emitted only when the condition is structurally decidable from topology, not from a
  tuned severity score. `corner_triangle` is exact: a 3-vertex face all of whose vertices sit on a
  corner where 3+ edges converge either is or is not present.
- Every ticket carries the persistent agent IDs of the elements involved, so the planner's
  downstream selection is scene-owned and the skill never has to guess a target.
- No ticket carries `operation_params`. Repair parameters are technique knowledge and belong to
  the skill (see `planner._skill_guided_ticket_decision`). A classifier that also supplied the fix
  parameters would recreate the same circularity in a new place.
- Unknown/ambiguous geometry emits nothing. Silence is correct when the condition is not decidable.
"""

from __future__ import annotations

from typing import Any


def classify_corner_triangles(
    faces: list[dict[str, Any]],
    vertex_edge_valence: dict[int, int],
    *,
    minimum_corner_valence: int = 3,
) -> list[dict[str, Any]]:
    """Emit one `corner_triangle` ticket per triangle sitting at a multi-edge corner.

    ``faces`` is a list of ``{"agent_id": int, "vertex_ids": [int, ...]}`` for the BASE cage
    (not the evaluated mesh -- the repair operates on the cage). ``vertex_edge_valence`` maps a
    vertex agent_id to how many edges meet at it.

    A triangle whose vertices are ordinary grid points is not necessarily a defect; a triangle
    produced where several beveled edges converge is the specific artifact the bevel-parity
    knowledge repairs. Requiring at least one vertex at/above ``minimum_corner_valence`` keeps
    this to the corner case rather than flagging every triangle in any mesh.
    """
    tickets = []
    for face in faces:
        vertex_ids = list(face.get("vertex_ids", []))
        if len(vertex_ids) != 3:
            continue
        corner_vertices = sorted(
            vid for vid in vertex_ids
            if vertex_edge_valence.get(vid, 0) >= minimum_corner_valence
        )
        if not corner_vertices:
            continue
        tickets.append({
            "type": "corner_triangle",
            "target": f"corner_triangle_face_{face['agent_id']}",
            "face_ids": [face["agent_id"]],
            "vertex_ids": sorted(vertex_ids),
            "corner_vertex_ids": corner_vertices,
            "priority": 1,
            "severity": 0.7,
            "observed": (
                "a 3-vertex face is present where "
                f"{len(corner_vertices)} of its vertices sit on a corner with "
                f"{minimum_corner_valence}+ converging edges"
            ),
        })
    return tickets


def classify_geometry(
    faces: list[dict[str, Any]],
    vertex_edge_valence: dict[int, int],
) -> dict[str, Any]:
    """Run every available structural classifier over one base cage.

    Returns the ticket list plus the vocabulary actually produced, so a caller can assert
    against skill trigger vocabularies without re-deriving it.
    """
    tickets: list[dict[str, Any]] = []
    tickets.extend(classify_corner_triangles(faces, vertex_edge_valence))
    tickets.sort(key=lambda t: (int(t.get("priority", 10**6)), -float(t.get("severity", 0.0)), str(t.get("target"))))
    return {
        "tickets": tickets,
        "ticket_types": sorted({t["type"] for t in tickets}),
        "claim_boundary": (
            "Structural classification only. A ticket asserts a named topological condition is "
            "present, not that it is visually objectionable in context, and carries no repair "
            "parameters -- those are technique knowledge owned by the retrieved skill."
        ),
    }
