# Development priorities

The objective is autonomous creation of editable Blender assets from references. Work is ordered by
the bottleneck that currently prevents that objective, not by the number of supported Blender
operators.

## P0 — shape inference and topology planning

1. Camera and projection estimation from real reference sets.
2. Reliable foreground masks, landmarks, negative spaces, and uncertainty.
3. Generic semantic shape families with bounded parameters.
4. Multiview fitting that exposes disagreement instead of averaging it away.
5. Topology compilation into connected edit-mode cages with real assembly boundaries.
6. Synthetic recovery, real-reference rejection, and post-result human review.

Do not resume prop benchmarking until the relevant shape family can recover known synthetic ground
truth and reject an incompatible family.

## P1 — surface and production

SubD/crease/support-loop strategy, physical bevels, Smooth by Angle, high/low variants in separate
collections, UVs, materials, baking, export, and fresh-file verification. Modifiers stay live and
unapplied unless the user applies them.

## P2 — deferred specialization

Advanced sculpting, characters, facial systems, and anatomy remain deferred. Retopology fundamentals
remain active because they directly support reference reconstruction and editable hard-surface
assets.

## Non-negotiable rules

- Research unknown form and camera questions before modeling.
- Prefer 12–16 radial cage segments for ordinary blockouts.
- Grow continuous geometry through loops, inset, extrusion, bridge, and related edit-mode tools.
- Use separate objects only for real assembly, articulation, replacement, or output boundaries.
- Do not smooth or bevel indiscriminately; author sharpness from intended surface behavior.
- No target-named builders, HTML approval boards, or historical run archives in the active tree.
- No capability claim from technical validity, aggregate scores, or generated 3D priors alone.
