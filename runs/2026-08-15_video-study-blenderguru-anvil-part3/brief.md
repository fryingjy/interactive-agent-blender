# Blender Guru -- Anvil Modeling Tutorial, Part 3: Sharpening Edges

Third video in the four-part Blender Guru (Andrew Price) anvil-modeling series (`lITV4F_P4E0`,
18:04). Part 1 was already processed by this project
(`runs/2026-08-14_video-study-blenderguru-anvil/`). This run is transcript-only (auto-generated
captions, no frame analysis) -- everything below is grounded in narration, not in anything
"shown on screen" or "demonstrated visually," since no visual frames were reviewed.

Processed now specifically because the video's stated focus is edge sharpness control under a
Subdivision Surface modifier, which is exactly the open question this project already has live:
the same-day unresolved contradiction between the standing bevel-weight policy (Bevel modifier
ordered *before* Subdivision Surface) and a second source's Bevel-*after*-SubD technique (see
`runs/2026-08-15_video-study-cgboost-100-tips-modifiers/brief.md`).

## Most important finding: a third technique, not a resolution of the Bevel/SubD order question

This video does not use the Bevel modifier at all, at any point, for edge sharpness -- and it does
not use bevel weight either. Its entire sharpening technique is **support loops** (also called
"proximity loops" in the narration): add a loop cut near a target edge and slide it close, which
narrows the span of geometry the Subdivision Surface modifier averages across at that edge,
making it read sharper. More/closer loops equal more sharpness. This is a genuinely distinct third
approach from both sides of the existing contradiction, not evidence for either "before" or
"after."

The video does explicitly evaluate Edge Crease (Shift+E) as an alternative and rejects it as the
primary tool: per the narration (2:00-3:14), crease "doesn't really work in between values" --
it's reliable at maximum but not at partial values like 0.5, giving no real intermediate control.
This doesn't resolve the Bevel/SubD ordering question either, but it's a relevant adjacent data
point: if this project ever considers Edge Crease as a lighter-weight stand-in for bevel-weight,
this source has already flagged a specific, narrated reason not to trust it at partial values.

The video also surfaces a real, recurring failure mode worth carrying forward regardless of which
sharpening technique is used: a loop cut added to sharpen one local edge can wrap all the way
around a connected mesh region and create an unwanted sharp edge somewhere else, invisible until
the model is zoomed out. The video's fix -- vertex-slide (double-tap G) the unwanted loop segment
into an adjacent loop and Remove Doubles, rather than Dissolve/Collapse Edge -- is kept for the
stated reason that it preserves direct visual control over exactly where the loop lands, which a
one-shot dissolve/collapse operator doesn't give you.

## What was captured

- PRINCIPLE: keep the base mesh lean and use Subdivision Surface for resolution/roundness control
  rather than hand-modeling rounded geometry into the base mesh (0:14-1:54).
- DECISION: Edge Crease (Shift+E) rejected as the primary sharpness tool because it only behaves
  predictably at maximum value, not at partial values -- support loops used instead (2:00-3:14).
  Flagged with a `reason` tying it to the live Bevel/SubD contradiction, since this is a third,
  bevel-free technique that touches the same problem space.
- PROCEDURE: the support/proximity-loop technique itself -- add a loop cut near the target edge and
  slide it close to narrow the SubSurf averaging span; add more loops for more sharpness
  (3:47-5:05).
- FAILURE: a loop cut meant to sharpen one edge can wrap around a connected mesh region and create
  an unwanted sharp edge elsewhere, not obvious until zoomed out (11:19-12:03).
- PROCEDURE: the fix for that failure -- vertex-slide (double-tap G) the unwanted segment into an
  adjacent loop, Remove Doubles, fill the gap with F -- preferred over Dissolve/Collapse Edge for
  keeping direct control of exactly where the loop is redirected (12:52-15:17).
- VISUAL_CUE: a mesh region that looks noticeably more rounded/blobby than its neighbors is the
  signal that a support loop is missing there (10:47-10:58).

## Not captured as formal items

The inset-tool-plus-boundary-dissolve sequence (`I` then `B`) used to build the anvil's stepped
horn geometry (6:19-7:26) is a real, narrated procedure but is about general blockout/extrude
workflow, not edge sharpness -- outside this run's stated focus, and not distinct enough from
already-captured extrude/inset knowledge in this project to justify a separate item. The
mirror-modifier clipping behavior noted in passing around 9:49-10:01 is incidental context for
that same section, not a standalone claim. The closing generalization about this being a common,
recurring problem across many kinds of models (car trim/taillight example, 16:04-16:31) repeats
the FAILURE item above in more general terms without adding new mechanical detail, so it wasn't
captured as a separate item.
