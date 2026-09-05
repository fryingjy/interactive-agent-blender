# Bootstrap B0: frozen baseline, 2026-09-05

Status: **PARTIAL**. This records failures at the reference stages and one
annotation-assisted exterior-envelope fitting diagnostic. It is not four completed
models, a passed apprenticeship track, or B4 authorization.

The [freeze manifest](../knowledge/foundation/bootstrap_baseline_manifest.json) binds
the current curriculum and baseline commit `ec9ddcf`. The
[measured results](../knowledge/foundation/bootstrap_baseline_results.json) retain
per-image outcomes and all eight review channels. Missing model evidence is
`NOT_EVALUATED`, not a favorable score. No production runtime or solver was changed.

## What was actually run

The unchanged image extractor processed ten downloaded manufacturer images; seven
were accepted by its extraction checks and received unchanged appearance-region
proposals. Those seven acceptances do **not** establish seven valid semantic masks.

| Task | Observed baseline failure | Next evidence needed |
| --- | --- | --- |
| OLFA 180Black, profile | Two appearance regions do not identify channel, blade, slider and clip. Disassembly illustration includes an arrow and a different pose. | Component labels and a justified depth view |
| Hammond 1590A, housing | Assembled photo produces 247 image holes and thousands of appearance fragments. | Review physical boundaries separately from metal texture; use section views for cavity depth |
| GN 526, radial | Family photo produces 46 image holes; underside and exact-size identity remain unresolved. | Exact-variant drawing and bore/underside evidence |
| MAUL 2132590, assembly | Two appearance regions merge the two wire handles; alternate image changes articulation. Another image visually repeats the first view. | Per-component pose/correspondence and reviewed wire-loop negative spaces |

These are agent observations, not independent review or verified geometric hole counts.
The existing proposal API already labels appearance regions non-semantic. The failure
would be treating that proposal as physical construction evidence. Likewise, blindly
filling every hole would destroy genuine handle-loop negative spaces.

Sources: [OLFA](https://www.olfa.co.jp/en/products/493.html),
[Hammond](https://www.hammfg.com/part/1590A),
[Ganter](https://www.ganternorm.com/en/products/1.4-Adjusting-positioning-locking-with-and-without-position-indication/Control-knobs/GN-526-Control-Knobs-Plastic-Bushing-Steel),
[MAUL](https://www.maul.de/en/foldback-clips-213-in-white-cardboard-box-2132590).
The source manifest records exact download URLs and hashes. References remain local;
this change does not bulk-publish third-party media.

## Isolating fitting from photograph extraction

A separate diagnostic uses the top and end-section views in the
[1590A drawing](https://www.hammfg.com/pdf/1590A.pdf). The agent annotated two 2D
regions, their shared scale and axes. The existing reference audit, registration,
bundle, mask initializer and family fitter then ran without geometry coordinates
being authored or CAD/source meshes being imported.

This diagnostic intentionally measures **only the assembled exterior envelope**.
It does not replace the full housing baseline. Internal section lines are excluded
from envelope masks, and small dimension-line remnants remain at the bounds; these
are not independently reviewed ground-truth masks.

| Candidate | Front IoU | End IoU | Mean view loss |
| --- | ---: | ---: | ---: |
| Section loft | 0.99425 | 0.97475 | 0.01577 |
| Profile extrusion | 0.99049 | 0.99032 | 0.00977 |

Both pass the existing silhouette-compatibility limits, but their loss margin is
**0.00600**, below the unchanged **0.02** family-selection margin. Selection therefore
returns `AMBIGUOUS_OR_INCOMPATIBLE`, with compilation unauthorized. No Blender
construction was forced through the gate.

Authored-face-only CPU images were also inspected: the profile extrusion lacks its
end faces despite the high intended-volume score. The drawing and opened-product
photo show a cavity and separate lid; neither an exterior solid nor open proxy side
walls establish that construction. This is useful negative evidence, not a new
professional model or a Blender-render comparison.

## Replay

These files are manual experiment support, not a second production CLI or a new
shape solver. Run from the repository root at the pinned baseline implementation
(or explicitly label a later-code replay as an intervention):

```powershell
python tests/fixtures/bootstrap_baseline/replay_photos.py
python -m pip install pypdfium2==5.13.0
python tests/fixtures/bootstrap_baseline/replay_envelope.py
```

The photo replay downloads only missing source files and refuses changed hashes.
The envelope replay renders the frozen PDF, repeats the recorded annotations and
calls the retained implementation. Existing project Python dependencies are also
required. A changed upstream reference requires a new experiment record, not
silent replacement of the baseline.

Outputs live under `work/bootstrap-baseline-lab/`: source bytes, masks, component
previews, annotation contract, actual audit/registration/bundle records, initialized
candidates, family scores, and intended-volume/authored-face diagnostic images.

Verification: both committed replay scripts were executed; the repeated envelope
run reproduced both losses exactly. The full suite passed **413 tests and 30
subtests**, including the opt-in fresh Blender 5.2.1 regression. The curriculum
validator, repository audit and architecture audit passed. That Blender regression
checks retained runtime behavior; it is not a Blender execution of these four
reference tasks.

## Continuation

Keep the raw outcomes immutable. Complete the reference-to-form intervention using
reviewed component masks, pose-aware correspondence, landmarks and actual depth
evidence, then rerun under a distinct intervention record. Compare the first stage
that changes, not just final IoU. Full reference-to-Blender baselines and all eight
surface/editability/repair channels remain outstanding. Do not skip to a held-out
prop or promote the earlier crease fixtures to fill those missing channels.
