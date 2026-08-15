# Blender Guru -- Blender Intermediate Modelling Tutorial, Part 4: Final Touches

Video `9ViVKUiG8ks`, 26:29 total, transcript-only extraction (narration audio, no frames
reviewed). This is the fourth and closing modeling video in Blender Guru's anvil series --
Part 1 was already processed in `runs/2026-08-14_video-study-blenderguru-anvil/`. A separate
UV-unwrapping video follows this one but is out of scope here.

The video is entirely retopology and finishing work on a mesh that's already blocked out:
cleaning up loop-cut placement, fixing edge flow around corners so light reflects in one
continuous line instead of breaking, adding the last two small details (an indent cube and a
circular boss), and closing out with judgment calls about how much polish a given imperfection
is actually worth. No new primitives or major forms are introduced.

## Most important finding

The two decision items about the indent-cube corner (loop-cut sharpness tradeoff, 17:52-19:18;
checking reference before hardening an edge, 19:22-20:01) are the most transferable pair in this
video. The stated logic is explicit and generalizable: a fully-encircling loop cut that would
correctly sharpen one corner can *also* wrongly sharpen an unrelated edge elsewhere on the same
topological loop, with no easy reroute available short of introducing a triangle or ngon. Rather
than treating that as a problem requiring a clever topology solution, the video frames it as a
cost/value question ("how much value do you put on this problem") and settles for a partial fix --
then, on review, discovers via reference photos that the edge shouldn't have been fully sharp
anyway and settles for a Crease instead of added geometry. The lesson compounds: verify the
target sharpness against reference *before* spending effort solving a topology problem that may
not need solving in the first place.

The Alt+M merge-based technique for redirecting edge flow around a corner (delete the face
between two target vertices, merge them together with a chosen target position) recurs twice in
the video as the modeler's preferred fix for T-junction-style edge splits, and is explicitly
contrasted against Ctrl+E Rotate Edge, which is rejected by name as too imprecise to control.

## Items captured (9)

1. Loop-cut confine shortcuts (E to snap shape, F to flip which edge it copies) -- precise
   placement instead of eyeballing an in-between position.
2. DECISION: reject Ctrl+E Rotate Edge in favor of explicit delete-face + Alt+M merge for
   redirecting edge flow, because Rotate Edge is hard to visually orient/control.
3. The delete-face + Alt+M ("At Center") merge procedure itself, plus the double-tap-G /
   Remove Doubles / Delete-Edge cleanup that follows it.
4. FAILURE: deleting an unwanted loop cut by vertex selection also destroys perpendicular edges
   passing through the same vertices; the fix is Edge-select mode + Alt-click the horizontal
   edges specifically, then Delete > Edge Loops.
5. DECISION: accept a one-sided (less sharp) loop cut at a corner rather than a fully-encircling
   one that would wrongly sharpen an unrelated edge on the same loop -- an explicit cost/value
   tradeoff, not an oversight.
6. PRINCIPLE: check reference photos for actual edge sharpness before hardening an edge with
   geometry or a Crease -- the video's real final choice (Crease only, no added loop cut) came
   from discovering the reference showed the edge is smooth, not sharp.
7. VISUAL_CUE: Matcap shading (Display > matcap) reveals creases that default solid shading can
   hide depending on the current light angle.
8. PRINCIPLE: topology-perfection effort should scale with whether the mesh will ever deform --
   static props tolerate imperfections that a rigged character could not.
9. DECISION: duplicate the object and park the copy in a trash collection before applying a
   Mirror modifier, as a cheap backup against a destructive, hard-to-reverse operation.

## Not captured as formal items

The indent-cube and circular-boss construction itself (basic extrude-down + loop-cut-to-fix-
rounded-corners) is mechanically identical to loop-cut techniques already captured from Part 1
and items 1/4 above -- not elevated separately. The mid-video aside about a viewer-feedback
survey and a possible future course (23:41-24:56) is channel business, not modeling content. The
closing recap (24:56-26:29) is a spoken summary of "what you learned" with no new mechanical
claims beyond what's already captured, plus a pointer to the next (UV-unwrapping) video, which is
out of scope for this run.

This closes out first-pass coverage of the 4-part Blender Guru anvil modeling series. Parts 2 and
3 are being processed in parallel by other agents in `runs/2026-08-15_video-study-blenderguru-anvil-part2/`
and `runs/2026-08-15_video-study-blenderguru-anvil-part3/`.
