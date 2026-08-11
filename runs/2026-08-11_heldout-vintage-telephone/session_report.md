# Held-out vintage telephone wall-clock report

**Status: PASS for the predeclared automated product-prop gates; not an expert-acceptance claim.**

## Source boundary

The visual source is Poly Haven's CC0 `vintage_telephone_wall_clock` by Adrian C. The benchmark
contract and thresholds were recorded before source download or rendering. The source GLTF was
opened only by the neutral reference renderer; candidate scripts consumed pixels and measurements,
never source topology, object names, modifiers, UVs, materials, or construction.

## Construction result

- Main housing: one closed connected 208-quad box/profile cage. Twelve vertical cross-section loops
  route the lower plinth, shoulder transition, arched crown, depth changes, and recessed front band.
- Handset: one closed connected 162-quad longitudinal skin with 12-vertex circularized sections. The
  bells, necks, shaft, and central grip are not joined primitive shells.
- Separate parts are limited to defensible assemblies: trim, dial/clock insert, linked radial
  apertures, articulated hands, linked cradle supports, latch, and editable curve-based rods/cord.
- Main housing weighted-bevel edges are derived from semantic dihedral changes and verified against
  the authored weight attribute. Bevel precedes Subdivision Surface.
- Every renderable mesh has a populated UV layer and node material. Repeated dial apertures share one
  mesh datablock; cradle supports share data in the editable source.

Fresh Blender 5.2 verification passes all 14 assertions. Housing base/evaluated geometry is
208/1,888 quads; handset is 162/2,592 quads. Both remain one component, closed, nondegenerate, and
free of loose vertices at base and evaluated stages.

## Visual gates

Thresholds were unchanged after reference inspection.

| View | Required IoU | Result |
| --- | ---: | ---: |
| Front | 0.78 | 0.949677 |
| Side | 0.68 | 0.746578 |
| Top | 0.68 | 0.823735 |
| Mean | 0.74 | 0.839997 |

The isometric review shows coherent housing depth, shoulder flow, a recessed face, a unified
receiver, and plausible assembly separation. It does not establish historical internal accuracy or
independent professional approval.

## Preserved failures

1. `candidate_v1/`: linked aperture data collapsed to one position, curve names broke silhouette
   rendering, trim bevels created evaluated boundary edges, and the minute-hand bevel degenerated.
2. `candidate_v2/`: technical fixes worked, but front/top/mean IoU remained 0.686527/0.628827/
   0.691107. Diagnosis showed the handset was nearly twice the correct width relative to the body.
3. `production_failed_neutral_bake/`: wiring the active target image into the normal shader before
   baking created a circular dependency and a neutral result.
4. `production_failed_neutral_bake_v2/`: disconnected overlapping high-source boxes still baked
   neutral. A single continuous displaced relief grid replaced them.
5. `production/godot_failed_negative_scale.json`: Godot loaded all geometry and normal semantics
   but rejected the mirrored cradle's negative node scale. Export-only single-user transform
   application fixed the package while preserving linked editability in the saved Blender source.

## Production handoff

The production scene adds a replaceable baked manufacturer badge. A missing-high-source control is
rejected, then a continuous authored high-detail relief bakes to a 256x256 tangent normal map with
26,290 non-neutral pixels. The image is Non-Color and decoded through a Tangent Normal Map node.

The GLB is 535,612 bytes. Fresh Godot 4.7.1 import reports 27 mesh instances/surfaces, 9,296
vertices, UVs and tangents on all 27 surfaces, one correctly normal-mapped surface, and unit node
scales. The negative-scale failure remains preserved.

## Evidence

- `benchmark_brief.md`, `source_selection.json`, `reference_analysis.json`
- `reference/`, `candidate_v1/`, `candidate_v2/`, `candidate_v3/`
- `production/heldout_vintage_telephone_production.blend`
- `production/telephone_badge_tangent_normal.png`
- `production/heldout_vintage_telephone.glb`
- `production/godot_project/godot_import_report.json`

## Bounded conclusion

This closes one additional automated held-out product-family gate and transfers the controlled bake
and named-engine pipeline onto the same asset. It materially strengthens connected-skin, receiver
cage, visual-reference, and production-handoff evidence. It does not prove expert judgment across
unseen assets, independent retention, unknown-defect diagnosis, or human professional acceptance.
