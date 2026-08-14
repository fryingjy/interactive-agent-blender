# Operator card: Edge Crease (Subdivision Surface sharp-edge protection)

**Status:** RUNTIME EXPERIMENT ✓ (Blender 5.2.0 LTS) | TYPED SUPPORT ✓ | TRANSFER ✓ (within-lab) | SOURCE ✓ (professional `.blend`) | RUNTIME TRANSFER pending

## What it does

Edge crease (Blender's `crease_edge` float attribute, 0-1, authored via Ctrl+E > Edge Crease or the
N-panel) tells a Subdivision Surface modifier to pull its limit surface toward the control cage at
that edge, resisting the modifier's own smoothing. At crease value 1.0 the edge reads as fully sharp.

This is genuinely different from Bevel, not a weaker substitute for it:

- **Bevel** adds real new geometry (a physical chamfer) to create an explicit, controllable radius.
  Needed whenever the reference shows a visible flat/rounded strip at that edge.
- **Crease** adds no geometry at all. It only protects an existing edge from an already-active SubD
  modifier's smoothing. Needed when an edge just has to stay sharp/flat, with no visible chamfer
  width required.

They are complementary, not competing: a real object can use Bevel on edges that need a specific
physical radius and Crease on edges that just need to stay flat, in the same mesh.

## Origin: found by studying a professional `.blend`, not invented from documentation alone

`docs/BLEND_FILE_STUDY_PROTOCOL.md` was followed against a professional battle-axe reference file
(`battle axe.blend`, `runs/2026-08-13_blend-file-study/battle_axe/`). All 5 of its objects (blade,
guard, handle, pommel, wrap) use full edge crease (value 1.0, confirmed by direct inspection of the
`crease_edge` attribute) for every sharp edge, and **zero Bevel modifiers appear anywhere in the
file**. Shading uses a "Smooth by Angle"-equivalent Geometry Nodes group (node-for-node identical to
Blender's own `shade_smooth_by_angle` output: Edge Angle -> Compare -> Boolean Math -> Set Shade
Smooth), confirming this project's existing shading policy independently. This project had never used
crease as a sharp-edge mechanism before this; every prior asset used Bevel + WEIGHT exclusively.

## Reproduction and a real failure mode found along the way

`runs/2026-08-13_blend-file-study/crease_experiment/` (`tools/run_crease_vs_bevel_lab.py`) tested the
principle on a controlled fixture (a rectangular box, crease/bevel only its 4 vertical edges, leave
top/bottom edges free to round under SubD):

- **A** (no protection): rounds into a blob, as expected (negative control).
- **B** (crease, single quad per side face, no internal support): the creased edges themselves stayed
  sharp, but each unsupported flat face **pillowed** (bulged outward) under SubD anyway -- a real,
  initially unexpected failure this lab caught rather than assumed away. Crease protects an edge, not
  the face it bounds; a bare single-quad face has nothing to resist SubD inflating its center.
- **C** (Bevel + WEIGHT instead): stayed genuinely flat, no pillowing, because Bevel adds its own
  physical geometry independent of the surrounding cage's density.
- **D** (crease, same edges, but each face pre-subdivided into a 3x3 grid first): pillowing
  disappeared entirely -- the flat, sharp read now matches C almost exactly.

This confirms and generalizes an already-known project principle
(`knowledge/foundation/operator_cards/topology_context_subd.md`: sparse/uneven density raises
evaluated area variation) rather than contradicting it: **crease-only sharp edges require the cage to
already have adequate supporting face density.** The professional axe file's objects all have
substantial base density (112-1092 verts) for exactly this reason -- it is not incidental.

Evaluated geometry cost, same base cage, same 4 protected edges:

| Variant | Evaluated vertices | Non-manifold edges | Notes |
| --- | --- | --- | --- |
| B (crease, no support) | 98 | 0 | pillowed -- visually wrong |
| C (Bevel + WEIGHT) | 290 | 0 | flat, correct |
| D (crease, with support) | 218 | 0 | flat, correct, still cheaper than Bevel |

Crease adds **zero** vertices over the unprotected baseline (A and B both evaluate to 98 verts); Bevel
roughly triples the evaluated vertex count on this fixture. When a flat/sharp read is all that's
needed (no explicit chamfer width), crease is markedly cheaper, provided the cage density
precondition is met.

## Typed support

`blender_ops/object_ops.py`'s `set_edge_crease_by_ids(name, edge_ids, value=1.0, clear_others=False)`
writes the `crease_edge` attribute via persistent edge IDs (mirrors `set_bevel_weight_by_ids`'s
pattern exactly) and records `hard_surface_intended_crease_edge_ids` for later audit. Registered in
`blender_ops/modeler_server.py`'s `_OPS` for the typed decision-transaction protocol.

`hard_surface_shading_audit()` now recognizes a third sanctioned path (`crease_path_ok`) alongside the
existing WEIGHT-Bevel and ANGLE/VGROUP-Bevel paths: intended crease IDs matching actual creased edges,
with no Bevel-before-SubD ordering requirement when no Bevel modifier is present at all (crease has no
such dependency -- the SubD modifier reads crease values directly). Verified live: a crease-only
object with zero Bevel modifiers reaches `status: "PASS"`.

## Failure modes

- **Pillowing on sparse cages** (see above) -- the actual failure mode this card's own reproduction
  hit. Check face density, not just edge crease values, before trusting a crease-only sharp read.
- Crease has no independent width/segment control the way Bevel does; if the reference needs a
  specific visible chamfer size, crease cannot provide it regardless of cage density.
- A crease value between 0 and 1 (not just full 0 or full 1) partially resists smoothing rather than
  fully protecting the edge -- this card only tested and validated the full-crease (1.0) case, matching
  what the studied professional file actually used. Partial crease remains untested here.

## Cross-file confirmation (9 more professional files studied, 2026-08-13)

Extending the study to the other 9 files the user provided
(`runs/2026-08-13_blend-file-study/`) gives a real pattern for WHEN professionals reach for crease
vs. Bevel, not just that both exist:

- **Stylized/fantasy weapons** (`axe.blend`, `batarang.blend`, `adventure time sword.blend`,
  `broken sword.blend`) predominantly use crease, matching `battle axe.blend`.
- **Precision mechanical firearms** (`ap15.blend`: 38 objects, real Bevel+SubD throughout;
  `ak47.blend`: 129 objects, Bevel used 90 times vs. crease essentially absent) predominantly use
  Bevel instead.

Read together, this is a legible, evidence-based heuristic rather than an arbitrary style choice:
Bevel's explicit, controllable physical radius suits machined/manufactured precision edges (panel
lines, slide serrations); crease's cheaper, softer sharp read suits sculptural/stylized forms where
no specific chamfer width needs to be legible. `bat.blend` (a plain tapered baseball bat, single
object, no modifiers at all beyond Smooth by Angle) is the useful negative case: a genuinely simple
round/tapered form needs neither technique, only adequate base density.

`batarang.blend`'s "Plane" object also has a Bevel modifier present with **zero edges actually
weighted** (0/224) alongside 73/224 edges creased -- direct evidence that a Bevel modifier merely
existing in the stack is not evidence it's doing anything; check the actual weighted/creased edge
count, not just modifier presence, matching this project's own `hard_surface_shading_audit()`
discipline.

## Video source (2026-08-13, via CloudGlue): a mechanistic "why" for the crease-vs-Bevel heuristic

`SOURCE OBSERVATION`, not yet experimentally verified -- keep separate from the tested findings
above per `docs/RESEARCH_ROADMAP.md`'s four knowledge layers. "The MOST IMPORTANT Hard Surface
Modeling Tip - Edge Creasing" (youtube.com/watch?v=3sXbUC7l70w, retrieved and comprehended via the
CloudGlue MCP connector, full scene-by-scene transcript with timestamps) argues against using crease
for hard-surface work, on two claims:

1. **A crease value between roughly 0.7 and 1.0 produces visually identical results** ("0.7, 0.71,
   0.72, 73, all the way up until 1, it's all the same") -- a specific, testable claim this card's
   own "what this does not establish" section already flagged as untested (only full crease=1.0 has
   been tried here). Not yet reproduced.
2. **A mathematically sharp edge (crease or otherwise zero-radius) reads less realistic under smooth
   shading than a small real Bevel radius**, because a true zero-width edge cannot catch the subtle
   specular highlight a physical chamfer does -- demonstrated by comparing a 2-level-SubD creased
   cube (looks flat/synthetic, described in the video as "Minecraft"-like) against the same cube with
   a small Bevel instead (reads as a realistic manufactured edge).

**This is not a contradiction of the findings above -- it's a missing mechanistic reason, and it
refines rather than overturns the existing crease-vs-Bevel heuristic.** Claim 2 is not really about
crease as a mechanism; it's that *any* fully-sharp (value-1.0) edge, however produced, lacks a
highlight a nonzero-radius chamfer has. The battle axe's crease-only choice is for a stylized asset
where a fully-sharp read matches the reference's own intended look -- claim 2 would predict exactly
this same "flat, no micro-highlight" character there, and the reference shows that character, so this
is consistent, not contradictory. It sharpens the existing heuristic's "why": precision mechanical
firearms (`ap15.blend`, `ak47.blend`) use real Bevel not merely by convention but because a
manufactured edge visibly needs the highlight a physical radius provides; stylized weapons use crease
because the reference calls for a flatter, non-highlighted read where that highlight would look wrong.

Claim 1 (0.7-1.0 crease values behaving identically) is a concrete, cheap experiment to run before
trusting it -- not yet done. Neither claim changes this card's own tested conclusion that crease with
adequate support produces a genuinely flat, non-pillowed result; they add a *when to prefer Bevel over
crease even though crease "works"* consideration (the reference wants a visible highlight) that this
card did not previously have a mechanistic reason for.

## What this does not establish

- Only tested on a rectangular box fixture within this same lab (a within-lab transfer, box-with-
  support vs. box-without). Transfer to a genuinely different shape family, and application within a
  real held-out modeling task, remain open -- this is `TRANSFER` and `RUNTIME_VALIDATED` work, not yet
  done, per `docs/KNOWLEDGE_SYSTEM.md`'s promotion lifecycle. Status here is `EXPERIMENTALLY_TESTED`
  with one internal transfer, not `PROMOTED`.
- Does not establish when a professional would choose crease over Bevel for a NEW asset (the axe file
  only shows a completed choice, not the design reasoning behind it) -- this is inference, not
  observation, and is flagged as such rather than presented as a firm rule.

## CRITICAL failure mode found on real transfer: crease breaks roundness on a revolved ring's own loop

Found live rebuilding the watering can (`runs/2026-08-13_watering-can-rebuild/`, a genuinely
different shape family from the box lab -- this is the cross-shape-family transfer the section above
flagged as open, and it surfaced a real negative result, not a clean pass).

Building the lid (a hemisphere dome lofted from stacked circular rings), the seat and shoulder rim
loops were creased the same way the box lab creased its 4 vertical edges. The first render showed the
dome as a visibly faceted 16-gon, not round at all. Root cause, understood only after direct visual
inspection caught it (automated fresh-process checks all passed -- this was purely a shading/visual
defect): **Bevel and crease are not interchangeable "sharp edge" mechanisms even when both are legal
choices for the same edge.** A WEIGHT Bevel modifier *replaces* the sharp edge with fresh, unweighted
geometry (a chamfer band); that new geometry has no crease/weight on its own tangential edges, so it is
still free to round under a later Subdivision Surface. Crease has no such replacement -- it freezes
the *exact* edges you give it in place, permanently. For a straight edge (the box lab's vertical
edges) that costs nothing, since a straight line has no curvature to lose. For a **ring's own
circumferential loop on a revolved/lofted shape**, those edges ARE the polygon's cross-sectional
shape -- creasing them locks in the discrete N-gon forever, no matter the Subdivision Surface level.

**Rule going forward: never crease a ring's own tangential loop on a circular-loft part if that ring
needs to read as round.** Crease is for edges that are already straight/planar in their own tangential
direction (a box edge, a panel-line break on a flat face) -- never for a boundary loop of a lofted
revolve where the very shape being protected is the curve itself. If a circular-loft part needs a
genuine hard seam (the vessel's rim, where a real stamped-metal fold is visible in the reference),
Bevel+WEIGHT is the correct mechanism, not crease -- confirmed by the vessel's own rim staying
perfectly round in the same rebuild. Where the reference shows no seam at all (the dome, the spout
taper), the honest fix is no hard-edge treatment whatsoever, not defaulting to crease just because it
exists as an option (see `mark_no_sharp_edges_needed`, added the same session for exactly this case).

## Second, subtler failure mode: Smooth by Angle can silently reproduce the same bug

After fixing the crease mistake above, the lid's small knob (built at half the ring density, 8 sides,
no crease or Bevel applied at all) still rendered as a visible octagon. Cause: `shade_smooth_by_angle`
marks BASE-mesh edges sharp wherever the angle between their two adjacent faces exceeds its threshold
(30 degrees by default), and Subdivision Surface then respects that sharp flag exactly like a manual
crease. An 8-sided boss has a 45-degree turning angle between adjacent side faces -- past the
threshold -- so it got marked sharp automatically and stayed faceted under SubD regardless of
subdivision level, with no explicit crease call anywhere. The dome and vessel (16 sides, 22.5 degrees)
never hit this because they sit under the threshold. **Any circular detail with fewer than roughly 12
sides is at real risk of Smooth by Angle silently locking in its own facets** -- this is the same
underlying failure as the crease mistake above, triggered automatically rather than by an explicit
call, so it is easy to miss even after fixing the first bug. Fixed by giving the knob the same ring
density as the rest of the dome (16 sides) rather than halving it for a "small detail."

## Evidence

`runs/2026-08-13_blend-file-study/battle_axe/` (inspection JSON, crease/node-group dump, reference
render). `runs/2026-08-13_blend-file-study/crease_experiment/` (`crease_vs_bevel_lab.blend`, per-
variant fresh-process verification, silhouette and shaded comparison renders, `report.json`).
