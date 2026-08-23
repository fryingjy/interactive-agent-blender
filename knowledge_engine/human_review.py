"""External visual-review evidence and revision-bound repair tickets.

Automated image metrics can identify a mismatch, but an experienced reviewer may
notice a wrong construction, proportion, or negative space that scores well.  This
module preserves that authority without allowing an unstructured comment (or the
agent reviewing itself) to silently become a geometry mutation.
"""

from __future__ import annotations

from typing import Any


FAILURE_TYPES = {
    "proportion",
    "component_shape",
    "component_relationship",
    "negative_space",
    "depth_overlap",
    "silhouette",
    "surface_highlight",
    "topology",
    "construction_strategy",
}

# Root-cause classification (docs/FAILURE_TAXONOMY.md, added 2026-08-23): a
# separate axis from FAILURE_TYPES above. FAILURE_TYPES says what looks wrong
# in the render; this says which stage of reasoning produced it. One symptom
# can come from more than one root cause, so both are recorded, not merged.
ROOT_CAUSE_CATEGORIES = {
    "REFERENCE_FAILURE",
    "INTERPRETATION_FAILURE",
    "REPRESENTATION_FAILURE",
    "PROPORTION_FAILURE",
    "COMPONENT_FAILURE",
    "DEPTH_FAILURE",
    "SURFACE_FAILURE",
    "EXECUTION_FAILURE",
    "EVALUATOR_FAILURE",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_external_visual_review(review: dict[str, Any]) -> dict[str, Any]:
    """Validate a human review without deciding whether its artistic judgment is right.

    A rejection needs localized failure categories and a source scene revision so it
    can guide a repair, yet it remains external evidence rather than an automated
    quality score.  Agent/self reviews are rejected deliberately.
    """
    if not isinstance(review, dict):
        raise ValueError("external visual review must be an object")
    if review.get("review_result") not in {"accept", "reject"}:
        raise ValueError("review_result must be 'accept' or 'reject'")
    if review.get("reviewer_type") != "human":
        raise ValueError("only a human reviewer can supply external visual-review authority")
    if not isinstance(review.get("reviewer_id"), str) or not review["reviewer_id"].strip():
        raise ValueError("external visual review requires a non-empty reviewer_id")
    if not isinstance(review.get("asset_id"), str) or not review["asset_id"].strip():
        raise ValueError("external visual review requires an asset_id")
    if not _is_number(review.get("scene_revision")) or review["scene_revision"] < 0:
        raise ValueError("external visual review requires a non-negative scene_revision")
    failure_types = review.get("failure_types", [])
    if not isinstance(failure_types, list) or any(item not in FAILURE_TYPES for item in failure_types):
        raise ValueError(f"failure_types must be drawn from {sorted(FAILURE_TYPES)}")
    root_cause_categories = review.get("root_cause_categories", [])
    if not isinstance(root_cause_categories, list) or any(
        item not in ROOT_CAUSE_CATEGORIES for item in root_cause_categories
    ):
        raise ValueError(f"root_cause_categories must be drawn from {sorted(ROOT_CAUSE_CATEGORIES)}")
    regions = review.get("regions", [])
    if not isinstance(regions, list):
        raise ValueError("regions must be a list")
    for region in regions:
        if not isinstance(region, dict) or not isinstance(region.get("target"), str) or not region["target"].strip():
            raise ValueError("each review region requires a target")
        if "failure_type" in region and region["failure_type"] not in failure_types:
            raise ValueError("region failure_type must be declared in failure_types")
        severity = region.get("severity", 1.0)
        if not _is_number(severity) or not 0.0 <= severity <= 1.0:
            raise ValueError("region severity must be in [0, 1]")
    severity = review.get("severity", {})
    if not isinstance(severity, dict) or set(severity) - set(failure_types):
        raise ValueError("severity may only score declared failure_types")
    if any(not _is_number(value) or not 0.0 <= value <= 1.0 for value in severity.values()):
        raise ValueError("failure severity values must be in [0, 1]")
    notes = review.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError("review notes must be text")
    if review["review_result"] == "reject" and (not failure_types or not notes.strip()):
        raise ValueError("a rejection requires failure_types and concrete notes")
    if review["review_result"] == "reject" and not root_cause_categories:
        raise ValueError(
            "a rejection requires root_cause_categories (docs/FAILURE_TAXONOMY.md) so a correction "
            "targets the stage that actually failed, not just the visible symptom"
        )
    return review


def review_to_repair_tickets(review: dict[str, Any], *, current_scene_revision: int | float) -> list[dict[str, Any]]:
    """Convert a current human rejection into localized, inspect-first repair tickets.

    The conversion intentionally proposes no blind geometry operation.  A reviewer
    identifies *what* is visibly wrong; the planner must first inspect current
    geometry/reference evidence to diagnose the smallest repair or decide to rebuild.
    """
    review = validate_external_visual_review(review)
    if review["scene_revision"] != current_scene_revision:
        raise ValueError(
            f"review targets scene revision {review['scene_revision']}, not current revision {current_scene_revision}; recapture review"
        )
    if review["review_result"] == "accept":
        return []
    severity_by_type = review.get("severity", {})
    regions_by_type: dict[str, list[dict[str, Any]]] = {item: [] for item in review["failure_types"]}
    for region in review.get("regions", []):
        if "failure_type" in region:
            regions_by_type[region["failure_type"]].append(region)
    tickets = []
    for failure_type in review["failure_types"]:
        regions = regions_by_type[failure_type] or [{"target": "asset", "severity": severity_by_type.get(failure_type, 1.0)}]
        for region in regions:
            tickets.append({
                "type": f"human_review_{failure_type}",
                "target": region["target"],
                "view": region.get("view", "human_review"),
                "severity": float(region.get("severity", severity_by_type.get(failure_type, 1.0))),
                "evidence": review["notes"],
                "source": "EXTERNAL_HUMAN_REVIEW",
                "reviewer_id": review["reviewer_id"],
                "scene_revision": review["scene_revision"],
                "root_cause_categories": list(review.get("root_cause_categories", [])),
            })
    tickets.sort(key=lambda ticket: (-ticket["severity"], ticket["type"], ticket["target"]))
    for priority, ticket in enumerate(tickets, start=1):
        ticket["priority"] = priority
    return tickets


def build_repair_record(review: dict[str, Any], *, current_scene_revision: int | float) -> dict[str, Any]:
    """Build the retainable artifact consumed by a later planner/repair session."""
    validated = validate_external_visual_review(review)
    tickets = review_to_repair_tickets(validated, current_scene_revision=current_scene_revision)
    return {
        "schema_version": 1,
        "record_type": "EXTERNAL_HUMAN_VISUAL_REVIEW_REPAIR_HANDOFF",
        "asset_id": validated["asset_id"],
        "scene_revision": validated["scene_revision"],
        "review": validated,
        "repair_tickets": tickets,
        "disposition": "REVIEW_ACCEPTED_NO_REPAIR" if validated["review_result"] == "accept" else "INSPECT_BEFORE_REPAIR",
        "limitation": (
            "This preserves human feedback and creates inspection tickets. It does not prove that a repair "
            "was performed, that the current scene still matches a later edit, or that a future review will pass."
        ),
    }
