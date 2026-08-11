# Visual reference comparison

## Use

Measure whether a modeling edit improves reference agreement across multiple views without letting
camera reframing conceal proportion changes.

## Procedure

1. Define reference bounds once and reuse them to frame every candidate render.
2. Render at least front, side, and top silhouettes for forms that can be judged orthographically.
3. Compare foreground IoU, centroid, bounding box, and contour distance per view.
4. Reject a change when one view improves by damaging another unless that tradeoff is intentional.
5. Keep base-mesh, evaluated-mesh, and visual checks separate.
6. Use surface-normal/highlight and landmark checks for curved or semantic forms; silhouette alone
   is insufficient.

## Failure modes

- Auto-framing each object independently erases scale and proportion evidence.
- A transparent dark silhouette can appear blank in viewers with a black canvas; inspect alpha or
  composite for display without changing the measured mask.
- IoU can be high while local contour or feature placement is wrong.
- Orthographic agreement does not prove perspective or camera-matched agreement.
- A light or non-white source background can become false foreground under a generic threshold;
  inspect the binary mask and foreground bounds before accepting any metric.

## Evidence

`runs/2026-08-10_visual-comparison/` improved mean three-view IoU from 0.739440 to
0.979045 and reduced mean normalized contour error from 0.021805 to 0.002058. This is controlled
synthetic evidence and is not credited as held-out modeling.

`runs/2026-08-10_profile-authored-axe/` adds same-reference transfer evidence on a supplied
single-view object: 0.942380 silhouette IoU, 0.771739 negative-space IoU, 0.001314 normalized
centroid error, and 0.001523 normalized contour error. An initial threshold of 240 included the
light-gray background and yielded a meaningless 0.269494 IoU; threshold 220 was accepted only after
mask and bounds inspection. This is corrective transfer evidence, not held-out or multi-view proof.
