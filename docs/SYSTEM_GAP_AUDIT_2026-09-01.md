# System gap audit and repair — 2026-09-01

## Outcome

The repository has strong Blender execution, rollback, topology inspection, diagnostic rendering,
and a substantial technique library. Its principal failure was not missing mesh operators. The
failure was an underconstrained **perception → diagnosis → mutation** loop: camera, pose,
segmentation, representation, and geometry errors could be conflated, then a single noisy critic or
aggregate silhouette score could authorize another incorrect edit.

New prop modeling was placed on an enforced hold while the repair gates were open. The runtime
permitted only explicitly declared `SYSTEM_VALIDATION_FIXTURE` work until every gate passed. That
hold was cleared later on 2026-09-01 by the frozen calibration described below.

## Root causes found

| Gap | Failure mechanism | Repair now |
| --- | --- | --- |
| Camera/geometry conflation | Comparing a photograph and render before matching projection makes correct geometry appear wrong | Typed reference classes and camera-registration gate in `knowledge_engine/reference_registration.py` |
| Unsafe reference authority | A Pinterest or product hero image could silently make depth/proportion claims it cannot prove | `UNCALIBRATED_PERSPECTIVE_STYLE_ONLY` views cannot authorize geometry |
| Segmentation false confidence | Opaque alpha, full-canvas polarity, GrabCut closure, or lost holes can manufacture misleading IoU | Component, foreground fraction, border, and expected-negative-space audit in `knowledge_engine/segmentation_audit.py` |
| Single-critic instability | One VLM call could issue contradictory directional advice or prematurely approve surface work | Hash-bound repeated critics; majority-localized repair tickets; unanimous surface advancement; split votes become `EVALUATOR_FAILURE` |
| Hand-tuned coordinate guessing | Bespoke scripts adjusted arbitrary coordinates without bounded measurable search | SciPy-backed deterministic bounded fitting for declared semantic parameters only |
| Aggregate-score gaming | A gain in one metric/view could hide a serious local regression | Frozen per-metric perception anchor; every rule must pass independently |
| Readiness drift | Target authorization and old automated passes left `ready_for_held_out_modeling` true despite repeated human rejection | Repository-wide `REFERENCE_MODELING_READINESS` hold and runtime enforcement |
| Unbounded local edits | A nominally local operation could silently distort or delete already-correct regions and still pass whole-object checks | Persistent-ID vertex-position/existence footprints; commits fail when protected existing vertices move or disappear |
| Evidence bloat | Iteration folders retained many equivalent revisions without a baseline/best/failure policy | Keep baseline, retained best, and one named failed hypothesis; purge equivalent intermediate artifacts |

## Controlled proof

`runs/2026-09-01_reference-perception-lab/report.json` uses known synthetic ground truth, not a new
asset. The same correct silhouette scores 0.6409 under the wrong camera and 0.9937 after registered
homography. A genuinely wrong shape under that same registration remains at 0.7332 and loses its
expected negative space. The bounded semantic-parameter fit improves its objective by 0.4529. The
frozen six-rule non-regression anchor passes without averaging.

This proves the repaired mechanisms in a controlled setting. It does **not** prove reliable
real-photo calibration or professional modeling ability.

## Research translated into architecture

- [OpenCV calibration/3D reconstruction](https://docs.opencv.org/4.8.0/d9/d0c/group__calib3d.html)
  supports explicit control points, camera solutions, homography, and reprojection checks.
- [SciPy differential evolution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html)
  supplies bounded, reproducible global parameter search; it is used only after representation and
  topology are frozen.
- [BlenderGym](https://github.com/richard-guyunqi/BlenderGym-Open) demonstrates generator/verifier
  branching and verifier-side inference scaling. The local critic now samples and reconciles rather
  than trusting one call.
- [Blender Agent Studio](https://github.com/ifBars/blender-agent-studio) contributes strict
  non-regression, identical evidence rechecks, source-level repair, and blinded multi-view review.
- [Thinking in Blender / SEIG](https://arxiv.org/abs/2606.02580) reinforces staged scene-factor
  reconstruction. Camera/composition, geometry, surface, and lighting are not optimized together.
- [3DCodeBench](https://github.com/gaoypeng/3dcodebench) reinforces retaining attempts, failures,
  settings, and raw agent traces for image-to-3D evaluation.
- [fSpy](https://github.com/stuffmatic/fSpy) is retained as an optional rectilinear-photo adapter.
  It is unsuitable when reliable parallel lines are absent.
- [COLMAP](https://github.com/colmap/colmap) is retained for genuine overlapping same-object
  multiview sets, not arbitrary product boards.
- [PIL Agent](https://github.com/bsmi021/pil-agent-plugin) provides direct counterevidence that
  confident visual claims must yield to measurements that actually discriminate the tested change.
- [ViSculpt](https://arxiv.org/abs/2608.24169) reinforces visual feedback and localized in-place
  edits. Transactions can now declare an allowed persistent-vertex set; movement outside it blocks
  commit instead of merely lowering a whole-object score.
- [BlenderModelFitting](https://github.com/hansgaensbauer/BlenderModelFitting) reinforces explicit,
  low-dimensional model parameters and documents camera/no-overlap failure modes. The local fitter
  therefore runs only after registration and never controls topology or representation choice.

`image-matcher` was not adopted because its repository targets Blender 3.6 and is no longer
maintained. `Blender Agent Bridge` was also not installed: its scene-awareness, reversible-edit, and
evidence concepts are already covered by this repository's stronger transaction and probe system,
and a second bridge would create conflicting control paths.

The current `image2blender` plugin was rechecked rather than installed. Its spec-first stages,
fixed-view reviews, and bounded repair loop were already incorporated on 2026-08-24; its
one-component-per-object/procedural-primitive bias conflicts with the connected-cage requirements,
and its second raw-code MCP would weaken the single authoritative transaction path.

CUDA-first SAM2, PyTorch3D, dense COLMAP, and image-to-3D foundation models are not installed as the
core path. This host has Intel integrated graphics and roughly 1 GB reported graphics memory. The
implemented core is CPU-first OpenCV, NumPy, SciPy, Blender Workbench, and remote VLM verification.

The local Blender installation was upgraded from 5.2.0 to 5.2.1 LTS after checking the current
official maintenance release. The localized transaction fixture was rerun successfully under
5.2.1; this records compatibility rather than claiming a modeling-quality gain.

## Mandatory order after this repair

1. Classify each reference view and list exactly what it can prove.
2. Audit segmentation and expected negative spaces.
3. Register camera/pose or downgrade the view to style-only.
4. Freeze representation and expose only semantic parameters.
5. Compare deterministic measurements per component and view.
6. Run three independent semantic critics.
7. Mutate only a majority-localized ticket; reject evaluator disagreement.
8. Re-render identical evidence and apply strict per-task non-regression.
9. Keep baseline, retained best, and one named failed hypothesis; purge intermediate duplicates.
10. Require held-out human visual calibration before clearing the modeling hold.

## Calibration resolution — no false completion claim

The controlled mechanisms and frozen three-target real-reference rejection regression pass. That
regression covers the TERTIAL lamp, curved sword, and Panasonic radio families and refuses
aggregate-score substitution. The later external response agreed with all four precommitted
calibration decisions, so the system hold is cleared for a new Level-1 prop.

The external calibration is now prepared, not silently self-scored. Four frozen cases cover the
CG Cookie crate, Sweaty Grease carabiner, Blender official watering can, and a pixel-identical
positive control. Three independent Gemini reviews are retained per case. A human must review the
public image pairs without reading the frozen critic outputs. The retained response and result show
4/4 agreement: all three model candidates were rejected and the identical control was accepted.
This calibrates rejection behavior only; it does not prove modeling competence.
