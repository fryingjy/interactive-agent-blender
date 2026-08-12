# Retroactive hard-surface shading policy audit

> **2026-08-12 addendum:** the boombox findings below are historical. The boombox asset was
> separately rejected on direct human visual review (did not resemble its reference at all) and all
> boombox files, including the production `.blend` this report's boombox findings are based on, were
> removed. `no_bevel_triage.json` and `retroactive_audit_report.json` in this run directory have had
> their boombox entries removed to match; the boombox rows/counts described in the prose below no
> longer correspond to any file in this repository and are kept only as a record of what was found
> before the asset was removed.

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

## Correction (second pass)

The first pass of this audit (`blender_ops/object_ops.py` before PR #16) only distinguished
`WEIGHT`-limited Bevel from "everything else," which made every non-`WEIGHT` object read as
undifferentiated "no bevel scoping." That conflated two different things: objects with **no Bevel
modifier at all**, and objects with a real, named `ANGLE`- or `VGROUP`-limited Bevel that simply
isn't the specific method this audit can compare against recorded semantic-edge-ID intent. PR #16
adds `bevel_limit_methods_present` to the audit output and a distinct warning for the ANGLE/VGROUP
case, and this report is corrected to use it. The table below replaces the original pass's numbers.

| Family | Mesh objects | `WEIGHT` bevel | `ANGLE`/`VGROUP` bevel | No Bevel modifier |
| --- | ---: | ---: | ---: | ---: |
| Boombox | 41 | 0 | 30 (29 `ANGLE`, 1 `VGROUP`) | 11 |
| Camera (corrective) | 1 | 1 | 0 | 0 |
| Vintage telephone | 24 | 1 | 6 (`ANGLE`) | 17 |
| Watering can | 7 | 1 | 0 | 6 |

## Reading the result correctly (three separate causes, not one)

1. **Bookkeeping gap, all four families.** `semantic_intent_recorded` and `smooth_by_angle_recorded`
   are `False` everywhere, because the custom properties the audit checks for
   (`hard_surface_intended_bevel_edge_ids`, `shading_policy == "SMOOTH_BY_ANGLE"`) did not exist as a
   concept until this same tranche. This alone would make every pre-existing asset `REVIEW_REQUIRED`
   even if its construction were otherwise ideal, and is not evidence of a modeling defect.
2. **A real, differently-auditable construction choice, mainly the boombox.** 30 of the boombox's 41
   objects (and 6 of the telephone's 24) use a genuine, named, deliberately parameterized `ANGLE`- or
   `VGROUP`-limited Bevel (e.g. `"Purposeful edge radius"`, `"Scoped central recess radius"`) — not
   blanket smoothing with no edge treatment at all. `knowledge/foundation/operator_cards/bevel_modifier.md`
   already documents that `ANGLE` limiting correctly excludes coplanar triangulation edges in a
   controlled test, so this is a legitimate, previously-validated technique the audit simply cannot
   yet compare against a recorded semantic edge-ID map the way it can for `WEIGHT`.
3. **A real gap with no bevel treatment at all.** 11 boombox objects, 17 telephone objects, and 6
   watering-can objects have no Bevel modifier of any kind. Some of these may be legitimately simple
   flat/thin parts that do not need one; this run does not classify which, and that classification is
   left as future work rather than asserted here.

Only each family's single primary body (camera cage, telephone housing, watering-can vessel) has a
`WEIGHT`-limited Bevel with inspectable semantic edge-ID coverage — the specific, fully-auditable
mechanism this policy standardized on.

## What this does and does not establish

This does not mean the four held-out families are visually wrong — their normalized silhouette gates
and fresh-process topology/manifoldness checks already passed independently, and the source files are
left untouched by this run. It establishes that the hard-surface shading policy, as currently
implemented, has a genuinely auditable path (`WEIGHT`) that only each family's primary body used, a
real-but-differently-auditable path (`ANGLE`/`VGROUP`) used by a meaningful fraction of secondary
components, and a real no-bevel-at-all gap on the rest that has not been triaged.

## No-Bevel triage (third pass)

`tools/run_no_bevel_dihedral_triage.py` measures the actual dihedral angle of every edge on each of
the 34 no-Bevel objects (11 boombox, 17 telephone, 6 watering-can) and classifies an object as
`LEGITIMATELY_FLAT` only if its maximum dihedral angle is under 1 degree — i.e. it could not
meaningfully be beveled at all. Output: `no_bevel_triage.json`.

**Result: 33 of 34 are `UNTREATED_SHARP_EDGE_GAP`, not legitimately flat.** Only one object,
`WateringCan_Baked_Badge` (a 4-vertex flat decal plane with zero two-face edges), is genuinely
bevel-inapplicable. Every other no-Bevel object has real sharp geometry with a maximum dihedral angle
between 58.5 and 139.4 degrees — most at exactly 90 degrees (cassette reels, fasteners, dial
apertures, trim panels) — that received no edge treatment of any kind.

This is a materially larger finding than "some decorative trim is unbeveled." Two of the untreated
objects are entire **primary structural components**, not secondary detail, that their own session
reports described as finished connected cages:

- The vintage telephone's **`Handset`** (324 two-face edges, up to 168 over 25 degrees, max 71.82
  degrees) — the session report calls it "one closed connected 162-quad longitudinal skin," on par
  with the housing, but only the housing actually received the `WEIGHT`-limited Bevel.
- The watering can's **`Connected_Tapered_Spout`** and **`Arched_Handle`** (156 and 228 two-face
  edges respectively, up to 92.2 degrees) — both described in the session report as their own closed
  all-quad path lofts alongside `Connected_Vessel`, but only the vessel received edge treatment.

Only `Connected_Vessel` (watering can) and the telephone's `Housing` are confirmed to carry the full
policy; their sibling primary components do not.

## Not done in this run

- No production `.blend` was modified, re-shaded, or re-saved.
- The untreated objects identified above have not been rebuilt with semantic bevel weights; this run
  measures and classifies, it does not repair.
- Retrying any of the four families' secondary components under the full `WEIGHT` policy, or
  deciding whether `ANGLE`/`VGROUP` should become a second fully-sanctioned `PASS` path with its own
  auditable-intent mechanism, is separate, larger follow-on work.
