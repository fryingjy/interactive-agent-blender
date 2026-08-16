# Westclox 70010A — reference and construction plan

Target: the current silver Westclox 70010A twin-bell quartz alarm clock. The reference package is
from one matching product listing and includes front, oblique, rear, and dimensioned views. It
supports primary-form work, but not hidden internal construction.

The formal evidence-bound [scene decomposition](scene_decomposition.json) and its verified
[planner strategy record](planner_strategy_record.json) are authoritative over this prose for any
future retry. They were added after the primitive-only Stage 01/02 attempt was rejected.

## Observable hierarchy

1. A shallow circular main shell: silver outer rim and front bezel, white face inset, dark rear plate.
2. Two symmetric, pressed-metal dome bells and a thin inverted-U rod handle above the shell.
3. A small centered hammer on a vertical strut, visually between the bells.
4. Two outward-splayed tapered front legs with collar steps and round feet.
5. Rear-only controls: two deep black wells, slider, four screws, light button, and battery door.

## Intended editable construction

- `ClockShell_HIGH`: one 12–16-sided shallow radial connected cage. Use sparse radial/longitudinal
  loops to create the face recess, bezel lip, and rear transition. Do not stack default cylinders.
- `FrontFace`, `RearPlate`, `Bell_L`, `Bell_R`, `Handle`, `Hammer`, `Leg_L`, and `Leg_R` are distinct
  only because the reference shows separate manufactured or functional assemblies.
- Start the bells and legs from low-sided editable profiles; use a curve or bent box-derived cage for
  the handle rather than a high-sided tube by habit. Mirror bilateral assemblies where it preserves
  editability.
- Keep the source cage and modifiers live. Crease/support loops come only after front/oblique/rear
  primary silhouettes and component proportions are compared.

## Blockout checks before any dial graphics or rear controls

- overall envelope: 4.56 in length × 2.36 in depth × 6.49 in height;
- body diameter-to-depth ratio and bezel-to-face ratio;
- bell width/span, handle arch height, hammer placement, and leg splay;
- front, oblique, and rear component silhouettes independently;
- explicit uncertainty: hidden bell mounting, glass retention, and internal rear-shell detail.

No HTML reference board or pre-model approval is required. A later visual rejection still overrides
technical checks and stops detail work.
