# Beginner tutorial reproduction: connected chair

Source: Game Asset Factory, “16 Curso Blender para Iniciantes COMPLETO - Exercicio Prático -
Cadeira Básica com Loop & Extrude” (`LyPPgW9GpKo`, 124 seconds).

This is the first exercise in the stricter tutorial-apprenticeship restart. It reproduces the
lesson's construction rather than using a chair-specific primitive assembly:

1. flatten one cube in Edit Mode to establish the seat;
2. create four perimeter loop cuts, leaving a three-by-three seat grid;
3. extrude the four bottom corner regions into legs;
4. extrude the complete rear top row into one connected backrest;
5. inspect the base mesh in front, side, and isometric solid-mode views.

## Result

- one mesh object;
- one connected component;
- 56 vertices, 108 edges, and 54 quad faces;
- zero boundary or non-manifold edges;
- no modifiers and no disconnected joined shells;
- final `.blend` plus three solid-mode diagnostic renders.

The deterministic mesh generator constructs the same topology implied by the demonstrated loop-cut
and extrusion sequence. It removes shared internal faces as adjacent regions grow, so the result is
a manifold connected cage rather than overlapping boxes.

## Evidence and limitations

Gemini inspected the complete audiovisual lesson. Its payload was initially rejected twice: one
response used percentage confidence and another encoded `01:05` as numeric `105` seconds. The
pipeline now retains rejected payloads and deterministically normalizes only unambiguous percentage
and MM:SS cases, recording every correction. Thirty-one focused tests pass.

The in-app browser connection failed during independent frame inspection, and the public thumbnail
contains only title artwork. Therefore the result is **MODELED / SOURCE-FRAME REVIEW PENDING**, not
a fidelity pass. The observed construction is strong enough to execute, but advancement requires a
later independent source-frame comparison when browser/video-frame access is available.

This exercise validates a bounded beginner principle only: compatible chair regions can be grown
from loop-cut faces of one base cage. It does not imply that every chair should be one object or that
one connected mesh is always preferable to genuine assemblies.
