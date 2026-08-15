# Secondary-view component strategy

**Status:** controlled two-family transfer | real-prop runtime use open

## Problem

A front silhouette can conceal depth. A full-depth continuous housing and a narrow body carrying a
separate full-front plate may have the same front mask even though they require different topology,
component organization, and edit-mode strategy.

## Executable policy

`knowledge_engine.component_strategy.resolve_component_strategy()` compares explicit construction
candidates. If the primary view is tied within the declared tolerance, the policy returns
`TARGETED_REFERENCE_RESEARCH` until every candidate has a discriminating same-variant secondary
view. Selection requires both an absolute secondary-view fit and a frozen margin over the runner-up.

The planner consumes this result in two places:

- `REFERENCE_ANALYSIS`: unresolved evidence returns `RESOLVE_SECONDARY_VIEW_STRATEGY` and blocks the
  stage transition without geometry mutation.
- Component blockout: a resolved policy overrides the generic component prior and records the
  selected measured candidate in the decision contract.

`CONTINUOUS_MESH` evidence must describe exactly one object and one connected component. Joining
multiple disconnected shells or merely placing them in one collection does not satisfy continuity.

## Blender 5.2 experiment

The controlled run uses rectangular and 16-sided radial housing families. In each family:

- the continuous full-depth body and separate-faceplate control both score `1.0` front IoU;
- the continuous candidate remains `1.0` from the top;
- the separate control falls to `0.711577` (box) and `0.695574` (radial);
- the resulting secondary margins are `0.288423` and `0.304426`;
- a fresh Blender process confirms object count, connected-component count, dimensions, collection
  organization, and exact mask reproduction.

Evidence: `runs/2026-08-15_secondary-view-component-strategy/`.

## Boundary

This is synthetic reconstruction evidence, not automatic image understanding. It does not prove
that the system can discover the correct component boundary in a real photograph or that the
chosen construction improves a held-out prop. That requires a real multi-view task and human visual
review.
