# Retroactive hard-surface shading policy audit

## Scope

`get_hard_surface_shading_audit()` (added and merged in PR #13, 2026-08-12) was built and verified
against fresh fixtures only. It had never been run against the four already-published held-out
production files. This run opens each production `.blend` read-only (no save, no geometry change)
and calls the audit on every mesh object in the file.

Source: `tools/run_shading_policy_retroactive_audit.py`. Targets and their production files:

- `heldout_cc0_boombox_001` -> `runs/2026-08-11_heldout-boombox/final/heldout_boombox.blend`
- `heldout_cc0_camera_001` -> `runs/2026-08-11_connected-camera-corrective/connected_camera_corrective.blend`
- `heldout_cc0_vintage_telephone_001` -> `runs/2026-08-11_heldout-vintage-telephone/production/heldout_vintage_telephone_production.blend`
- `heldout_cc0_watering_can_001` -> `runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend`

## Result

Every mesh object in all four files returns `REVIEW_REQUIRED`. Zero objects `PASS`.

| Family | Mesh objects | Flagged unannotated-blanket-smooth | Objects with a WEIGHT-limited Bevel |
| --- | ---: | ---: | ---: |
| Boombox | 41 | 0 | 0 |
| Camera (corrective) | 1 | 1 | 1 |
| Vintage telephone | 24 | 23 | 1 |
| Watering can | 7 | 6 | 1 |

## Reading the result correctly (two separate causes, not one)

1. **Bookkeeping gap, all four families.** `semantic_intent_recorded` and `smooth_by_angle_recorded`
   are `False` everywhere, because the custom properties the audit checks for
   (`hard_surface_intended_bevel_edge_ids`, `shading_policy == "SMOOTH_BY_ANGLE"`) did not exist as a
   concept until this same tranche. This alone would make every pre-existing asset `REVIEW_REQUIRED`
   even if its construction were otherwise ideal, and is not evidence of a modeling defect.
2. **Real construction gap, three of four families.** The camera, telephone, and watering-can files
   each have exactly one object with a `WEIGHT`-limited Bevel modifier — the single primary body each
   session report described in detail (housing, vessel, one-object cage). Every other component in
   those files (23/24 telephone parts, 6/7 watering-can parts) has **no** weight-limited Bevel at all
   and is blanket Shade-Smooth. That is a real, pre-policy construction gap, not a recording gap: the
   secondary/detail components (trim, dial, hands, cradle, rose head, opening rim, etc.) were shaded
   with ordinary Shade Smooth rather than semantic-weight/Bevel/SubD, because the policy this audit
   enforces did not exist while they were built. The boombox has zero `WEIGHT` bevels anywhere; its
   session report documents it used `ANGLE`-limited Bevel scoped by vertex groups instead, which this
   audit does not currently recognize as an equivalent sanctioned path.

## What this does and does not establish

This does not mean the four held-out families are visually wrong — their normalized silhouette gates
and fresh-process topology/manifoldness checks already passed independently, and the source files are
left untouched by this run. It establishes that the hard-surface shading policy, as currently defined,
is real new capability that has not yet been applied to secondary/detail geometry in any prior
held-out asset, and that `ANGLE`-limited Bevel (used by the boombox) is currently outside what the
audit checks for as a sanctioned alternative to `WEIGHT`-limited Bevel.

## Not done in this run

- No production `.blend` was modified, re-shaded, or re-saved.
- The audit's `ANGLE`-limited-Bevel gap is recorded here as a finding, not fixed.
- Retrying any of the four families' secondary components under the full policy is separate,
  larger follow-on work.
