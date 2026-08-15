# Nailsea primary-form correction

## Outcome

The retained human rejection was correct. The earlier 33-ring cage allocated axial topology
uniformly, so Subdivision smoothed away several tight profile transitions even though the mesh was
one connected all-quad object. This correction keeps the same-object reference evidence and the
same single-object strategy, but redistributes a 45-ring budget toward bounded measured slope and
curvature before scaling each ring.

The corrected result is one connected 12-sided rotational shell: 540 vertices, 1,068 edges, and
528 quads, with no triangles, n-gons, loose vertices, or degenerate faces. Subdivision followed by
inward Solidify produces a closed evaluated mesh and a visible hollow socket. Smooth by Angle is
retained; no fake stacked primitives or structural ridge cylinders were added.

The saved production file contains editable `HIGH_POLY` and `LOW_POLY` collections created through
the rollback-owned typed `package_high_low_variants` operation. Each contains one independent copy
of that connected cage. Both keep their Subdivision and Solidify modifiers unapplied; the high
variant uses SubD level 2 and the low variant keeps SubD at level 0. The overlapping low object is
hidden from viewport/render by default and can be revealed from its collection when needed. This is
editable variant packaging, not a claim of purpose-authored production retopology.

## Measured comparison

Against the exact rejected baseline and retained front reference mask:

- silhouette IoU: `0.847929 -> 0.954569`;
- normalized row-profile RMSE: `0.098833 -> 0.031162` (68.47% reduction);
- normalized symmetric contour error: `0.005695 -> 0.001450` (74.54% reduction).

A fresh Blender 5.2 process independently loaded the saved `.blend` and passed every structural,
modifier, evaluated-health, circularity, dimension-ratio, hollow-socket, and render check. Evaluated
dimensions are `8.981 x 8.981 x 30.500 cm`, consistent with the documented `9 x 9 x 30.5 cm` size.

## Failures found and fixed

1. The generator used a stale prose-only stage transition after the runtime had moved to strict
   structured evidence. It now passes the reference and blockout gates in sequence.
2. The first adaptive build exposed a ring-grouping defect: BMesh loop cuts can differ by tiny
   floating-point Z values around one radial edge. Exact rounded-Z grouping split 41 loops into
   `11 + 1` vertices and created a slight helical distortion. Generator and independent verifier now
   cluster axial rings with a bounded tolerance; the final file has exactly 45 planar 12-vertex rings.
3. Full transaction payloads duplicated evidence and inflated the runtime report. `--compact-report`
   retains decision IDs and operation counts while reducing the report from about 375 KB to about
   66 KB.
4. Normalized silhouette comparison hid absolute scale. Fresh evaluated-dimension inspection caught
   the oversize result; measured compensation restored the published width/height ratio.

## Honest disposition

`CORRECTED_PENDING_HUMAN_FORM_REVIEW`. This is strong relative and technical evidence, not proof of
professional multi-view accuracy. The old rejection remains unchanged, no skill is promoted, and
the Bialetti reference gate remains model-free and pending.

## Reproduction

```powershell
blender --background --factory-startup --python tools/run_runtime_candlestick.py -- --output runs/2026-08-15_nailsea-form-correction --measurement runs/2026-08-15_runtime-use-nailsea/reference_measurement.json --reference-evidence runs/2026-08-15_nailsea-form-correction/reference_stage_evidence.json --object-name Corrected_Nailsea_Candlestick_HIGH --height 30.5 --max-width 9.663663 --radial-vertices 12 --rings 45 --blend-name corrected_nailsea_candlestick.blend --smooth-shell --adaptive-profile --profile-smoothing-window 21 --compact-report --production-variants
python tools/evaluate_profile_correction.py runs/2026-08-15_runtime-use-nailsea/reference_silhouette.png runs/2026-08-15_runtime-use-nailsea/final_candidate_mask.png runs/2026-08-15_nailsea-form-correction/final_candidate_mask.png runs/2026-08-15_nailsea-form-correction
blender --background runs/2026-08-15_nailsea-form-correction/corrected_nailsea_candlestick.blend --python tools/verify_runtime_candlestick_blend.py -- --run-dir runs/2026-08-15_nailsea-form-correction --object-name Corrected_Nailsea_Candlestick_HIGH
```
