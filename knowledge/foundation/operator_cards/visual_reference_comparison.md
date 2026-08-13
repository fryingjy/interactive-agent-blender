# Visual reference comparison

## Use

Measure whether a modeling edit improves reference agreement across multiple views without letting
camera reframing conceal proportion changes.

## Procedure

0. **Before any real construction on an asymmetric or articulated reference**, confirm which world
   plane the reference's "full profile" view actually corresponds to. Run
   `tools/verify_reference_view_orientation.py <reference_dir> --in-plane-axis {X,Y,Z} --wide-view
   {front,side}` with the axis you intend to build the primary detail along -- it builds a trivial
   elongated proxy, renders it through the real `render_silhouette` pipeline, and empirically
   confirms whether that axis reads as wide in front or side view, rather than assuming it. This
   step exists because of a real, costly failure (see Evidence): a full articulated-lamp candidate
   was built end to end in the wrong plane before the mismatch was discovered.
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
- A shaded/beauty render can show a visual pattern (rippling, a twist, an odd highlight) that looks
  like a construction defect but is a faithful reproduction of real reference detail -- check the
  same angle against the actual reference before spending time "fixing" it. A wrench candidate's
  shaded render showed a rippled band that was initially diagnosed as a loft-parameterization bug and
  two plausible-sounding corrections were built and measured (both reduced silhouette IoU with no
  visible change to the pattern) before comparing against the reference at the same angle showed the
  real object has genuine ridged worm-screw threading in that exact spot. See
  `runs/2026-08-12_heldout-adjustable-wrench/session_report.md`'s 2026-08-13 addendum.
- **Building the primary construction plane along the wrong world axis is invisible until first
  render, and by then real construction time is already spent.** `render_silhouette`'s "front" looks
  along -Y (exposes the X-Z plane) and "side" looks along +X (exposes the Y-Z plane) -- not the
  reverse, and not something to assume from a reference image's own front/side labeling. A
  full-length articulated desk-lamp candidate was built in the X-Z plane while its reference's full
  profile was the Y-Z plane, producing a side-view IoU of 0.0045 (a near-complete miss) that was
  indistinguishable from a genuine proportion failure until the axes were checked directly. Step 0
  above exists specifically to catch this before it happens again.

## Evidence

`tools/verify_reference_view_orientation.py`, run against
`runs/2026-08-12_heldout-desk-lamp/reference/` in
`runs/2026-08-12_reference-orientation-check/`: tested with `--in-plane-axis X` (the axis the first
desk-lamp candidate actually used) correctly fails, reporting the probe reads wider in `front` than
`side` -- the exact inversion that produced that candidate's 0.0045 side-view IoU. Tested with
`--in-plane-axis Y` (the axis the corrected second candidate used) correctly passes. This is direct
empirical proof the check would have caught the real bug before construction, not just after.

`runs/2026-08-10_visual-comparison/` improved mean three-view IoU from 0.739440 to
0.979045 and reduced mean normalized contour error from 0.021805 to 0.002058. This is controlled
synthetic evidence and is not credited as held-out modeling.

`runs/2026-08-10_profile-authored-axe/` adds same-reference transfer evidence on a supplied
single-view object: 0.942380 silhouette IoU, 0.771739 negative-space IoU, 0.001314 normalized
centroid error, and 0.001523 normalized contour error. An initial threshold of 240 included the
light-gray background and yielded a meaningless 0.269494 IoU; threshold 220 was accepted only after
mask and bounds inspection. This is corrective transfer evidence, not held-out or multi-view proof.

`runs/2026-08-12_heldout-adjustable-wrench/` is step 0's first genuinely prospective use -- run
before any construction on a brand-new CC0 reference, not retroactively against an already-known
bug. It correctly confirmed `--in-plane-axis X --wide-view front`, and the resulting candidate (a
dual-view-measured elliptical loft, a new construction strategy for this project) reached 0.924339
mean silhouette IoU, the highest of any held-out asset here to date. This is the concrete evidence
the check changes real modeling outcomes, not just avoids a documented past mistake.

**Second gap in this same tool, found live 2026-08-13**: the check only verified that
`--in-plane-axis` and `--wide-view` were self-consistent with EACH OTHER, never that the claimed
`--wide-view` actually matched the reference's own measured aspect ratios (already printed in the
report as `reference_aspect_ratios`, just never checked against). On the hand-plane benchmark this
let a wrong-but-mutually-consistent pair (`--in-plane-axis Y --wide-view side`) report
`orientation_consistent: true`, when the reference itself is wider in front (1.6708) than side
(0.4286). `tools/verify_reference_view_orientation.py` now runs a second, independent check
(`claim_matches_reference`) comparing the claim directly against `reference_aspect_ratios`; both
checks must agree to pass. Confirmed this doesn't regress the desk-lamp evidence above (X still
fails, Y still passes) before relying on it for the hand plane.
