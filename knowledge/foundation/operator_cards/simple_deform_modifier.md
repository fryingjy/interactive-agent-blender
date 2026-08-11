# Operator card: Simple Deform modifier

**Status:** DOCS ✓ (Blender 3.6/5.x Manual generations) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE pending | SECOND_SHAPE pending

## Official behavior studied

Source: <https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/simple_deform.html>

- Twist/Bend use an angle; Taper/Stretch use a factor.
- Deformation is calculated in local coordinates around the object origin or an optional origin object.
- Limits and vertex groups restrict influence.
- Geometry distribution matters: unsuitable axes or insufficient samples can produce no deformation or poor surfaces.

## Blender 5.2 controlled findings

Evidence: `runs/2026-08-10_array-deform-retopology/`

A 180° Twist on an eight-vertex elongated cube produced four degenerate evaluated faces and failed independent verification. Adding three levels of Simple subdivision before Twist produced a 386-vertex all-quad manifold output; compared with a subdivision-only control, mean vertex displacement was 0.5645 and maximum displacement 1.2.

A planar grid bent on an unsuitable local X axis moved zero vertices, reproducing the documented no-op class.

The lab also exposed an API pitfall: in Blender 5.2, setting `angle` and then `factor` on the same Simple Deform modifier reset the deformation amount to zero. Set only the property appropriate to the selected mode and verify evaluated displacement.

## Decision rule

Confirm local axes, origin, deform mode, amount, and mesh resolution before relying on the result. Compare against the undeformed evaluated control, not just the base cage. Treat degenerates or an unchanged output as failure even when the modifier exists and Blender reports no exception.
