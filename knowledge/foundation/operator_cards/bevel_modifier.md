# Operator card: Bevel modifier

**Status:** DOCS ✓ (Blender Manual 4.5 LTS) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ~ | SECOND_SHAPE ✓

## Purpose

Use the Bevel modifier as a non-destructive alternative to the Edit Mode bevel operation. It changes evaluated geometry while preserving the base cage until applied.

## Official behavior studied

Source: <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html>

- `Affect` selects edge or vertex beveling.
- Width methods (`OFFSET`, `WIDTH`, `DEPTH`, `PERCENT`, `ABSOLUTE`) interpret the same numeric width differently.
- `Segments` controls loops added across the bevel profile.
- Limit methods can target all edges, an angle threshold, bevel-weight attributes, or a vertex group.
- `Clamp Overlap` restricts width when neighboring bevels would overlap.
- Miter and intersection modes change corner topology; shading options can harden normals and propagate seam/sharp attributes.

The accessible Manual page is labeled Blender 4.5 LTS. Runtime findings below were reproduced independently in installed Blender 5.2.0 LTS; do not silently treat the version gap as proof that every option is unchanged.

## Controlled Blender 5.2 findings

Evidence: `runs/2026-08-10_modifier-foundation/`

| Variant | Evaluated verts | Faces | Non-manifold |
| --- | ---: | ---: | ---: |
| Triangulated cube, limit `NONE`, width 0.2, segments 2 | 80 | 84 | 0 |
| Same cube, limit `ANGLE` at 30°, width 0.2, segments 2 | 56 | 60 | 0 |
| Cube, segments 1 | 24 | 26 | 0 |
| Cube, segments 3 | 96 | 98 | 0 |

Angle limiting excluded coplanar triangulation edges in this test. Unrestricted beveling processed those internal diagonals and created substantially more geometry.

Increasing segments from 1 to 3 quadrupled evaluated vertex count on the test cube (24 to 96). Choose segment count from silhouette/highlight requirements rather than treating more segments as automatically better.

## Failure case: excessive width

On a 2×2×2 cube with width 2.0 and three segments:

- Clamp enabled: minimum evaluated edge length was approximately `2.38e-7`.
- Clamp disabled: minimum evaluated edge length was approximately `0.731`.

Both results remained manifold, but Clamp produced nearly collapsed edges. Therefore:

> Clamp Overlap prevents a class of overlap; it does not guarantee healthy topology or a visually useful bevel at excessive width.

Inspect evaluated edge lengths, corner topology, and highlights after large bevels. Manifoldness alone is insufficient.

## Cylindrical second-shape transfer

Evidence: `runs/2026-08-10_bevel-mirror-transfer/`

A closed cylinder stretched to world height 4 was beveled at width 0.1 with one segment. Applying the Z scale before Bevel produced a measured world-space top band of 0.1. Leaving object Z scale at 2.0 produced a 0.2 band. Both evaluated meshes were closed and independently verified clean (allowing their two intentional cap n-gons).

The scale warning therefore transferred beyond the original box-like cases: a manifold result can still have inconsistent world-space bevel width.

## Weighted-edge production transfer

Evidence: `runs/2026-08-11_connected-camera-corrective/`

Experienced review identified excessive softness after a clean one-component camera already passed
silhouette and topology gates. A live user example demonstrated `Bevel` limited by edge weight before
two SubD levels. On the corrective camera:

- Weighting all 198 lens/front/back candidate edges sharpened the image but created 48 Bevel-stage
  and 192 post-SubD non-manifold edges.
- Reducing width from `0.028` to `0.004` did not change those counts, disproving excessive width as
  the cause.
- Scope probes isolated the cause: 14 front-perimeter weighted edges produced 12 Bevel-stage
  non-manifold edges; 24 back/star-cap edges produced 36; 144 lens-ring edges produced zero before
  and after SubD.
- The accepted stack therefore uses 144 edges at weight `1.0`, Bevel width `0.028`, two Bevel
  segments, then two SubD levels. The shell perimeter uses closer authored support loops instead.

Weighted bevel is a fast sharpness control, not a blanket license. Probe edge scope separately from
width and verify the evaluated mesh after every downstream modifier.

## Preconditions and verification

- Apply or account for non-uniform object scale before judging world-space bevel consistency.
- Confirm the limit method targets the intended edges.
- Inspect both base cage and evaluated surface.
- Check density, minimum edge lengths, corner intersections, shading, and silhouette.
- Test modifier order whenever another modifier creates or removes edges relevant to the bevel.
