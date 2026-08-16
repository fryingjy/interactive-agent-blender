# Smeg KLF03 rejected primary-form attempt

This run reconstructs the KLF03NBUS from the official multi-view package. Stage 1 is deliberately limited to the body, lid, base band, continuous handle, tapered spout, lid button, and switch. It is not a final asset and does not claim likeness until direct visual comparison.

Body, lid, and base are connected 16-segment revolved quad cages. The spout begins as one box and is tapered by editing its end vertices. The handle is one continuous curve converted to editable mesh. Modifiers remain live and unapplied.

Stage 2 slightly strengthens the body flare, flattens the continuous handle in depth, and refines the spout projection. `stage_02_visual_review.json` keeps the stage explicitly partial: the spout valley/lip, handle section and collars, and base foot cutouts still block likeness acceptance.

Stage 3 adds paired centerline cuts to the same spout cage, connects them into a fully quad longitudinal layout, and moves the tip centerline into the observed V-valley. Fresh transaction evidence reports 12 vertices, 10 quad faces, zero n-gons, and zero non-manifold edges.

The stage-08 checkpoint is **rejected for reference mismatch**. It is technically inspectable, uses editable cages and live modifiers, but it does not reproduce the specific KLF03 body, spout, handle, or base geometry well enough to continue polishing. `stage_08_visual_review.json` is the acceptance record. The retained final checkpoint and component-level comparisons exist to diagnose the failure, not to claim a successful asset.

The corrective repository outcome is reusable tooling, not more kettle repair: reference-component masking with aspect-preserving alignment and recoverable component replacement/archive operations. The next benchmark must validate this workflow on an unrelated prop before it supports a broader capability claim.
