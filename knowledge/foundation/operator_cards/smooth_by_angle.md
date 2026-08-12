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

`get_hard_surface_shading_audit(name)` is a read-only runtime review. It checks recorded semantic
edge intent against the actual weight attribute, WEIGHT-Bevel presence/order, Smooth by Angle,
and non-uniform scale. It deliberately returns `REVIEW_REQUIRED` when intent is absent: it cannot
truthfully infer every sharp design edge from arbitrary geometry.

`ANGLE` and `VGROUP`-limited Bevel are recognized as distinct, real scoping mechanisms (reported in
`bevel_limit_methods_present`) and given a more accurate warning than "no bevel at all" when no
intent is recorded. A retroactive run against the four already-published held-out families
(`runs/2026-08-12_shading-policy-retroactive-audit/`) found the boombox's real construction uses
`ANGLE`/`VGROUP`-limited Bevel extensively with no `WEIGHT` bevel anywhere; that is a legitimate,
documented technique (`bevel_modifier.md` records `ANGLE` correctly excluding coplanar triangulation
edges), not equivalent to having no deliberate edge treatment.

`set_bevel_scoping(name, method, angle_deg=..., vertex_group=..., width=..., segments=...)` is a
second sanctioned decision operation, alongside `set_bevel_weight_by_ids`, giving `ANGLE`/`VGROUP`
their own auditable path to `PASS` instead of only a softer warning. It records the caller's
parameter as a deliberate claim (`hard_surface_bevel_scoping_method` plus the matching
`hard_surface_bevel_angle_deg` or `hard_surface_bevel_vertex_group` property) -- not a default value
the caller happened to leave untouched. The audit's `angle_or_vgroup_intent_recorded` and
`angle_or_vgroup_intent_matches_actual` checks require both the property and the modifier's actual
parameter to agree. This is strictly additive: an `ANGLE`/`VGROUP` Bevel configured directly through
`bpy` (as every one of the boombox's 30 existing objects were, before this operation existed) never
retroactively gains recorded intent and still returns `REVIEW_REQUIRED` -- the lab's third fixture
proves this explicitly (`unrecorded_angle_bevel_still_review_required`), alongside a fourth fixture
that reaches `PASS` through the real typed decision lifecycle
(`recorded_angle_intent_reaches_pass`).

The lab runs each operation through `ModelerServer`'s
`begin_decision -> perform_decision -> verify_decision -> commit_decision` path. The semantic
weight decision advances revision `0 -> 1`; Smooth by Angle advances it `1 -> 2`. An initial
fixture variant added modifiers between those decisions outside the transaction and was correctly
rejected as an external modifier-state edit. Fixture creation therefore occurs before the first
runtime observation; real modifier changes must be their own typed decisions.

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

`runs/2026-08-12_hard-surface-shading-policy/` saves a Blender 5.2 lab scene and JSON report, 18/18
assertions passing. It verifies four deliberate vertical rails, persistent-ID weight assignment,
`BEVEL -> SUBSURF` order, and Smooth by Angle without treating blanket smooth shading as the policy.
A second fixture is unannotated, blanket smooth, and non-uniformly scaled; the audit correctly
returns `REVIEW_REQUIRED` rather than passing it on technical mesh validity. A third fixture uses a
real `ANGLE`-limited Bevel configured directly through `bpy` (reproducing the boombox pattern) with
no `set_bevel_scoping` call; it also stays `REVIEW_REQUIRED`. A fourth fixture uses
`set_bevel_scoping` through the real typed decision lifecycle and reaches `PASS`, proving the new
mechanism is a genuine second auditable path rather than a blanket exemption for `ANGLE`/`VGROUP`.
