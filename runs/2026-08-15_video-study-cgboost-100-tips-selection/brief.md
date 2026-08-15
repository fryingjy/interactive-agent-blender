# CG Boost -- 100+ Tips to Boost Modeling in Blender (Selection chapter)

Third chapter of curriculum item #4's first pass (see
[[../2026-08-15_video-study-cgboost-100-tips-meshmodeling/brief.md]] for the Mesh Modeling chapter
and [[../2026-08-15_video-study-cgboost-100-tips-modifiers/brief.md]] for the Modifiers chapter).
This run covers **Selection** (24:42-29:22, tips #23-29 of 101). Unlike the two prior chapter
passes, no video-understanding tool was used here -- only a plain transcript-with-timestamps text
file was available (auto-generated captions, no frames). Supporting evidence below is quoted
narration, not a description of what was seen on screen.

## Scope note

This is a short chapter (~5 minutes, 7 tips) and several of the tips are simple, low-transfer-value
keyboard shortcuts. Per the task instructions, only the mechanically interesting techniques were
captured as formal items (5, not 7) -- the trivial ones are listed under "not captured" below rather
than padded into items for their own sake.

## Items captured (5)

1. **Select Linked with Delimit: Seam** (tip #24, [25:01]-[25:46]) -- `L` floods a connected
   selection; setting Delimit to Seam in the operator panel bounds that flood-fill to the area
   inside marked UV seams, letting one keypress select a named mesh region instead of manually
   selecting its boundary.
2. **Invert-selection strategy** (tip #25, [25:46]-[26:13]) -- captured as a `DECISION`: to select
   "everything except one part," select the smaller/simpler excluded part first and press Ctrl+I,
   rather than selecting all and manually Shift+L-deselecting the unwanted part. The narration
   explicitly frames the manual-deselect approach as getting harder as mesh complexity increases.
3. **Checker Deselect** (tip #26, [25:59]-[26:36]) -- deselects every Nth element of a selected loop
   with adjustable select-count/deselect-count/offset, demonstrated feeding directly into an extrude
   for an alternating pattern effect.
4. **Select Shortest Path / Fill Region** (tip #27, [26:43]-[27:35]) -- Ctrl+click selects the
   shortest path between two elements (with Face Stepping / Topology Distance sub-options); the
   related Fill Region option (direct shortcut: Ctrl+Shift+click) selects an entire enclosed patch
   between two faces in one action. Flagged as the chapter's most mechanically interesting tool --
   the narration itself calls it "one of the coolest selection features."
5. **Select Similar (Shift+G)** (tip #29, [28:21]-[29:16]) -- selects every other element sharing a
   property with the active selection: Bevel (Weight) in edge mode, Face Normal with an adjustable
   threshold in face/vertex mode, and object-level properties like Type in Object Mode.

None of these are framed in the transcript as resolving a specific problem this project has already
hit (unlike the Mesh Modeling chapter's T-junction fix candidates) -- they are captured as generally
transferable selection techniques, at the lower end of the confidence range (0.5-0.55) appropriate
for transcript-only extraction.

## Not captured as formal items

Tip #23 (Select More/Less via Ctrl+Numpad+/-, [24:44]-[25:01]) -- a basic, widely-known grow/shrink
shortcut with no further nuance in the narration. Tip #28 (Select Random, [27:39]-[28:24]) --
percentage/seed/select-vs-deselect controls for randomly selecting elements, demonstrated only as a
throwaway Alt+S deform ("looks pretty ugly" per the narration) with no stated modeling use case worth
recording as a transferable claim. Both are straightforward enough that a future pass can re-derive
them from the tip list without a dedicated knowledge item.

## Remaining chapters for curriculum item #4

User Interface (0:00-24:42), Transformation (58:16-1:07:24), Organization (1:42:01-1:49:27), Bonus
(1:49:27-1:56:03) still not processed. None flagged as urgent the way Mesh Modeling and Modifiers
were -- lower priority for a future pass, not blocking.
