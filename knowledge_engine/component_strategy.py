"""Select continuous-versus-separate construction from measured multi-view evidence.

This module does not infer geometry from images. It consumes explicit Blender/reference metrics and
refuses to let an ambiguous primary view decide a depth-sensitive component boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


VALID_COMPONENT_POLICIES = {"CONTINUOUS_MESH", "SEPARATE_COMPONENTS"}


@dataclass(frozen=True)
class ComponentStrategyEvidence:
    candidate_id: str
    component_policy: str
    object_count: int
    connected_component_count: int
    view_iou: dict[str, float]

    def validate(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if self.component_policy not in VALID_COMPONENT_POLICIES:
            raise ValueError(f"invalid component policy: {self.component_policy}")
        if self.object_count < 1 or self.connected_component_count < 1:
            raise ValueError("object and connected-component counts must be positive")
        if not self.view_iou:
            raise ValueError(f"candidate '{self.candidate_id}' requires measured view IoU")
        invalid = {view: value for view, value in self.view_iou.items() if not 0.0 <= value <= 1.0}
        if invalid:
            raise ValueError(f"view IoU must be in [0, 1]: {invalid}")
        if self.component_policy == "CONTINUOUS_MESH" and (
            self.object_count != 1 or self.connected_component_count != 1
        ):
            raise ValueError(
                "CONTINUOUS_MESH evidence requires exactly one object and one connected component"
            )
        if self.component_policy == "SEPARATE_COMPONENTS" and self.object_count < 2:
            raise ValueError("SEPARATE_COMPONENTS evidence requires at least two objects")


def resolve_component_strategy(
    candidates: list[ComponentStrategyEvidence],
    *,
    primary_view: str,
    secondary_views: tuple[str, ...],
    primary_ambiguity_max: float = 0.01,
    secondary_margin_min: float = 0.10,
    secondary_iou_min: float = 0.80,
) -> dict[str, Any]:
    """Resolve a construction policy only when a discriminating secondary view supports it.

    When top primary-view candidates are nearly tied, missing or weak secondary evidence returns a
    targeted research disposition. Runtime history, object count, or a plausible front silhouette
    cannot silently resolve the ambiguity.
    """
    if len(candidates) != 2:
        raise ValueError("exactly two component-strategy candidates are required")
    if not primary_view.strip():
        raise ValueError("primary_view is required")
    if len(secondary_views) != len(set(secondary_views)):
        raise ValueError("secondary_views must be unique")
    if any(not view.strip() for view in secondary_views):
        raise ValueError("secondary view names cannot be blank")
    if primary_view in secondary_views:
        raise ValueError("primary_view cannot also be a secondary view")
    if not 0.0 <= primary_ambiguity_max <= 1.0:
        raise ValueError("primary_ambiguity_max must be in [0, 1]")
    if not 0.0 <= secondary_margin_min <= 1.0:
        raise ValueError("secondary_margin_min must be in [0, 1]")
    if not 0.0 <= secondary_iou_min <= 1.0:
        raise ValueError("secondary_iou_min must be in [0, 1]")
    ids = [candidate.candidate_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("component-strategy candidate ids must be unique")
    policies = [candidate.component_policy for candidate in candidates]
    if len(set(policies)) != len(policies):
        raise ValueError("each candidate must represent a distinct component policy")
    for candidate in candidates:
        candidate.validate()
        if primary_view not in candidate.view_iou:
            raise ValueError(
                f"candidate '{candidate.candidate_id}' is missing primary view '{primary_view}'"
            )

    primary_ranked = sorted(
        candidates,
        key=lambda item: (-item.view_iou[primary_view], item.candidate_id),
    )
    primary_gap = primary_ranked[0].view_iou[primary_view] - primary_ranked[1].view_iou[primary_view]
    primary_ambiguous = primary_gap <= primary_ambiguity_max
    base = {
        "primary_view": primary_view,
        "primary_scores": {
            candidate.candidate_id: candidate.view_iou[primary_view] for candidate in candidates
        },
        "primary_gap": primary_gap,
        "primary_ambiguous": primary_ambiguous,
        "required_secondary_views": list(secondary_views),
        "thresholds": {
            "primary_ambiguity_max": primary_ambiguity_max,
            "secondary_margin_min": secondary_margin_min,
            "secondary_iou_min": secondary_iou_min,
        },
    }
    if not secondary_views:
        return {
            **base,
            "disposition": "TARGETED_REFERENCE_RESEARCH",
            "chosen_candidate_id": None,
            "chosen_policy": None,
            "reason": "primary view is ambiguous and no secondary view was supplied",
            "queries": ["acquire a same-variant side, top, or oblique view that reveals component depth"],
        }

    missing = {
        candidate.candidate_id: [view for view in secondary_views if view not in candidate.view_iou]
        for candidate in candidates
    }
    missing = {candidate_id: views for candidate_id, views in missing.items() if views}
    if missing:
        return {
            **base,
            "disposition": "TARGETED_REFERENCE_RESEARCH",
            "chosen_candidate_id": None,
            "chosen_policy": None,
            "reason": "one or more candidates lack the discriminating secondary views",
            "missing_secondary_views": missing,
            "queries": [
                f"acquire same-variant {view} evidence for component depth and boundary continuity"
                for view in sorted({view for views in missing.values() for view in views})
            ],
        }

    secondary_scores = {
        candidate.candidate_id: mean(candidate.view_iou[view] for view in secondary_views)
        for candidate in candidates
    }
    ranked = sorted(
        candidates,
        key=lambda item: (-secondary_scores[item.candidate_id], item.candidate_id),
    )
    best, runner_up = ranked[:2]
    margin = secondary_scores[best.candidate_id] - secondary_scores[runner_up.candidate_id]
    if secondary_scores[best.candidate_id] < secondary_iou_min or margin < secondary_margin_min:
        return {
            **base,
            "disposition": "TARGETED_REFERENCE_RESEARCH",
            "chosen_candidate_id": None,
            "chosen_policy": None,
            "reason": "secondary evidence does not discriminate the construction strategies strongly enough",
            "secondary_scores": secondary_scores,
            "secondary_margin": margin,
            "queries": ["acquire a closer oblique or sectional view of the disputed component boundary"],
        }

    return {
        **base,
        "disposition": "SELECT_STRATEGY",
        "chosen_candidate_id": best.candidate_id,
        "chosen_policy": best.component_policy,
        "secondary_scores": secondary_scores,
        "secondary_margin": margin,
        "rejected_candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "component_policy": candidate.component_policy,
                "reason": (
                    f"secondary-view mean IoU {secondary_scores[candidate.candidate_id]:.6f} is "
                    f"below selected candidate {secondary_scores[best.candidate_id]:.6f}"
                ),
            }
            for candidate in ranked[1:]
        ],
        "reason": "secondary-view evidence resolves a primary-view construction ambiguity",
    }
