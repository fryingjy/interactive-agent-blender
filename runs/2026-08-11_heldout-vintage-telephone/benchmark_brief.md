# Held-out benchmark: vintage telephone wall clock

**Declared before downloading, opening, or rendering the source model.**

## Source and isolation

- Visual source: Poly Haven `vintage_telephone_wall_clock`, CC0,
  <https://polyhaven.com/a/vintage_telephone_wall_clock>.
- The source GLTF may be imported only by `tools/render_multiview_reference.py` to create neutral,
  fixed-view pixels and silhouette masks.
- Candidate tools may consume those renders and their pixel measurements only. Source topology,
  object names, mesh/component counts, modifiers, UVs, materials, transforms, and construction are
  excluded from modeling guidance.
- The source GLTF is reference media, not a candidate starting point. No source object may be linked,
  appended, copied, converted, shrinkwrapped, or queried by the candidate builder or verifier.

## Why this target

This prop is unrelated to the previous barrel, boombox, and rangefinder camera families. It combines
a vertically curved stamped-metal housing, a genuine detachable handset assembly, cradle supports,
a circular rotary-dial/clock region, mounting details, and a hanging cord. It tests whether connected
product-skin topology, sparse radial cages, weighted hard edges, assembly reasoning, and production
handoff transfer without another box-with-cylinders construction.

## Predeclared construction rules

1. The continuous main housing must begin from one box/profile cage and remain one connected editable
   component. Its front crown, shoulders, side returns, lower taper, dial recess, and rear depth must
   be routed with Edit Mode topology; overlapping body primitives are forbidden.
2. The handset is a real removable assembly and may be a separate object, but it must itself be one
   connected authored cage. The two bells and grip may not be three disconnected primitive shells
   joined into one object.
3. Cradle supports, dial/clock insert, hands, fasteners, and cord may be separate only where assembly,
   articulation, material, or replacement provides a concrete reason.
4. Circular controls use intentionally sparse authored radial loops (normally 12-16 vertices at this
   scale) and rectangle-to-circle routing where embedded in a continuous skin. Evaluated smoothness
   does not excuse rounded-square control cages.
5. Hard manufactured edges must be selected semantically for bevel weighting. A technically active
   Bevel modifier with incomplete edge coverage fails.
6. The primary housing and handset cages target all-quads. Any unavoidable triangle or n-gon must be
   outside a deforming/highlight-critical surface, counted, localized, and justified; otherwise the
   gate fails.
7. Candidate generation may use direct mesh/BMesh construction, extrusion, inset, bridge, spin,
   mirror, bevel, and subdivision logic, but may not call mesh primitive operators to assemble the
   visible result.

## Predeclared visual and technical gates

1. Normalized silhouette IoU: front at least `0.78`, side at least `0.68`, top at least `0.68`, and
   three-view mean at least `0.74`. Isometric review is qualitative and non-overridable for visible
   pinching, lumpy housing flow, primitive assembly, or implausible depth.
2. Front-view landmark gates must preserve handset span/height, housing shoulder width, circular
   insert center/radius, and lower-body taper within tolerances fixed after reference pixel analysis
   but before candidate modeling.
3. Main housing and handset must each be one connected component with no loose vertices,
   non-manifold edges, zero-area faces, duplicate faces, or unintended self-intersection signatures
   at base, Bevel-only, and final evaluated stages.
4. Every renderable mesh must have a populated UV layer and named node material. The final scene must
   retain editable modifiers and linked repetition where appropriate.
5. A real tangent-space normal bake must be produced from an authored high/low detail pair. The bake
   must include a preserved failure control and verify Non-Color handling and tangent availability.
6. GLB round trip must preserve combined dimensions, evaluated triangle count within exporter/importer
   semantics, UVs, materials, POSITION/NORMAL/TEXCOORD_0, and TANGENT where the normal-mapped material
   requires it.
7. A fresh Godot import must verify axis/scale, mesh/material presence, normal-texture binding, and
   PBR factors. Successful import alone cannot override wrong material semantics or visible damage.
8. At least one meaningful failed checkpoint must be retained if a declared visual, topology, bake,
   or handoff gate fails. Technical cleanliness cannot override a visibly weak model.
9. Passing supports one bounded held-out product-family result. Human professional acceptance,
   exact historical internals, texture artistry, and broad autonomous proficiency remain open.

## Planned closed loop

Isolated neutral reference generation -> pixel-only ratio/landmark analysis -> strategy retrieval ->
connected housing and handset blockout -> fixed-view silhouette checkpoint -> routed dial/cradle/detail
topology -> evaluated surface review -> UV/material/high-low bake -> GLB export -> fresh Blender and
Godot verification -> accept, repair, rollback, or rebuild.
