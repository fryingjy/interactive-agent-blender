# CG Boost -- 100+ Tips to Boost Modeling in Blender (Mesh Modeling chapter)

Curriculum item #4 (`docs/BLENDER_MODELING_CURRICULUM_V2.md`, Level 1, REQUIRED), first pass.
Video `JMBMHSca_j0`, 1:57:05 total. This run covers only the **Mesh Modeling** chapter
(29:22-58:16, tips #30-62 of 101) -- not the full video. The curriculum explicitly frames this
video for a second, differently-focused pass at Level 10 ("why would a professional choose this
tool here"), so a full first-pass transcription of all ~117 minutes in one sitting isn't the right
unit of work; the Mesh Modeling chapter was chosen deliberately because it's the section most
directly relevant to this project's active, real problems (clean topology, hole-cutting, booleans),
not because it's first in the video.

## Context: held-out test restart and scrap, then pivot back to curriculum

Before this run, the session had scrapped a second held-out reference-reconstruction test attempt
(a desk stapler, after the first attempt -- a padlock -- was also scrapped mid-shackle). Direct
user instruction: "scrap the modelling tests and continue with the curriculum until you're done."
`reference/padlock/notes.md` and `reference/stapler/notes.md` are left in place as honest records;
`Stapler_Body` was left in the live Blender scene mid-build (revision 22, base plate + bevel-weight
policy partially applied, Subdivision Surface modifier added) since no destructive cleanup was
requested. This run is the first curriculum work after that pivot.

## Why this chapter, specifically

Tip #31 (Connect Vertex Path, `J`) is a genuine, sourced fix candidate for the T-junction ngon bug
that has now blocked three separate attempts at cutting a hole into an existing face
(`subdivide_selection`/`bisect_selection` on the padlock shackle-hole, 2026-08-14/15, documented in
[[decision_transaction_protocol_gotchas]]). The video explicitly frames `J` as splitting the
existing face itself along the shortest selected-vertex path -- not inserting a vertex into a
shared boundary edge, which is the actual mechanism of the T-junction bug. This has NOT yet been
tested against the project's typed `mesh_ops.py` (no `connect_vertex_path`-equivalent operation
exists there yet); it's captured as a knowledge item with `status: CAPTURED`, not
`TRANSFER_VALIDATED` -- next real step is either adding a typed wrapper for it or testing it via
`execute_blender_code` on a controlled bare-cube case, the same way the extrude-ID bug was
root-caused.

Two more independent alternatives to the same T-junction problem surfaced in the same chapter:
Bridge Edge Loops between two matching-vertex-count opposing faces (tip #48), and Loop Tools'
Circle operator for turning a face patch into a clean circular loop (tip #61) -- both worth keeping
in mind as options depending on the specific hole shape needed, rather than treating "avoid
subdivide/bisect on isolated faces" as a single fix with one answer.

## Items captured (8)

1. Connect Vertex Path (`J`) as a T-junction-avoiding alternative to subdivide/bisect -- HIGHEST
   priority, direct bug-fix candidate.
2. Bridge Edge Loops for direct hole-punching between matching opposing faces.
3. Loop Tools Circle for clean circular holes/bosses without hand-computed arcs.
4. Grid Fill for all-quad capping of open loops (vs. ngon fill or triangle fans).
5. Select All by Trait -> Non-Manifold + Fill + Triangulate + Tris-to-Quads as a batch hole-repair
   pass.
6. Offset Edge Slide for symmetric paired holding loops (SubD-falloff control, alternative to a
   geometric Bevel for the same crispness goal).
7. Bool Tool add-on's Auto Boolean shortcuts -- noted as a Blender-side convenience layer, not a
   capability gap in this project's own typed boolean path (`add_modifier` + `set_modifier_parameter`
   already reach the same result).
8. Merge by Distance vs. Collapse, confirming and clarifying the existing typed `merge_by_distance`
   op's target failure mode (cancelled-extrude/bridge doubles specifically).

## Not captured as formal items (observed, lower transfer value for this project right now)

Tips #30 (multi-object edit mode), #32 (edge slide GG), #34 (auto-merge toggle), #35 (dissolve /
limited dissolve), #36 (extrude-to-cursor), #37 (mesh symmetry in edit mode), #38 (shear tool), #39
(move along normals / shrink-fatten), #41 (interactive bevel in edit mode -- already covered by the
project's own `bevel_selection`), #42 (solidify in edit mode), #43 (boolean in edit mode), #45/#46
(knife tool / knife project), #49 (auto smooth / mark sharp -- already covered by the project's own
`set_smooth_by_angle` + bevel-weight policy), #50 (hide in edit mode), #51 (inset shortcuts --
already covered by `inset_selection`), #53 (sculpt-mode organic grab), #54 (separate by loose
parts -- already covered by `separate_selection`), #55-58 (transform pivot/orientation options),
#59 (repeat history for arrays). These are either UI/workflow conveniences with no clean typed-op
analogue worth adding yet, or techniques this project's typed surface already covers under a
different name -- listed here so a future pass doesn't re-derive the same "not worth a knowledge
item" judgment from scratch.

## Next step for this curriculum item

Remaining chapters not yet processed: User Interface (0:00-24:42), Selection (24:42-29:22),
Transformation (58:16-1:07:24), Modifiers (1:07:24-1:42:01), Organization (1:42:01-1:49:27), Bonus
(1:49:27-1:56:03). Modifiers is the next highest-value chapter (multiple Bevel modifiers, Weld
modifier for beveled booleans, Array patterns, circular arrays) -- worth a dedicated pass before
calling curriculum item #4's first pass complete.
