# Current-state to professional-modeler gap matrix

Updated: 2026-08-19 after an independent audit that WITHDREW two of the three previously recorded RUNTIME_VALIDATED claims as circular (see `runs/2026-08-19_observation-to-skill-gap-audit/README.md`). Read that audit before trusting any runtime-validation language below. **Every named-product model-build attempt referenced in the table below as
of 2026-08-16 (Swingline, Scotch C38, Panasonic RF-2400D, and others from the same period) was
deliberately deleted 2026-08-17** on direct instruction, having been judged not good enough to
keep as modeling evidence; their historical retention is classified in
`knowledge/foundation/source_retention_ledger.json` (`HISTORICAL_ARTIFACT_REMOVED_FROM_GIT_HISTORY`).
Rows below that cited those runs as evidence have been corrected to say so plainly rather than
leave dangling references to artifacts that no longer exist. The active track since then has been
converting captured video-study knowledge into fully validated, retrieval-integrated, planner-
usable runtime skills (`review -> reproduce -> transfer -> visual+technical verify -> retrieval ->
planner use -> runtime validation`), not more model builds. This matrix distinguishes demonstrated
evidence from capability still lacking proof.

## 2026-08-17/18 additions (the current real state)

- **`bevel.segments.parity_avoids_corner_triangle`** (`knowledge/skills/bevel-segments-parity-corner-triangle.json`):
  `RUNTIME_VALIDATED` -- and, after the 2026-08-19 audit, the ONLY skill for which that status is
  earned: it is the one skill whose planner trigger a real observer can emit. Reproduced the
  source's triangle-vs-parity claim exactly; transfer-tested on
  full-object vs. partial-corner bevels and found the source's stronger "even segments = all-quad"
  claim was false in general (conditional on beveling every edge at a vertex together). Retrieval
  ranks it first for matching queries and abstains correctly on unrelated ones; a planner-driven
  typed transaction on a synthetic ticket committed cleanly. **Not yet proven on a real unfamiliar
  reference**, only a synthetic bracket-corner fixture.
- **`extrude.inset_first.local_containment`** (`knowledge/skills/inset-before-extrude-containment.json`):
  `TRANSFER_VALIDATED` -- runtime status WITHDRAWN 2026-08-19 as circular (the runtime test
  hand-authored a ticket copied from this skill's own trigger list). The transfer evidence below
  is real and unaffected. Reproduced on a fine flat grid and found the source's "even on an
  already-subdivided plane" claim did *not* hold there (direct and inset were near-identical);
  transfer-tested on a coarser curved surface where a real, visually-confirmed difference appeared.
  Found that raw dihedral angle and pole count both pointed the wrong way or didn't discriminate at
  all -- only a shaded render caught the real defect (an uncontained, drooping feature vs. a
  contained one). Same retrieval/planner/typed-transaction integration as above, same limit: not
  yet proven on a real unfamiliar reference.
- **Curved-surface join via Shrinkwrap+Bridge (reproduced from McGlasham's "Connecting Cylinders"
  video): attempted, found a genuine seam-fold defect, cross-validated it two independent ways
  (a from-scratch dihedral-angle sweep and this project's own live `get_evaluated_defect_regions`
  tool), tried and rejected one fix hypothesis with real evidence, and was then scrapped outright**
  on direct instruction rather than left as a claimed success. This is recorded as a real, useful
  negative result, not hidden.
- **Attached-curved-form construction, grown directly from the body mesh** (not reproduced from a
  video -- re-examined and transferred from this project's own earlier live-built mug handle,
  `runs/2026-08-14_shrinkwrap-vs-join-handle-correction/`): a fresh live transfer test
  (`runs/2026-08-17_live-spout-transfer-test/`) grew a spout from a cylindrical body via
  inset-then-extrude, with zero non-manifold edges at every step and no defect flagged in the
  region the naive Shrinkwrap+Bridge reproduction had failed on. This is now the project's
  strongest evidence for attached-component construction, stronger than the scrapped tutorial
  reproduction it replaced.

## 2026-08-20 additions

A magnifying-glass build (`runs/2026-08-18_magnifying-glass-reference/`,
`runs/2026-08-19_magnifying-glass-build/`) was purged the same day for repeated overclaiming
(declaring a neck/ring junction "fixed" from flat-grey renders and non-manifold counts alone while
it was still visibly broken). Two trust-rebuild exercises followed, both **technique-proof builds
using authored/known forms, not reference-driven builds** -- they do not touch the reference-
interpretation gap this table has called the single highest-value open item since 2026-08-16:

- **Mallet** (`runs/2026-08-20_mallet-build/`): single continuous revolved profile, 928 faces,
  all-quad, 0 non-manifold. Deliberately avoided any join, sidestepping the exact failure class that
  broke the magnifying glass.
- **Mug-handle-join** (`runs/2026-08-20_mug-handle-join/`): the actual join re-test the mallet
  avoided. An authored bridge between two boundary loops on the body mesh, weld-by-construction
  (canonicalized matched vertex order, no `bridge_loops`/merge-by-distance), 584 faces, all-quad.
  Found and fixed a real cross-section-shear bug (rigid centroid-offset sweep instead of per-vertex
  independent lerp) only visible under material lighting, not flat shading.

Both are the **first builds in this project's history to receive and pass an actual human-authored
visual review record** (`REVIEW_ACCEPTED_NO_REPAIR` via `tools/record_external_visual_review.py`)
rather than only self-assessment or a recorded rejection -- see
`knowledge/foundation/directive_coverage_matrix.json` requirement 4. This closes the "seek
independent visual review" mechanism gap; it does not close the reference-interpretation gap below,
which remains open and unstarted since the 2026-08-17 deletions.

## 2026-08-21 addition: the MasterLock 140D is now the real reference-driven candidate

Found and resumed `runs/2026-08-16_reference-gathering-masterlock-140d/` -- a padlock blockout
that reached stage 12 with a frozen reference contract and real `decision_revision` history,
then simply stopped (never purged, never rejected, untracked in this project's own curriculum
docs). Unlike the mallet and mug-handle-join, this genuinely is a reference-driven build: real
photos, an official dimensional spec, and an active measured comparison against both.

Since resuming: added two shackle sockets and a front corner chamfer, each confirmed against
the actual reference photo (a close crop settled whether the chamfer was a real facet or just a
highlight) rather than assumed; re-measured the silhouette/negative-space IoU against the
reference and found today's construction correctly left those numbers flat (chamfers and
sockets don't move an outer-silhouette measurement); investigated the one real localized gap
(negative-space IoU trailing silhouette IoU) and deliberately did NOT narrow the shackle to
close it, because the reference photo is labeled `PERSPECTIVE`/oblique in its own manifest and
the shackle spacing reproduces a verified 21mm clearance spec -- chasing the pixel metric would
have meant trading a verified measurement for a worse one. A structured human-review board
(`runs/2026-08-20_masterlock-140d-resume/review_board/review_board.html`) is now prepared but
not yet reviewed.

**Update, same day:** the review board reached a recorded human review --
`REVIEW_ACCEPTED_NO_REPAIR`, on the reviewer's own qualified terms ("its ok for the most part").
This is the first genuinely reference-driven build in this project's history to reach a recorded
human accept, closing the specific "get a human review recorded" step -- it does not establish
repeatability, and the open items above (wordmark, rear/underside, negative-space) remain exactly
as open as before acceptance.

| Capability needed for the ultimate goal | Current evidence | State | Highest-value proof still required |
| --- | --- | --- | --- |
| Evidence-bound reference interpretation | Typed decomposition plus question-driven unknown/search/candidate/constraint records, explicit reference-to-blockout contracts, strict stage rejection, and focused controls. The Swingline, Scotch C38, and Panasonic RF-2400D runs previously cited here were all deleted 2026-08-17 as not good enough to retain as modeling evidence (classified in the source retention ledger, not left dangling). The tooling itself (`knowledge_engine/reference_analysis.py`, `verify_reference_set_gate.py`, the reference-audit pipeline) is untouched and was reused directly to gather real AA-battery reference (authoritative Wikipedia/Wikidata dimensions plus a Wikimedia Commons photo) for the next real-reference attempt, still in progress. | The MasterLock 140D (runs/2026-08-20_masterlock-140d-resume/) reached its first recorded human review 2026-08-21: REVIEW_ACCEPTED_NO_REPAIR, on the reviewer's own qualified terms ("its ok for the most part") -- the first genuinely reference-driven build in this project's history to reach a recorded human accept, not just a technique exercise | Front wordmark/seam detail, rear/underside, and the negative-space gap remain open by design. Repeat the measured, reference-checked discipline on a new component or a second reference-driven asset -- one accepted build does not establish repeatability |
| Component/depth/continuity/separation reasoning | Typed categories plus a two-family Blender experiment where front-identical continuous/separate candidates are resolved by top-view depth, connected-component truth, and planner gating | Controlled synthetic transfer; real-image inference and real-prop use remain manual/unproven | Apply the policy to unrelated real multi-view references and obtain human review |
| Knowledge changes runtime behavior | Supported claims alter planner representation/component policy; weak/conflicting claims cannot silently harden. An evidence-ready decomposition requests a revision-bound live component capture before further blockout. | Demonstrated in declared policy cases and a controlled Blender planner→runtime→stage-gate loop | Runtime telemetry from actual Blender decisions and measured outcome improvement |
| Delayed knowledge retrieval | Four self-administered quizzes now span 2026-08-08 through 2026-08-16; quiz 004 contains 20 fresh applied scenarios after a five-day interval, with executable checks for count, answer depth, interval, and low textual similarity | Contextual five-day self-retrieval demonstrated; validator cannot certify correctness, independence, or professional use | Independent delayed assessment plus measured reuse on a fresh human-authorized asset |
| Knowledge provenance integrity | `tools/audit_source_registry.py` distinguishes artifact paths, non-path references, explicit removals, and a Git-history-backed retention ledger | **Incomplete but classified:** historical artifacts and intentionally non-retained source media are not presented as reproducible proof | Recover evidence only where authorized and useful, or keep claims bounded |
| Bridge Edge Loops twist control | Protocol 0.3, typed `twist_offset`, unequal-density rejection, rollback, and two-shape Blender evidence | Controlled transfer; real-asset use open | Apply to a real modeling case through the typed decision path |
| Connect Vertex Path / T-junction prevention | Typed two-endpoint `connect_vertex_path`, copy-first preflight, continuous three-face split, rollback controls, persistent IDs, planar and curved/SubD fresh-process verification | Controlled planar and nonplanar evidence; strict mode rejects a curved diagonal that would retain endpoint triangles, but does not choose a repair on a real prop | Apply on a human-authorized real prop and inspect the chosen path and highlights |
| Progressive benchmark discipline | User-supplied 30-prop ladder is encoded with six ordered tiers, A-G gates, evidence requirements, human override, and executable validation. Pre-model approval is optional; post-model human rejection still overrides automated checks. All prop-ladder candidates evaluated through 2026-08-16 (including the former prop-2 candidate) were deleted 2026-08-17. | Gate machinery is operational and unchanged; no ladder prop currently exists or has passed final human review | Restart the ladder from a fresh tier-1 (simple manufactured object) candidate, building only after the skill base gained real runtime-validated evidence rather than restarting the count from zero informally |
| Conditional Bevel/SubD order judgment | Matched-cage order experiment plus a typed crown/saddle transfer with explicit semantic rim declarations, live Bevel→SubD stacks, fixed-view MatCap differences, and fresh verification | Controlled flat and double-curvature transfer; real reference-driven order choice remains unproven | Use on an unfamiliar hard-surface asset with visual surface review |
| Scoped Shrinkwrap footprint transfer | Sphere/cylinder transfer, destructive unscoped control, and fresh verifier | Controlled second-shape transfer | Integrated runtime use on a real asset and evaluated-surface inspection |
| Narrated tutorial understanding | Local ingestion, structured Gemini extraction, native start/end range scoping, metadata discovery, held-out contamination filters, source-identity enforcement, and independent frame+speech review gate | Genuine loop-cut and UV episodes plus one public reference-setup episode are verified. The reference lesson also demonstrates why independent checking matters: its later whole-video timestamps drifted and were rejected, while the scoped 24–124 s pass aligned and transferred. TubeAlfred is not callable in the current environment and is not falsely credited. | Repeat bounded review/reproduction/transfer/runtime use on an authorized prop and integrate optional transcript metadata only when a real provider is available |
| Reference-profile correction | A rejected rotational model was rebuilt as one connected 12-sided all-quad shell with curvature-aware loop placement; fresh Blender verification passed | Corrective technical evidence; human form review still pending | Human comparison against same-object views and transfer to a non-rotational unfamiliar prop |
| Multi-view reference fidelity and error localization | Silhouette, landmark, component, negative-space metrics and mismatch tickets exist; typed Image Empty setup records and audits FRONT/RIGHT/TOP card normals and rejects duplicated imagery as distinct multi-view evidence. The C38 run that exercised this tooling was deleted 2026-08-17; the tooling itself is unchanged. | Machinery proven functional on deleted evidence; no current candidate exercises it | Apply to the next real-reference build and turn rendered-view mismatches into structured corrections |
| Adaptive professional Blender modeling | Typed operations, transactions, rollback, fingerprints, state probes, stages, and independent verifiers. Since 2026-08-16 the live connection was debugged and made reliable (root-caused a broken third-party bridge, bootstrapped this project's own server directly over a raw socket instead of working around it indefinitely), and two knowledge_engine.planner-routed typed transactions were proven end to end on synthetic tickets (bevel-segment-parity, inset-before-extrude-containment). Separately, a curved-surface-join reproduction was attempted, diagnosed with real evidence, and correctly scrapped rather than kept as a false success -- then a working alternative (grow the attached form from the body) was found by re-examining this project's own earlier live-built example, not by guessing again. | Infrastructure and self-correction are both demonstrated; artistic autonomy on a genuinely unfamiliar reference is still the open item | Complete an unfamiliar nontrivial prop from reference through repair and production prep without an object-specific builder |
| Recoverable curve-based form correction | Curves now use the same one-decision transaction boundary as mesh decisions: direct spline-state observation, control-point rollback on rejection or post-mutation failure, curve-aware external-edit fingerprints, and typed-server execution. The Blender 5.2 lab verifies both the direct and server paths. | Runtime safety demonstrated; reference-driven curve judgment remains unproven | Use it for a source-backed handle, shackle, cable, or trim only after multi-view evidence establishes that a curve is the right representation |
| Curved hard-surface and SubD judgment | Flat/radial normal-policy evidence plus connected all-quad positive-crown and saddle panels under live Bevel→SubD; MatCap review localizes bumps/broken highlights even on technically-clean meshes. Since 2026-08-16, two skills were transfer-tested with a real correction to their source's overreach in each case. The 2026-08-19 audit then WITHDREW the runtime claim on one of them as circular; only `bevel.segments.parity_avoids_corner_triangle` retains `RUNTIME_VALIDATED`, now on non-circular evidence (a real classifier emits its trigger, knowledge supplies the segment parameter, and the loop rolls back rather than committing a defect). Testing that loop also falsified a recovery claim already sitting in the knowledge base. A Shrinkwrap+Bridge curved-join reproduction was attempted, diagnosed, and correctly scrapped; a body-grown attached-form alternative was proven instead with zero non-manifold edges. | One skill genuinely `RUNTIME_VALIDATED` on observation-driven evidence; a second demoted to `TRANSFER_VALIDATED` when its runtime proof was found circular; two separate false claims (a tutorial's and the project's own) caught and recorded | Same as before, sharper now: a held-out curved manufactured asset where these validated skills would naturally need to fire, showing whether retrieval actually improves the resulting model |
| UV/material/production preparation | A verified official seam lesson now has current Blender 5.2 reproduction and different-shape transfer: radial and bent rounded-rectangle connected all-quad source cages, matched no-seam distortion controls, measured UVs, separate high/low collections, live unapplied Solidify→Bevel stacks, tangent bakes, three-view production audits, low-only GLBs, and fresh verification | Strong controlled transfer; still not end-to-end production proof on a reviewer-accepted unfamiliar prop | Retrieve and apply the seam policy during an authorized asset's production stage, then obtain visual/material/export review |
| Editable high/low packaging | Typed operation creates reusable separate collections for multi-component props, independent cages, live modifier stacks, and exact rollback including array custom properties. The C38 run that used this path was deleted 2026-08-17; the operation itself is unchanged. | Machinery proven functional on deleted evidence; still not retopology, and no current candidate exercises it | Purpose-authored low topology with UVs, bake, and export on an accepted unfamiliar asset |
| Advanced sculpting/organic specialization | Explicitly deprioritized by current directive | Deferred by design | No action until prop modeling and reference interpretation gates are stronger |
| Final professional acceptance test | No evidence satisfies all acceptance requirements repeatedly on unfamiliar Level 7–8 references | Not achieved | Multiple held-out assets with interpretation, research, adaptive construction, correction, independent verification, editable `.blend`, and retained learning |

The bottleneck is unchanged in kind, sharper in specifics: it is still converting uncertain visual
evidence into the right editable construction, measuring whether it improved resemblance, and
recovering when it did not. What is new is that ONE technique sits in the library as genuinely `RUNTIME_VALIDATED`, on
evidence that survives the 2026-08-19 audit: a real classifier emits its trigger from geometry,
knowledge rather than the ticket supplies the technique parameter, and the defect is rolled back
instead of committed. Two other skills lost that status when their runtime proof turned out to
hand-author the answer. None of this project's validated skills has fired during the MasterLock
140D build in progress (`runs/2026-08-20_masterlock-140d-resume/`) -- its construction so far
(sockets, chamfer) used direct bmesh work, not retrieval-driven skill selection. That is
the single highest-value open gap: not more validated skills, not more documentation, but a
reference-driven build where the existing validated skills actually fire, with mandatory shaded
multi-view inspection at every stage (now demonstrated on MasterLock) rather than mesh-health
metrics alone -- and, since this session, a build that has reached the human-review step for the
first time, pending an actual recorded review. The detailed boundary
predating the 2026-08-17 deletions is recorded in
[`COMPLETION_AUDIT_2026-08-16.md`](COMPLETION_AUDIT_2026-08-16.md), itself now a historical
snapshot rather than a description of current repo contents.
