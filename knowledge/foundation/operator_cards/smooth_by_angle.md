# Operator card: Smooth by Angle / hard-surface normal policy

**Status:** RUNTIME EXPERIMENT ✓ (Blender 5.2.0 LTS) | TYPED SUPPORT ✓ | FAILURE BOUNDARY ✓ | RUNTIME TRANSFER pending

## What it does

`bpy.ops.object.shade_smooth_by_angle(angle, keep_sharp_edges)` controls normal interpolation
across a mesh. It is Blender's current Smooth by Angle action in the object shading workflow.
It does **not** add an edge radius, support loop, or any other geometry. A hard-surface object
that is merely smooth-shaded can still look melted because the control cage never encoded its
intended edges.

The installed Blender 5.2.0 LTS runtime was exercised with `angle=0.5235987756` (30 degrees) and
`keep_sharp_edges=True`; both the operator result and the selected policy are recorded in the saved
lab artifact below. The relevant manual/API entry points to cross-check for a later Blender version
are [Normals](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/normals.html)
and [`bpy.ops.object`](https://docs.blender.org/api/current/bpy.ops.object.html).

## Hard-surface decision sequence

1. Inspect the base cage and classify transitions: flat design break, curved shell, intentionally
   rounded edge, or purely visual seam.
2. Use the smallest compatible cage. A literal box remains a box until its intended corner rails
   are deliberately beveled; do not pre-round it and expect later settings to recover crispness.
3. Assign the `bevel_weight_edge` attribute only to intended sharp design edges using persistent
   edge IDs (`set_bevel_weight_by_ids`). Tight support loops that only control a SubD transition are
   normally not weighted.
4. Add a WEIGHT-limited Bevel for the actual edge radius. If the shell genuinely needs SubD, put
   Bevel before SubD and inspect both stages.
5. Apply Smooth by Angle to finish normal interpolation, preserving explicit sharp edges where
   appropriate. Inspect Solid/MatCap highlights and evaluated geometry from oblique views.

## Tested typed operations

- `set_bevel_weight_by_ids(name, edge_ids, weight=1.0, clear_others=False)` writes the generic
  Blender 5 edge attribute through stable persistent edge IDs. It requires Object Mode and reports
  requested IDs that no longer exist rather than silently weighting a renumbered edge.
- `set_smooth_by_angle(name, angle=0.5235987756, keep_sharp_edges=True)` makes the object active,
  runs Blender's operator, and records the selected normal policy on the object.

Both are sanctioned decision operations; the agent must still observe the current cage and make one
semantic decision before calling them. They are not procedural asset generators.

## Failure boundary

- Blanket `polygon.use_smooth=True` is not a hard-surface default. It changes appearance only and
  can conceal missing bevels or an already over-rounded cage.
- Smooth by Angle cannot make a low-sided circular control circular, repair poor topology, or make
  an unjustified SubD modifier appropriate.
- Weighting every edge creates uncontrolled highlight breakup and does not mean every edge is a
  physical design edge.
- A Bevel cannot undo a capsule-like base shape. Rebuild the primary cage when the silhouette is
  already wrong.

## Evidence

`runs/2026-08-12_hard-surface-shading-policy/` saves a Blender 5.2 lab scene and JSON report. It
verifies four deliberate vertical rails, persistent-ID weight assignment, `BEVEL -> SUBSURF` order,
and Smooth by Angle without treating blanket smooth shading as the policy.
