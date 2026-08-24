# Carabiner tutorial reproduction

Source: [Sweaty Grease Studio — Blender - Carabiner Modeling Tutorial](https://www.youtube.com/watch?v=46XJ6_V5PN0)

Result: **6.4/10 — not passing the 8/10 I0 gate.** The run produced a recognizable, manifold carabiner and demonstrated transferable curve-resolution control, but it did not reproduce the target's triangular flattened body, interlocking nose, knurling, or assembly fidelity.

Primary evidence:

- `carabiner_tutorial.blend`
- `fresh_final_solid.png` and `fresh_final_wireframe.png`
- `fresh_verification_report.json`
- `tutorial_assessment.json`
- `bent_handle_transfer.blend` and `transfer_evaluation.json`

The run also added a reusable typed `set_curve_resolution` operation so curve-to-mesh density can be selected deliberately before conversion.
