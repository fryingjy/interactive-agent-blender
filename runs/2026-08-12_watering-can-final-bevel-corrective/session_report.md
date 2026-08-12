# Watering can final bevel corrective

## Trigger

`runs/2026-08-12_shading-policy-retroactive-audit/no_bevel_triage.json` classified all six
no-Bevel watering-can objects except one (a flat badge decal) as `UNTREATED_SHARP_EDGE_GAP`. The
spout and handle were corrected in `runs/2026-08-12_watering-can-secondary-bevel-corrective/`. This
closes the last three: `Opening_Rim`, `Opening_Shadow`, and `Rose_Head`.

`Opening_Shadow` is worth flagging specifically: at 1.76 x 1.76 x 0.015 units it looked, from
dimensions alone, like it might be another legitimately-flat decal similar to
`WateringCan_Baked_Badge`. The triage's dihedral measurement (max 90 degrees) already showed
otherwise -- it is a genuinely thin disc with real sharp rim edges, not a flat plane -- and that
result held up: it applied cleanly with a proportionally small bevel width (0.004, versus 0.015 for
the thicker `Opening_Rim`).

## Builds on the spout/handle correction

`SOURCE` is `runs/2026-08-12_watering-can-secondary-bevel-corrective/heldout_watering_can_production_corrected.blend`,
not the original published file, so this output carries all three watering-can fixes cumulatively.
Both the spout/handle-corrected file and the original published file are confirmed byte-for-byte
unmodified.

## Result

All three objects applied cleanly on their first candidate width; no winding-consistency repair was
needed for any of them (unlike two of the telephone's trim panels).

| Object | Sharp edges | Width | Audit |
| --- | ---: | ---: | --- |
| `Opening_Rim` | 64 | 0.015 | `PASS` |
| `Opening_Shadow` | 32 | 0.004 | `PASS` |
| `Rose_Head` | 64 | 0.015 | `PASS` |

`Connected_Vessel`, `Connected_Tapered_Spout`, and `Arched_Handle` are all confirmed undisturbed.

## Visual review

`rose_head_profile_before.png`/`_after.png` isolate `Rose_Head` (the watering can's spray-head
fitting) in an edge-on side view. Before: a smooth, blurry, rounded blob with one diffuse hazy
highlight. After: distinct planar facets with sharp highlight breaks between them -- a clearly
faceted hard-surface form instead of an organic-looking mass. This is the strongest single visual
delta in this whole correction series.

## Independent verification

`tools/verify_watering_can_final_bevel_corrective.py` is a separate script from the generator. It
confirms all three objects pass and are evaluated-clean, the vessel/spout/handle corrections remain
undisturbed, and both the spout/handle-corrected source and the original published file are
byte-for-byte unmodified (SHA-256). All 11 checks pass.

## Status

This closes the no-Bevel triage's remaining-work list entirely. Every object across all three
retroactively-audited families (boombox, telephone, watering can) that the triage identified as a
genuine untreated sharp-edge gap now has a real, verified, visually-confirmed bevel correction. The
only objects the triage left untreated are the ones it correctly classified as legitimately flat.
