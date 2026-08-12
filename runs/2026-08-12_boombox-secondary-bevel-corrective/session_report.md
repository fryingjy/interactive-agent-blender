# Boombox secondary-part bevel corrective

## Trigger

`runs/2026-08-12_shading-policy-retroactive-audit/no_bevel_triage.json` found 11 boombox objects
with real sharp edges (58.5-139.4 degree max dihedral) and zero bevel treatment: four cassette
reels, four fascia fasteners, two speaker cones, and the telescoping antenna. Unlike the boombox's
30 other secondary parts, none of these 11 had any `ANGLE`- or `VGROUP`-limited Bevel either -- no
modifiers of any kind.

## Method

`tools/run_boombox_secondary_bevel_corrective.py` applies the same policy used for the watering-can
and telephone corrections to all 11 objects in one pass. Unlike those two, none of the 11 carry any
existing modifier, so there is no stack-order concern -- the new Bevel is simply appended.

1. Opens the published production file directly; never saves over it.
2. Computes sharp edges (25-degree dihedral threshold) per object, mapped to persistent edge IDs.
3. Assigns `bevel_weight_edge = 1.0` and records `hard_surface_intended_bevel_edge_ids`.
4. Adds a `WEIGHT`-limited Bevel with a per-object candidate width list sized from each object's own
   dimensions (cassette reels and fasteners are a few centimeters across; speaker cones and the
   antenna have their own separate scale), evaluating the full stack after each candidate.
   **All 11 objects passed cleanly on their first, most generous candidate width** -- no narrowing
   was needed for any of them.
5. Applies `set_smooth_by_angle` to each.
6. Saves as a new file, reopens that saved file, and audits/verifies against what is actually on
   disk.
7. Renders MatCap before/after comparisons, plus a dedicated edge-on side view of `Speaker cone L`'s
   rim, since a whole-scene render makes these small parts nearly invisible.

## Result

| Object | Sharp edges | Accepted width | Audit |
| --- | ---: | ---: | --- |
| `Cassette reel` (x4) | 48 each | 0.008 | `PASS` |
| `Fascia fastener` (x4) | 32 each | 0.005 | `PASS` |
| `Speaker cone L`/`R` | 128 each | 0.015 | `PASS` |
| `Telescoping antenna` | 32 | 0.006 | `PASS` |

All 11 evaluated meshes are 0 non-manifold edges, 0 degenerate faces.

## Visual review

A whole-scene MatCap render makes these parts too small to judge (see `matcap_*_isometric.png`), so
`speaker_cone_rim_profile_before.png`/`_after.png` isolate `Speaker cone L` in an edge-on side view.
The difference is clear and real: before, the rim reads as a blocky, faceted, stepped edge; after,
it is a continuous curved bevel profile with one clean highlight streak -- the same class of
improvement the desk-lamp feedback identified, not visible from mesh validity alone.

## Independent verification

`tools/verify_boombox_secondary_bevel_corrective.py` is a separate script from the generator. It
confirms: all 11 objects pass the audit and are evaluated-clean, the object roster (including the
three pre-existing `ReviewLight` objects, unrelated to this correction) is unchanged, and the
original production file is byte-for-byte unmodified (SHA-256). All 23 checks pass.

## What this does not establish

- The 30 boombox objects using `ANGLE`/`VGROUP`-limited Bevel are untouched by this run; whether
  that method should become a second fully-sanctioned audit path is a separate open decision.
- Overall silhouette/UV/GLB production gates for this asset were not rerun.
- This corrected file is a new artifact alongside the original; whether it should replace the
  published production reference is a follow-on decision, not made here.

## Status of the three primary-body/structural corrections

With this run, all three objects the no-Bevel triage identified as primary structural components
with real untreated sharp edges are now fixed: watering-can spout/handle, telephone handset, and (as
detail parts rather than a single primary body) the boombox's 11 untreated components. The remaining
open items are the telephone's dial apertures/trim and the ANGLE/VGROUP sanctioned-path decision.
