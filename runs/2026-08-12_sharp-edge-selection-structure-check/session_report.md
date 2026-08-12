# Structural verification: discrete-ring vs. continuous-drift edge selection

## Purpose

Follow-up to the rounded-parts bevel revert. That correction was found by direct human visual
review; this pass builds a reusable structural check
(`tools/verify_sharp_edge_selection_structure.py`) from the same live-artist-scene evidence
(`smooth_by_angle.md`'s "What correct selection actually looks like" section) and applies it to the
two corrections that were left as visually-plausible-but-unverified: the telephone's flat trim and
the watering can's `Opening_Rim`/`Opening_Shadow`.

## Method

For each weighted-bevel object, group its weighted edges' dihedral angles into integer-degree
buckets. A real stepped seam (a pressed lip, a panel edge, a rivet base) produces a small number of
distinct buckets because the same physical transition repeats at the same angle all the way around.
A continuously tapering design line (the sword's facet edge, a lathed body's shoulder profile)
produces many buckets because the angle genuinely changes along the line -- but so does an
indiscriminately over-selected round part, which is the actual failure this session found and
reverted. Bucket count alone cannot tell those two apart; it can only flag which objects need a
closer look.

## Result

| Object | Weighted edges | Distinct angle buckets | Classification |
| --- | ---: | ---: | --- |
| `Opening_Rim` | 64 | 1 (90 deg) | discrete ring |
| `Opening_Shadow` | 32 | 1 (90 deg) | discrete ring |
| `Clock_Face` | 32 | 1 (90 deg) | discrete ring |
| `Lower_Panel_Trim` | 24 | 1 (90 deg) | discrete ring |
| `Upper_Face_Trim` | 24 | 1 (90 deg) | discrete ring |
| `Dial_Aperture` | 36 | 2 (30, 90 deg) | discrete ring |
| `Connected_Vessel` | 192 | 10 | flagged, see below |
| `Main_Housing` | 100 | 13 | flagged, see below |

The six previously-unverified objects (`Opening_Rim`, `Opening_Shadow`, `Clock_Face`,
`Lower_Panel_Trim`, `Upper_Face_Trim`, `Dial_Aperture`) all produced exactly one or two discrete
angle buckets -- the same signature as the mechanical plate in the live-scene evidence, not the
sword or the reverted round parts. This closes the "left as an open question" status
`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md` previously gave `Opening_Rim`/`Opening_Shadow`: they are
now confirmed correct by structure, not merely visually plausible.

`Connected_Vessel` and `Main_Housing` were included as controls -- they are this project's original,
deliberately hand-refined `WEIGHT`-bevel examples (not this session's automated corrections) and were
already known-good. Both trip the tool's `CONTINUOUS_DRIFT_PATTERN` flag anyway, because a lathed
body's shoulder-to-neck profile is a legitimate continuous design line with a genuinely wide angle
spread, structurally indistinguishable from bad blanket selection by bucket count alone. This is
recorded as a known limitation in the tool itself: a `CONTINUOUS_DRIFT_PATTERN` result means "check
this against the reference," never "this is wrong."

## What this does not establish

This is a structural consistency check, not a reference-comparison tool. It cannot by itself confirm
an object matches its source photo -- only that its weighted edges follow one of the two patterns
seen in real (good and bad) examples this session. The rounded-parts mistake was caught by looking
at the actual reference image, not by any geometric property of the mesh; this tool is a faster
first-pass triage for future corrections, not a replacement for that comparison.
