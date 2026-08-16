# Modeling capability repair

This is a corrective workflow record, not a claim that the agent has reached
professional modeling quality. It addresses the recurring failure where clean
Blender operations produced a generic prop rather than a faithful model.

## Diagnosed failures

1. **Generic-seed acceptance.** A scaled and rounded primitive was treated as
   progress before its multi-view silhouette had been compared to the source.
2. **Component-boundary mistakes.** Separate assemblies were sometimes
   represented as solid overlays; the first Seiko bezel hid its dial instead of
   forming an open retaining ring.
3. **Technical signals mistaken for visual proof.** Manifold topology,
   modifiers, and a passing transaction are necessary evidence, but are not a
   resemblance verdict.
4. **Too little reference-driven iteration.** A visible disagreement in a
   secondary view must create a localized cage correction before secondary
   detail is added.

## Required reconstruction loop

1. Source same-target, same-variant front and secondary views; record what is
   observed, inferred, and unknown.
2. Decompose the object into continuous cages and physically separate
   assemblies. A primitive is only a seed; it is not a finished continuous
   form.
3. Build a reversible primary silhouette and inspect front, side, and solid or
   MatCap views. Reject or correct a generic silhouette immediately.
4. Add only the observed major assemblies. For connected housings, use
   selection-scoped Edit Mode operations such as loops, extrusion, inset, and
   vertex movement. Keep modifiers unapplied.
5. Re-render after each meaningful decision. Convert each visible mismatch into
   a localized repair ticket rather than covering it with detail.
6. Promote nothing from a technical pass to an accepted reconstruction without
   a real reference comparison and, when required, human review.

## Concrete runtime changes

The typed modeling surface now includes
`assign_selected_material`. It assigns a material only to selected faces of an
editable connected cage, which supports real fascia/shell boundaries without
splitting the body into decorative objects. Material creation and mesh material
slots are included in transaction-owned rejection cleanup; the live Blender
lab at `runs/2026-08-16_material-decision-transaction/report.json` proves that
a rejected assignment restores empty slots and removes the newly created
material.

`tools/render_blend_beauty.py` can render either neutral solid shading or
Workbench material color. Material mode is a diagnostic aid for observed
surface boundaries; it is not a materials-quality render.

It also has a transparent `silhouette` mode, so the alpha channel can be
compared to a source image without thresholding a shaded result. The typed
`translate_object` operation is available only for independently manufactured
assemblies; connected primary cages still require Edit Mode geometry changes.
Its commit and rollback path is evidenced by
`runs/2026-08-16_object-transform-decision/report.json`.

## Current controlled exercise

`runs/2026-08-16_reference-gathering-seiko-qhe195rlh/` is deliberately held at
**primary assembly, not accepted final model**. Its source-backed sequence
caught and corrected both a generic side silhouette and an occluding solid
bezel by using a connected housing fascia extrusion and a bezel cap
inset/delete operation. It remains evidence of an improved corrective loop,
not evidence that modeling quality no longer needs review.

The official front and side product images are perspective product photos, not
calibrated orthographic drawings. Uniform-bounding-box comparison is therefore
used only to localize normalized proportion and contour disagreements. In the
Seiko run, the first side comparison scored 0.823 IoU. Inspection exposed an
over-deep housing caused by adding front assemblies after freezing the body at
the published full depth. A connected rear-cage move reduced the depth and
raised the same normalized side comparison to 0.916 IoU; the before/after
reports and overlays live beside stages 11 and 12. This is a measured localized
improvement, not a substitute for direct visual review or an acceptance claim.

## Component-bound comparison correction

Global silhouette agreement can hide an oversized or undersized secondary
assembly. `knowledge_engine/component_layout.py` compares named normalized
component bounds from a controlled Blender component-mask pass with an explicit
source-layout interpretation and returns prioritized local tickets. It reports
disagreement; it intentionally has no visual-pass threshold.

The Seiko exercise also demonstrates the required reconciliation step. A first
manual bezel bound suggested an oversized correction, but constrained circle
observations showed the candidate bezel/dial widths already matched closely.
That edit was rejected before mutation. The top-control width/height reading
was then tested: an over-tall trial was rejected by the material render, and a
moderated rebuild with a live physical-radius bevel was retained. See stages
12–16 and `component_measurement_reconciliation.json`. This is evidence of a
repair discipline, not proof that automatic source component segmentation is
solved or that the asset is reviewer-accepted.
