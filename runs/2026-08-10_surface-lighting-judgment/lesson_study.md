# Three Point Lighting — source-to-skill study

Source: Blender Studio, *Three Point Lighting*, 06:42, official lesson with 130 authored-caption
segments. Twelve decoded frames cover key, fill, rim, placement, relative intensity, and light-type
adaptation.

## Observed reasoning

- 00:39–01:01 assigns the key as the main directional statement.
- 01:02–01:20 uses a weaker fill to preserve shadow detail and control contrast rather than erase it.
- 01:20–01:43 places a bright rim/back light to separate the silhouette from the background.
- 03:24–04:27 treats relative position and power as purposeful, not a fixed preset.
- 05:21–06:30 changes the rim from omnidirectional point to directed spot to retain the subject rim
  without washing the environment. The lesson ends by explicitly framing the setup as adaptable.

## Different-shape experiment

One continuous curved product surface was duplicated with identical topology, material, camera,
engine, resolution, and exposure. The defect copy has a localized 0.065-unit dent and rebound ring
that does not change silhouette. Clean and defective versions were rendered under a broad frontal
control and under an asymmetric key/fill/rim review rig.

The final grazing-key rig increased clean-versus-defect mean RGB difference from 0.000972 to
0.002497 (2.57×) and pixels over the 0.015 threshold from 2,628 to 7,691 (2.93×). Both meshes passed
fresh-process topology, manifold, normal, and degeneracy verification.

## Failures and correction

- Attempt 1 wrote four renders but tried to read an empty transient `Render Result` buffer. The
  verifier now reloads durable PNGs before measurement.
- Attempt 2 used a conventional but non-grazing three-light placement and made the dent *less*
  visible than the frontal control (0.34× mean difference). It is retained because three lights do
  not automatically form a diagnostic rig.
- The corrected key is small and grazing across the tested surface. This is a review-lighting rule,
  not a universal beauty-light preset.

## Encoded skill

Use light roles deliberately, but orient the key to the surface feature being judged. Keep fill weak
enough to preserve diagnostic contrast, use rim for silhouette separation, and compare clean/control
or before/after renders with fixed camera/material/exposure. Lighting can hide a defect as easily as
it can reveal one.
