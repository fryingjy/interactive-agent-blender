# Stage 24 — Registered front comparison review

## Evidence

- Reference: uncropped official Panasonic RF-2400D front photograph,
  segmented with a reviewed GrabCut mask that preserves the carry-handle
  opening.
- Candidate: `panasonic_rf2400d_stage_21_handle_corrected.blend`, rendered
  from its controlled orthographic front view.
- Registration: two manually declared handle-mount anchors; it normalizes
  only in-plane translation, uniform scale, and rotation.

## Result

The comparison **rejects** the candidate as a reference-faithful blockout:

- silhouette IoU: `0.4369`;
- normalized symmetric contour error: `0.0675`;
- handle/assembly negative-space IoU: `0.0611`.

The overlay visibly confirms the figures: the candidate handle has the wrong
arch and relationship to the body; the body is too generic and the side/knob
silhouette does not match. The reference antenna is a disconnected visual
element in the source photo and is excluded from the GrabCut component mask,
so this comparison does not assess antenna fidelity.

## Decision

Do not add front-surface micro-detail, materials, or production packaging to
this radio candidate. A future retry must start with an explicit measured
front construction sheet and rebuild the primary housing/handle relationship
before secondary panels are considered.  This stage validates the evaluator
and makes the rejection reproducible; it does not validate the model.
