# Current modeling-development priorities

**Effective:** 2026-08-11
**Status:** binding override for research, experiments, and benchmark selection

The current target is professional prop modeling. Resource allocation should therefore favor
skills that improve editable hard-surface and subdivision assets from references:

1. Core mesh modeling and contextual topology judgment.
2. Hard-surface and Subdivision Surface workflows.
3. Production modifier strategy: Mirror, Bevel, Boolean, Subdivision Surface, Solidify, Array,
   Curve, and task-relevant secondary modifiers.
4. Reference analysis: silhouette, proportion, landmarks, component decomposition, and multi-view
   reasoning.
5. Stylized, curved, and complex multi-component props.
6. Retopology fundamentals, especially edge flow, density transitions, poles, repair, editability,
   and surface preservation.
7. UVs, materials, baking, export, and production preparation.
8. Sculpting and advanced organic specialization only after the preceding capabilities are much
   stronger.

Directional allocation is 70-80% hard surface/SubD/topology/reference/modifiers, 15-25%
UV/material/export/retopology/production, and 0-5% foundational sculpt maintenance.

## Effective priority order

### P0 — core professional modeling

Mesh modeling fundamentals; topology, edge flow, poles, loop termination, and contextual
quad/triangle/n-gon judgment; SubD; hard surface; modifier strategy (Mirror, Bevel, Boolean,
SubD, Solidify, Array, Curve); reference and multi-view reasoning; silhouette/proportion;
surface/highlight and shading/normal diagnosis; complex multi-component props; strategy
selection; failure recovery; cross-asset transfer; held-out benchmarks; independent verification.

### P1 — production modeling

Retopology fundamentals; UVs; high/low workflows; baking; materials; inspection lighting and
rendering; export; game-ready preparation; stylized/low-poly; curves/procedural modeling; and
Geometry Nodes only where it materially improves the asset workflow.

### P2 — deferred specialization

Advanced sculpting, character/facial sculpting, advanced organic modeling, anatomy,
character-specific workflows, advanced facial retopology, and character-deformation
specialization. Existing evidence remains **KNOWN / DEFERRED**; it is not deleted or invalidated.

## Binding decisions

- Sculpting remains in the knowledge base as **FOUNDATIONAL / DEFERRED**.
- Do not start sculpt-brush systems, character sculpting, anatomy/facial specialization, advanced
  remeshing, or sculpt-specific production tooling while higher-priority prop gaps remain.
- Retopology fundamentals remain active because they support general edge-flow, reconstruction,
  density, pole-placement, and repair judgment; sculpt-heavy organic pipelines do not.
- A minimal sculpt operation is allowed only when it is the most suitable local technique inside
  a primarily higher-priority prop workflow.
- New held-out work should favor electronics, mechanical or stylized equipment, furniture,
  containers, appliances, product-like assets, curved SubD objects, and complex hard-surface props.
- For continuous product skins, predeclare one-object and one-connected-component expectations.
  Grow compatible features from routed loops, inset, extrusion, bridge, spin, or related Edit Mode
  operations. Separate objects require a real assembly, articulation, replacement, or output reason;
  joining disconnected primitive-like shells does not satisfy the rule.
- Keep radial control cages intentionally sparse. The camera correction supports 12-16 authored
  vertices at that lens scale with SubD providing evaluated smoothness; this is evidence for a
  tested scale, not a universal segment count.
- Do not blanket-smooth hard-surface props. Identify intended sharp transitions first, assign
  semantic weighted bevels where physical edge radius is required, use Bevel before SubD when both
  modifiers apply, and use Blender's Smooth by Angle/Auto Smooth behavior for remaining normal
  interpolation. SubD belongs only on continuous curved shells whose cage supports it.
- The next-task question is: does this materially improve hard-surface, SubD, topology,
  reference-modeling, or production-prop capability? If not, defer it unless it blocks such work.

The expressive facial articulation run predates this override and is retained as a bounded
topology/deformation experiment. It does not begin an organic-development phase.
