# Operator card: Solidify modifier

**Status:** DOCS ✓ (Blender Manual) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ ~ | RUNTIME_USE ~ | SECOND_SHAPE pending

## Purpose

Use the Solidify modifier to add wall thickness to a surface while preserving the editable source shell.

## Official behavior studied

Source: <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/solidify.html>

- Thickness is computed in local coordinates; non-uniform object scale can produce different world-space thickness on differently oriented surfaces.
- Offset `-1`, `0`, and `1` place generated thickness inside, centered on, or outside the original surface relative to its normals.
- Fill Rim connects inner and outer boundaries; Only Rim retains only generated side walls.
- Vertex groups can vary thickness.
- Even Thickness improves corner consistency but does not guarantee exact thickness for every topology.
- Clamp and Angle Clamp reduce self-intersection risk but do not remove the need for evaluated inspection.
- Simple and Complex/Constraints modes use different thickness strategies and have different cost/robustness tradeoffs.

## Controlled Blender 5.2 findings

Evidence: `runs/2026-08-10_boolean-solidify-foundation/`

On a single quad with thickness `0.2`:

| Variant | Evaluated verts/faces | Boundary edges | World Z bounds |
| --- | --- | ---: | --- |
| Fill Rim on, offset -1 | 8 / 6 | 0 | -0.2 to 0.0 |
| Fill Rim off, offset -1 | 8 / 2 | 8 | -0.2 to 0.0 |
| Offset 0 | 8 / 6 | 0 | -0.1 to 0.1 |
| Offset +1 | 8 / 6 | 0 | 0.0 to 0.2 |

Fill Rim produced a closed manifold shell. Disabling it intentionally left eight boundary/non-manifold edges and failed independent evaluated verification.

## Failure case: non-uniform scale

With requested thickness `0.2` and unapplied object scale `(1, 1, 2)`, world-space thickness became `0.4`. Resetting/applying the same scale before Solidify restored world thickness to `0.2`.

Therefore:

> Apply or explicitly account for non-uniform scale before judging Solidify thickness.

## Preconditions and verification

- Confirm face normals because Offset direction depends on them.
- Decide whether open boundaries should be capped; an open rim may be intentional but must not be reported as a closed solid.
- Inspect evaluated wall thickness at corners and high-valence regions.
- Check self-intersections and minimum edge lengths after Clamp/Even Thickness changes.
- Put Solidify before Bevel when a flat shell needs real dihedral edges for the bevel to affect.
- Preserve the source surface and modifier until thickness and offset are approved.
