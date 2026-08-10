# Planning the Facial Retopology — source-to-skill study

Source: Blender Studio / Julien Kaspar, 08:51, free official lesson with 140 authored-caption
segments. Fifteen decoded frames were sampled, including the general flow, primary/secondary
creases, articulation lines, pole/patch plan, and finished colored topology.

## Observed reasoning

- 01:07–01:46 begins with loops around eyes, nose, mouth, chin, jaw, and temple. These paths support
  both visible shape and muscle movement; they are not generated from even-density aesthetics.
- 02:08–02:22 matches separate eyebrow topology to the face so both deform in unison.
- 03:07–04:00 distinguishes primary creases that exist at rest from secondary creases created by
  compression. Close support loops preserve a hard resting crease; wider loops preserve a smooth
  rest surface while leaving room to compress.
- 04:03–05:32 prioritizes brows, eyelids, and lips as articulation zones. At least three loops define
  an arc; additional perpendicular loops preserve curvature during closed, stretched, or compressed
  poses.
- 05:43–06:33 redirects flow through square/circular patches. Poles move away from creases, hard
  edges, and heavy deformation into flatter, lower-motion, or hidden regions.
- 07:31–08:32 treats the plan as editable: expression requirements can demand new loops and poles.
  Better topology is evaluated by the animated result, not by a static all-quad screenshot alone.

## Different-shape experiment and failure

The existing Blender 5.2 deformation-density lab is a tube bend rather than a face, so it tests the
transferable articulation-density claim without copying the lesson. Under the same 70-degree bend,
the 17-ring quad cage had mean surface error 0.011306 and maximum 0.031818 against the dense
reference. The sparse 5-ring failure rose to 0.029585 mean and 0.097542 maximum. This is 2.62× mean
error and 3.07× maximum error from undersampling articulation.

This does **not** validate facial loop layout, pole placement, mouth interior, or expression shapes.
It validates only the narrower rule that deformation-driven density must be budgeted before the
bend. A facial patch/pole experiment and shape-key expression test remain required.

## Encoded skill

Plan retopology from motion and compression first; reserve loops for articulation and curvature;
route poles through low-motion surfaces; align attached deforming components; and validate with the
actual target poses. Static cleanliness is necessary but not sufficient.
