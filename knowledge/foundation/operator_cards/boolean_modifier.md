# Operator card: Boolean modifier

**Status:** DOCS ✓ (Blender 5.0 Manual) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ ✓ | RUNTIME_USE ✓ | SECOND_SHAPE ✓

## Purpose

Use the Boolean modifier to combine volumes through Difference, Union, or Intersect. Treat it as a fast shape-construction strategy whose evaluated topology must be inspected rather than assumed production-ready.

## Official behavior studied

Source: <https://docs.blender.org/manual/en/dev/modeling/modifiers/generate/booleans.html>

- **Difference** subtracts source volume from the modified mesh.
- **Union** combines source and target while removing interior faces.
- **Intersect** keeps only shared volume.
- The **Fast** solver is quick but does not support overlapping geometry robustly.
- The **Exact** solver is slower and is intended for coplanar or overlapping geometry.
- The **Manifold** solver is usually fastest but requires manifold operands, except for the documented plane-Difference special case.
- Self Intersection and Hole Tolerant are Exact-solver options with performance costs.
- Only manifold inputs are guaranteed to produce proper results; non-manifold operands may create artifacts.

Blender 5.2 exposes the UI's Fast solver through the Python enum identifier `FLOAT`; `EXACT` and `MANIFOLD` retain matching identifiers. Record UI labels and API identifiers separately.

## Controlled Blender 5.2 findings

Evidence: `runs/2026-08-10_boolean-solidify-foundation/`

Overlapping closed boxes produced:

| Operation / solver | World volume | Evaluated faces | N-gons | Non-manifold |
| --- | ---: | ---: | ---: | ---: |
| Difference / Exact | 5.75 | 12 | 1 | 0 |
| Union / Exact | 9.125 | 12 | 1 | 0 |
| Intersect / Exact | 2.25 | 6 | 0 | 0 |
| Difference / Manifold | 5.75 | 12 | 1 | 0 |

The operations produced the expected volumes and closed meshes. Exact and Manifold Difference agreed on volume in this controlled manifold case. The resulting n-gon in Difference and Union is contextual rather than automatically invalid, but it prevents claiming all-quad production topology.

## Failure case: tangent groove

A torus cutter whose major radius matched a cylinder's surface radius reproduced the project's prior tangent/near-coincident defect class:

```text
314 vertices
526 edges
214 faces
0 non-manifold edges
90 n-gons
18 degenerate faces
minimum evaluated edge length = 0
```

Independent evaluated verification failed for n-gons and degenerate faces while the non-manifold check passed.

Therefore:

> A Boolean can produce the intended volume and remain manifold while still containing unusable seam topology.

Inspect n-gons, degenerate faces, zero-length edges, shading, density, and downstream editability immediately after evaluation/application. Prefer changing cutter placement or strategy over repeatedly repairing a tangent/coincident setup when cleanup cost exceeds the modeling benefit.

## Runtime and transfer evidence

The existing `boolean-groove-cut-topology-cleanup` guidance was learned on a Difference groove, retrieved on a later Flashlight, and generalized successfully to a Mug handle Union. That is meaningful cross-asset/runtime evidence, but the Mug retopology session also proved that valid cleanup does not guarantee good global topology.

## Strategy guidance

- Use Boolean when it expresses the intended volume more directly than manual topology.
- Choose solver from operand validity and overlap conditions; do not default blindly.
- Keep cutters separate and editable until the form is approved.
- Check modifier order when Bevel, Mirror, or SubD depends on Boolean-created edges.
- Rebuild manually when the final asset requires deliberate deformation flow or the repaired Boolean seam remains dense and hard to edit.
