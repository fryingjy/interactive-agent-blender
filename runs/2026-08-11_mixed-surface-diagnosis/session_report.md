# Mixed-cause surface diagnosis report

**Status:** PASS for controlled mixed-cause diagnosis and repair on an editable production-style
testbed; not a claim of unknown-defect diagnosis or held-out modeling.

## Testbed and defects

The lab reuses the verified connected-quad barrel body: one 5,376-face/5,376-quad connected
manifold shell with integrated seams, hoops, and corrugations. Five faults are injected together:

- a localized radial dent;
- an 18-face reversed-winding patch;
- a localized rough blue material assignment;
- an unnecessary global one-segment Bevel modifier;
- a faulty flat/hot-rim review-light rig.

The model is reused only as a surface-diagnosis testbed. This is not new reference-modeling or
held-out asset evidence.

## Adaptive diagnosis and repair

Every step rendered all remaining one-variable repairs, verified that only the targeted state
channel changed, and selected the candidate with the lowest fixed-camera image error. Fixed-seed
Cycles produced a zero-error repeat of the clean control.

Selected sequence and mean absolute RGB error:

1. mixed state: `0.10833657`
2. repair lighting: `0.03310559`
3. remove unnecessary bevel: `0.00826209`
4. repair material assignment: `0.00130707`
5. restore geometry: `0.00061091`
6. restore normals: `0.00000000`

Changed pixels over a 0.02 RGB threshold fall from 104,319 to 0. The final clean-control,
last-sequence, and final-repaired PNG pixel buffers are identical.

## Failed evidence retained

- `failed_initial/`: a preset repair order became non-monotonic when the normals step interacted
  with remaining faults.
- `failed_sampling/`: Eevee variation reversed small ablation deltas.
- `failed_stale_depsgraph/`: a missing update left a stale light state.
- `failed_light_recreation/` and `failed_eevee_light_cache/`: deleting/recreating or merely hiding
  Eevee lights did not yield a trustworthy repeated background-render state.

The final method uses persistent light rigs, explicit visibility/energy state, dependency-graph
updates, and fixed-seed Cycles. The failed blanket bevel also reproduces a technical fault:
the generator measures 65 evaluated degenerates, while the independent BMesh verifier measures 67
degenerate faces plus 152 non-manifold edges. Both channels agree that the modifier is invalid.

## Independent verification

`tools/verify_mixed_surface_diagnosis.py` opens the saved `.blend` in factory-startup Blender and
imports no project code. It proves:

- clean and repaired bodies are exact datablock matches;
- both are one connected, closed, 5,376-quad component at base and evaluated states;
- the mixed state independently differs in coordinates, winding, material indices, and bevel;
- the mixed evaluated result contains degenerates/non-manifold edges;
- the saved final scene uses the neutral rig, not the faulty rig;
- fixed-seed Cycles settings are preserved.

All independent assertions pass.

## Limitations

- Ground-truth defects are injected intentionally. Unknown real-production diagnosis remains open.
- One camera/material/light setup cannot substitute for experienced surface judgment.
- The barrel was already source-tuned, so this adds no held-out generalization claim.

## Primary evidence

- `mixed_surface_diagnosis.blend`
- `mixed_surface_diagnosis_report.json`
- `mixed_surface_diagnosis_verify.json`
- `control_clean_neutral.png`
- `mixed_five_cause.png`
- `fully_repaired.png`
- `greedy_s*.png`
