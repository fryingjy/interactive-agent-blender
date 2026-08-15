# Documentation study: Bevel, Weighted Normal, Bridge Edge Loops (official manual)

**New source type for this project: the official Blender manual (bundled RST, accessed via
`mcp__Blender__search_manual_docs`), not a video.** Started per direct instruction to actually learn
the documentation, not just skim it -- extracted real, cited knowledge items the same way a video
gets processed, with `source_id` pointing at the manual page instead of a YouTube ID.

## What was read

Three connected manual pages, chosen because they're directly relevant to standing project policy
and an unresolved bug from this session, not picked at random:

- `manual/modeling/meshes/editing/edge/bevel.rst` -- full Bevel tool/modifier reference (Harden
  Normals, Clamp Overlap, Miter Outer/Inner, Face Strength, Loop Slide, Profile Type).
- `manual/modeling/modifiers/normals/weighted_normal.rst` -- Weighted Normal modifier, specifically
  the Face Influence option that consumes Bevel's Face Strength tagging.
- `manual/modeling/meshes/editing/edge/bridge_edge_loops.rst` -- Bridge Edge Loops options
  (Connect Loops, Merge, Twist, Number of Cuts, Interpolation).

## Why these three, not a random sample

1. This project has a standing "bevel-weight policy" for new hard-surface assets
   (`blender_modeling_technique_corrections.md`). Reading Bevel's Face Strength option and
   Weighted Normal's Face Influence option together explains the actual mechanism that policy
   depends on -- confirmed it's a winner-take-all (strongest face wins at a shared vertex), not a
   blend, which the project's own prior work never explicitly verified against the source.
2. Bevel's Miter Outer/Inner options are documented explicitly as existing to avoid pinching at
   multi-edge intersections -- directly relevant to this project's own pinch-candidate surface
   diagnostics (`get_evaluated_defect_regions`, `classify_surface_defect_cause`).
3. **Bridge Edge Loops' Twist parameter directly root-causes an unresolved bug from earlier in this
   session.** The teapot handle's second attachment attempt (`runs/2026-08-14_teapot-body-revolve/`)
   produced a twisted/crossed bridge connecting a 10-vertex loop to a 12-vertex loop -- at the time,
   logged as "confirmed real, root cause not fully understood." The manual states plainly that
   Bridge Edge Loops' vertex correspondence is a positional offset ("Twist") that isn't guaranteed
   correct by default, and this project's own `bridge_selection` wrapper
   (`blender_ops/mesh_ops.py`) never exposed that parameter at all. This isn't a new hypothesis --
   it's the documented mechanism, read directly from the source that defines the operator's own
   behavior.

## What this changes

- Five knowledge items captured, all `CAPTURED` status (documentation-sourced items don't get a
  transfer test the same way a video-sourced technique does -- these are direct factual claims
  about tool behavior, verifiable by reading the same manual page again, not requiring a build to
  confirm).
- Updated `decision_transaction_protocol_gotchas.md` (the memory entry already tracking the
  teapot's bridge-twist bug) with this root cause, replacing "unresolved, not fully understood"
  with a concrete, documented mechanism and a real next step: expose `twist` as a parameter on
  `bridge_selection` before attempting the handle's loop closure a third time.

## Scope honesty

This is three pages out of a manual with many hundreds. Treating "read the whole Blender
documentation" as a single pass is not realistic -- this establishes the pattern (search
purposefully, extract cited claims, connect findings back to real project work) to repeat on an
ongoing basis, the same way the video curriculum is worked through level by level rather than all
at once. Forums (Blender Stack Exchange, Blender Artists) are a separate, not-yet-started source
under the same standing instruction.
