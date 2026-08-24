# CG Cookie sci-fi crate — bounded I0 tutorial reproduction

This run studies [CG Cookie's *Modeling a Sci-Fi Crate in Blender | Box Modeling Fundamentals*](https://www.youtube.com/watch?v=1hQuynokYu0). It is retained as useful learning evidence, **not** as an I0 pass.

## Outcome

- Final score: **6.8/10 — NOT PASSING the 8/10 gate**.
- Modeling stopped after one reproduction, one render-driven latch correction, fresh-process verification, and one different-geometry transfer. The result is not being polished indefinitely.
- `crate_tutorial.blend` contains one connected all-quad main shell derived from one cube, connected panel/handle recesses, and fitted latch/bumper assemblies derived from source faces. Mirror, Solidify, and Bevel modifiers remain unapplied.
- `curved_fitted_panel_transfer.blend` validates the fitted duplicate/separate/live-thickness principle on a 12-sided curved shell.

## Evidence

- Source and modality record: `source_metadata.json`
- Full Gemini audiovisual extraction, explicitly unverified: `gemini_full_video_unverified.json`
- Independent bounded transcript/player review: `independent_episode_review.json`
- Strict assessment and named failures: `tutorial_assessment.json`
- Fresh Blender inspection: `fresh_crate_asset_inspection.json`, `fresh_crate_evaluated_verification.json`
- Transfer assessment: `transfer_evaluation.json`
- Runtime corrections: `runtime_corrections.json`
- Final views: `crate_final_v2_solid.png`, `crate_final_v2_material.png`, `crate_final_wireframe.png`

## What transferred

The run added two general runtime capabilities rather than an object-specific builder:

1. `inset_selection` now exposes Blender's boundary and even-offset controls, allowing a mirrored handle recess without inventing a separate primitive.
2. `duplicate_selection` implements the Edit Mode fitted-assembly half of duplicate-then-separate while assigning new persistent IDs to copied elements.

The modifier report serializer was also corrected so Blender RNA array values such as Mirror axes remain JSON-safe.

## Named limitations

- No unobscured creator-final frame was independently captured; pixel-level likeness is therefore not claimed.
- The latch, bumper coverage, and panel layout are simplified relative to the lesson target.
- The bumper evaluates manifold but contains 32 n-gons around dense rib intersections.
- This attempt does not complete I0 or unblock I1. The next attempt must use a different complete intermediate lesson with a clearly inspectable final result.
