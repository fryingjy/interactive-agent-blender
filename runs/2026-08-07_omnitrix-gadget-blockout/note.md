# Session note: sci-fi wristband gadget (first image-reference milestone)

Reference: `reference/omnitrix_gadget/reference_image.png` + `reference/omnitrix_gadget/notes.md`
(see that file for why this image was chosen over the user's literal "simplest" instruction --
their reference folder was dominated by weapon content the master directive excludes).

## What this session actually did: PRIMARY BLOCKOUT stage only

Per `docs/MASTER_DIRECTIVE.md` section 11, primary blockout only needs to pass "major proportions
plausible, primary silhouette sufficiently close, component layout stable" -- it explicitly should
NOT include detail work yet ("do not polish detail while the major form is still wrong"). This
session reached that stage and stopped there deliberately, not because the prop is finished.

Four separate objects, matching the reference's real component seams (dome / band / two buttons),
each created via `create_primitive` (free, pre-decision scaffolding, same convention as every
earlier prop) then adjusted via 2 real, individually verified typed decisions
(`decision_log.jsonl`, `gadget_001`/`gadget_002`):

1. `GadgetDome`: UV sphere (16 seg/8 ring -- deliberately light for a blockout-stage cage, not the
   default 32/16), scaled Z to 0.6 to approximate the reference's squat, flattened dome profile
   rather than a full sphere.
2. `GadgetBand`: torus (major_radius 0.5, minor_radius 0.22), rotated 90 deg about X so its loop
   stands vertically with the hole axis along Y -- verified directly via world-space vertex bbox
   (X/Z span 1.44 = ring diameter, Y span 0.42 = ring thickness) rather than trusting the rotation
   math unchecked.
3. `GadgetDome` moved +0.35 on Z (decision `gadget_002`) to nest onto the band's top surface,
   closing a real gap found by inspecting actual coordinates (band top at world Z=0.67, dome
   bottom at Z=0.2 before the move).
4. `GadgetButtonL`/`GadgetButtonR`: small cylinders, rotated 90 deg about Y to point outward
   along X, flanking the dome at its equator height -- free scaffolding, not yet adjusted via a
   verified decision.

## Real, honestly-stated limitations of this first pass -- not fixed yet

Rendered via the new multi-object `render_silhouette` (front + side, both saved in `renders/`)
and compared against the reference by eye, not just assumed correct:

- The reference's band shows a visible GAP (a wrist would insert there) -- this blockout's band is
  a closed, gapless torus. Not addressed yet.
- The reference's dome has a flat-ish angled top face with a hazard-symbol graphic and a distinct
  raised bezel ring -- this blockout's dome is a plain flattened sphere with no such features.
- All proportions (dome radius 0.5, band major/minor radius, button size/placement) are estimated
  by eye from the reference image, not measured against any pixel/scale reference -- expect real
  adjustment once compared more carefully.
- The reference is a 3/4-angle photo; this session's silhouette comparisons used clean front/side
  orthographic views, which is a reasonable first pass but not a like-for-like comparison to the
  actual reference framing.

This is genuinely a rough first blockout, stated as such -- not "matches the reference," per the
master directive's anti-fake-progress rules (section 54): technical validity (clean topology, 0
non-manifold across all four objects) is not being presented as visual/reference quality.

## Next steps (not started)

- Add the band gap (a real topology change, not just a visual gap).
- Add the dome's bezel/top-face detail as separate blockout components once major form is judged
  stable.
- A more careful pixel-level comparison between the rendered silhouette and the actual reference
  image (the directive's own described "Blender-native silhouette comparison -> local correction"
  loop) before calling PRIMARY BLOCKOUT complete and moving to TOPOLOGY/SURFACE stage.
