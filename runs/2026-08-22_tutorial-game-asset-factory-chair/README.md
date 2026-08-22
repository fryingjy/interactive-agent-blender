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

## Correction: the video-inspection evidence was already there, just underused

Revisited this run's own `gemini_full_video_unverified.json`, which was underused: its provenance
records `video_inspected: true` and `audio_inspected: true` with `evidence_modalities: ["AUDIO",
"UI_TEXT", "VIDEO"]` and 0.95 confidence on every one of its four episodes -- meaning this is real
frame-level video inspection, not a caption-only transcript. The "browser connection failed" note
above refers to a *separate* attempt at pulling a comparison frame directly, not to this file, which
was sitting unused the whole time.

Comparing this run's actual construction against what Gemini observed frame-by-frame:

| Step | Gemini's observed real video | This run's build |
| --- | --- | --- |
| Seat | Flatten default cube on Z in Edit Mode | Flatten one cube in Edit Mode -- match |
| Loop cuts | Four perimeter loop cuts near outer edges, top and bottom -- "subdivided top and bottom faces into a 3x3 grid" | Four perimeter loop cuts leaving a three-by-three seat grid -- match |
| Legs | Extrude Individual on the four bottom corner faces | Extrude the four bottom corner regions into legs -- match |
| Backrest | Extrude Individual on the three rear top faces, resulting in "one solid backrest panel" (Gemini's own observed result, not assumed) | Extrude the complete rear top row into one connected backrest -- match |
| Leg proportion | A distinct follow-up step: X-Ray + vertex select + G Z to lengthen the legs independently of the backrest | Not run as a separate step, but the saved render already shows legs proportioned clearly longer than a naive single-height extrusion would give (visible in `chair_isometric_solid.png`) |

Four of five real, observed construction decisions match this build's own construction directly and
specifically, not just in spirit. The one difference (leg length as a separate adjustment step versus
built into the initial extrusion height) doesn't change the resulting topology or proportions in a
way the render contradicts.

**Status, evidence-grounded rather than left pending indefinitely**: this is process/topology
fidelity evidence, not a pixel-level comparison against a finished-result photo the way the other
beginner lessons had (no such image exists for this tutorial). Scored **7.5/10** on that narrower
basis -- the construction sequence and resulting form both match real video-inspected evidence
closely, but this is a different, more limited kind of verification than direct visual comparison,
and is documented as such rather than conflated with it. This does not, on its own, count as one of
the two consecutive 8/10 passes the apprenticeship ladder requires (that gate is already satisfied
by B1 and B4), but it closes the evidence gap that was leaving this lesson in an indefinite pending
state for no real reason.

This exercise validates a bounded beginner principle only: compatible chair regions can be grown
from loop-cut faces of one base cage. It does not imply that every chair should be one object or that
one connected mesh is always preferable to genuine assemblies.
