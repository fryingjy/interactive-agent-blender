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

## What this does not establish

- Only one of ten provided files studied so far.
- No genuine cross-shape-family transfer test yet, only within-lab.
- No real-task application/measurement yet.
- The "why crease over Bevel" reasoning is inference, not observed fact, and is documented as such.
