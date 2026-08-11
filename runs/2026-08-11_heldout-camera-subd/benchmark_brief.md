# Held-out benchmark: vintage rangefinder camera

**Declared before downloading or rendering the source asset.**

## Source and isolation

- Visual source: Poly Haven `Camera_01`, CC0, <https://polyhaven.com/a/Camera_01>.
- The source GLTF may be imported only by `tools/render_multiview_reference.py` to create neutral
  fixed-view pixels and masks.
- Source topology, object names, modifiers, dimensions beyond rendered bounds, UVs, materials, and
  construction are excluded from candidate modeling guidance.
- The candidate must be modeled from neutral renders only. Once those renders are opened, no new
  generic capability may be credited as held-out evidence from this benchmark.

## Why this target

This is unrelated to the prior wide box-like boombox: it combines a compact rounded body, stepped
radial lens assembly, viewfinder/rangefinder apertures, top controls, strap lugs, and asymmetric
secondary details. It directly tests the still-open held-out Subdivision Surface transfer gate and
whether connected-cage judgment transfers to a curved product shell.

## Predeclared quality gates

1. Neutral front, side, and top normalized silhouette IoU must reach at least `0.80`, `0.68`, and
   `0.70`, with mean at least `0.76`. Isometric review is qualitative and non-overridable for visible
   surface damage.
2. The main manufactured camera shell must be one connected editable all-quad cage with a deliberate
   Subdivision Surface/support strategy. It may not be replaced by overlapping body cubes.
3. Genuinely separate parts—lens rings/glass, controls, aperture frames, lugs, and fasteners—may be
   separate, but repeated radial or bilateral components must share data or use explicit repetition.
4. The primary body must show clean evaluated highlight flow in front and isometric views, with no
   blanket-bevel spikes, SubD pinching, accidental intersections, or paper-thin facade construction.
5. Lens rings and controls require authored radial/profile topology rather than untreated default
   primitives. Zero-radius profile endpoints must not create coincident rings.
6. Every deliverable mesh must have no loose vertices or zero-area faces. Closed manufactured parts
   must be manifold, and both base and evaluated geometry must be checked in a fresh Blender process.
7. Every renderable mesh needs a populated UV layer and named node material. The final scene must
   retain modifiers and editable linked repetition where appropriate.
8. A GLB round trip must preserve evaluated triangle count, combined dimensions, UV/material
   presence, and required POSITION/NORMAL/TEXCOORD_0 attributes. Tangent requirements must match the
   actual material semantics and may not be overclaimed.
9. At least one meaningful failed checkpoint must be retained if any declared topology, visual, or
   verification gate fails. Technical cleanliness cannot override a visible-quality failure.
10. Passing this benchmark supports only a bounded second-family automated transfer claim. Human
    professional acceptance, exact wear/graphics, and broad low-intervention proficiency remain open.

## Planned closed loop

Neutral reference generation -> measured primary ratios/component graph -> strategy retrieval ->
single-cage SubD blockout -> fixed-view silhouette checkpoint -> secondary radial and aperture forms
-> evaluated-surface review -> UV/material pass -> GLB export -> independent verification -> accept,
repair, rollback, or rebuild.
