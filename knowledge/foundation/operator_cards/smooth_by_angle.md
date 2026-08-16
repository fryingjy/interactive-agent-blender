# Operator card: Smooth by Angle / hard-surface normal policy

**Status:** RUNTIME EXPERIMENT ✓ (Blender 5.2.0 LTS) | TYPED SUPPORT ✓ | FAILURE BOUNDARY ✓ | RUNTIME TRANSFER pending

## What it does

`bpy.ops.object.shade_smooth_by_angle(angle, keep_sharp_edges)` controls normal interpolation
across a mesh. It is Blender's current Smooth by Angle action in the object shading workflow.
It does **not** add an edge radius, support loop, or any other geometry. A hard-surface object
that is merely smooth-shaded can still look melted because the control cage never encoded its
intended edges.

### Current Blender UI/API terminology

On the installed Blender 5.2.0 LTS runtime, the related Object Mode operators are distinct:

- **Shade Auto Smooth** — `bpy.ops.object.shade_auto_smooth(use_auto_smooth=True, angle=...)`.
  It adds a live `Smooth by Angle` Geometry Nodes modifier, pinned last in the stack.
- **Shade Smooth by Angle** — `bpy.ops.object.shade_smooth_by_angle(angle=...,
  keep_sharp_edges=True)`. This is the typed modeler path because it preserves explicitly marked
  sharp edges while establishing the same normal-policy outcome.

Both control normal interpolation; neither authors physical sharpness. `Shade Smooth` alone is not
an equivalent hard-surface policy. This distinction was checked directly in Blender 5.2.0 LTS on
2026-08-16 and matches the current Manual's [object shading](https://docs.blender.org/manual/en/latest/scene_layout/object/editing/shading.html), [edge data](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html), and [Bevel modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html) documentation.

The installed Blender 5.2.0 LTS runtime was exercised with `angle=0.5235987756` (30 degrees) and
`keep_sharp_edges=True`; both the operator result and the selected policy are recorded in the saved
lab artifact below. The relevant manual/API entry points to cross-check for a later Blender version
are [object shading](https://docs.blender.org/manual/en/latest/scene_layout/object/editing/shading.html),
[edge data](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html),
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
- Equal segment count does not guarantee circular highlight quality. A controlled 12-sided circle
  with alternating 20°/40° spacing retained `5.0°` analytic side-normal error even when Harden
  Normals perfectly removed Bevel-induced error; Weighted Normal increased it to `9.9988°`.
- Weighting every edge creates uncontrolled highlight breakup and does not mean every edge is a
  physical design edge.
- A Bevel cannot undo a capsule-like base shape. Rebuild the primary cage when the silhouette is
  already wrong.

## Confirmed failure: a geometric-angle threshold is not a valid sharp-edge selector

This is the "weighting every edge" bullet above, but it was reproduced at scale by automation, not
just theorized, and is worth its own record. This session's no-Bevel triage corrective scripts
(`runs/2026-08-12_watering-can-secondary-bevel-corrective/`,
`runs/2026-08-12_telephone-handset-bevel-corrective/`) selected sharp edges by a single rule: any
edge with a dihedral angle over 25 degrees between its two faces gets a real geometric Bevel weight.
Direct human visual review against the reference photos, and a follow-up comparison confirming it,
found this was wrong for round members: the watering can's `Rose_Head`, `Connected_Tapered_Spout`,
`Arched_Handle`, and the telephone's `Handset` are all smoothly rounded forms in their source
photos. The rule conflates two different things:

1. **Shading hardness** -- already handled correctly by Smooth by Angle alone, from geometric angle,
   with no Bevel modifier needed at all.
2. **Physical edge rounding** -- a real geometric operation that should only be applied where the
   reference shows an actual machined/pressed seam.

On a low-segment-count round member (8-16 sides around the circumference, not 100+), the natural
angle between adjacent segments is large simply because there are few segments -- not because those
edges are an intended hard transition. The rule selected nearly every circumferential edge on these
parts and gave each one a real chamfer, turning "faceted-but-smoothly-shaded" (correct, matches the
reference) into "actually faceted" (wrong, reads as a cut gemstone instead of a rounded nozzle or a
bakelite receiver). `runs/2026-08-12_watering-can-rounded-parts-bevel-reverted/` and
`runs/2026-08-12_telephone-handset-bevel-reverted/` remove the incorrect weighting, keeping only
Smooth by Angle -- the same strategy `Connected_Vessel` already used successfully (real Bevel weight
only at its genuine rim/shoulder seams, smooth shading elsewhere via adequate segment count).

**The rule to apply instead:** decide which edges are sharp by checking the reference photo for that
specific part, not by measuring an angle on the low-poly proxy. A part that reads as continuously
curved in the reference (a nozzle, a handle, a receiver, a tube) should get Smooth by Angle alone,
regardless of how large its base-cage facet angles are. A part that reads as having a real seam,
lip, or machined edge in the reference gets `WEIGHT`-limited Bevel at exactly that seam. The technical
audit (`get_hard_surface_shading_audit`) can verify that recorded intent matches the applied
weights, but it cannot judge whether the intent itself was correct -- that check has to be a
reference comparison, done per object, not a blanket geometric rule applied to every untreated
object in one pass.

## What correct selection actually looks like (live artist-scene inspection)

Read-only inspection (`mcp__blender__execute_blender_code`, no file saved or mutated) of the user's
own live reference scene -- a hard-surface mechanical plate and a faceted crystal-blade sword, both
`Mirror -> Bevel(WEIGHT) -> Subdivision -> Smooth by Angle` -- makes the correct rule concrete:

- **The mechanical plate**: all 153 weighted edges have a two-face dihedral angle of 90-146 degrees,
  and none of them are mirror-seam edges. It is a simple box-derived part, so every real design edge
  happens to be a right angle, and the mirror seam is a flat, invisible plane with nothing to
  preserve. A threshold rule would have accidentally worked here -- which is exactly why it looked
  plausible in the first place.
- **The sword blade**: 43 weighted edges span 0-90.5 degrees, and a meaningful fraction of them
  (edges with only one linked face in the base half-mesh) are **mirror-seam edges along the blade's
  centerline** -- weighted specifically so the central ridge stays crisp once Mirror joins the two
  halves and Subdivision would otherwise round it away. The remaining weighted edges trace one
  continuous facet line running from the guard to the tip, and its measured angle changes
  continuously along that single line -- about 67 degrees near the wide base, down to about 15
  degrees near the narrow tip -- because the blade tapers. It is one intentional design line the
  whole way, selected because it *is* that line, not because any individual edge cleared a angle
  cutoff; a fixed threshold would have silently dropped its tip half.

**The actual rule:** trace continuous design lines across the surface -- a mirror-seam ridge that
should stay visible, a facet boundary that runs from one landmark to another -- and weight every
edge along that traced line, even as its local angle drifts. Do not evaluate edges independently by
angle. Whether a mirror seam itself needs weighting depends on whether the seam is a visible ridge
in the design (the sword) or an invisible flat plane (the mechanical plate) -- another case that
requires looking at the actual shape, not a rule that applies uniformly to every Mirror modifier.

## Evidence

`runs/2026-08-12_hard-surface-shading-policy/` saves a Blender 5.2 lab scene and JSON report, 20/20
assertions passing. It verifies four deliberate vertical rails, persistent-ID weight assignment,
`BEVEL -> SUBSURF` order, and Smooth by Angle without treating blanket smooth shading as the policy.
A second fixture is unannotated, blanket smooth, and non-uniformly scaled; the audit correctly
returns `REVIEW_REQUIRED` rather than passing it on technical mesh validity. A third fixture uses a
real `ANGLE`-limited Bevel configured directly through `bpy` with no `set_bevel_scoping` call; it
also stays `REVIEW_REQUIRED`. A fourth fixture uses `set_bevel_scoping` through the real typed
decision lifecycle and reaches `PASS`, proving the new mechanism is a genuine second auditable path
rather than a blanket exemption for `ANGLE`/`VGROUP`. (The `ANGLE`-limited-Bevel example that
originally motivated this mechanism was a held-out boombox benchmark, removed 2026-08-12 after being
rejected on visual review for unrelated reasons -- color and proportion, not its bevel construction;
the mechanism itself is validated independently by these lab fixtures.)
