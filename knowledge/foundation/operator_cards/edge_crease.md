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

## What this does not establish

- Only tested on a rectangular box fixture within this same lab (a within-lab transfer, box-with-
  support vs. box-without). Transfer to a genuinely different shape family, and application within a
  real held-out modeling task, remain open -- this is `TRANSFER` and `RUNTIME_VALIDATED` work, not yet
  done, per `docs/KNOWLEDGE_SYSTEM.md`'s promotion lifecycle. Status here is `EXPERIMENTALLY_TESTED`
  with one internal transfer, not `PROMOTED`.
- Does not establish when a professional would choose crease over Bevel for a NEW asset (the axe file
  only shows a completed choice, not the design reasoning behind it) -- this is inference, not
  observation, and is flagged as such rather than presented as a firm rule.

## Evidence

`runs/2026-08-13_blend-file-study/battle_axe/` (inspection JSON, crease/node-group dump, reference
render). `runs/2026-08-13_blend-file-study/crease_experiment/` (`crease_vs_bevel_lab.blend`, per-
variant fresh-process verification, silhouette and shaded comparison renders, `report.json`).
