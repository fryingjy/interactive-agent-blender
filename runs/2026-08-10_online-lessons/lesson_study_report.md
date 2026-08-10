# Official Blender Fundamentals lesson study

**Date:** 2026-08-10

**Sources:** Blender-authored CC BY 3.0 videos mirrored by Wikimedia Commons

**Modalities actually processed:** decoded video frames, audio, local machine transcript

**Transcript backend:** faster-whisper `tiny.en`, CPU `int8`
**Rule:** machine transcript wording is fallible; important claims below are corroborated by frames,
current official documentation, or controlled Blender 5.2 evidence.

## Modeling Introduction (75.401 s)

Source observations:

- 00:08.8-00:16.8: modeling is presented as Edit Mode manipulation of mesh vertices, edges, and faces.
- 00:22.2-00:32.3: Extrude, Bevel, Knife, and Loop Cut are identified as central modeling tools.
- 00:37.1-00:48.1: modifiers are introduced as part of the modeling workflow.

Interpretation: modeling strategy is not “add primitives until the outline is close”; it is staged
control of mesh elements and modifiers. This directly rejects the failed chair approach as
professional evidence.

## Extrude (286.901 s)

Source observations:

- 00:25.2-00:46.2: an extrusion duplicates the selection, moves it, and creates connecting
  geometry; a successful command is therefore not enough—new side topology must be inspected.
- 01:15.2-02:06.2: cancelling movement can leave coincident extruded geometry. The lesson advises
  a true undo when the extrusion itself was accidental.
- 02:34.2-02:56.2: Extrude Along Normals keeps a multi-face region connected while displacing by
  face normals.
- 02:56.2-03:18.2: Extrude Individual deliberately disconnects the behavior of neighboring faces
  and is appropriate only when independent projections are intended.

Corroboration: the current Blender Manual operator inventory and existing typed extrude labs record
the same topology/selection distinctions. No new skill is promoted solely from the video.

## Bevel Tool (211.361 s)

Source observations:

- 00:24.2-00:31.2: destructive Edit Mode bevel and non-destructive Bevel modifier are separate
  strategy choices.
- 01:04.2-01:28.2: width type changes the meaning of bevel amount; segments control resolution;
  profile controls curvature. More segments are not automatically better.
- 01:48.2-02:31.2: bevel faces can use a material index, which must correspond to an actual object
  material slot.
- 02:31.2-03:20.2: modifier Limit Method changes which edges are affected; Angle is selective,
  while Weight and Vertex Group permit explicit targeting.

Corroboration: Blender 5.2 bevel/modifier cards and controlled modifier labs already verify limit,
profile, clamp, scale, and material-slot consequences. The lesson strengthens source breadth but
does not erase the remaining custom-profile/width-type experiment gap.

## Learning disposition

- Source observations remain distinct from interpretation and experiments.
- Existing Extrude and Bevel skills are **reinforced**, not newly promoted.
- Blender 2.80 UI details are version-limited; conceptual claims were checked against Blender 5.2
  documentation/evidence.
- Speech comprehension is now genuinely present through timestamped machine transcripts, but exact
  wording is not treated as authoritative.
