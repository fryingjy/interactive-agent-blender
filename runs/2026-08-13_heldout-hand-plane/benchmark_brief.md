# Held-out benchmark: vintage No.4 wooden hand plane

Frozen 2026-08-13, before download or any neutral-reference rendering.

## Source

Poly Haven CC0 `hand_plane_no4` ("Hand Plane No4" by Satyaki Mandal, donated, CC0). Source geometry
will be isolated to neutral reference renders only, the same way every other held-out family in this
project has been handled -- construction will use pixels/measurements only, never the source
topology, object names, modifiers, or materials.

## Why this asset

- Ladder rungs A ("Subdivision transfer") and C ("Unknown-problem asset") in
  `knowledge/foundation/benchmark_readiness.json` are the only two entries still marked
  `NOT_RUN_HELD_OUT`. Every held-out asset this project has modeled so far (camera, telephone,
  watering can, desk lamp, wrench) used either a lofted/revolved profile or a flat inset-and-extrude
  cage; none used a genuine low-poly SubD cage on curved organic-reading geometry as the PRIMARY
  strategy, verified fresh and held out. The connected-camera-corrective evidence does use a real
  weighted-Bevel-then-SubD modifier chain, but the registry explicitly marks that pass
  `COMPLETED_NOT_HELD_OUT` (it was built with the specific rejection feedback already in hand), so it
  cannot satisfy a held-out rung by this project's own stated policy.
- Different shape and material family from everything modeled this session: a low, wide hand tool
  (source dimensions 330.8 x 84.3 x 197.8mm -- wider than tall, unlike every prior asset's
  taller-than-wide profile) combining a rounded wooden body (a genuine SubD-cage candidate: humped
  top, worn curved sides) with a flat machined steel sole/blade assembly (a genuine sharp-Bevel
  candidate) and small brass adjustment hardware. Which parts need a SubD cage, which need flat
  Bevel-only construction, and whether they're one connected object or several is not given in
  advance -- that is rung C's actual test, not a labeled "this needs a pole" exercise.
- P0 category fit: hand tool / carpentry.

## Contract, frozen before any reference inspection

- **Step 0, before any landmark measurement or construction**: run
  `tools/verify_reference_view_orientation.py` against the neutral references with the intended
  in-plane build axis, and do not proceed with construction on an axis it flags as inconsistent. This
  asset's own source dimensions suggest its "wide" view differs from every prior asset's (wider than
  tall), so this is not assumed from habit.
- Construction rule: the wooden body is expected to need a genuine low-vertex-count SubD cage
  (Subdivision Surface modifier over a controlled base mesh with deliberate support-loop placement),
  not a dense pre-smoothed loft -- this is the specific capability this benchmark exists to exercise
  as held-out evidence. The sole/blade assembly is expected to need flat construction with
  weighted-Bevel sharp edges per this project's established hard-surface shading policy
  (`knowledge/foundation/operator_cards/smooth_by_angle.md`). Whether these are one connected object
  or separate objects will be decided from what the reference actually shows (a visible material/part
  break vs. a continuous skin), not assumed before looking.
- Landmarks will be measured from the reference row/column profile via `tools/measure_reference.py`
  and `tools/measure_reference.py`-style column profiles where needed (this object is wide, so a
  column profile may matter as much as the row profile used for every prior taller-than-wide asset),
  not eyeballed.
- Visual gates (normalized silhouette IoU against the isolated reference, comparison method matching
  `tools/compare_alpha_multiview.py`, this project's standing 0.97 front/side/top/mean thresholds)
  apply and are not adjusted after seeing results.
- SubD-specific verification: the wood body's evaluated mesh will be checked against the same
  contextual-topology metrics used in `runs/2026-08-10_topology-subd/` (adjacent-face angle change,
  evaluated face-area coefficient of variation), not silhouette IoU alone -- this is what makes it
  transfer evidence for ladder rung A rather than a restatement of the same silhouette check every
  prior asset already used.
- Fresh-process independent verification (no non-manifold edges, no degenerate faces, no loose
  vertices, positive volume) is required on the base AND evaluated mesh before any pass is claimed.
- Per this project's own boombox/camera lesson, a shaded beauty render will be checked directly
  against the reference at the same angle before any visual pattern is treated as either a defect or
  a success -- not silhouette masks alone.
- This benchmark is not claimed as professional-quality or expert-accepted regardless of outcome;
  automated gates passing is not the same as visual fidelity.
