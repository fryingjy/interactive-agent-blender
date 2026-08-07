# Interactive Agent Blender — Master Continuation + Professional Learning Curriculum

Repository: `fryingjy/interactive-agent-blender`

This document is the master continuation directive. Do not restart the project. Do not replace
working systems merely for architectural neatness. Do not optimize for impressive demos, high
action counts, or finished objects at the expense of the actual product.

**This document does not override the repository.** Section 3 below is explicit: verify current
repo/live-Blender state before trusting anything written here, including this file. Where this
directive's assumptions conflict with something already empirically found in this project (see the
"Known deviations from this directive" note maintained in README.md), the empirical finding wins
and the directive's approach should be adapted, not blindly re-attempted.

## 1. Actual Product Definition

The system is NOT: a text-to-3D generator; a Blender Python script generator; a collection of
procedural asset builders; a screenshot-clicking macro; a benchmark-gaming system; a large tutorial
database; an LLM that only describes modeling.

The system IS: a persistent interactive Blender agent that continuously observes, understands,
decides, models, verifies, repairs, researches, experiments, learns, and adapts like an
increasingly proficient professional modeler.

Core live loop:

```
OBSERVE
→ UNDERSTAND CURRENT MODELING STATE
→ RETRIEVE RELEVANT KNOWLEDGE
→ CHOOSE ONE LOCAL MODELING ACTION
→ PERFORM ACTION
→ RECEIVE AUTHORITATIVE BLENDER FEEDBACK
→ EVALUATE RESULT
→ ACCEPT / UNDO / REPAIR
→ OBSERVE NEW STATE
→ CONTINUE
```

Knowledge-gap loop:

```
MODELING PROBLEM
→ SEARCH INTERNAL KNOWLEDGE
→ KNOWLEDGE SUFFICIENT?
   ├─ YES → USE IT
   └─ NO
      → RESEARCH EXTERNAL SOURCES
      → INSPECT ACTUAL SOURCE CONTENT
      → FORM HYPOTHESIS
      → TEST IN BLENDER
      → MEASURE
      → CREATE / REVISE EXECUTABLE SKILL
      → RETURN TO ORIGINAL ASSET
      → USE SKILL
      → VERIFY
      → CONTINUE
```

Everything in this repository must serve one of: observe, understand, decide, act, verify,
recover, research, learn.

## 2. Long-Term Goal

Not merely "Claude can control Blender." The target is: given unseen digital concept art or a
modeling brief, autonomously produce an editable Blender asset approaching the judgment,
cleanliness, adaptability, consistency, and efficiency of a proficient professional Blender
modeler, across hard-surface props, stylized props, tools/equipment as digital assets, furniture,
appliances, electronics, sci-fi objects, vehicle components, architectural objects, containers,
accessories, subdivision-surface objects, sculpted/organic forms, production-ready game/animation
props, and fictional fantasy/combat-themed game props using general artistic hard-surface methods.

**Safety/scope constraint**: do not use real-world weapon-construction references or engineering
instructions as training sources. If modeling a fictional combat-themed asset, learn transferable
DIGITAL art techniques from general hard-surface, topology, silhouette, prop-design, and
reference-modeling sources only.

Professional capability includes form judgment (primary/secondary/tertiary forms, proportion,
silhouette, shape language, negative space, component relationships), modeling strategy
(box/poly/subdivision/boolean/bevel/surface/curves/mirror/manual topology/retopology/sculpt→retopo/
non-destructive modifiers), topology judgment (edge flow, support topology, pole placement,
density, tri/ngon context, shading consequences, subdivision behavior, editability), workflow
judgment (what to solve now vs. postpone, when to rebuild vs. patch, when "clean" ≠ good), and
self-critique (silhouette, proportions, reference match, pinching, shading artifacts, density,
poles, transitions, bevel consistency). Recovery: a professional recognizes mistakes quickly and
recovers efficiently rather than avoiding every mistake.

## 3. First Action in Every New Claude Session

Before editing code: inspect current `main`; read `README.md`; read `docs/RESEARCH_ROADMAP.md`;
inspect `blender_ops/`; inspect `knowledge/`; inspect recent `runs/`; inspect verification reports;
inspect the current Blender/MCP connection; identify the current Blender PID/session; verify
capabilities in code/live runtime rather than trusting documentation.

**Do not blindly trust this document either. The repository is the current truth.**

## 4. Current Known Repository State (as prepared)

Already demonstrated/implemented at the time this directive was prepared: persistent Blender
process; Blender MCP live connection; decision revision tracking; DecisionTransaction; decision-cycle
logs; independent mesh verification; selection inspection; local vertex-neighborhood inspection;
valence distribution; modifier inspection; mesh-health metrics; mode-aware BMesh helper; persistent
vertex/edge/face IDs; duplicate persistent-ID detection/repair; per-decision persistent-ID deltas;
consolidated state reads; basic skill storage/retrieval; mistake detection; repair; skill
reuse/generalization evidence; evidence of user/agent edit collisions; explicit research roadmap.

Important failures already discovered (valuable evidence, not to be hidden):

```
technical validity != professional topology
raw Blender indices != stable identity
BMesh operations may copy custom attributes onto generated geometry
Object Mode mesh reads may be stale during live Edit Mode
window_manager.operators is not a reliable transaction oracle
manual GUI edits can alter the live scene outside the script-owned revision
arbitrary execute_blender_code can bypass sanctioned transaction conventions
```

## 5. Immediate Engineering Priority: Stronger Direct Claude ↔ Blender Connection

Blender itself becomes the authoritative source for live state changes, including agent mutations
and human GUI edits. Move toward:

```
Claude Modeling Planner
        ↕
Typed Modeler Tools / MCP
        ↕
Modeler Runtime
        ↕
Blender Companion / Modeler Bridge
        ↕
Persistent Live Blender
```

Blender MCP may remain underneath/alongside this. Do not rebuild everything only for architectural
purity — add the smallest modeler-specific layer required to provide guarantees generic arbitrary
Python execution cannot provide.

## 6. Blender-Originated Scene Revision

Caller-driven revision tracking is insufficient if the GUI can change the mesh without advancing
the counter. Target: any meaningful scene mutation (typed agent commands, debug arbitrary-code
calls, manual Object/Edit Mode edits, object add/delete, transforms, mode changes, active-object
changes, selection changes, modifier changes, undo, redo, file load, checkpoint restore) advances
scene_revision and emits an event, invalidating stale observations.

Investigate and test Blender-native mechanisms: dependency-graph update handlers; Blender message
bus; undo/redo handlers; load/save handlers; state fingerprints where an exact event API is
unavailable. **Do not assume any one hook catches all changes. Test against the actual Blender
version.**

## 7. Separate Identifiers

Maintain distinct `session_id`, `scene_revision`, `decision_id`, `command_id`, `event_id`. Do not
overload a revision counter as decision count.

## 8. Push Event Channel

Event types: session_ready, heartbeat, scene_changed, mesh_changed, selection_changed,
mode_changed, active_object_changed, object_added, object_removed, modifier_changed,
operator_started, operator_finished, operator_cancelled, undo_completed, redo_completed,
external_edit_detected, checkpoint_created, file_saved, file_loaded, error.

Origins: AGENT_COMMAND, USER_GUI, UNDO_REDO, FILE_LOAD, UNKNOWN_EXTERNAL. **Use UNKNOWN_EXTERNAL
rather than inventing provenance.**

## 9. Event Coalescing

One Blender operator may create many dependency-graph updates — do not expose every callback as a
separate modeling decision. Coalesce to one logical revision transition per command/edit burst.
Avoid uncontrolled sleeps; use deterministic settle criteria where possible.

## 10. Mode-Correct Live State

Audit all live mesh reads to use the mode-aware BMesh path consistently. Required proof: enter Edit
Mode, mutate topology, remain in Edit Mode, query state, confirm the exact current edit-BMesh state
is returned. Audit at least: selection, mesh health, valence, local neighborhoods, topology-region
queries, persistent IDs, transaction before/after reads, repair code, live verification.

## 11. Persistent IDs as Primary Identity

Claude should remember persistent IDs, not Blender's temporary indices. Selection responses should
include both index and agent_id. Reason with agent_id; resolve to Blender indices only immediately
before executing Blender operations.

Invariants: all live elements have nonzero IDs; no duplicate IDs per element domain; deleted IDs
are not silently reused; IDs survive save/load; unrelated edits preserve surviving identity.

Test against: extrude, inset, bevel, loop cut, subdivide, bridge, spin, dissolve, merge by
distance, boolean/apply. If an operation destroys meaningful identity, record an identity
discontinuity rather than pretending continuity.

## 12. Typed Modeler Commands

Make `execute_blender_code` a debug/experimental fallback, not the primary artistic-modeling
interface. Command envelope includes command_id, decision_id, session_id,
expected_scene_revision, operation, target, parameters. Response includes success,
revision_before/after, delta, warnings. A stale command must fail before mutation.

Initial typed vocabulary: observe_state; inspect_vertex/edge/face/region; select_by_persistent_ids;
select_region; set_selection_mode; set_active_object; set_mode; move/rotate/scale_selection;
extrude_selection; inset_selection; bevel_selection; loop_cut; add_modifier;
set_modifier_parameter; undo; redo; save_checkpoint; restore_checkpoint; save_file.

**Do not create asset builders.**

## 13. Command Idempotency

Retries must not duplicate geometry — a retried command_id should return the stored prior result,
not mutate again. Maintain a bounded command journal.

## 14. Session/Heartbeat/Reconnect

Handshake exposes session_id, PID, Blender version, protocol version, scene revision, blend
filepath, heartbeat, capabilities. On reconnect: confirm same session/PID, fetch authoritative
state, invalidate stale plans, continue.

## 15. Human / Agent Ownership

Explicit modes: AGENT_CONTROL, USER_CONTROL, SHARED_OBSERVATION. If an external user edit occurs
during AGENT_CONTROL: detect it, invalidate the pending command/decision, stop mutation,
re-observe, resume only from actual live state. **Never fight the user's mouse. Never silently
overwrite user edits.**

## 16. Semantic Geometry

After persistent IDs are reliable, add semantic regions (region_id, object, role, vertices, edges,
created_revision, last_validated_revision). Roles: primary_form, secondary_form, outer_contour,
silhouette_feature, corner, transition, support_loop, feature_edge, mirror_seam, hole_boundary,
attachment_region, bevel_edge. Operations: create/get/validate/update/select/delete_region.
Topology changes must update/invalidate regions honestly.

## 17. Region-Level Topology Perception

`inspect_topology_region(object, center_ids, rings=2)` returning persistent IDs, positions,
valence, boundary state, neighbors, edge lengths/angles, face areas/sizes/normals, local
tri/quad/ngon counts, local edge-length and face-area ratios, pole locations, connected components.
Later: curvature estimates, surface continuity, subdivision comparison, shading distortion,
proximity to silhouette/high-curvature areas. **Do not label every non-4-valence vertex bad —
context matters.**

## 18. Separate Validity From Quality

Validity: non-manifold edges, loose geometry, degenerate faces, zero-length edges, normal
consistency, forbidden ngons. Quality: edge flow, pole placement, triangle placement, face-area
consistency, edge-length consistency, support-loop behavior, subdivision response, shading,
silhouette, density, editability. **Never report mesh_health clean as equivalent to professional
topology.**

## 19. Direct Viewport State

Expose active editor, view orientation/matrix, projection, view location, zoom/distance, local
view, x-ray, shading mode, overlays, active tool, active camera and transform — so Claude knows
whether it's evaluating a front-orthographic silhouette vs. perspective volume vs. wireframe
topology without inferring that from desktop pixels.

## 20. Blender-Native Visual Channel

After direct state/events are reliable, add controlled Blender-generated visual outputs:
render_viewport, render_reference_view, render_silhouette, render_wireframe, render_normals,
render_depth, render_object_mask, render_selected_region. Every artifact must identify scene
revision, object, camera/view, projection, resolution, relevant settings. Structured state is the
truth for facts; visual outputs are for aesthetic/reference judgment.

**Note**: this item directly reverses this project's founding "no-screenshot" design tenet (see
top of README.md) and needs an explicit confirmation from the user before being built, not a
blanket go-ahead absorbed into a larger bundle.

## 21–22. Reference Understanding and Correction

Reference ingestion should eventually determine view type, symmetry, object/component masks,
landmarks, component hypotheses, proportions, known dimensions, uncertainty. Begin simple; do not
attempt perfect automatic concept-art decomposition immediately. For suitable orthographic views,
compare reference mask vs. Blender silhouette (IoU, contour distance, bounding-box/centroid/
landmark/proportion error) and create localized repair tickets. Prefer deterministic measurement
over LLM opinion when possible.

## 23–50. Professional Learning Curriculum (gated, see below)

Full source-tier system (Tier A official docs, Tier B established professional education, Tier C
technical community discussion, Tier D weak/unverified), a starting curriculum of vetted sources
(Blender Manual sections, Blender Studio, Blender Guru, CG Cookie, Blender Secrets, Blender Stack
Exchange, Blender Artists, Polycount), a video-study protocol (coarse segmentation → fine action
study → speech/action alignment → mistake/recovery capture → four knowledge layers: observation /
interpretation / experimental evidence / executable skill), controlled-experiment requirements
before promoting any skill, a skill format and promotion lifecycle (CAPTURED → INTERPRETED →
CANDIDATE → EXPERIMENTALLY_TESTED → BENCHMARK_SUPPORTED → RUNTIME_VALIDATED → PROMOTED, plus
CONTRADICTED/DEPRECATED/VERSION_LIMITED/INSUFFICIENT_EVIDENCE), contradiction handling (make advice
conditional on deforming/static, flat/curved, low-poly/high-poly, etc. rather than picking a side by
popularity), a requirement that every learning episode return to and improve the live model, mining
of the agent's own session history for lessons, a curriculum order (A. fundamentals → B. topology →
C. simple hard-surface → D. subdivision surface → E. reference-based hard-surface → F. retopology →
G. complex stylized → H. sculpting → I. sculpt→retopo → J. materials/UV/production → K. broader
asset classes), and an explicit anti-overfitting rule (no single educator becomes "the truth";
triangulate official docs + educator + community edge case + own experiment).

**Explicitly gated** (section 49, "DO NOT MASS-INGEST BEFORE RUNTIME CAN USE KNOWLEDGE"): the
correct sequence is closed-loop modeler → small validated skill library → runtime retrieves/uses
skills → *then* problem-driven browser research → video understanding → experiments →
self-learning → larger curriculum. Do not start section 23-50 work until the closed-loop
engineering items (5-17ish) are substantially done. This matches this project's pre-existing
`docs/RESEARCH_ROADMAP.md` gating, which this directive supplements rather than replaces.

## 51. Professional Benchmark Ladder

Stage 1 Reliable Blender Operator → Stage 2 Closed-Loop Modeler → Stage 3 Reference-Based Modeler →
Stage 4 Competent Stylized/Hard-Surface Modeler → Stage 5 Knowledge-Adaptive Modeler → Stage 6
Proficient Specialist → Stage 7 Broader Professional Modeler. **Do not call one successful prop
"professional-level."**

## 52. Held-Out Evaluation

Never evaluate a capability using assets whose dimensions/topology/action-sequence/decomposition/
helper-functions/repair-recipe were developed specifically for that evaluation. Maintain
hidden/held-out references encountered only at evaluation time.

## 53. Professional Metrics

Track separately: technical validity (non-manifold/loose/degenerate/normals/zero-length), topology
quality (valence distribution, pole placement by region, tri/ngon placement by region, face-area
ratio, edge-length ratio, density, subdivision behavior, editability), visual quality (silhouette
IoU, contour error, landmarks, proportions, component relationships, hierarchy), process quality
(decisions accepted/rejected/undone/repaired, human interventions, stale-command attempts, Blender
restarts, recovery success), learning quality (skills retrieved/used/reused cross-asset, research
episodes, experiments, contradicted/promoted skills).

## 54. Strict Anti-Fake-Progress Rules

Never count as professional-modeler progress: a complete asset generated by one bpy/BMesh script;
an asset-specific builder; 100 precomputed operations presented as 100 decisions; a helper that
encodes substantial artistic design; a manual revision bump used as proof Blender changed;
technical validity presented as professional topology; a desktop screenshot used for facts Blender
can expose directly; a tutorial summary marked as a learned skill; forum advice promoted without
testing; a human correction attributed to the agent; a benchmark threshold changed after seeing the
result; a result accepted only because no exception occurred. **Keep failures visible.**

## 55. Immediate Implementation Order From Current Main

```
1. verify current repo/live Blender state
2. migrate live topology reads to mode-correct APIs
3. return persistent IDs in selection/state
4. harden persistent-ID invariants
5. separate scene revision from decision identity
6. build Blender-originated external-change detection
7. build minimal push event stream
8. event coalescing
9. automatic stale-observation invalidation
10. typed command envelope
11. expected_scene_revision enforcement
12. command idempotency
13. route common artistic actions through typed tools
14. log arbitrary execute_blender_code fallback
15. session handshake + heartbeat
16. reconnect without Blender restart
17. explicit user/agent ownership
18. semantic regions
19. richer local topology graphs
20. direct viewport state
21. Blender-native visual passes
22. deterministic reference comparison
23. fresh 20-40-decision held-out modeling benchmark
24. independent technical/topology/visual verification
25. activate problem-driven browser research
26. implement research → experiment → skill
27. use learned skill on original task
28. begin systematic expert curriculum expansion
```

## 56. Next-Session Engineering Tests (required)

Edit Mode truth (mutate in Edit Mode without exiting, query, confirm true live topology); external
GUI edit (agent observes revision N, user edits, bridge emits N+1, stale agent command rejected);
persistent IDs (remember region A, edit unrelated B, A's identity survives); duplicate custom IDs
(topology-generating operator, verify uniqueness, repair if needed); duplicate command retry (lost
response, retry, no duplicate mutation); reconnect (client disconnects, Blender stays up, reconnect
same PID/session, continue).

## 57. Required End-of-Session Report Format

```
STATUS: PASS / PARTIAL / FAIL
Git commits:
Blender PID / session / restarts:
Protocol version:
Implemented: [mode-correct live state / persistent-ID selection / Blender-originated revision /
  push events / external GUI edit detection / typed commands / idempotent commands / heartbeat /
  reconnect / user-agent ownership]
Tests: [Edit Mode truth / external GUI mutation / stale command rejection / persistent-ID
  stability / duplicate-ID repair / duplicate command retry / reconnect without restart]
Arbitrary execute_blender_code calls: (count + reasons)
Human interventions:
Known limitations:
Evidence paths:
Next recommended milestone:
```

Do not mark undocumented/unverified code PASS.

## 58. Research Session Report Format

(For use once research work is unblocked per the section 23-50 gate.) Problem; why internal
knowledge was insufficient; search queries; sources considered/rejected (with reasons)/selected;
source trust tier; video modalities actually available; direct observations; interpretations;
contradictions; candidate hypotheses; Blender experiments; measured results; skill created/updated;
promotion status; returned to original asset (Y/N); runtime skill used (Y/N); measured effect;
remaining uncertainty.

## 59. Final Behavior Target

User provides an unseen digital reference → Claude studies and decomposes forms → Blender reports
exact state and viewport → Claude chooses a primary-form operation → Blender performs it and emits
revision/delta → Claude evaluates against the reference → ... → Claude hits a topology problem with
low retrieval confidence → searches official docs + expert tutorial + technical forum → studies the
actual tutorial segment → extracts a candidate principle → runs a controlled Blender experiment →
creates a candidate skill → returns to the original model, retrieves and applies the skill →
Blender reports improvement → continues → independent verifier checks topology/validity → visual
evaluator checks reference quality → an editable `.blend` is delivered.

## 60. Final Rule

The project must become a modeling system, not a tutorial collector. Every new source must answer:
is it authoritative, clear, relevant, reproducible, and useful for a real modeling decision? Every
new piece of knowledge must answer: was it observed, tested, used, and verified? Every new feature
must answer: does it make the system better at continuously observing, understanding, deciding,
modeling, verifying, recovering, researching, or learning in Blender? If not, do not build it yet.
