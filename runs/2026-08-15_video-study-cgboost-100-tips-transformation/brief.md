# CG Boost -- 100+ Tips to Boost Modeling in Blender (Transformation chapter)

Third chapter of curriculum item #4's first pass (see
[[../2026-08-15_video-study-cgboost-100-tips-meshmodeling/brief.md]] for the Mesh Modeling chapter
and [[../2026-08-15_video-study-cgboost-100-tips-modifiers/brief.md]] for the Modifiers chapter,
plus the overall video's scope). This run covers **Transformation** (58:16-1:07:24, tips #63-73 of
101). Unlike the two prior chapter passes, this one is transcript-only: no frame/video-understanding
observations were available, just auto-generated-caption text with [M:SS] timestamps. Confidence on
every item here is therefore kept in the 0.4-0.55 band regardless of how explicit the narration
sounds, and every `supporting_evidence` field is a direct transcript quote or close paraphrase, never
a claim about what was "shown on screen."

## Most relevant findings for this project's open problems

**Snap to Surface (tip #68)** is a second, independent mechanism -- distinct from the Shrinkwrap
modifier already flagged in [[video-curriculum-mug-diagnosis]] and confirmed again in the Modifiers
chapter pass -- for conforming a secondary part to a curved host. It combines Face snapping + Align
Rotation to Target + Project Individual Elements to snap an object's position and orientation onto a
surface interactively while moving it (G + hold Ctrl). It is captured as its own item rather than
folded into the Shrinkwrap hypothesis because the mechanism is genuinely different: this is a one-time
interactive snap at the moment of placement (well suited to scattering discrete parts, e.g. bolts),
not a persistent modifier that keeps re-conforming the part if the host mesh changes later. It does
not resolve the mug's handle problem on its own (a handle is a continuous strip, not a discrete
snapped instance), but it's a relevant tool for the bolt/hardware-scattering use case described in
the same chapter.

**Duplicate Linked (Alt+D) / Copy Object Data (Ctrl+L) / the "temporary link data" trick (tips
#69-71)** form one coherent kitbash workflow: Alt+D shares mesh data across instances (so editing one
instance's geometry updates every instance, while modifiers stay independently adjustable per
instance); Ctrl+L > Object Data retroactively links objects that were duplicated independently by
mistake; and the "duplicate at a convenient pose, edit, delete the duplicate" trick lets a mesh that's
awkwardly transformed be edited without ever touching its actual transform, because the edit
propagates through the shared mesh data-block before the duplicate is thrown away. All three are
directly applicable to any future modular/repeated-hardware asset (bolts, rivets, standardized
brackets) this project builds.

## Other items captured

- Alt+G / Alt+R / Alt+S (tip #63) -- one-key reset of location/rotation/scale, useful during
  iterative modeling to clear exploratory transforms.
- Move tool's "Origins" option (tip #65) -- repositions an object's origin using ordinary
  transform/snap tools instead of the 3D-cursor-based origin-setting menu.
- Move tool's "Parents" option (tip #66) -- transforms a parent object without dragging its children,
  for correcting a parent's placement after children are already positioned relative to it.
- Copy Transform Data via the N-panel's right-click "Copy All to Selected" on Location/Rotation (tip
  #73) -- precisely aligns one object's origin to another's; distinguished in the item's own reason
  field from Snap-to-Surface/Shrinkwrap since it aligns origin-to-origin rather than conforming a
  footprint to a curved surface.

## Not captured as formal items

Tip #64 (always-show transform gizmo via the viewport-gizmos dropdown) is a pure display-preference
convenience with no typed-op-surface implication, so it was left out. Tip #67 (changing the distance
between two selected objects by enabling "Location" under the Scale tool's options, so pressing S
moves rather than resizes them) and tip #72 (Object > Transform > Randomize Transform, with per-axis
location/rotation/scale randomization and an "Even" uniform-scale option) were both left out of the
captured set to stay within the 5-8 distinct-item range for this pass -- both are real, usable
techniques (tip #67 for spacing/exploding parts, tip #72 for de-uniforming a batch of Duplicate-Linked
hardware so it doesn't read as obviously copy-pasted) and are reasonable candidates to add if a future
asset actually needs them.

## Remaining chapters for curriculum item #4

User Interface (0:00-24:42), Selection (24:42-29:22), Organization (1:42:01-1:49:27), Bonus
(1:49:27-1:56:03) still not processed. None flagged as urgent the way Mesh Modeling, Modifiers, and
this chapter were -- lower priority for a future pass, not blocking.
