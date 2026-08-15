# CG Boost -- 100+ Tips to Boost Modeling in Blender (Organization chapter)

Third chapter of curriculum item #4's first pass (see
[[../2026-08-15_video-study-cgboost-100-tips-meshmodeling/brief.md]] for the Mesh Modeling chapter
and [[../2026-08-15_video-study-cgboost-100-tips-modifiers/brief.md]] for the Modifiers chapter and
the overall video's scope). This run covers **Organization** (1:42:01-1:49:27, tips #94-100 of 101):
Quickly Rename and Batch Rename, Collections Galore, Move to Collection, Instancing Collections,
Mirror Collections, Collection Instances with 3D Cursor Offset, and Parent in Outliner.

This chapter was processed transcript-only (auto-generated captions, no frames available), so
confidence on every item is capped in the 0.4-0.55 range and supporting evidence is cited as "per
the narration" rather than "shown on screen" -- nothing here was visually verified, only heard.

## Most important finding: two real alternatives to whole-object Mirror, at a different scope than the modifier

Tips #97-98 (Instancing Collections, Mirror Collections) describe a mechanism this project has not
captured before: a Collection Instance (Shift+A > Collection Instance) generalizes Alt+D's
linked-duplicate behavior from a single object to an entire multi-object group, and applying Ctrl+M
to that instance mirrors the whole group as one live-linked unit -- any edit to the source
sub-collection propagates to the mirrored side automatically. This is a genuinely different mechanism
from the already-captured Mirror-modifier-Bisect finding (Modifiers chapter): Bisect operates inside
one object's own mesh data via a modifier, while Mirror Collections operates across an arbitrary
multi-object sub-assembly at the collection level. Recorded as two DECISION items, not folded into
the modifier finding, since they solve different scope problems (single-mesh symmetry vs.
whole-assembly symmetry) rather than one superseding the other.

## Second finding: this chapter's nesting axis is orthogonal to the Model/low-poly convention, not a replacement for it

Tip #95 (Collections Galore) demonstrates nesting collections by functional/anatomical part-group
(head, tank, arms, with left/right arm nested further inside arms) so each group's visibility can be
toggled independently. This project's own standing convention (blender-modeling-technique-corrections.md
#4) splits collections by purpose/LOD -- a Model collection and a low-poly collection. Nothing in this
chapter contradicts that convention; the part-group nesting shown here looks like it would nest inside
a Model or low-poly collection (one more level of organization by body part, not an alternative
top-level split), but this combination has not actually been tried on a built asset, so it is recorded
as an open question rather than a settled extension.

## Other items captured

- Move to Collection via the M shortcut (tip #96) -- moves the current selection into an existing
  collection or a newly named one in one step, without needing the Outliner visible (works even with
  the viewport maximized via Ctrl+Space).
- Collection Instance origin defaults to the world/scene origin regardless of where the source
  collection's contents sit (tip #99) -- recorded as a FAILURE item since the video frames it
  explicitly as "a small problem." Fix: snap the 3D cursor to an object inside the source collection,
  then use that object's Object Properties > Collections > "Set Offset from Cursor" to reposition the
  whole collection's instancing origin. Directly relevant any time tips #97/#98 above are used on a
  source collection that isn't centered at world origin.
- Parent directly in the Outliner via Shift+drag-drop, and clear a parent the same way by dragging
  onto a collection row instead (tip #100) -- lower-friction than Ctrl+P from the viewport when already
  working in the Outliner to sort collections.

## Not captured as formal items

Tip #94 (Quickly Rename / Batch Rename via F2 and Ctrl+F2) -- pure UI/workflow convenience for
renaming one or many objects at once, with no modeling-technique or typed-op-surface implication, in
line with how similarly trivial UI-convenience tips were excluded from the Modifiers chapter pass.

## Remaining chapters for curriculum item #4

User Interface (0:00-24:42), Selection (24:42-29:22), Transformation (58:16-1:07:24), Bonus
(1:49:27-1:56:03) still not processed. None flagged as urgent -- lower priority for a future pass, not
blocking.
