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
