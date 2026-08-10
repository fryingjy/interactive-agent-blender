# Operator card: Mirror modifier

**Status:** DOCS ✓ (Blender Manual 4.2/4.5 generation) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ ~ | RUNTIME_USE ~ | SECOND_SHAPE pending

## Purpose

Use the Mirror modifier to duplicate geometry across one or more local axes around the object origin or a designated Mirror Object. Keep it non-destructive when continued symmetric editing is valuable.

## Official behavior studied

Source: <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/mirror.html>

- The mirror plane uses the modified object's local axes unless a Mirror Object supplies the position and rotation.
- Enabling multiple axes produces multiple mirrored copies.
- `Merge` welds matching vertices within `Merge Distance`.
- `Clipping` constrains Edit Mode movement at the plane; it does not retroactively merge vertices already outside the merge distance.
- `Bisect` cuts geometry crossing the plane before mirroring; `Flip` chooses which side remains.
- UV and vertex-group data have dedicated mirroring rules.

The experiment used installed Blender 5.2.0 LTS. Treat the accessible older Manual labeling and the newer runtime as separate evidence.

## Controlled Blender 5.2 findings

Evidence: `runs/2026-08-10_modifier-foundation/`

The source mesh was an open half-box whose missing face lay at the intended mirror seam.

| Seam X | Merge threshold | Evaluated verts | Boundary/non-manifold edges |
| ---: | ---: | ---: | ---: |
| 0.000 | 0.001 | 12 | 0 |
| 0.002 | 0.001 | 16 | 8 |
| 0.002 | 0.010 | 12 | 0 |

An exact seam merged into a closed evaluated mesh. Moving the seam outside the threshold left two open boundaries. Raising the threshold closed the same source mesh.

A full cube crossing the mirror plane with X Bisect enabled evaluated to a closed 12-vertex, 10-face mirrored result with zero non-manifold edges, confirming that Bisect discarded one side before mirroring in this controlled case.

## Failure diagnosis

When a mirror seam remains visible or non-manifold, inspect:

1. object origin or Mirror Object placement;
2. local axis orientation and unapplied transforms;
3. seam vertex distance from the plane;
4. `Merge` state and threshold;
5. whether Clipping was enabled before the edit;
6. modifier order and evaluated, not only base-cage, topology.

Do not increase Merge Distance blindly: a broad threshold can weld nearby geometry that was intended to remain distinct.
