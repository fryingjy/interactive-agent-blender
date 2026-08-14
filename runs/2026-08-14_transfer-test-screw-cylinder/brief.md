# Transfer test: "screw that cylinder" (JL Mussi, 5-tips video)

**Purpose:** the first real transfer test run against the video-learning knowledge base, per
`docs/VIDEO_EXTRACTION_PROTOCOL.md` steps 11-14. Modeling work was paused all session; the user
explicitly lifted the pause for exactly this kind of bounded, single-claim experiment.

## Claim under test

From `runs/2026-08-14_video-study-jl-mussi-5-tips/knowledge_items.json`, item 1: building a
revolved shape from a flat profile plus a Screw modifier keeps the segment count as a live,
changeable modifier parameter, instead of baking a fixed vertex count into the mesh at creation
time the way a standard Cylinder primitive (or this project's own `revolve_closed_profile`) does.

This is the technique flagged in memory (`video-curriculum-mug-diagnosis.md`) as a plausible fix
for the tumbler/mug builds' segment-count problem -- untested until now.

## What was built

A 5-vertex open profile (`ScrewTest_Profile`, a POLY curve, bevel_depth 0, not closed) tracing a
simple waisted cross-section, converted to a mesh (`ScrewTest_Body`), with a Screw modifier
(angle 360 degrees, screw_offset 0 -- a pure revolve, no vertical translation). Every mutation went
through the normal begin/perform/verify/commit decision-transaction protocol, not a raw script.

## Result

| Screw modifier `steps` | evaluated vertices | evaluated faces | degenerate faces | pinch candidates |
|---|---|---|---|---|
| 8  | 40 | 32 | 0 | 0 |
| 16 | 80 | 64 | 0 | 0 |

The base mesh stayed at exactly 5 vertices the entire time -- both evaluated states came from
editing one modifier parameter (`steps`), not from rebuilding anything. Vertex/face counts scaled
exactly proportionally (2x steps -> 2x verts/faces), with zero degenerate faces and zero pinch
candidates at either setting.

**Pass.** Screenshot: `silhouette_16steps.png` (front-view silhouette render at steps=16). Blend
file: `screw_cylinder.blend`.

## Honest limitations

- This tests only the core claim (segment count is live-adjustable post-creation) on a small,
  simple profile. It does not test the claim under later-stacked modifiers (booleans, mirror) the
  way the source video specifically emphasizes ("even after later modifiers like Boolean are
  stacked on top") -- that's a real gap between what was tested and the full claim as captured.
- The open top/bottom rim (no end caps) is expected and intentional for this test -- not a defect,
  just not a finished asset.
- This does not by itself prove the technique would have fixed the mug/tumbler's actual segment-
  count problem, only that the mechanism it depends on works as described. That's a weaker claim,
  recorded honestly as such in the transfer_test entry rather than overstated.
