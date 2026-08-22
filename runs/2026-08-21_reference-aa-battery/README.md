# AA/LR6 reference-to-construction blockout

This is the post-audit real-reference execution case. It is intentionally a small manufactured
object so the repository can prove the missing reasoning chain without hiding behind complexity.

## Observation and uncertainty

- The Duracell/IEC drawing bounds the complete cell to 49.2-50.5 mm high and 13.5-14.5 mm in
  diameter. The 50.5 mm maximum includes the positive terminal.
- The positive terminal is at most 5.5 mm in diameter and projects at least 1.0 mm.
- A second public-domain line drawing independently supports a representative 50 x 14 mm form.
- Wrapper artwork, crimp micro-profile, and manufacturer-specific bottom details are deliberately
  outside this primary-form blockout.

## Competing interpretations

`representation_hypotheses.json` separates independent observations from candidate predictions.
The evaluated result selects one connected cylinder whose original top face is inset and extruded.
It contradicts the alternative that treats 50.5 mm as body-only height and stacks another terminal
on top. The decision is supported by side and top evidence, not list order or prose confidence.

## Blender construction and correction

The model was made in one persistent Blender 5.2 session through the typed runtime. It starts from
one 16-sided cylinder, not a collection of stacked cylinders. The existing top face was inset and
extruded 1 mm, preserving a single connected mesh. Four circular transition loops were then given a
small two-segment physical bevel, followed by Blender's Smooth by Angle operation rather than blanket
Shade Smooth. The resulting dimensions are exactly 14.5 x 14.5 x 50.5 mm in both base and evaluated
geometry.

The first attempted side render used an unsupported `right` view token and was rejected by the
renderer; it was corrected to the typed `side` view. This is an interface correction, not a geometry
success claim.

Fresh-process inspection then exposed a real scene-cleanliness defect: the persistent GUI had
started with Blender's default Cube, Camera, and Light. `tools/clean_blend_scene.py` removed those
three undeclared objects through an explicit keep allowlist. Reinspection now reports exactly one
mesh object in the file.

## Evidence and boundary

- `aa_battery_blockout.blend` — editable connected blockout.
- `aa_front_solid.png`, `aa_side_solid.png`, `aa_top_solid.png`, and `aa_iso_solid.png` —
  Blender-native solid review views.
- `typed_action_record.json` — revision-linked construction summary and final mesh state.
- `hypothesis_evaluation.json` — independent competing-representation result.
- `reference_audit.json` — structured source/readiness audit.
- `scene_cleanup.json`, `asset_inspection.json`, and `verify/` — allowlist cleanup plus independent
  fresh-process scene and mesh verification.

The object is a technically and dimensionally grounded primary form. It has not received human
visual approval and does not count as a finished prop or a promoted benchmark.
