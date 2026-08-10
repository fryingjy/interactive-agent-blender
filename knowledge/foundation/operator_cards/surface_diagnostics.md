# Evaluated surface diagnostics

## Signals

- **Robust Laplacian outlier:** concentrated local displacement relative to median edge length;
  useful for locating a sharp pinch on an otherwise uniform surface.
- **Signed-Laplacian oscillation:** repeated alternating displacement across adjacent edges;
  useful for locating high-frequency waviness.
- **Neighbor-normal angle:** supporting faceting/curvature evidence.

Video context source: <https://www.youtube.com/watch?v=RRilLLyyn1Y>

## Interpretation

These signals generate inspection tickets, not confirmed defects. Hard cap transitions, boundaries,
intentional corrugation, and extraordinary topology can score strongly. Always combine them with
surface intent and Blender-native normal/solid/highlight views.

## Evidence

`runs/2026-08-10_surface-diagnostics/` separates a clean and one-vertex-pinched sphere and a uniform
and alternating-radius cylinder. The pinch score changed from 0.9534 to 80.6796; waviness sign
changes changed from 0.0 to 0.476190. All specimens remained technically clean.

`runs/2026-08-10_surface-lighting-judgment/` adds visual observability evidence derived from the
official Three Point Lighting lesson. A grazing key/weak fill/rim rig made a localized curved-surface
dent 2.57× stronger by mean pixel difference and affected 2.93× more thresholded pixels than a broad
frontal control. An initial non-grazing three-point rig performed worse and is retained. Therefore
“three-point” is not itself diagnostic; key direction relative to the tested surface matters.

`runs/2026-08-10_surface-cause-classification/` converts the official Intro to Shading lesson's
material/world/render-context separation into a conservative intervention protocol. On one manually
authored chamfered enclosure it correctly separated five controlled causes: base geometry, flipped
face orientation, material assignment/roughness, lighting, and bevel profile. Every discrepancy was
visually measurable (4,089 to 68,737 pixels over a 0.02 RGB delta), and 5/5 evaluated specimens
passed fresh mesh verification after an inward-winding failure was corrected.

## Cause-classification rule

Never classify from a beauty view alone. Hold camera and unaffected state fixed, then compare base
and evaluated geometry, normal/face-orientation state, a neutral material override, a neutral review
light, and bevel parameters. Credit a cause only when its matching intervention neutralizes the
discrepancy without changing earlier causal layers. Multiple qualifying signatures are
`CONFLICTING`; absent signatures are `UNRESOLVED`. The typed MCP surface
`classify_surface_defect_cause` exposes this policy, while `get_evaluated_defect_regions` remains a
candidate-localization tool rather than a confirmed diagnosis.
