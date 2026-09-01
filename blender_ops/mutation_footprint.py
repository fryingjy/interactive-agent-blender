"""Pure audit for localized persistent-vertex mutation contracts."""

from __future__ import annotations

import math
from typing import Mapping, Sequence


def audit_vertex_footprint(
    before: Mapping[int, Sequence[float]],
    after: Mapping[int, Sequence[float]],
    allowed_vertex_ids: set[int] | None,
    *,
    tolerance: float = 1e-6,
) -> dict:
    if allowed_vertex_ids is None:
        return {
            "enforced": False,
            "moved_existing_vertex_ids": [],
            "removed_existing_vertex_ids": [],
            "unexpected_moved_vertex_ids": [],
            "unexpected_removed_vertex_ids": [],
            "pass": True,
        }
    allowed = {int(value) for value in allowed_vertex_ids}
    if any(value <= 0 for value in allowed):
        raise ValueError("allowed persistent vertex ids must be positive integers")
    moved = []
    for agent_id in sorted(set(before) & set(after)):
        old = tuple(float(value) for value in before[agent_id])
        new = tuple(float(value) for value in after[agent_id])
        if len(old) != 3 or len(new) != 3:
            raise ValueError("vertex positions must be three-dimensional")
        if math.dist(old, new) > tolerance:
            moved.append(agent_id)
    unexpected = [agent_id for agent_id in moved if agent_id not in allowed]
    removed = sorted(set(before) - set(after))
    unexpected_removed = [agent_id for agent_id in removed if agent_id not in allowed]
    return {
        "enforced": True,
        "allowed_vertex_ids": sorted(allowed),
        "moved_existing_vertex_ids": moved,
        "removed_existing_vertex_ids": removed,
        "unexpected_moved_vertex_ids": unexpected,
        "unexpected_removed_vertex_ids": unexpected_removed,
        "pass": not unexpected and not unexpected_removed,
        "claim_boundary": "This audit protects positions and existence of pre-existing persistent vertices outside the declared footprint. Added topology and visual quality require separate checks.",
    }
