# CG Boost -- 100+ Tips to Boost Modeling in Blender (User Interface chapter)

Third chapter of curriculum item #4's first pass (see
[[../2026-08-15_video-study-cgboost-100-tips-meshmodeling/brief.md]] and
[[../2026-08-15_video-study-cgboost-100-tips-modifiers/brief.md]] for the Mesh Modeling and
Modifiers chapters and the overall video's scope). This run covers **User Interface**
(0:00-24:42, tips #01-22 of 101), the first chapter of the video chronologically but the third one
processed for this curriculum item, picked up now mainly to close out the earlier chapters rather
than because it was flagged as high-value.

This pass is transcript-only: extraction is from the auto-generated caption transcript with
timestamps, not from reviewed video frames. No claim below should be read as "shown on screen" or
"demonstrated visually" -- only as "per the transcript." Confidence is capped in the 0.4-0.55 range
across all items for that reason, versus the 0.5-0.6 range used in the two earlier chapters, which
had frame-level video-understanding observations backing some claims.

## Why fewer items than the earlier chapters, deliberately

This chapter is UI/viewport/navigation convenience (shading modes, pie menus, panel pinning, search
menu, math in number fields, tooltip settings, and so on), not hard-surface mesh or modifier
technique. This project's current priorities rank topology, SubD, and boolean/bevel workflow well
above viewport ergonomics, so this chapter is genuinely lower-value for active work right now. The
Mesh Modeling and Modifiers chapters each captured 8 items because they contained specific,
technique-level, transferable modeling decisions (T-junction avoidance, bevel/SubD ordering,
boolean cleanup). This chapter mostly contains keyboard-shortcut trivia (mode pie menu, wireframe
toggle, splash-screen/tooltip preferences, F9 to reopen the last operator panel, F1 for the online
manual) with no modeling-judgment content to extract -- so only 7 items were captured here, and the
bar for inclusion was "does this change how a shape gets read or isolated while modeling," not
"is this a useful shortcut."

## Items captured (7)

1. MatCap switching to reveal surface imperfections that studio-lighting shading hides (VISUAL_CUE).
2. Cavity shading's two independently-tunable modes -- Screen (sharp, thin, edge-focused) vs. World
   (soft, wide, AO-like) -- for reading edge crispness vs. overall shape depth (PRINCIPLE).
3. Random per-object viewport colors as a fast way to check whether visually-touching geometry is
   actually one object or two (PROCEDURE).
4. Local View (`/` on Numpad) as the preferred way to isolate a subset of the scene, over the
   hide-then-invert-then-hide pattern, because the latter's "unhide everything" step disturbs
   unrelated, deliberately-hidden objects (DECISION).
5. Align View to Face Normal (Shift+Numpad7) as a way to visually detect that a face isn't actually
   flush/flat, by looking straight down its normal (PROCEDURE).
6. Clipping Region (Alt+B) as a non-destructive, view-only way to see and edit inside an enclosed
   shape without deleting or hiding any of its own geometry (PROCEDURE).
7. Quad View (Ctrl+Alt+Q) and its Lock/Box/Clip sidebar options for simultaneous multi-angle
   reference while modeling (PROCEDURE).

## Not captured as formal items (skimmed, no transferable modeling-judgment content)

Mode Pie Menu (Ctrl+Tab) and the Tab-for-pie-menu / pie-menu-on-drag preference toggle, Viewport
Shading Pie Menu (Z), X-Ray toggle (Alt+Z), Frame Selected (Numpad `.`/`,`, or View > Frame
Selected, or right-click > View > Show Active in the outliner), the three 3D-viewport navigation
preferences (zoom to mouse position, auto depth, orbit around selection), disabling the splash
screen and tooltips (and the Alt-hold-to-temporarily-show-tooltip trick), the F3 search menu,
typing math expressions directly into any numeric field, click-drag to change multiple X/Y/Z values
at once, Backspace to reset a hovered value to default, Shift-drag for slow/fine-precision
adjustments, pinning sidebar panels (Shift+left-click) so they stay visible across tabs, F9 to
reopen the last operator's redo panel, and F1 to jump to the online manual page for a
hovered-over feature. All of these are real, usable Blender shortcuts, but none of them carry a
modeling decision, a visual diagnostic technique, or a procedure specific to shape-building -- they
are interface/input-efficiency habits that don't have a clean analogue in this project's typed
decision-transaction/mesh_ops surface and wouldn't change any modeling outcome, only the speed of
getting there. Recorded here so a future pass doesn't re-derive the same "not worth a knowledge
item" judgment from scratch.

## Remaining chapters for curriculum item #4

Selection (24:42-29:22), Transformation (58:16-1:07:24), Organization (1:42:01-1:49:27), Bonus
(1:49:27-1:56:03) still not processed. None flagged as urgent the way Mesh Modeling and Modifiers
were; Selection is the smallest remaining chapter and the most likely to contain a small number of
genuinely useful items (selection-by-trait patterns), similar in character to this one.
