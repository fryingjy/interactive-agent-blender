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
- The next-task question is: does this materially improve hard-surface, SubD, topology,
  reference-modeling, or production-prop capability? If not, defer it unless it blocks such work.

The expressive facial articulation run predates this override and is retained as a bounded
topology/deformation experiment. It does not begin an organic-development phase.
