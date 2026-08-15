# Current-state to professional-modeler gap matrix

Updated: 2026-08-15 after integration PR #51. This matrix distinguishes merged evidence from
capability still lacking proof.

| Capability needed for the ultimate goal | Current evidence | State | Highest-value proof still required |
| --- | --- | --- | --- |
| Evidence-bound reference interpretation | `scene_decomposition.py`, planner integration, focused tests, and `runs/2026-08-15_reference-interpretation-contract/` merged through PR #51 | Policy experimentally tested; visual inference unproven | Extract real narrated reference-to-decision episodes, apply to images, then show improved Blender outcomes on unrelated objects |
| Component/depth/continuity/separation reasoning | Typed categories, relationships, unknown handling, and candidate/rejected strategies on the current branch | Implemented as a contract; inference source still manual | Controlled component, depth-order, and continuous-vs-separate reconstruction experiments with secondary-view truth |
| Knowledge changes runtime behavior | Supported claims now alter planner representation/component policy; weak/conflicting claims cannot silently harden | Demonstrated in declared policy cases | Runtime telemetry from actual Blender decisions and measured outcome improvement |
| Bridge Edge Loops twist control | Protocol 0.3, typed `twist_offset`, unequal-density rejection, rollback, and two-shape Blender evidence are merged | Controlled transfer; real-asset use open | Apply to a real modeling case through the typed decision path |
| Conditional Bevel/SubD order judgment | Matched-cage Blender 5.2 experiment and fresh verifier are merged | Experimentally tested, not runtime-transfer validated | Runtime retrieval/use on an unfamiliar hard-surface asset with visual surface review |
| Scoped Shrinkwrap footprint transfer | Sphere/cylinder transfer, destructive unscoped control, and fresh verifier are merged | Controlled second-shape transfer | Integrated runtime use on a real asset and evaluated-surface inspection |
| Narrated tutorial understanding | Local ingestion, structured Gemini extraction, metadata discovery, held-out contamination filters, and source-identity enforcement exist. `runs/2026-08-15_video-discovery-queue/` preserves one cross-video rejection and one independently found timestamp defect | Discovery operational; speech/action understanding partial | Successful visible-frame review, tighter synchronization, reproduction, different-geometry transfer, and runtime use |
| Multi-view reference fidelity and error localization | Silhouette, landmarks, components, negative-space metrics and mismatch tickets exist | Partial | Depth/overlap/component truth from real multi-view tasks; human visual rejection converted into structured corrections |
| Adaptive professional Blender modeling | Typed operations, transactions, rollback, fingerprints, state probes, stages, and independent verifiers exist | Strong infrastructure; artistic autonomy partial | Complete unfamiliar nontrivial prop from reference through repair and production prep without object-specific builder |
| Curved hard-surface and SubD judgment | Multiple operator studies and modifier experiments exist | Partial | Held-out curved manufactured asset showing topology, highlight flow, modifier rationale, and recovery |
| UV/material/production preparation | Foundation coverage exists but remains shallower than modeling/runtime infrastructure | Partial | End-to-end editable asset with UV distortion/packing, material reproducibility, organization, and export verification |
| Advanced sculpting/organic specialization | Explicitly deprioritized by current directive | Deferred by design | No action until prop-modeling and reference-interpretation gates are materially stronger |
| Final professional acceptance test | No evidence yet satisfies all 18 acceptance requirements repeatedly on unfamiliar Level 7-8 references | Not achieved | Multiple held-out assets with interpretation, research, adaptive construction, correction, independent verification, editable `.blend`, and retained learning |

The current bottleneck is not operator count. It is converting uncertain visual evidence into the
right editable construction, measuring whether that decision improved resemblance, and recovering
when it did not.
