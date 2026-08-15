# Session report — Bevel/Subdivision order reconciliation

## Question

Does the CG Boost workflow (crease/weight base edges, Subdivision, then weighted Bevel) invalidate
the project's standing weighted-Bevel-before-Subdivision policy?

## Method

Blender 5.2.0 LTS, factory-startup background process. Three identical 56-vertex/54-quad box cages
were subdivided in Edit Mode to provide moderate, identical face support. The same 36 outer design
edge segments were used in every case:

1. weighted Bevel -> Subdivision;
2. crease 0.75 + Subdivision -> weighted Bevel;
3. Subdivision -> weighted Bevel with no crease (negative control).

The generator recorded modifier-evaluated health, surface-quality signals, localized curvature
candidates, dimensions, panel planarity, a fixed MatCap comparison, and evaluated-wire geometry.
A second clean Blender process loaded the saved `.blend` and independently checked modifier order,
crease placement, evaluated topology, render dimensions, image dynamic range, and scene cleanup.

## Reproduction

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 2 --python tools\run_bevel_subd_order_lab.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background runs\2026-08-15_bevel-subd-order\bevel_subd_order.blend --python-exit-code 2 --python tools\verify_bevel_subd_order_lab.py -- runs\2026-08-15_bevel-subd-order
```

## Preserved failures and corrections

- The first render attempt failed because factory-startup had no World datablock. The lab now owns
  that setup explicitly, and reproduction commands use `--python-exit-code 2` so Blender-side
  Python exceptions cannot exit as apparent success.
- The first result expected face counts and bounds to distinguish all three strategies. They did
  not: both post-Subdivision variants had 1,176 faces and identical bounds despite visibly and
  measurably different surfaces. That coarse predicate was rejected and is recorded in the JSON.
- Background Workbench ignored viewport-only wire overlay/mode settings. The final wire evidence is
  real temporary geometry generated from each evaluated mesh, rendered, then removed before save.

## Result and boundary

The experiment rejects a universal order. Pre-Subdivision Bevel is the broad-radius/smoothed-form
path. Protected post-Subdivision Bevel is a lower-cost, flatter-panel/tight-chamfer path that needs
explicit multi-edge-corner inspection. Unprotected post-Subdivision Bevel loses the intended edge
location on this fixture. See `visual_review.md` for the visual judgment.

This is `EXPERIMENTALLY_TESTED`, not `TRANSFER_VALIDATED`: a curved hull or real prop still needs
the same comparison under a reference-defined edge requirement.
