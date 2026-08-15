# Current-state to professional-modeler gap matrix

Updated: 2026-08-15. This matrix distinguishes merged `main`, work published in draft pull requests,
and capability still lacking evidence. A draft branch is progress, not merged project state.

| Capability needed for the ultimate goal | Current evidence | State | Highest-value proof still required |
| --- | --- | --- | --- |
| Evidence-bound reference interpretation | `scene_decomposition.py`, planner integration, focused tests, and `runs/2026-08-15_reference-interpretation-contract/` on the current branch | Policy experimentally tested; visual inference unproven | Extract real narrated reference-to-decision episodes, apply to images, then show improved Blender outcomes on unrelated objects |
| Component/depth/continuity/separation reasoning | Typed categories, relationships, unknown handling, and candidate/rejected strategies on the current branch | Implemented as a contract; inference source still manual | Controlled component, depth-order, and continuous-vs-separate reconstruction experiments with secondary-view truth |
| Knowledge changes runtime behavior | Supported claims now alter planner representation/component policy; weak/conflicting claims cannot silently harden | Demonstrated in declared policy cases | Runtime telemetry from actual Blender decisions and measured outcome improvement |
| Bridge Edge Loops twist control | Draft PR #37, commit `c84bf40`; controlled Blender lab previously reported passing | Published draft, not in `main` | Review/merge, then apply to a real modeling case and a second unrelated shape in the integrated branch |
| Conditional Bevel/SubD order judgment | Draft PR #38, commit `733ca50`; controlled supported/unprotected stack comparison | Published draft, not in `main` | Runtime retrieval/use on an unfamiliar hard-surface asset with visual surface review |
| Scoped Shrinkwrap footprint transfer | Draft PR #39, commit `a8e7653`; two-shape declared transfer and failure controls | Published draft, not in `main` | Integrated runtime use on a real asset and evaluated-surface inspection |
| Narrated tutorial understanding | Real local video ingestion and several decoded studies exist; current directive records that speech/action alignment and genuine reference-decision extraction remain thin | Partial | Source discovery, frame/audio/caption synchronization, episode extraction, reproduction, and transfer |
| Multi-view reference fidelity and error localization | Silhouette, landmarks, components, negative-space metrics and mismatch tickets exist | Partial | Depth/overlap/component truth from real multi-view tasks; human visual rejection converted into structured corrections |
| Adaptive professional Blender modeling | Typed operations, transactions, rollback, fingerprints, state probes, stages, and independent verifiers exist | Strong infrastructure; artistic autonomy partial | Complete unfamiliar nontrivial prop from reference through repair and production prep without object-specific builder |
| Curved hard-surface and SubD judgment | Multiple operator studies and modifier experiments exist | Partial | Held-out curved manufactured asset showing topology, highlight flow, modifier rationale, and recovery |
| UV/material/production preparation | Foundation coverage exists but remains shallower than modeling/runtime infrastructure | Partial | End-to-end editable asset with UV distortion/packing, material reproducibility, organization, and export verification |
| Advanced sculpting/organic specialization | Explicitly deprioritized by current directive | Deferred by design | No action until prop-modeling and reference-interpretation gates are materially stronger |
| Final professional acceptance test | No evidence yet satisfies all 18 acceptance requirements repeatedly on unfamiliar Level 7-8 references | Not achieved | Multiple held-out assets with interpretation, research, adaptive construction, correction, independent verification, editable `.blend`, and retained learning |

The current bottleneck is not operator count. It is converting uncertain visual evidence into the
right editable construction, measuring whether that decision improved resemblance, and recovering
when it did not.
