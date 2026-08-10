# Intro to Sculpting — source-to-skill study

Source: Blender Studio, *Intro to Sculpting*, 25:11, official authored captions. The local media is
ignored by Git; the public ingest report records SHA-256, duration, streams, caption presence, and
20 sampled frames without reproducing the transcript.

## Observed reasoning

- 01:32–02:50 frames sculpting as changing surfaces and volumes; radius and strength determine the
  scale and intensity of that change.
- 06:01–06:37 shows Clay/Clay Strips adding or subtracting while flattening previous strokes. This
  makes them volume-building tools, not detail stamps.
- 08:24–09:36 shows Smooth averaging positions and warns that it can alter volume; Flatten/Fill/
  Scrape instead act relative to a surface plane.
- 12:48 onward uses masking to protect geometry, so local editing strategy includes exclusion, not
  only brush choice.
- 20:13–21:01 ties symmetry to object origin/rotation and distinguishes mirror/radial repetition.
- 21:27–24:08 shows Dyntopo changing local triangle density; constant and relative detail encode
  different scale assumptions.
- 24:29–25:10 presents Multires as the structured coarse-to-fine alternative.

## Different-shape experiment

`multistroke_sculpt_learning.blend` starts from one applied ellipsoid (10,242 vertices), not an
assembly. Five Draw and two Crease operator strokes moved 5,812 vertices, changed signed volume
from 4.523854 to 6.516185, and produced a clean closed surface in an independent Blender process.
The result is a mechanics study, not a claimed production sculpt or aesthetic benchmark.

## Failures and correction

The first scripted attempt returned `FINISHED` seven times but moved zero vertices because the
stroke events had no valid surface-hit locations. `failed_attempt_missing_surface_locations.json`
is retained. The corrected contract requires geometry deltas in addition to operator status.

A repeated broad Smooth control changed volume by +20.94% rather than reproducing the lesson's
typical volume loss. The direction is specific to the scripted hit path and deformed surface; the
generalized skill is therefore **smoothing changes form/volume and requires before/after metrics**,
not “Smooth always shrinks.” This branch is retained as uncontrolled overwork evidence.

## Encoded skill

Plan sculpt passes by form scale; choose brushes by their surface effect; treat topology/detail
mode as a modeling decision; protect regions explicitly; and accept a scripted stroke only when
the mesh changed as intended. A professional organic-form and articulation benchmark remains open.
