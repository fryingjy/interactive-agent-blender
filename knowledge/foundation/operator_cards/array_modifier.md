# Operator card: Array modifier

**Status:** DOCS ✓ (Blender 5.0 Manual generation) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE pending | SECOND_SHAPE pending

## Official behavior studied

Source: <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/array.html>

- Fixed Count, Fit Length, and Fit Curve determine copy count differently.
- Relative Offset uses the base object's local bounding-box dimensions; Constant Offset adds a fixed translation; Object Offset contributes another transform.
- Enabled offset components are additive.
- Merge only welds adjacent-copy vertices within the configured distance; broad thresholds can weld unintended geometry.
- Fit Length/Fit Curve calculations use local-space dimensions, so unapplied object/curve scale can produce unintuitive world-space outcomes.

## Blender 5.2 controlled findings

Evidence: `runs/2026-08-10_array-deform-retopology/`

A three-copy cube array produced 24 evaluated vertices and 18 faces. With the same relative factor, adding a 0.3 constant offset increased world X span from 6.0 to 6.6, confirming additive offsets. Leaving X object scale at 2.0 doubled world span from 6.0 to 12.0 while the modifier's relative factor remained 1.0.

## Decision rule

Use Array when repetition is genuinely regular and should stay editable. Before choosing count/fit/offset, inspect applied scale and local axes. Verify total span, gaps/overlaps, and evaluated merge behavior; do not infer correctness from copy count alone.
