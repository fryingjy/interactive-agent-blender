# Watering-can spout/handle bevel corrective

## Trigger

`runs/2026-08-12_shading-policy-retroactive-audit/no_bevel_triage.json` found that the watering
can's `Connected_Tapered_Spout` (max dihedral 92.2 degrees, 84 edges over 25 degrees) and
`Arched_Handle` (max dihedral 90.2 degrees, 142 edges over 25 degrees) are primary structural
components — their own original session report describes them as closed all-quad path lofts on par
with `Connected_Vessel` — that never received any Bevel treatment. Only the vessel had one.

## Method

`tools/run_watering_can_secondary_bevel_corrective.py`:

1. Opens the published production file (`runs/2026-08-11_heldout-watering-can/production/heldout_watering_can_production.blend`) directly. The original file is never saved over.
2. For each of the two objects, computes sharp edges as those with two linked faces and a dihedral
   angle over 25 degrees (the same threshold this repo has used elsewhere, e.g. the live-scene
   inspection recorded in `runs/2026-08-11_connected-camera-corrective/session_report.md`), mapped to
   persistent edge IDs.
3. Assigns `bevel_weight_edge = 1.0` to exactly those edges via `set_bevel_weight_by_ids`, which also
   records `hard_surface_intended_bevel_edge_ids` for later audit.
4. Adds/updates a `WEIGHT`-limited Bevel modifier, trying progressively narrower candidate widths
   (spout: 0.015/0.010/0.006; handle: 0.010/0.006/0.004) and evaluating the Bevel-only stage in
   isolation each time. Both objects passed cleanly on their **first**, most generous candidate
   width (spout 0.015, handle 0.010) — no narrowing was needed.
5. Applies `set_smooth_by_angle` to record the policy.
6. Saves the result as a new file in this run directory, then **reopens that saved file** (not the
   in-memory scene) before running the audit and evaluated-mesh checks, so the report reflects what
   is actually on disk.
7. Renders MatCap before/after comparisons using this repo's established `hard_surface_grey.exr`
   hard-surface review light (see `tools/run_connected_camera_corrective.py`).

## Result

Both objects reach `get_hard_surface_shading_audit` `PASS` and are evaluated-clean (0 non-manifold
edges, 0 degenerate faces) at base and after the full modifier stack:

| Object | Sharp edges weighted | Accepted Bevel width | Audit status |
| --- | ---: | ---: | --- |
| `Connected_Tapered_Spout` | 84 | 0.015 | `PASS` |
| `Arched_Handle` | 142 | 0.010 | `PASS` |

`Connected_Vessel` (already had a `WEIGHT` bevel) is untouched and its bevel weighting is confirmed
undisturbed. `Opening_Rim`, `Opening_Shadow`, `Rose_Head`, and `WateringCan_Baked_Badge` are
unchanged — this run does not claim to have fixed those.

## Visual review (separate gate from the numeric pass)

`crop_before_spout_handle.png` vs `crop_after_spout_handle.png` (matcap, cropped/upscaled from the
isometric MatCap render) show a real, visible difference: before, the spout/handle read as a fully
rounded tube with one soft, undifferentiated specular highlight across the top. After, there is a
crisp facet/highlight break running along the top edge — genuine hard-surface definition instead of
a smoothed blob. This matches the MatCap pass's documented purpose (highlight continuity, missing
bevels) rather than relying on mesh validity alone, which is exactly the class of defect the desk-lamp
feedback identified as invisible to technical checks.

## Independent verification

`tools/verify_watering_can_secondary_bevel_corrective.py` is a separate script from the generator: it
opens only the saved corrected file (never imports the generator), and confirms both objects pass the
audit and are evaluated-clean, that `Connected_Vessel`'s pre-existing bevel weighting is undisturbed,
and — by SHA-256 hash comparison — that the original published production file on disk is byte-for-
byte unmodified. All 6 checks pass.

## What this does not establish

- `Opening_Rim`, `Opening_Shadow`, `Rose_Head` are still untreated and were not addressed here.
- The overall silhouette/UV/GLB/Godot production gates for this asset were not rerun; the bevel
  widths are small enough that a meaningful silhouette regression is very unlikely, but this was not
  independently measured in this run.
- This corrected file is a new artifact alongside the original; the original published production
  file and its downstream GLB/Godot evidence are unchanged and still represent the previously merged
  benchmark. Whether this corrected file should replace the published production reference is a
  follow-on decision, not made here.
