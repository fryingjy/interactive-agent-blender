# Held-out benchmark: vintage boombox

**Declared before neutral reference renders or source topology inspection.**

## Source and isolation

- Visual source: Poly Haven `boombox`, CC0, <https://polyhaven.com/a/boombox>.
- The source GLTF may be imported only by `tools/render_multiview_reference.py` to create neutral
  front/side/top/isometric pixels and masks.
- Source object names, topology, dimensions beyond rendered bounds, modifiers, and construction are
  excluded from modeling guidance.
- This asset was not used to develop the existing modeling runtime, strategy selector, topology
  cards, modifier cards, or visual comparator. Once its renders are opened, no new generic
  capability may be credited as held-out evidence from this benchmark.

## Why this target

The boombox is a product-like, asymmetric-depth, multi-component hard-surface prop. It exercises
the current priority stack: box/SubD form control, repeated but semantically distinct components,
recesses and panels, radial controls, handle construction, multi-view proportion reasoning,
modifier strategy, editability, UVs/materials, and production cleanup. It is not sculpt-heavy.

## Predeclared quality gates

1. Fixed neutral front, side, and top comparisons; normalized silhouette IoU at least `0.82` front,
   `0.72` side, `0.72` top, and `0.78` mean. Isometric review remains qualitative.
2. Main case has purposeful bevel/support strategy and no visible blanket-bevel pinching, floating
   coplanar panels, or accidental intersections.
3. Speaker assemblies are bilateral and editable; repeated details use explicit symmetry/array
   intent rather than unrelated duplicated primitive piles.
4. Circular controls and speaker rims use authored radial/profile topology. A cylinder may be an
   appropriate starting topology, but default primitive output alone is not accepted as finished
   modeling.
5. Handle, tuner/cassette regions, speakers, and controls read as a coherent product in front and
   isometric views; side/top views must establish real depth rather than a shallow facade.
6. Every deliverable mesh is nondegenerate, has no loose geometry, and has justified component
   separation. Closed manufactured components must be manifold; intentionally open trim must be
   declared.
7. Evaluated geometry and modifier order are independently checked in a fresh Blender process.
8. All renderable meshes have non-empty UV layers and named materials; the final package includes
   a saved `.blend`, reference manifest, strategy/decision log, report, and visual checkpoints.
9. At least one rejected checkpoint must be retained if the first construction fails a declared
   visual, topology, or strategy gate. A first-pass success is allowed only if all gates genuinely
   pass.
10. No professional-quality claim is made without experienced human acceptance. This benchmark can
    support low-intervention held-out hard-surface transfer only within its declared scope.

## Planned closed loop

Reference pixels -> measured landmarks/component graph -> retrieve existing hard-surface/SubD and
modifier skills -> choose representation per component -> blockout -> fixed-view comparison ->
primary-form correction -> connected/detail topology -> UV/material pass -> technical and visual
review -> independent verification -> accept, repair, or preserve failure.
