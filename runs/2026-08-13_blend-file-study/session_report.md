# Blend file study: battle axe.blend

First real pass through `docs/BLEND_FILE_STUDY_PROTOCOL.md`'s loop, run against `battle axe.blend`
(one of ten files the user provided as professional modeling study material). This is a report of
what the loop actually produced, not a substitute for it -- the operational deliverable is the new
`set_edge_crease_by_ids` typed operation and the `edge_crease.md` card, not this document.

## INSPECT (read-only; the source file was never modified)

`tools/inspect_blend_file.py` and `tools/inspect_blend_crease_and_nodes.py` opened the file, recorded
raw facts, and exited without saving. Full data in `battle_axe/inspection.json` and
`battle_axe/crease_and_nodes.json`. Key OBSERVED facts:

- 5 objects: `blade`, `guard`, `handle`, `pommel`, `wrap` -- a genuine component decomposition, not
  one continuous swept form.
- Zero Bevel modifiers anywhere. Every sharp edge on all 5 objects uses full edge crease (value 1.0)
  instead.
- A Geometry Nodes modifier named "Auto Smooth" on 4 of 5 objects, node-for-node identical to
  Blender's own `shade_smooth_by_angle` output.
- `blade` uses Mirror (Y axis); `wrap` uses Solidify (offset -1.0) then Subdivision then Auto Smooth.
- Base cages: 112-1092 verts per object, not minimal.
- 0 ngons across all 5 objects (1 stray triangle on `blade` only).

## UNDERSTAND (separating observed fact from inference)

OBSERVED: the file uses crease exclusively, never Bevel, for sharp edges. INFERRED (not directly
readable from the file, a plausible guess about why): the artist likely chose crease because none of
this prop's edges needed an explicit physical chamfer width -- everything reads as either sharp
(crease) or already-curved-in-the-cage (SubD), never as a machined bevel highlight. This inference is
flagged as such and not treated as a confirmed fact.

## EXTRACT PRINCIPLE

Crease and Bevel are not interchangeable "sharp edge" mechanisms -- they solve different problems
(protect an edge from an active SubD modifier's smoothing, vs. add an explicit physical radius as new
geometry) and can be combined or used independently depending on what the reference actually needs.

## REPRODUCE

`tools/run_crease_vs_bevel_lab.py`, `crease_experiment/`. A controlled fixture (protect 4 vertical
edges of a box, leave 8 horizontal edges free) tested the principle directly, and caught a real,
initially unexpected failure mode along the way rather than confirming the hypothesis blindly:

| Variant | Technique | Evaluated verts | Result |
| --- | --- | --- | --- |
| A | none (control) | 98 | rounds into a blob |
| B | crease only, no face support | 98 | edges sharp, but faces **pillow** (bulge) |
| C | Bevel + WEIGHT | 290 | flat, correct |
| D | crease + supported faces | 218 | flat, correct |

B's pillowing was not assumed away -- it was rendered, seen, and used to form a second hypothesis
(inadequate face support), which D then tested and confirmed. All four variants independently
verified fresh-process clean (0 non-manifold edges, 0 degenerate faces) after fixing two real bugs
found along the way in the lab fixture itself (a duplicate-face artifact from misusing
`inset_individual`, then simplified to a topologically trivial box to remove that variable entirely).

## TRANSFER

Within-lab only so far: box-without-support (B) vs. box-with-support (D) is a transfer of the
technique across a support-density variable, not yet across a different shape family. Recorded
honestly as a limitation in `edge_crease.md`, not overstated.

## VALIDATE

D's fresh-process verification (0 non-manifold edges, 0 degenerate faces) plus the direct visual
comparison (D's render matches C's almost exactly) is the validation for the "crease + support works"
half of the principle. The "crease without support pillows" half is validated by B's own render and
stats. `hard_surface_shading_audit()` extended with a third sanctioned path (`crease_path_ok`) and
confirmed live: a crease-only object with zero Bevel modifiers now reaches `status: "PASS"`.

## STORE

- `blender_ops/object_ops.py`: `set_edge_crease_by_ids()` (new), `hard_surface_shading_audit()`
  extended with the crease path, registered in `blender_ops/modeler_server.py`'s `_OPS`.
- `knowledge/foundation/operator_cards/edge_crease.md` (new card).
- `knowledge/foundation/operator_cards/mandatory_mesh_editing_inventory.md` and
  `tests/test_knowledge_engine.py` updated to include Crease in the mandatory operator inventory.
- `knowledge/foundation/topic_coverage_matrix.md` updated.
- `knowledge/foundation/source_registry.json`: registered as `professional-blend-battle-axe`,
  `source_type: "professional_blend_file"`, a deliberate minimal schema extension (`blend_data: true`
  access modality) rather than a parallel system, per the protocol's own instruction.

## APPLY / MEASURE

Not yet done in this session -- the typed operation and audit path are ready to use, but have not yet
been applied to a real held-out modeling task. This is the next real step for this specific
capability, separate from continuing to the remaining 9 provided files.

## What this does not establish (as of the first file, battle axe)

- Only one of ten provided files studied so far.
- No genuine cross-shape-family transfer test yet, only within-lab.
- No real-task application/measurement yet.
- The "why crease over Bevel" reasoning is inference, not observed fact, and is documented as such.

## Addendum: the remaining 9 files (lighter-weight pass)

The first file (battle axe) got the full reproduce/transfer/validate/store cycle because it
surfaced a genuinely new capability (edge crease). The remaining 9 files
(`batarang`, `alien force watch`, `broken sword`, `adventure time sword`, `asta`, `axe`, `bat`,
`ap15`, `ak47`) were each inspected (object/collection/modifier inventory) and rendered for direct
visual comparison, with findings recorded as they emerged rather than run through a full lab cycle
each -- reserving that deeper cycle for genuinely new techniques, not every repeated confirmation of
one already found. Per-file evidence is under each file's own subdirectory here.

Cross-file findings, most to least novel:

1. **High-poly/low-poly production collection pipeline**, confirmed in 7/10 files with real baked
   PBR textures on the low-poly target -- new operator card
   `knowledge/foundation/operator_cards/highpoly_lowpoly_pipeline.md`. Refines this project's
   `models/` convention: real production low-poly is a genuine separate retopology, not just a
   modifier-toggle duplicate.
2. **Crease vs. Bevel now has an evidence-based heuristic**, not just "both exist": stylized/fantasy
   weapons favor crease (axe, batarang, both swords, confirming battle axe); precision mechanical
   firearms favor Bevel (ap15: real Bevel+SubD throughout; ak47: Bevel used 90 times across 129
   objects). Added to `edge_crease.md`.
3. `batarang.blend`'s "Plane" object has a Bevel modifier present with **zero edges actually
   weighted**, alongside 73 creased edges -- direct evidence that modifier presence alone (already a
   known trap for the `hard_surface_shading_audit()` design) is not evidence of active use.
4. `broken sword.blend`'s grip wrap is built from 14 separate small identical Solidify+SubD strip
   objects, vs. `battle axe.blend`'s single continuous wrap mesh -- two valid alternative
   constructions for the same visual result.
5. `broken sword.blend` and `alien force watch.blend` both have a `zbrush hp`/`zbrush cut`
   collection holding untouched, very dense sculpted meshes (up to 1,126,023 verts) used purely as
   bake sources -- genuine sculpt-to-hardsurface integration, noted but not pursued further per this
   project's own P2/deferred sculpting boundary.
6. `alien force watch.blend`'s "runes" use Mirror + Array + Bevel + two Subdivision Surface passes +
   a Curve modifier to repeat ornamental symbols along a curved path -- a real technique for
   circular/curved-path ornamental repetition, noted but not reproduced in this pass.
7. `bat.blend` (a plain tapered baseball bat) is a useful negative case: one object, 354 verts,
   Smooth by Angle only, no SubD/Bevel/crease at all -- a genuinely simple body-of-revolution form
   needs neither technique, only adequate base density. Directly confirms the wrench's own shaft/
   handle strategy (measured loft + Smooth by Angle, no Bevel needed) was correct even though its
   jaw/housing strategy was not.
8. `ak47.blend`'s curved magazine is a real overhung/hook-shaped part, the same structural category
   that repeatedly broke the wrench's jaw -- direct evidence this shape category is normal in
   professional work and is handled through real component construction, not a parametric sweep
   (though this specific part's own construction method was not traced in this pass).
9. `adventure time sword.blend`'s working "model" collection lays its parts out separated/exploded
   in space rather than assembled -- a workflow detail (build components in isolation, position
   later), noted but not further investigated.

## What this whole pass does not establish

- No new typed capability was extracted from files 2-10 the way `set_edge_crease_by_ids` was from
  file 1 -- their findings are organizational/confirmatory (pipeline structure, technique-choice
  heuristics) rather than a new discrete Blender operation.
- No genuine cross-shape-family TRANSFER test of the crease-vs-bevel heuristic itself (e.g.
  deliberately building the same part both ways and measuring which reads better) -- this remains
  inference from observed professional choices, not an experiment this project ran itself.
- No real held-out modeling task has yet applied any of these 9 additional files' findings.
