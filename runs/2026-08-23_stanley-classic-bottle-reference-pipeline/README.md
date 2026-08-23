# Stanley Classic Legendary Bottle (1.0 QT, Hammertone Green) — reference-analysis phase

First real prop run under the strengthened `REFERENCE_ANALYSIS` gate landed in
[`1d9d071`](../..). Target chosen deliberately fresh: not attempted anywhere in this repo's
history (checked `runs/` first), neutral/manufactured, and structurally rich enough to actually
exercise the pipeline: 4 components, a real negative space (the pour opening under the cap), a
real depth/nesting relationship (how far the cap telescopes over the body), a genuinely ambiguous
construction question (see below), a curved/profile-sensitive surface (the cap's rolled rim), and
two independent reference views (a product photo and the official spec sheet).

This run covers steps 1-9 of the required protocol -- reference gathering through freezing the
construction contract. Step 10 (`PRIMARY_BLOCKOUT`) is next but requires the Blender typed modeler
server, which is not currently running (see Status at the bottom).

## Reference gathering (steps 1-3)

Two independent sources, both real, both fetched directly (not assumed):

- **`official_front_photo`** — a real product photograph, downloaded directly from Stanley's own
  CDN (`stanley1913.com/cdn/shop/files/B2B_Web_PNG-The-Legendary-Classic-Bottle-1QT-...-Front...png`,
  retained here as `reference_front_stanley1913.png`, 1500x1500). Not a screenshot -- the in-app
  browser's screenshot tool failed in this environment (a known limitation from earlier in this
  session), so the image was located via a DOM query for real `<img>` src URLs and downloaded
  directly via Python.
- **`official_spec_sheet`** — text from Stanley's own product page: overall dimensions
  `3.62 x 3.62 x 12.13 in`, capacity `1.0 quart`.

Every claim below is bound to a specific `component_id`
(`ReferenceItem.component_ids`/`PropertyClaim.component_id`, the new component-aware fields), not
left as global reference-set metadata -- `component_reference_coverage_pass: true`, all 4 declared
components covered.

**Measured, not eyeballed** (`measured_ratio_count: 5`): direct pixel measurement against the
photo (alpha-channel bounding-box scan, `total_height=30.8cm` from the spec used as the sole
cm/px scale anchor):
- Cap occupies the top ~20% of total height; cap diameter ≈ 0.795x body diameter (330px/415px at
  stable rows).
- A visually distinct dark-green band sits at frac ~0.21-0.26 of height, exactly at the
  cap/body diameter step (the gasket ring).
- Body silhouette width varies only ~2.6% (408-419px) across frac 0.30-0.95 of height.
- Width holds steady through the base band, then drops sharply only in the final ~2% of height
  (a rounded/filleted bottom edge, not a sharp corner).

**One conflict, recorded and resolved, not silently reconciled**: a height-anchored pixel
measurement of body diameter came out ~8.6cm, about 6% narrower than the official spec's 9.2cm.
Resolution: adopted the spec value for absolute scale (a single-axis pixel-to-cm conversion of a
cross-axis measurement is expected to carry several percent error), kept the photo's *internal*
ratios as-is (far less sensitive to this error than an absolute conversion). See
`reference_manifest.json`'s `conflicts` entry.

**Deliberately out of scope**: the internal twist-and-pour stopper. Only a low-confidence
secondary-source dimension listing was found (a replacement-parts page, not this SKU's own spec,
and no photo). It is not externally visible when assembled and isn't needed to review the sparse
blockout's silhouette/proportions, so it was **not** declared as a component in this pass rather
than forcing a low-confidence claim through the same authoritative-evidence bar as everything
actually being built now (`knowledge_engine.reference_analysis.audit_reference_set` correctly
refuses to call a reference set "ready" while it contains any claim below `MEDIUM` confidence --
tried including the stopper claim first, watched it fail the gate for exactly this reason, and
scoped it out rather than inflating its confidence to make the number look better). It gets added
back with real reference once a later detail pass actually needs its geometry.

## Component graph (step 6 groundwork)

`body`, `base_ring`, `cap_cup`, `gasket_ring`, related by `attaches_to`/`seals`
(`component_graph.json`). Validated structurally clean (`validate_component_graph`, no
duplicate/missing/dangling references).

## The real catch: competing hypotheses on the body profile (steps 5, 7, 8)

This is the actual proof-of-value moment, not a synthetic demo. Looking at the photo, the visible
shoulder/foot steps could plausibly be read as the ends of a **barrel/waisted curve** -- a
reasonable first impression. Recorded as a genuine competing hypothesis specifically so it could be
tested rather than assumed:

| Hypothesis | Predicted body-width variation (front photo) | Predicted: does one diameter value describe the body (spec sheet)? |
| --- | --- | --- |
| `straight_cylinder` | 0.95-1.0 (near-constant) | true |
| `barrel_taper` | 0.80-0.93 (visibly tapered) | false |

Real independent observations: measured width ratio `[0.965, 0.98]`; the spec sheet lists exactly
one diameter pair, no separate widest-point callout (`true`).

**Result**: `straight_cylinder` — CONFIRMED on both views (0 contradictions), selected.
`barrel_taper` — CONTRADICTED on both views, rejected. The initial visual impression from the
photo alone would have been wrong; the pixel measurement caught it before any geometry was built.
This is exactly the class of mistake (`REPRESENTATION_FAILURE`, per `docs/FAILURE_TAXONOMY.md`)
the strengthened gate exists to catch upstream of downstream proportion patching.

Full ranking detail in `visual_reconstruction_audit.json`; `contradiction_count: 2` confirms the
hypotheses were actually discriminating, not decorative.

## Construction contract (step 9 — frozen)

| Component | Structure type | Construction family | Basis |
| --- | --- | --- | --- |
| `body` | `revolved_body` | `profile_revolution` | Selected by evidence above (near-constant radius) |
| `base_ring` | `revolved_body` | `profile_revolution` | Rounded bottom edge inferred from the sharp late-height width drop |
| `cap_cup` | `revolved_body` | `profile_revolution` | Slight flare at the very top (rolled cup rim) |
| `gasket_ring` | `wrapped_band` | `profile_revolution` | Distinct color band exactly at the measured diameter step |

Every component — contested or not — carries a structurally-checked, non-empty justification
(`knowledge_engine.visual_reconstruction`'s new uncontested-region path); this was verified to
actually reject an unjustified region during development of the mechanism itself (see
`tests/test_visual_reconstruction.py`).

## Gate result

```
component_graph pass:              True
reference_set_audit pass:          True   (disposition: READY_TO_MODEL)
component_reference_coverage pass: True   (0 uncovered components)
visual_reconstruction pass:        True   (contradiction_count: 2)
REFERENCE_ANALYSIS gate pass:      True
```

All raw results retained: `reference_manifest.json`, `reference_audit.json`,
`component_graph.json`, `component_reference_coverage.json`, `visual_reconstruction.json`,
`visual_reconstruction_audit.json`, `reference_stage_gate_evidence.json`,
`reference_stage_gate_result.json`. Generated by a one-off script that calls the real project
functions directly (`audit_reference_set`, `validate_component_reference_coverage`,
`audit_visual_reconstruction`, `evaluate_stage_gate`), not hand-typed JSON asserted to be correct.

## Status: REFERENCE_ANALYSIS PASSED / PRIMARY_BLOCKOUT NOT STARTED

Per the explicit instruction this run follows: "Do not treat 'gate passed' as proof the
interpretation is correct." The gate passing proves the reasoning chain is structurally complete
and internally consistent, not that reality matches it — that only gets tested once geometry
exists and gets rendered against these same references (step 10 onward).

**Update**: the typed modeler server was restarted (via `blender_ops.modeler_server.start()` run
through the generic connector, so no manual Text Editor step was needed this time) and the sparse
blockout below is complete.

## Sparse blockout (step 10)

Built directly from the frozen construction contract above — every ring's radius/height comes
from the measured fractions and ratios recorded during reference analysis, not re-eyeballed at
build time. All four components use `create_quad_radial_surface` (matching their shared
`profile_revolution` construction family), authored along world Z with no reorientation needed.

One real refinement made *during* construction, not before: the cap's justification in the frozen
contract undersold its shape ("near-cylindrical with a slight rim flare"). Building it required a
finer 6-point pixel scan of the cap region, which showed a **clear, monotonic taper across the
whole cap height** (radius ratio 0.643 at the very top rising steadily to 0.807 near the gasket) —
a real frustum, not a cylinder with a flourish. Caught and corrected before modeling, using the
same measure-first discipline, not after.

| Component | Object (original) | Object (after correction, see below) | Rings | Segments |
| --- | --- | --- | --- | --- |
| `base_ring` | `BaseRing` | `Vessel` | 6 (rounded-edge taper, finely sampled: frac 0.90-1.00 in 8 real pixel readings) | 16 |
| `body` | `Body` | `Vessel` | 3 (constant radius, per the confirmed straight-cylinder hypothesis) | 16 |
| `gasket_ring` | `GasketRing` | `Vessel` | 2 (linear taper bridging body radius to cap radius) | 16 |
| `cap_cup` | `CapCup` | `CapCup` (unchanged) | 7 (monotonic taper, 6 real measured points + gasket-matching base) | 16 |

`base_ring`/`body`/`gasket_ring` were originally built as 3 separate objects, then merged into one
`Vessel` object per direct human review — see the correction record below before trusting the
"Object" column above as final.

### Verification against the reference (not self-declared)

Re-measured the actual built geometry's rendered silhouette (`blockout_component_mask_front.png`)
the same way the reference photo was measured, to check for scale/construction errors rather than
trusting the authored numbers went in correctly:

| Boundary | Intended (from reference analysis) | Measured in the built render |
| --- | --- | --- |
| Cap top | frac 0.000 | frac 0.000 |
| Cap/gasket | frac 0.211 | frac 0.211 |
| Gasket/body | frac ~0.256 | frac 0.256 |
| Body/base | frac ~0.921 | frac 0.921 |

Exact match. The `side` view's `foreground_fill_ratio` (0.180016) is bit-identical to `front`'s,
confirming genuine radial symmetry — a real structural sanity check, not just visual similarity.

Renders (all in this directory, original 4-object version): `blockout_silhouette_front.png`,
`blockout_shaded_front.png`, `blockout_shaded_side.png`, `blockout_shaded_isometric.png`,
`blockout_component_mask_front.png`, `blockout_wireframe_front.png`. Post-correction 2-object
renders: `blockout_v2_shaded_front.png`, `blockout_v2_shaded_isometric.png` (see the correction
record below). The isometric view also confirms the negative space requirement
was satisfied without extra work: `create_quad_radial_surface` produces an open cage by
construction, so the cap's open top ring *is* the bottle's real drinking opening — visibly hollow
in the isometric render, not a solid capped cylinder.

## Correction: too many separate objects (human review)

**Symptom**: direct user feedback on the blockout renders — "i dont think so much seperation is
needed." Four separate mesh objects (`BaseRing`, `Body`, `GasketRing`, `CapCup`) for what reads,
correctly, as an over-fragmented blockout.

**Root cause**: `REPRESENTATION_FAILURE` (per `docs/FAILURE_TAXONOMY.md`) — not a proportion or
execution defect (the shape and measurements were already correct), but the wrong *object-level*
modeling representation. The reference-analysis phase correctly identified 4 semantically distinct
components by material/color (that stays true and isn't being retracted), but a sparse blockout
doesn't need every material/color boundary to be a separate mesh object — `base_ring` and
`gasket_ring` are color/material distinctions within what is physically one continuous vacuum-flask
shell, not independently removable parts. `cap_cup` is different in kind: it's a genuinely
separate, removable component (you unscrew/lift it off to drink), the one real functional boundary
in this object, matching this project's own established convention (separate objects for
genuinely separate/removable real-world parts, not for every material change).

**Evidence**: the human reviewer's direct instruction is first-class evidence per
`docs/HUMAN_VISUAL_REVIEW_PROTOCOL.md` and overrides the passing automated gate/render state,
which never claimed to certify construction strategy in the first place.

**Rejected repair ideas**:
- *Merge everything into one single object, including the cap* — rejected: the cap is a genuinely
  separate, removable part, unlike the base/gasket boundaries, which are purely material
  distinctions on one continuous shell. Collapsing that real functional boundary would trade one
  representation mistake for another.
- *Leave the 4 objects and only note the feedback* — rejected: direct human visual-review
  authority is meant to change the model, not just get filed as a comment.

**Selected correction**: archived `BaseRing`, `Body`, `GasketRing` (moved to `REJECTED_COMPONENTS`,
recoverable, not deleted — 3 separate single-operation decision transactions, each verified: the
new `geometry_shift_flag` mechanism from this session's own execution-safety prelude correctly
reported no implausible shift on any of the three archive-only transactions). Rebuilt as one
connected `Vessel` object spanning all 9 combined rings (the exact same authored radii/heights,
concatenated and deduplicated at the shared boundaries) via a single `create_quad_radial_surface`
call. `CapCup` unchanged.

**Before/after render**: `blockout_shaded_front.png`/`blockout_component_mask_front.png` (before,
4 objects) vs. `blockout_v2_shaded_front.png`/`blockout_v2_shaded_isometric.png` (after, 2
objects). `foreground_fill_ratio` is bit-identical before and after on both front (0.180016) and
isometric (0.160701) framing — confirms the correction changed only the object/topology
representation, not the silhouette or proportions that were already verified correct.

## Status: PRIMARY_BLOCKOUT built, NOT self-certified as correct

Per the explicit instruction this run follows: a passed gate and a matching render are not the
same claim as "the interpretation is correct" — this blockout matches the *reference photo and
measurements gathered in this pass*, which is the honest limit of what's been checked. It has not
been reviewed by the user, has no material/lighting pass, no bevels, and the internal stopper
remains out of scope (see above). Stopping here for review rather than advancing to secondary
detail, per the protocol this run is following.

