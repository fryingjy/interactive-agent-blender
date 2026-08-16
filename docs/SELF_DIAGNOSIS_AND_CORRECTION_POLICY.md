# Self-diagnosis and correction policy

## Observed failure pattern

Recent prop attempts demonstrate that the system can execute Blender
operations and preserve editable construction, yet still produce a visibly
generic result.  The Panasonic RF-2400D blockout is the clearest example:
its global front aspect ratio is close, but its housing surround, handle,
speaker grille, tuner layout, and control silhouette are materially unlike
the reference.  A topology pass or a successful render is not evidence of
reference fidelity.

## Root causes

1. **Reference evidence was not converted into local shape constraints.**
   Broad dimensions were measured, but critical relationships—handle-to-body
   clearance, handle top straightness, front-surround width, panel boundary
   radii, speaker/tuner proportion, and knob placement—were not measured
   before construction.
2. **The primary cage was refined before its silhouette was earned.**
   Subdivision, crease, and separate panels were introduced while the base
   envelope remained a generic rounded box.
3. **Evaluation over-weighted mechanical checks.**
   Manifoldness, quad count, modifier presence, and global silhouette aspect
   can all pass for the wrong object.  They are safeguards, not visual
   acceptance criteria.
4. **The correction surface was incomplete for curve assemblies.**
   A curve could be created and given a flattened profile, but its path could
   not be revised through the typed runtime.  That encouraged replacement
   rather than correction.
5. **Regression coverage drifted.**
   The retrieval suite added a case without updating its expected count;
   passing tool output alone was not enough to expose it.

## Mandatory corrective workflow

Before any new prop passes a blockout stage:

1. Build an orthographic reference set with at least a declared front view
   and one view that resolves depth/attachment ambiguity.
2. Write a compact constraint sheet containing normalized ratios for all
   silhouette-defining boundaries and actual separate-assembly decisions.
3. Use one connected editable cage for each continuous manufactured shell.
   Do not use SubD, bevel, creases, materials, or micro-detail to disguise a
   wrong envelope.
4. Render a solid front, side, and isometric diagnostic after the cage stage.
   Compare each declared constraint—not only the overall bounding box.
5. If any high-salience boundary fails, revise the existing cage/path in
   place.  A successful tool call does not advance the stage by itself.
6. Only add surface-control tools once the cage reads correctly: use creases
   where a live SubD transition must stay sharp, and weighted bevels only for
   explicitly selected hard edges where the reference supports a bevel.
7. Treat a human visual rejection as the final verdict.  Preserve the evidence
   for learning, but stop polishing that asset until the failed primary form
   is rebuilt or the study is explicitly discarded.

## Implemented corrections in this change

- `set_curve_points` exposes editable control-point revision for a single
  authored curve path, retaining its native profile/taper settings rather
  than replacing it with a new curve or a mesh conversion.
- The RF-2400D handle correction is a reproducible, saved test of that path;
  its review explicitly records that the model remains visually unacceptable.
- `knowledge_engine.reference_constraints` now evaluates declared normalized
  point, box, and scalar relationships independently.  A missing or failed
  high-salience constraint blocks blockout advance and produces prioritized
  repair tickets; it remains a correction aid rather than a visual-acceptance
  substitute.
- The retrieval benchmark test now tracks the actual 24-case corpus.

## Next engineering gap

The first scene bridge is now implemented for up to four named renderable
components: Blender's controlled component-mask pass feeds normalized local
bounds into the evaluator.  The remaining high-value step is explicit camera
registration to a same-view reference, so candidate and reference bounds use
the same declared coordinate frame.  This must remain a correction aid, never
presented as a substitute for human visual judgment.

## 2026-08-16 correction: judging a weak reference-driven result honestly

The Seiko QHE195RLH clock exercise demonstrates the same core limitation in a
new shape family. Its saved stage-17 front render has an organized, editable
scene, but the housing reads as a generic rounded rectangle and the dial,
hands, side profile, and control lack the characteristic relationships visible
in the supplied product views. It is therefore a **failed visual-quality
outcome**, not a portfolio asset or evidence that the modeling capability has
improved.

The failure is not that Blender modifiers or collections were unavailable. The
main causes are more specific:

1. **Component boxes were mistaken for component design.** Normalized bounds
   could keep the bezel and control in approximately plausible positions while
   failing to describe their profiles, thickness transitions, detail hierarchy,
   and negative spaces.
2. **A perspective product image was used too much like an orthographic
   drawing.** A front/side pair resolves broad depth, but does not by itself
   provide a registered construction coordinate frame or enough local profile
   samples to infer the fascia and shell transition.
3. **The first detail pass was generic.** The hands and dial were made from
   minimal forms before the primary and secondary silhouettes had earned that
   simplification. This is exactly the primitive-starting-cage failure mode the
   user identified: a cube seed is acceptable only when it is subsequently
   developed through deliberate edit-mode topology into the observed form.
4. **Technical packaging was allowed too early.** Separate collections and
   live modifiers are useful production hygiene, but cannot compensate for a
   weak primary form. Packaging is now explicitly downstream of visual-quality
   evaluation in all future exercises.

### Corrective gates

No new reference-driven prop may be described as a successful modeling result
until it has all of the following evidence:

1. A source set whose role and view ambiguity are recorded, with a same-target
   depth-resolving view. A perspective image must be marked as perspective;
   it must not be silently treated as an orthographic blueprint.
2. A measured constraint sheet for every high-salience contour, clearance,
   and attachment—not merely object bounding boxes. Each constraint must say
   which view supports it and its uncertainty.
3. A primary-cage checkpoint containing only the continuous shell(s), rendered
   in solid/MatCap front, side, and three-quarter views before details,
   materials, bevels, or SubD polish are allowed to conceal proportion errors.
4. A deliberate construction record for each continuous shell: loops, insets,
   extrusions, bridge operations, or a profile/revolve. Separate objects are
   permitted only for physically separate assemblies.
5. A visual mismatch ledger after every checkpoint. If the dominant mismatch
   is primary or secondary form, revise the existing cage before adding
   tertiary detail. Automated silhouette/component scores may prioritize work;
   they cannot clear this gate.

### Concrete runtime repairs completed

- `tools/package_editable_asset_variants.py` now packages a complete
  multi-object asset through serial typed decisions. It preserves independent
  editable meshes and live modifiers, reduces only the *low variant's* live
  Subdivision level, and does not apply modifiers.
- `package_high_low_variants` now writes persistent `hide_viewport` as well as
  view-layer hide state. A fresh Blender-process inspection of
  `runs/2026-08-16_reference-gathering-seiko-qhe195rlh/seiko_qhe195rlh_stage_17_editable_high_low.blend`
  confirms seven high objects and seven low objects in separate collections;
  every low object is hidden in both saved viewport and render state.
- The same fresh inspection is intentionally retained with the stage-17 file.
  It also shows that this is an **editable duplicate package**, not a
  purpose-authored game low-poly/UV/bake result.

### Focused knowledge to retain

The corrective workflow maps directly to Blender's documented tools: Image
Empty reference cards can be axis-aligned and depth-controlled; edit-mode
extrusion and loop/edge operations are the primary cage tools; creases hold a
SubD transition, while Bevel Weight controls only deliberately selected bevel
edges. These are construction controls, not post-hoc substitutes for looking
at the reference.

Sources: [Blender reference-image empties](https://docs.blender.org/manual/en/latest/modeling/empties.html),
[Edge Data: crease, bevel weight, and sharpness](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html),
and [Bevel Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html).
