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

## Current controlled exercise

`runs/2026-08-16_reference-gathering-seiko-qhe195rlh/` is deliberately held at
**primary assembly, not accepted final model**. Its source-backed sequence
caught and corrected both a generic side silhouette and an occluding solid
bezel by using a connected housing fascia extrusion and a bezel cap
inset/delete operation. It remains evidence of an improved corrective loop,
not evidence that modeling quality no longer needs review.
