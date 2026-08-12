# Vintage telephone handset bevel corrective

## Trigger

`runs/2026-08-12_shading-policy-retroactive-audit/no_bevel_triage.json` found `Handset` (max
dihedral 71.82 degrees, 168 edges over 25 degrees) is a primary structural component -- the original
session report describes it as "one closed connected 162-quad longitudinal skin" on par with
`Main_Housing` -- that never received any Bevel treatment. Only the housing had one.

## Method

`tools/run_telephone_handset_bevel_corrective.py` mirrors the watering-can spout/handle corrective,
with one structural difference: `Handset` already carried a `Subdivision Surface` modifier with no
Bevel before it, so the new Bevel had to be **inserted** at the correct stack position (index before
`SUBSURF`), not simply appended.

1. Opens the published production file directly; never saves over it.
2. Computes sharp edges (two-face edges with dihedral angle over 25 degrees, this repo's established
   threshold) mapped to persistent edge IDs: 168 edges.
3. Assigns `bevel_weight_edge = 1.0` to those edges and records `hard_surface_intended_bevel_edge_ids`.
4. Inserts a `WEIGHT`-limited Bevel before the existing Subdivision modifier, trying candidate widths
   `[0.015, 0.010, 0.006]` and evaluating the full modifier stack (not just Bevel-only, since SubD is
   already present) after each. **Passed cleanly on the first, most generous width (0.015)** -- no
   narrowing needed.
5. Applies `set_smooth_by_angle`.
6. Saves as a new file, reopens that saved file, and audits/verifies against what is actually on
   disk rather than in-memory state.
7. Renders MatCap before/after comparisons with `hard_surface_grey.exr`.

## Result

| Object | Sharp edges weighted | Accepted Bevel width | Modifier order | Audit status |
| --- | ---: | ---: | --- | --- |
| `Handset` | 168 | 0.015 | `BEVEL -> SUBSURF` | `PASS` |

Evaluated Handset: 11,426 vertices / 11,424 faces, 0 non-manifold edges, 0 degenerate faces.
`Main_Housing`'s pre-existing `WEIGHT` bevel is confirmed undisturbed.

## Visual review

`crop_before_handset.png` vs `crop_after_handset.png` (cropped/upscaled from the isometric MatCap
render) show the same class of improvement as the watering can: before, the earpiece/mouthpiece bells
and shaft read as one continuous soft, rounded, sausage-like blob. After, there is a crisp facet and
highlight break running the length of the shaft and around both bells -- a hard-surface molded-plastic
read instead of an organic shape. This is a real visible change, not merely a passing numeric check.

## Independent verification

`tools/verify_telephone_handset_bevel_corrective.py` is a separate script from the generator. It
opens only the saved corrected file and confirms: the audit passes, the evaluated mesh is clean,
Bevel precedes Subdivision in the modifier stack, the housing's existing bevel is undisturbed, and
(by SHA-256 hash comparison) the original published production file is byte-for-byte unmodified.
All 5 checks pass.

## What this does not establish

- `Dial_Aperture*`, `Clock_Face`, `Lower_Panel_Trim`, `Upper_Face_Trim`, and `Telephone_Baked_Badge`
  remain untreated (all real sharp-edge gaps per the triage except the flat badge).
- Overall silhouette/UV/GLB/Godot production gates for this asset were not rerun.
- This corrected file is a new artifact alongside the original; whether it should replace the
  published production reference is a follow-on decision, not made here.
