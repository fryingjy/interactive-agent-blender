# Production high/low readiness audit

**Status:** PASS

This run adds a fail-closed distinction between an editable equal-cage duplicate and a technically
production-ready low topology. The Blender source contains purpose-authored rounded-rectangular and
radial pairs. Their high and low objects live in separate `HIGH_POLY` and `LOW_POLY` collections,
use independent mesh datablocks, and retain live `Manual Bevel - Unapplied` modifiers. The build
script never calls `modifier_apply`, the GLB export uses `export_apply=False`, and the source file is
left for the user to apply modifiers manually.

| Family | High base faces | Low base faces | Ratio | Front IoU | Side IoU | Top IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rounded box | 22 | 6 | 0.2727 | 0.9968 | 1.0000 | 1.0000 |
| Radial flare | 864 | 72 | 0.0833 | 0.9907 | 0.9907 | 0.9592 |

Both lows have one connected component, a valid unit-tile UV layer with zero degenerate UV faces,
and a packed Non-Color tangent-normal bake connected through a Normal Map node. Independent GLB
imports each contain one mesh, UVs, one material, and that export's own normal image.

## Rejected attempt and correction

The first 12-sided radial low cage used four axial rings. It passed front/side impressions but lost
the high source's maximum-width middle profile; top-view silhouette IoU fell to **0.8247**, below the
frozen 0.90 gate. Adding one purposeful center ring raised top IoU to **0.9592**. This is localized
topology added where the form changes, not blanket density.

## Fail-closed controls

- Equal base cage in separate collections: `EDITABLE_VARIANT_ONLY`, not retopology.
- One-view-only silhouette evidence: rejected.
- Missing low UV: rejected.
- Missing live low modifier: rejected.
- Disconnected joined low shells: rejected.

The fresh source verifier passes all 13 checks, including the no-apply policy. The fresh export
verifier passes all six checks. The claim remains bounded: this validates the audit and two
controlled authored pairs, not autonomous retopology of an unfamiliar real prop or expert-accepted
production quality.
