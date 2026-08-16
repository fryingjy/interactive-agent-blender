# Real official-video episode review: Loop Cut chair blockout

This run independently checks one short modeling episode from **Loop Cut -
Blender 2.80 Fundamentals** (Blender / Dillon Gu), hosted on Wikimedia Commons
under CC BY 3.0. The temporary WebM was decoded with Blender's Video Sequence
Editor; it is not retained in this repository.

The four retained PNG checkpoints are evidence for the specific 151–178 second
episode only. `episode_evidence.json` records the frame observations and the
small, timestamped machine-transcript excerpts used for the review. It does not
claim a complete transcript or a substitute for the video.

The verified result is intentionally narrow: loop cuts are placed where a
single continuous mesh needs later-selectable face regions, rather than added
as generic density. `loopcut_chair_transfer.blend` reproduces that principle:
one cube is flattened, receives two purposeful loop-cut decisions, then grows
four legs and a back from its own faces. It has one connected all-quad mesh and
a live, unapplied `Manual Bevel - Unapplied` modifier; `chair_transfer_solid.png`
is its workbench-solid review render. This is not a claim of a finished or
reference-accurate chair.
