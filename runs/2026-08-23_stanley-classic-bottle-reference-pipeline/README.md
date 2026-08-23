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

**Blocked on Blender**: the typed modeler server (port 9878) is not currently running — it needs
`tools/start_modeler_in_blender.py`'s contents re-run from Blender's Text Editor (it does not
auto-start with Blender). Sparse blockout is the next step once that's back.
