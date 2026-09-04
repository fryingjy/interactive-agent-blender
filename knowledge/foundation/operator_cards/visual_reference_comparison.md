# Visual reference comparison

## Use

Measure whether a modeling edit improves reference agreement across multiple views without letting
camera reframing conceal proportion changes.

## Procedure

Before silhouette comparison or blockout, create construction cards only from a declared principal
view. `create_reference_image` records a FRONT, RIGHT, or TOP Image Empty and
`audit_reference_images` measures its saved world normal. A CUSTOM/free-view card is contextual,
not calibrated construction evidence. Distinct axes also require distinct same-target sources when
the board claims actual multi-view coverage; rotating one duplicated image supplies no new view.

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
  same angle against the actual reference before spending time "fixing" it, not just after.
- A per-height cross-section sweep (an ellipse or any other center+extent parameterization, however
  many independent parameters it takes) cannot represent a form with a genuine hook or overhang --
  a component that curls back over itself is not star-shaped from any central axis at any height, no
  matter how the cross-section is fit. Silhouette IoU can still read as high (front/side/top
  projections can each look reasonable) while the actual 3D form is unrecognizable. A form like this
  needs real component decomposition (separate parts for the overhanging piece, built from a traced
  or hand-placed profile) instead.
- **Building the primary construction plane along the wrong world axis is invisible until first
  render, and by then real construction time is already spent.** `render_silhouette`'s "front" looks
  along -Y (exposes the X-Z plane) and "side" looks along +X (exposes the Y-Z plane) -- not the
  reverse, and not something to assume from a reference image's own front/side labeling. A
  full-length articulated desk-lamp candidate was built in the X-Z plane while its reference's full
  profile was the Y-Z plane, producing a side-view IoU of 0.0045 (a near-complete miss) that was
  indistinguishable from a genuine proportion failure until the axes were checked directly. Step 0
  above exists specifically to catch this before it happens again.

- **A quick visual glance can be wrong in the opposite direction from the boombox/wrench lesson.**
  Those established that an automated pass (silhouette IoU, fresh-process checks) is not proof of
  visual fidelity -- always look at the render. But looking is not infallible either: rebuilding the
  watering can's vessel, a highly visually prominent curved element sitting right at one end (the
  domed lid) repeatedly produced the wrong quick-glance judgment about which end of the tapered body
  was actually wider, on at least four separate look-again attempts across one session, including a
  scale-matched side-by-side overlay that itself likely had an uncorrected alignment artifact. Five
  independent, non-redundant measurement methods (dense alpha-channel row profile, hard-edge
  verification against shadow contamination, independent color-threshold measurement, precise dot
  markers plotted at exact measured coordinates, and the top-down view's ring signature) all agreed
  with each other and against the repeated glance. Neither "trust the automated number" nor "trust
  the first glance" is safe alone on a shape with one visually dominant curved feature next to a
  subtler, larger-extent flat taper -- corroborate across independent methods before locking in a
  proportion decision, especially direction (wider-here-vs-there), not just magnitude.

## Evidence

`runs/2026-08-16_real-video-reference-setup-review/` independently verifies the public lesson's
perspective-import failure and orthographic re-import correction. The native 24–124 s Gemini range
pass keeps absolute source timestamps and avoids the later drift caught in the whole-video pass.
`runs/2026-08-16_reference-image-alignment-transfer/` reproduces FRONT alignment at 0° and transfers
it to distinct FRONT/RIGHT cards at 0°/0°; a CUSTOM card and a duplicated-source two-axis control
both remain rejected. This proves Blender setup state only, not source calibration or likeness.

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

`runs/2026-08-13_watering-can-rebuild/reference_analysis.md` records the vessel-taper glance-vs-
measurement conflict in full (all five corroborating methods, the recorded conflict block per
`docs/REFERENCE_PROTOCOL.md`'s format, and the resolved component evidence).
