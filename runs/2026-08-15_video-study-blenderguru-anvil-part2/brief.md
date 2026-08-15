# Blender Guru -- Anvil Modeling Tutorial, Part 2: Boolean

Video `WxMwa0njGSM`, "Blender Intermediate Modelling Tutorial - Part 2: Boolean!" (Andrew Price /
Blender Guru), 22:20 total. Second video in a 4-part anvil-modeling series; Part 1
(`yi87Dap_WOc`, blockout/proportional-editing) was already processed in
`runs/2026-08-14_video-study-blenderguru-anvil/`. This run is transcript-only -- no video frames
were reviewed, so every item below is grounded in narration text and timing, not anything "shown
on screen." Confidence scores reflect that limitation; nothing here exceeds 0.55.

The video's entire content is one worked example: cutting the anvil's angled notch with a
cylinder-shaped Boolean operand, then dealing with the mess that operation leaves behind before a
Subdivision Surface modifier is added. That second half -- the cleanup -- is the part most relevant
to this project's own boolean workflow, which currently has no Weld-modifier step and no
post-boolean-bevel step.

## Most important finding

The video's cleanup method is manual, not modifier-based, and it matches this project's existing
`boolean-groove-cut-topology-cleanup` skill (`knowledge/skills/boolean-groove-cut-topology-cleanup.json`)
more closely than expected: both land on "merge coincident/near-coincident vertices" (Remove
Doubles / merge-by-distance) as the actual fix for boolean seam artifacts, not a Weld modifier.
Neither the project's skill nor this video ever mentions a Weld modifier at all -- Remove Doubles
in edit mode is the tool both use. Where they diverge: the project's existing skill triangulates
remaining n-gons after merging (`bmesh.ops.triangulate`), while this video does the opposite --
it deliberately preserves quads by using the Knife tool (angle-constrained to 45-degree
increments) to manually cut n-gons into new quad faces along existing edge directions *before*
merging, specifically because the target is a Subdivision Surface modifier that needs 4-vertex
faces, not just a manifold, defect-free mesh. That's a real nuance the project's skill doesn't
currently encode: whether n-gon cleanup should triangulate or requad depends on whether SubD is
downstream. Separately, this video never applies a bevel to the boolean seam either -- rounding
the cut edge is explicitly deferred to "the next part" via ordinary support/proximity loops added
after the fact, not a Bevel modifier or bevel weight applied immediately post-boolean. So on both
counts (no Weld modifier, no post-boolean bevel step) the video confirms the project's current gap
rather than closing it -- it shows a working alternative (Remove Doubles + requad via knife, edge
rounding deferred) rather than the two missing mechanisms themselves.

## Items captured (8)

1. DECISION -- Boolean chosen over messy manual vertex-pushing or knife-cut-and-delete-faces as
   the "correct way" to build a cutout region with multiple intersecting slopes.
2. PROCEDURE -- Boolean modifier setup order: position the operand, select the mesh to KEEP (not
   the operand) as active, add the modifier, eyedropper-pick the operand, switch Intersect to
   Difference.
3. VISUAL_CUE -- Object Properties > Viewport Display > Maximum Draw Type = Wire on the operand,
   so its position stays visible while positioning it over solid geometry that would otherwise
   hide the overlap.
4. PROCEDURE -- Cut one side only, then Mirror modifier stacked below Boolean, with a loop cut
   added at the seam before deleting the redundant half (skipping the loop cut leaves the two
   halves unconnected).
5. DECISION -- Duplicate the object to a spare "trash" layer before Apply on any modifier, as
   the only way back once a modifier is applied and undo history is gone.
6. FAILURE -- Boolean output can look clean in flat-shaded Edit Mode while containing n-gons at
   the seam; the defect only becomes visible once Subdivision Surface is applied, producing
   pinched/broken geometry. States the underlying rule: SubD-bound meshes need 4 vertices per
   face everywhere.
7. PROCEDURE -- Knife tool (angle-constrained cuts) + Edge Slide (double-tap G) + Remove Doubles
   as the quad-preserving n-gon cleanup method, contrasted against the instructor's own
   slower "old method" of manual delete-extrude-refill.
8. PROCEDURE -- Closing the remaining open seam by extruding the boundary ring into itself along
   the mirror axis, relying on the Mirror modifier's Clipping option to auto-snap the new edge
   onto the mirror plane instead of leaving unwelded duplicate geometry.

## Not captured as formal items

- The generic definition of what a Boolean operation is (sphere/cube overlap demo, ~163-222s) --
  standard concept explanation, not a technique specific to this project's needs.
- The closing remark that pre-BMesh Blender produced much worse (all-triangle) Boolean results,
  and that many older Blender artists avoid Boolean for that historical reason (~1293-1320s) --
  historical color, not an actionable technique.
- A secondary failure mode noted in passing (~1073-1109s): imprecise operand positioning left
  three vertices needing merging into one instead of two coincident pairs, and ordinary Remove
  Doubles wasn't sufficient -- the instructor added an extra loop cut and used Merge at Center
  (Alt+M) instead. Real but narrow (a symptom of sloppy operand placement rather than a general
  boolean-cleanup technique); worth revisiting only if the same three-way-merge pattern recurs on
  a live build.
- The offhand remark that "there's a bunch of people that just do a bunch of booling stuff now
  and don't worry with the Sub Surf" (~1280-1289s) -- acknowledges cleanup is conditional on
  needing SubD, which is already folded into item 6's claim rather than captured separately.
