# Telephone trim bevel corrective

## Trigger

`runs/2026-08-12_shading-policy-retroactive-audit/no_bevel_triage.json` identified 17 telephone
objects with no Bevel modifier; the handset correction addressed the one primary structural
component (`Handset`). This closes the remaining 15: `Clock_Face`, `Lower_Panel_Trim`,
`Upper_Face_Trim`, and 12 `Dial_Aperture*` objects, all with real sharp edges and zero treatment.

## Builds on the handset correction, not the original file

This run's `SOURCE` is `runs/2026-08-12_telephone-handset-bevel-corrective/heldout_vintage_telephone_production_corrected.blend`,
not the original published production file, so the output cumulatively carries both fixes. The
original published file and the handset-corrected file are both left untouched (confirmed by
SHA-256 in the independent verifier).

## A real topology defect, not just missing bevels

`Clock_Face` and 10 `Dial_Aperture*` objects applied cleanly on the first attempt. Two objects --
`Lower_Panel_Trim` and `Upper_Face_Trim` -- initially failed at every candidate width with an
identical 64 non-manifold edges regardless of width, which is the signature of a topology defect,
not a width problem (this repo's own connected-camera corrective session report documents the same
pattern). Both panels report 0 non-manifold edges at the *base* mesh level, but 16 of their 32
two-face edges have inconsistent face winding -- topologically closed, but not normal-consistent,
which Bevel's algorithm cannot handle regardless of width.

`tools/run_telephone_trim_bevel_corrective.py` now checks winding consistency before weighting any
object's edges and applies Blender's "Recalculate Outside" equivalent
(`bpy.ops.mesh.normals_make_consistent(inside=False)`) when needed. Both panels' inconsistent-edge
count dropped from 16 to 0 after repair, and both then applied cleanly on their first candidate
width. This is a disclosed geometry repair, not a threshold change -- the sharp-edge selection and
candidate widths were unchanged; only the winding was fixed.

## Result

All 15 objects reach `get_hard_surface_shading_audit` `PASS` and are evaluated-clean.

| Object | Sharp edges | Width | Winding repair |
| --- | ---: | ---: | --- |
| `Clock_Face` | 32 | 0.010 | none needed |
| `Lower_Panel_Trim` | 24 | 0.010 | 16 -> 0 inconsistent edges |
| `Upper_Face_Trim` | 24 | 0.015 | 16 -> 0 inconsistent edges |
| `Dial_Aperture` (x12) | 36 each | 0.006 | none needed |

`Main_Housing`'s and `Handset`'s existing corrections are confirmed undisturbed.

## Visual review

A whole-scene render makes these parts too small to judge; `clock_face_rim_profile_before.png`/
`_after.png` isolate `Clock_Face` in an edge-on side view. Before: a flat, blocky rectangular
cross-section with hard 90-degree corners. After: a rounded bevel profile with a clean highlight
streak -- the same class of real, visible improvement as every prior correction in this series.

## Independent verification

`tools/verify_telephone_trim_bevel_corrective.py` is a separate script from the generator. It
confirms all 15 objects pass and are evaluated-clean, `Main_Housing` and `Handset` are undisturbed,
and both the handset-corrected source and the original published file are byte-for-byte unmodified
(SHA-256). All 34 checks pass.

## Status

This closes the last item from the no-Bevel triage's remaining-work list for the telephone. Combined
with the earlier watering-can and boombox corrections, every object identified as a real
untreated-sharp-edge gap by the triage now has one (except the telephone's own genuinely flat badge,
which the triage correctly never flagged).
