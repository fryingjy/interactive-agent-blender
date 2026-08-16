# Human visual review → repair protocol

Automated comparison is useful for measurable silhouette, landmark, component-mask, and
negative-space discrepancies. It is not an authority on product form, construction, depth, or
professional acceptability. A human visual rejection is therefore retained as first-class external
evidence and is never overwritten by a passing metric.

## Review record

`knowledge_engine.human_review.validate_external_visual_review()` accepts only a record with:

```json
{
  "review_result": "reject",
  "reviewer_type": "human",
  "reviewer_id": "reviewer identifier",
  "asset_id": "asset identifier",
  "scene_revision": 12,
  "failure_types": ["proportion", "negative_space"],
  "regions": [
    {"target": "main body", "failure_type": "proportion", "view": "front", "severity": 0.9}
  ],
  "severity": {"proportion": 0.9, "negative_space": 0.7},
  "notes": "Concrete observed defect and why it matters."
}
```

Valid failure categories are: `proportion`, `component_shape`, `component_relationship`,
`negative_space`, `depth_overlap`, `silhouette`, `surface_highlight`, `topology`, and
`construction_strategy`.

The record is intentionally not an aggregate score. The reviewer does not need to prescribe an
operator or a topology fix; that would conflate diagnosis with authoring.

## Repair loop

`review_to_repair_tickets(review, current_scene_revision=...)` converts a current human rejection
to ordered `EXTERNAL_HUMAN_REVIEW` tickets. The planner responds inspect-first, so the next action
must localize a cause against current base/evaluated/reference evidence before selecting a repair or
rebuild. A ticket from an older scene revision leads to `RECAPTURE_STALE_HUMAN_REVIEW`, not a blind
edit.

```text
human rejection
-> revision-bound localized ticket
-> inspect current geometry/reference evidence
-> diagnose likely cause
-> smallest bounded repair or explicit rebuild
-> re-measure
-> new human review
```

This protocol validates the *shape and freshness* of external feedback. It does not manufacture a
human review or certify a model.

## Retaining a review handoff

Use the provided CLI to validate a human-authored JSON file and write the exact review plus its
planner tickets into a dated run directory:

```powershell
python tools/record_external_visual_review.py REVIEW.json runs/YYYY-MM-DD_asset/human_review_repair_handoff.json --current-scene-revision 12
```

The command fails on an agent review, malformed review, or a stale scene revision. The resulting
artifact records an `INSPECT_BEFORE_REPAIR` disposition for a rejection; it does not assert that
any subsequent Blender edit was correct.

## Pre-model review is optional

Reference manifests and construction plans remain useful evidence, but the active workflow does
not require an HTML board or approval request before modeling. Direct user instruction may
authorize reversible modeling immediately. Human authority is then applied to concrete model
renders through the rejection/repair protocol above. The historical SHA-bound reference-gate tools
remain as tested utilities; they are not the default benchmark workflow and must not block work
unless the user explicitly requests that gate.
