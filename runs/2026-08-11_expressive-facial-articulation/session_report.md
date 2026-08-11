# Expressive facial articulation: bounded topology/deformation study

## Outcome

The final saved scene passes its declared technical gates and a separate fresh-process verifier.
It demonstrates that a broad smile shape can couple mouth-corner, cheek, lower-lid, and brow motion
more coherently than a mouth-only failure control. It does **not** establish autonomous facial
retopology, anatomy knowledge, production acting, or professional character quality.

## Source and authorship boundary

The head comes from Blender Studio's CC0 Human Base Meshes Bundle. That source supplies the anatomy
and topology. This run authors only the comparison setup, deformation shapes, non-deforming smile
controls, drivers, measurements, renders, and failure/revision sequence. The source contains 3,234
faces: 3,206 quads, 18 triangles, and 10 n-gons. The tested expression region is 99.3188% quads;
the report deliberately uses a contextual threshold instead of relabeling the whole source as
all-quad.

Relevant prior instruction includes Blender Studio's facial-retopology planning/live material and
Project Storm production notes about expression sculpt/model/rig feedback. Those sources motivated
regional coupling and visual review; they did not provide copied vertex positions for this shape.

## Iteration and strategy changes

1. The first result failed numeric mouth-corner and jaw-direction gates.
2. The second passed metrics but failed visual review due to compressed eyelids, cheek folds, and a
   broad jaw/neck crease.
3. Narrower armature weighting still produced a visible jaw/neck fold.
4. Replacing weighted jaw motion with a jaw shape key created an under-chin/neck bulge.
5. Removing jaw motion produced the clean bounded smile study, but an absolute all-quad gate
   incorrectly failed a predominantly-quad source.
6. The final gate measures the actual expression region and retains the source's non-quads
   honestly.

A later evidence audit also caught that Blender's `show_wire` flag affects the viewport but did not
produce lines in the saved render. The generator now creates temporary evaluated Wireframe geometry
for that checkpoint, and the verifier samples image color to distinguish the cool wire render from
the matching solid view.

All five rejected states remain under `failed_*` directories. A numeric pass is not treated as a
visual pass: the two jaw approaches were removed because the renders were visibly worse.

## Final evidence

- Driver value: `0.0` at rest and `1.0` at the declared bilateral smile pose.
- Mouth corners move outward and about `0.0100` units upward.
- Cheek landmarks rise about `0.00935`; lower lids about `0.00544`; brows about `0.00328`.
- Mouth-only control mean displacement outside the mouth is effectively absent at the lids/brows;
  the integrated shape has measured cheek/lid/brow coupling.
- Base mesh: closed and nondegenerate, 3,242 vertices and 3,234 faces.
- Evaluated mesh: closed, nondegenerate, and 12,948 quads.
- Six 1200x900 checkpoints cover rest, failure, final, comparison, three-quarter, and wireframe.

The independent verifier opens the saved `.blend` in Blender 5.2 LTS with factory startup and does
not import the generator. It checks exact objects, shape keys, bones, driver targets, pose gating,
landmark values, bilateral symmetry, expression-region membership, base/evaluated health, render
dimensions, and preservation of all five failed iterations.

## Files and reproduction

- Generator: `tools/run_expressive_facial_articulation_lab.py`
- Independent verifier: `tools/verify_expressive_facial_articulation.py`
- Primary report: `expressive_facial_articulation_report.json`
- Independent report: `expressive_facial_articulation_verify.json`
- Saved scene: `expressive_facial_articulation.blend`

```powershell
blender --background --factory-startup --python tools/run_expressive_facial_articulation_lab.py
blender --background --factory-startup --python tools/verify_expressive_facial_articulation.py -- runs/2026-08-11_expressive-facial-articulation
```

## Priority disposition

The 2026-08-11 sculpting-priority override makes advanced organic and facial work a late
specialization. This run is complete and retained, but follow-on development returns to held-out
hard-surface/SubD/reference-based prop work, topology judgment, modifiers, and production
preparation.
