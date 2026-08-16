# Curved Bevel normal-policy experiment

This Blender 5.2 experiment separates Bevel-induced normal error from error already encoded by a
curved cage. It compares four live, unapplied policies across three manufactured radial families:

| Columns, left → right | Rows, top → bottom |
| --- | --- |
| no-Bevel semantic baseline; plain smooth Bevel; Bevel Harden Normals; Bevel Face Strength → Weighted Normal | uniform 12-sided cylinder; uneven equal-count 12-sided cylinder; uniform 16-sided taper |

The uniform and uneven cylinders deliberately contain the same number of radial vertices. Only
their angular distribution differs.

## Result

- Plain smooth Bevel bends planar cap normals by `8.4464°–8.4823°` and curved-side normals by up
  to `7.8370°` beyond the semantic baseline.
- Harden Normals restores all three side families to their unbeveled baseline and reduces cap error
  to `0°`.
- Face Strength followed by Weighted Normal also flattens every cap (`<0.000085°` error) and stays
  near analytic on the uniform cylinder/taper.
- The uneven 12-sided cage already has `5.0°` side-normal error before Bevel. Harden Normals restores
  that same `5.0°` baseline; Weighted Normal increases it to `9.9988°`, worse than plain smooth
  Bevel at `9.0773°`.

Therefore normal correction is not topology correction. Equal segment count is insufficient;
angular distribution controls curved highlight quality. Harden Normals is the safer local rim
policy in these fixtures because it preserves surrounding normals. Weighted Normal remains useful
for suitable panel distributions but must be checked independently on curved regions.

## Evidence

- `curved_bevel_normal_policy_report.json` — hypotheses, full metrics, and lab assertions;
- `curved_bevel_normal_policy_fresh_verification.json` — independent reload, live-stack, topology,
  and numeric checks;
- `curved_bevel_normal_policy_matcap.png` — controlled MatCap comparison;
- `curved_bevel_normal_policy.blend` — twelve editable base objects with modifiers unapplied.

Boundary: controlled low-sided radial fixtures only. This does not establish arbitrary double
curvature, SubD interaction, real-prop fidelity, or human acceptance.
