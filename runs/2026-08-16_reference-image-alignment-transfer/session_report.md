# Session report

## Commands

```powershell
blender --background --factory-startup --python tools/run_reference_image_alignment_transfer.py
blender --background runs/2026-08-16_reference-image-alignment-transfer/reference_image_alignment_transfer.blend --python tools/verify_reference_image_alignment_transfer.py
```

## Outcome

The corrected builder passes 5/5 declared checks. The fresh saved-file verifier passes 9/9 checks,
including six editable Image Empties, existing source paths, 0° FRONT/RIGHT angular error, distinct
transfer sources, and retained rejection of both the CUSTOM free-view fixture and duplicated-source
multi-view fixture.

## Rejected path

The initial audit read all world normals as +Z because Blender had not refreshed object matrices
after direct rotation assignment. That run failed its reproduction and transfer checks. Adding a
view-layer update repaired the measurement channel; no threshold or expected result was changed.

## Boundary

Project-owned diagram cards isolate Blender setup behavior. The experiment does not establish
photographic orthography, same-target identity, dimensional calibration, visual sufficiency, or
reference-to-model fidelity.
