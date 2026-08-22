# Official Blender Fundamentals watering-can reproduction

This B4 lesson reproduces Blender Studio's maintained 4.5 LTS **Modeling the Watering Can**
training. It was selected because the published workflow directly addresses the system's repeated
construction error: the spout and handle are converted, snapped, and bridged into body openings,
not left as separate primitive/tube objects.

The official CC-BY comparison `.blend` and thumbnail remain under ignored `media/`. They were
opened read-only. `official_reference_inspection.json` and
`official_reference_asset_audit.json` retain only structural facts; no official mesh was copied or
appended into the reproduction.

## Result

`watering_can_tutorial_v5.blend` contains one mesh object named `GEO-watering_can` in one
`watering_can` collection. The editable base is one connected positive-X half-cage. Three 2x2 body
patches become eight-vertex openings; eight-sided handle/spout rings bridge directly into those
boundaries. Two added all-quad transition rings implement the lesson's final join-softening step.
The X Mirror uses clipping and merge and remains unapplied.

Fresh-process verification passes:

- one connected base component and one connected evaluated component;
- 554 quads, 16 intentional bottom-cap triangles, zero n-gons, zero degenerate faces;
- positive-X editable half-cage with a live Mirror;
- evaluated height/length `0.6410` versus official `0.6414`;
- evaluated depth/length `0.2987` versus official `0.2810`.

Direct side/isometric comparison is scored **8.1/10**. This is the first strict beginner pass. It
does not authorize intermediate work because the ladder requires two consecutive passes.

## Retained failure and correction chain

V1 is retained as the rejected visual baseline: body too tall, hooked/non-circular handle, and
weak transition shaping. V2–V4 were iterative local checkpoints summarized here rather than
committed as redundant evidence. Corrections were:

1. remove three loose center vertices created inside deleted 2x2 attachment patches;
2. replace a hand-shaped handle with a measured near-circular arc;
3. use a true half-cage plus unapplied clipping/merge Mirror;
4. match the official file's normalized height/length ratio in cage space;
5. add two all-quad transition rings at every bridged attachment and strengthen the shoulder ring.

Remaining visual differences are explicit in `visual_review_v5.json`: the upper handle attachment
is slightly rounder, the collar is stronger, and the rose/internal spout detail is simplified.

Source: <https://studio.blender.org/training/blender-fundamentals-45-lts/blender_4-5_lts_modeling-the-watering-can/>
