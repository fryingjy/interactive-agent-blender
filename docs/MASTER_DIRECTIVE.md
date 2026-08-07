# Interactive Agent Blender — Current Master Directive Toward Professional Modeling (Updated)

## Repository

Continue development in:

`fryingjy/interactive-agent-blender`

**Current repository snapshot reviewed for this directive:** commit `a0332746c2cfb39527ad4e74115af3e073f74714` (2026-08-07).

This file supersedes earlier continuation prompts when they conflict with empirically verified current repository behavior.

Do **not** restart the project.

Do **not** rebuild already-working systems simply to follow an older roadmap literally.

Do **not** optimize for impressive-looking demos, arbitrary action counts, or technical-validity checks at the expense of the real product.

The repository is now beyond the "can Claude talk to Blender?" stage. The next work must increasingly answer:

> Can the system perceive, judge, plan, adapt, recover, research, learn, and model unseen assets with the quality and workflow judgment of a proficient professional Blender modeler?

---

# 1. Product Definition

The system is NOT:

- a text-to-3D generator;
- a complete-mesh Python generator;
- an asset-specific procedural builder library;
- a benchmark-gaming project;
- a collection of Blender tricks;
- a tutorial summarizer;
- an LLM that merely calls Blender tools successfully.

The system IS:

> A persistent interactive Blender modeler that continuously observes the real live Blender state, understands the current modeling problem, selects one appropriate local modeling action, executes it through a controlled interface, verifies the actual result, repairs or reverses mistakes, judges visual and topology quality, researches unknown problems, validates new techniques experimentally, and reuses learned skills on unseen work.

Core modeling loop:

```text
OBSERVE
→ UNDERSTAND
→ RETRIEVE KNOWLEDGE
→ PLAN NEXT LOCAL DECISION
→ ACT
→ RECEIVE BLENDER RESULT
→ VERIFY
→ JUDGE
→ ACCEPT / ROLLBACK / REPAIR
→ RE-OBSERVE
→ CONTINUE
```

Knowledge-gap loop:

```text
UNKNOWN OR LOW-CONFIDENCE MODELING PROBLEM
→ SEARCH INTERNAL KNOWLEDGE
→ INSUFFICIENT?
→ RESEARCH HIGH-QUALITY EXTERNAL SOURCES
→ INSPECT ACTUAL SOURCE CONTENT
→ FORM HYPOTHESIS
→ TEST IN BLENDER
→ MEASURE
→ ENCODE / REVISE EXECUTABLE SKILL
→ RETURN TO ORIGINAL ASSET
→ APPLY
→ VERIFY
→ CONTINUE
```

The project succeeds only when these loops work together.

---

# 2. End Goal: Proficient Professional Modeler

The end goal is not "automation that can make some props."

The target is:

> Given an unseen digital reference or modeling brief, autonomously produce an editable Blender asset approaching a proficient professional artist's form judgment, topology judgment, modeling-strategy choice, visual matching, recovery skill, efficiency, and consistency.

The modeler should eventually generalize across digital asset categories such as:

- hard-surface props;
- stylized props;
- subdivision-surface assets;
- furniture;
- electronics;
- appliances;
- containers;
- architectural objects;
- sci-fi/fantasy game props;
- tool-like/equipment-like digital props;
- vehicle/interior components at an asset-modeling level;
- sculpted/organic forms;
- sculpt-to-retopology workflows;
- game/animation-ready assets.

For safety and scope, do not use real-world weapon-construction references or engineering instructions as learning material. If a fictional combat-themed game prop is modeled, learn from transferable digital-art subjects such as hard-surface form, topology, silhouette, prop design, materials, and reference matching.

Professional competence means improving simultaneously in:

```text
FORM
proportion
silhouette
primary / secondary / tertiary forms
negative space
shape language
component relationships

STRATEGY
box/poly modeling
subdivision
booleans
bevel workflows
curves
surface modeling
mirror/symmetry
separate components
manual topology
retopology
sculpt → retopo
modifier strategy

TOPOLOGY
edge flow
pole placement
support topology
density
surface continuity
triangle/ngon context
subdivision response
shading response
editability

WORKFLOW
what to solve now
what to postpone
when to simplify
when to rebuild
when to use a modifier
when to separate geometry
when a result is good enough

SELF-CRITIQUE
weak silhouette
bad proportions
poor reference match
pinching
shading artifacts
bad pole placement
unnecessary density
poor transitions
inconsistent bevels

RECOVERY
detect mistake
diagnose cause
rollback / repair / change strategy
continue efficiently

LEARNING
recognize knowledge gap
find strong sources
extract reasoning
experiment
validate
reuse skill
```

A mesh being manifold and exception-free is nowhere near sufficient evidence of professional capability.

---

# 3. Mandatory Session Start Procedure

At the start of every Claude development session:

1. inspect current `main`;
2. read `README.md`;
3. read `docs/MASTER_DIRECTIVE.md`;
4. read `docs/RESEARCH_ROADMAP.md`;
5. inspect latest commits;
6. inspect `blender_ops/`;
7. inspect `tools/modeler_mcp_server.py`;
8. inspect `knowledge/`;
9. inspect latest `runs/`;
10. inspect independent verification evidence;
11. connect to the actual live Blender/modeler server;
12. record Blender PID, session ID, protocol version, active file, revision, and capabilities;
13. verify claims in the live runtime rather than trusting documentation.

**Empirical current behavior wins over this document.**

If a current experiment disproves a claim in this file:

```text
record discrepancy
→ update documentation honestly
→ change architecture
```

Do not force the implementation to match an outdated assumption.

---

# 4. CURRENT REPOSITORY STATE — REVIEWED AT `a0332746c2cfb39527ad4e74115af3e073f74714`

Do not rebuild the following from scratch.

The current project has moved beyond the original "direct connection" milestone and has already demonstrated meaningful pieces of real autonomous modeling.

## 4.1 Typed Modeler Protocol Is Real and Has Been Used for Modeling

The repository contains a custom typed modeler server and MCP wrapper, not only generic `execute_blender_code`.

The protocol already supports, in current main:

```text
session identity
heartbeat
capability discovery
persistent element IDs
full-state queries
selection by persistent IDs
viewport-state queries
region inspection
semantic regions
explicit control modes
event polling
external-edit checks
decision transactions
command idempotency
checkpoints / file operations
```

Normal artistic work should continue moving through this typed interface.

`execute_blender_code` is now a fallback/debug path, not the preferred modeling surface.

## 4.2 The Speaker Benchmark Reached 20 Typed Decisions

`runs/2026-08-07_speaker-typed-protocol/` now contains 20 real sequential modeling decisions.

This is important because it demonstrates that the typed modeler protocol can support an actual held-out prop rather than only infrastructure tests.

The run also surfaced useful professional-style behavior:

```text
wrong face selected
→ inspect actual selection
→ correct target before proceeding

pole valence increased
→ inspect geometry/areas
→ judge context rather than blindly "fixing" it

persistent element identity changed under one bevel
→ record identity discontinuity rather than pretending continuity
```

However, the run is still **PARTIAL**, not a strict PASS:

- the Blender PID changed mid-session;
- decisions 9–20 were logged afterward as a batch rather than immediately;
- the anti-batching verifier correctly flags this.

Do not retroactively repair historical timestamps.

Improve logging/runtime integration so future decisions are persisted immediately when they happen.

## 4.3 Semantic Regions Are Now Used on a Real Asset

The finished SpeakerEnclosure contains semantic regions such as:

```text
driver_cavity
cable_port
```

The next objective is not "prove semantic regions can be created."

The objective is:

> Demonstrate that semantic regions improve multi-step reasoning, target memory, recovery, reference comparison, and knowledge retrieval across a longer modeling task.

## 4.4 Evaluated-Mesh Perception Now Exists

`blender_ops/evaluated_probe.py` was added because subdivision modeling cannot be judged only from the base control cage.

It currently provides modifier-evaluated inspection such as:

```text
evaluated_mesh_health
evaluated_valence_distribution
evaluated_surface_quality
```

This is a major conceptual improvement.

For modifier-driven modeling, maintain a distinction between:

```text
BASE CAGE STATE
what Claude edits

EVALUATED SURFACE STATE
what the artist/viewer actually sees
```

Professional decisions must consider both.

## 4.5 `subdivide_selection` Exists

The typed modeling vocabulary now includes `subdivide_selection`, built for subdivision-surface control-cage work.

It was live-tested with persistent IDs and DecisionTransaction behavior.

Do not waste the next session merely proving subdivision can split a plane.

Use it in a real control-cage modeling problem.

## 4.6 First Subdivision-Surface Reference Is Staged

`reference/soap_dish/notes.md` is the next deliberately unseen milestone.

It is the first project benchmark whose final visible surface is produced through a Subdivision Surface modifier rather than a bevel-only final mesh.

The intended learning challenge is:

```text
smooth rounded outer form
+
shallow continuous concave basin
+
clean support/control topology
+
no visible pinching
+
good pole placement
+
good evaluated surface
```

The exact control-cage solution is intentionally not pre-specified.

That is correct.

The system must exercise judgment.

---

# 5. CURRENT PRO-LEVEL GAP ANALYSIS

The project is no longer mainly blocked by "can Claude execute Blender actions?"

The largest remaining gaps between this system and a professional modeler are now:

## 5.1 Rollback Is Still Not Authoritative

Direct BMesh writes do not reliably create Blender undo entries corresponding one-to-one with typed modeler decisions.

Therefore:

```text
bpy.ops.ed.undo()
```

cannot be treated as:

```text
undo the immediately previous Claude decision
```

### Required

Build transaction-owned rollback.

Before a risky artistic operation:

```text
capture recoverable pre-state
→ perform one operation
→ inspect base + evaluated result
→ accept OR restore exact pre-state
```

Rollback must preserve or correctly restore:

```text
geometry
persistent IDs
semantic regions
selection where important
object transform
modifier state
scene revision consistency
```

This remains P0 because a professional modeler must be able to reject a bad edit safely.

## 5.2 External-Edit Detection Is Not Yet Fully State-Authoritative

Persistent-ID-set comparison detects topology additions/removals.

It does not by itself prove that existing geometry did not move.

A human may:

```text
move existing vertices
change object transforms
change modifier values
```

while preserving the same persistent-ID sets.

### Required

Introduce layered state fingerprints:

```text
topology identity
connectivity
vertex positions / geometry signature
object transform
relevant modifier parameters
selection/mode where necessary
```

A meaningful external edit must invalidate stale agent observations even if no IDs were created/deleted.

## 5.3 Event Delivery Is Useful but Not Yet a Perfect Real-Time Oracle

Dependency-graph handlers have already shown delayed behavior in this Blender environment.

Treat event handlers as signals, not infallible proof of when a mutation completed.

For typed decisions, direct before/after state comparison remains authoritative.

For user/external changes, combine handlers with state-fingerprint observation.

## 5.4 Visual Reference Modeling Is Still Missing

Current references are primarily structured notes.

That is useful for controlled capability development, but it is not enough for a pro-modeler goal.

A professional modeler works from actual visual evidence.

After the current SubD milestone, the project must move quickly toward:

```text
actual reference image
→ reference mask / landmarks
→ Blender-native render/silhouette
→ measurable comparison
→ localized correction
```

## 5.5 Modeling Strategy Choice Is Still Shallow

The system can execute operations and make local adaptations.

It still needs to get much better at deciding:

```text
what overall workflow fits this form?

subdivision?
boolean?
separate components?
box modeling?
curve?
retopology?
rebuild rather than patch?
```

This becomes increasingly important from the soap-dish milestone onward.

## 5.6 Knowledge Is Still Too Small for Professional Breadth

The current skill library is useful but tiny.

The long-term modeler will require robust knowledge of:

```text
hard-surface
subdivision
topology
retopology
reference matching
surface quality
sculpt/organic
production prep
```

The external research curriculum later in this document is therefore mandatory.

---

# 6. IMMEDIATE P0 — HARDEN RECOVERY AND STATE AUTHORITY

Do not stop the current subdivision milestone for weeks of infrastructure work.

But before claiming robust autonomy, complete these guarantees:

```text
1. transaction-owned rollback independent of Blender's global undo stack

2. topology-preserving external vertex movement is detected

3. object transform changes are detected

4. modifier-state changes are detected

5. external divergence invalidates stale decisions

6. rollback restores persistent-ID invariants

7. rollback restores semantic-region integrity or explicitly invalidates affected regions

8. decisions are logged immediately, not batch-written later

9. reconnect and command idempotency continue to work
```

Build these incrementally while the real modeling benchmark exercises them.

Avoid another infrastructure-only marathon.

---

# 7. IMMEDIATE P1 — COMPLETE THE SOAP-DISH SUBDIVISION MILESTONE

The current next modeling task is the held-out smooth soap dish.

This task is important because it tests a new modeling family.

Every major previous asset used a final surface that was essentially the editable mesh plus bevel-style treatment.

The soap dish requires:

```text
CONTROL CAGE
↓
Subdivision Surface modifier
↓
EVALUATED SMOOTH SURFACE
```

The system must reason about both.

## Required workflow

Start from a simple primitive/control cage.

Use a high-level plan only:

```text
establish outer rounded rectangle
→ establish thickness / rim
→ create shallow basin
→ control outer silhouette
→ control basin transition
→ evaluate SubD surface
→ diagnose pinching / waviness
→ adjust support topology
→ verify
```

Do not precompute the exact edge/vertex sequence.

## Required evidence

At multiple decisions record:

```text
base cage state
evaluated surface state
why the next action was chosen
expected surface effect
actual evaluated effect
accept / rollback / repair
```

## Required adaptive moments

The benchmark should contain genuine examples such as:

```text
support edge too close
→ evaluated surface pinches
→ detect
→ move/remove/reroute support topology

basin transition too flat
→ evaluated curvature insufficient
→ adjust cage

surface develops local irregularity
→ inspect pole / edge-density context
→ repair
```

Do not manufacture errors deliberately just to satisfy this list.

Use whatever real issues actually occur.

---

# 8. SUBDIVISION SURFACE QUALITY MUST BE LOCAL, NOT ONLY GLOBAL

The current evaluated probe reports useful global signals such as:

```text
face-area outliers
maximum adjacent-face angle
```

These are a starting point.

Professional SubD judgment requires localization.

Next extend evaluated inspection so the system can answer:

```text
WHERE is the curvature discontinuity?

WHICH control-cage region influences it?

WHICH persistent IDs are near the problematic evaluated area?

IS the problem:
support-loop distance?
pole placement?
edge density?
uneven control-cage spacing?
bad topology transition?
```

Develop a mapping strategy between:

```text
control cage semantic region
↔
evaluated surface region
```

It does not need perfect one-to-one evaluated vertex identity.

It needs enough spatial correspondence to create actionable local repair tickets.

---

# 9. FIRST REAL PROBLEM-DRIVEN RESEARCH TRIGGER MAY OCCUR DURING THE SOAP DISH

This is important.

Do not research subdivision tutorials preemptively just to collect notes.

Model first using existing knowledge.

If the system encounters a genuine unresolved issue such as:

```text
persistent pinching
poor basin-to-rim transition
bad pole routing
unexpected SubD collapse
uneven highlight flow
```

and internal knowledge is insufficient, **trigger the research loop**.

Required process:

```text
describe exact observed defect
→ search internal skills
→ record low confidence / gap
→ search vetted official + expert sources
→ inspect actual relevant content
→ form candidate explanation
→ create minimal Blender experiment
→ test variants
→ measure evaluated result
→ encode candidate skill
→ return to soap dish
→ apply skill
→ verify improvement
```

This should become the first authentic bridge between:

```text
modeling
and
external professional learning
```

Do not force a research episode if the task is solved confidently with existing knowledge.

---

# 10. AFTER SOAP DISH — ACTUAL IMAGE REFERENCE MODELING BECOMES THE NEXT MAJOR PRIORITY

Text notes cannot be the permanent benchmark format.

After the subdivision milestone, build:

```text
actual image reference ingestion

object / component mask

landmarks

view classification

Blender-native silhouette rendering

wireframe / normals / depth as needed

reference-to-model comparison
```

Begin with clean references.

Suggested first visual benchmark:

```text
single-view stylized hard-surface object
clear silhouette
limited components
no hidden complicated geometry
```

Then progress toward:

```text
multi-view references
perspective references
concept-art ambiguity
```

---

# 11. BUILD A PROFESSIONAL MODELING-STAGE CONTROLLER

Explicitly track:

```text
REFERENCE ANALYSIS
PRIMARY BLOCKOUT
PROPORTION / SILHOUETTE
SECONDARY FORMS
TOPOLOGY / SURFACE QUALITY
TERTIARY DETAIL
PRODUCTION PREP
FINAL REVIEW
```

The planner should know the current stage.

Professional rule:

> Do not polish detail while the major form is still wrong.

Create stage gates.

Example:

```text
PRIMARY BLOCKOUT passes when:
major proportions are plausible
primary silhouette is sufficiently close
component layout is stable

TOPOLOGY/SURFACE passes when:
technical validity is acceptable
surface quality is acceptable
topology is contextually appropriate
```

This is a major efficiency improvement.

---

# 12. PROFESSIONAL PLANNER INPUT

Before each artistic decision, planner context should progressively include:

```text
task / reference

modeling stage

scene revision

control mode

base cage state

evaluated surface state when modifiers matter

persistent selection

semantic regions

local topology

viewport state

reference evidence

visual error tickets

applicable skills

recent accepted actions

recent rejected/rolled-back actions

current uncertainty

rollback availability
```

Planner output should remain one local decision.

Example:

```json
{
  "intent": "reduce basin-transition pinching",
  "stage": "TOPOLOGY_SURFACE",
  "target_region": "basin_upper_transition",
  "action": "move_selection",
  "expected_effect": {
    "evaluated_curvature_discontinuity": "decrease"
  },
  "verification": [
    "evaluated surface quality improves",
    "outer silhouette remains stable"
  ]
}
```

---

# 13. QUALITY MODEL: BASE CAGE + EVALUATED SURFACE + VISUAL RESULT

For modifier-driven assets, professional evaluation should separate three layers.

## A. Base-cage quality

```text
edge flow
pole placement
density
support topology
editability
persistent-ID integrity
```

## B. Evaluated-surface quality

```text
pinching
waviness
curvature continuity
surface smoothness
highlight flow proxy
evaluated validity
```

## C. Reference/appearance quality

```text
silhouette
proportion
landmarks
negative space
component relationship
```

A clean control cage with a bad evaluated surface fails.

A beautiful evaluated surface with unnecessarily chaotic control topology may also fail production-readiness criteria.

---

# 14. NEXT HELD-OUT BENCHMARK SEQUENCE

Do not return to Bottle, Flashlight, Mug, or Speaker.

Current sequence should be:

```text
1. SOAP DISH
first genuine subdivision-surface control-cage benchmark

2. ACTUAL IMAGE REFERENCE PROP
first real visual correction benchmark

3. KNOWLEDGE-GAP HELD-OUT PROP
intentionally likely to expose an unfamiliar topology/surface problem

4. SECOND ASSET USING LEARNED SKILL
prove transfer/generalization
```

After those, broaden asset families.

---

# 15. STOP USING ACTION COUNT AS A PRIMARY SUCCESS METRIC

Speaker reaching 20 decisions is useful evidence, but the project should now optimize for decision quality.

Track:

```text
quality improvement per accepted decision

reference error reduction per decision

percentage of decisions aligned with current modeling stage

rollback/recovery success

unnecessary action count

topology-quality improvement

evaluated-surface improvement

skill usefulness

human intervention count
```

A professional should often solve a problem with fewer better decisions.

---

# 16. PROFESSIONAL RESEARCH ACTIVATION RULE

The research system should now transition from "future mandatory subsystem" toward "available on demand."

Do not launch a huge crawler.

Implement the smallest practical research workflow needed to solve a real task.

Trigger when:

```text
existing skills do not confidently explain a defect
repeated repair attempts fail
sources/skills conflict
new workflow family appears
Blender behavior is unclear
```

Research should be problem-specific and return to the active asset.

---

# 17. FIRST KNOWLEDGE-ADAPTIVE PASS CRITERION

The first convincing PASS requires:

```text
real modeling problem encountered

internal knowledge search performed

gap recorded explicitly

good sources selected deliberately

weak sources rejected

source content actually inspected

candidate principle extracted

Blender experiment performed

result measured

skill encoded with limited confidence

original model resumed

skill retrieved

skill applied

original defect improves measurably

skill later tested on another shape
```

A tutorial summary alone does not count.

---

# 18. PROFESSIONAL CURRICULUM COVERAGE

The long-term curriculum remains:

```text
FORM / BLOCKOUT

HARD SURFACE

SUBDIVISION SURFACE

TOPOLOGY / RETOPOLOGY

SCULPT / ORGANIC

REFERENCE MATCHING

MATERIAL / UV / PRODUCTION PREP
```

Do not get trapped indefinitely in boxy hard-surface props.

However, master each workflow family sufficiently before broadening.

---

# 19. SOURCE CURRICULUM RULE

The vetted source library later in this document remains a seed, not a ceiling.

For every source:

```text
verify creator/source quality
verify demonstrated competence
inspect actual content
separate version-specific Blender behavior from timeless modeling principles
extract WHY
capture failure/recovery when available
test important claims
```

Do not promote knowledge based on popularity.

---

# 20. CURRENT DEVELOPMENT ORDER FROM `a0332746`

Default priority:

```text
P0 RECOVERY / STATE AUTHORITY
1. transaction-owned rollback
2. geometry/transform/modifier fingerprints
3. topology-preserving external-edit detection
4. immediate decision logging
5. preserve reconnect/idempotency guarantees

CURRENT MODELING MILESTONE
6. model the soap dish through typed operations
7. use base + evaluated mesh inspection continuously
8. expand local evaluated-surface diagnosis only when the task exposes a need
9. add typed operations only when the soap-dish decisions require them
10. trigger genuine problem-driven research only if existing knowledge is insufficient

NEXT PROFESSIONAL PERCEPTION MILESTONE
11. Blender-native visual passes
12. actual image-reference ingestion
13. silhouette / landmark comparison
14. localized visual error tickets
15. stage-aware planning
16. held-out image-reference model

ACTIVE LEARNING MILESTONE
17. problem-driven browser research
18. synchronized video/audio/frame study
19. Blender experiments
20. executable skill
21. return-to-original-task use
22. second-shape validation

PROFESSIONAL EXPANSION
23. deeper hard-surface proficiency
24. subdivision proficiency
25. retopology proficiency
26. sculpt/organic pipeline
27. materials/UV/production prep
28. broader held-out asset families
```

This ordering is about reaching professional ability, not completing a checklist for its own sake.

---

# 21. REQUIRED NEAR-TERM TESTS

## Rollback

```text
perform unacceptable typed edit
→ reject
→ restore exact pre-state
→ verify geometry, IDs, semantic regions
```

## External position edit

```text
record state
→ user moves existing vertices
→ IDs unchanged
→ divergence still detected
```

## SubD evaluated truth

```text
base cage remains coarse
→ Subdivision modifier active
→ evaluated probe reports actual dense result
```

## Local pinching diagnosis

Create or encounter a localized SubD defect and verify the system can identify the affected spatial region rather than only return a global max-angle number.

## Decision logging

Every new decision entry is written at decision time, not reconstructed in one batch afterward.

---

# 22. REQUIRED END-OF-SESSION REPORT

End every session with:

```text
STATUS: PASS / PARTIAL / FAIL

Current commit:
New commits:

Blender PID:
Modeler session ID:
Protocol version:
Blender restarts:

Active benchmark:
Current modeling stage:

Typed artistic decisions:
Accepted:
Rejected:
Rolled back:

Base-cage quality:
Evaluated-surface quality:
Visual/reference quality:

Semantic regions used:
Persistent-ID issues:

External edits detected:
Stale decisions rejected:

Skills searched:
Skills used:

Research triggered:
YES / NO

If YES:
problem:
queries:
sources selected:
sources rejected:
experiment:
skill status:
effect on original asset:

Human interventions:

Fallback execute_blender_code usage:
<count + reasons>

Failures discovered:
Claims disproved:

Evidence paths:

BIGGEST REMAINING GAP TO PRO MODELING:

HIGHEST-VALUE NEXT STEP:
```

The final two fields are mandatory.

Do not finish a session by saying only that infrastructure works.

# 23. THE PROFESSIONAL LEARNING SYSTEM IS MANDATORY

The system will not reach professional modeling ability from a tiny fixed skill library.

It must eventually become capable of learning from high-quality external sources.

External research is a REQUIRED subsystem.

However:

> Quality matters more than source count.

Do not gather random tutorials.

Do not treat all YouTubers, forum posts, comments, or blog posts as equivalent.

---

# 24. Source Selection Quality Gate

Before studying any external source, score it.

Suggested dimensions:

```text
AUTHOR_AUTHORITY
TECHNICAL_ACCURACY
VISUAL_CLARITY
EXPLANATION_OF_WHY
WORKFLOW_COMPLETENESS
PRODUCTION_RELEVANCE
RECENCY / VERSION RELEVANCE
REPRODUCIBILITY
COMMUNITY_REPUTATION
EVIDENCE QUALITY
```

Example score:

```json
{
  "source_id": "...",
  "authority": 0.9,
  "technical_accuracy": 0.9,
  "visual_clarity": 0.8,
  "explains_reasoning": 0.9,
  "production_relevance": 0.8,
  "version_relevance": 0.7,
  "overall": 0.84
}
```

Do not automatically reject old sources.

Many topology/modeling principles are version-independent.

But separate:

```text
timeless modeling principle
```

from:

```text
version-specific UI/API instruction
```

For version-specific facts, prefer current Blender documentation.

---

# 25. Source Trust Tiers

## Tier A — Primary / Authoritative

Use for technical facts:

- Blender Manual;
- Blender Python API;
- Blender Studio;
- Blender developer resources.

Claims from Tier A may still require version checking.

## Tier B — Established Professional Education

Use for:

- modeling strategy;
- topology reasoning;
- workflow choices;
- form judgment;
- production habits.

Examples include established educators/training platforms with long histories and clear demonstrations.

## Tier C — Technical Community Discussions

Examples:

- Blender Stack Exchange;
- Blender Artists;
- Polycount.

Use these to discover:

- edge cases;
- competing techniques;
- failure modes;
- real troubleshooting;
- context-dependent opinions.

Community answers are candidate evidence, not automatic truth.

## Tier D — Weak / Unverified

Examples:

- isolated comments;
- unsourced claims;
- short social posts;
- random tutorials with no demonstrated result.

Use only to generate hypotheses.

Never promote directly.

---

# 26. VETTED STARTING SOURCE LIBRARY

The links below are a STARTING CURRICULUM, not the entire future internet.

Claude may later discover other sources, but new sources must pass the same quality gate.

---

## 26.1 Official Blender Documentation — Highest Priority for Blender Behavior

### Blender Manual — Mesh Primitives

https://docs.blender.org/manual/en/latest/modeling/meshes/primitives.html

Use for:

- primitive behavior;
- creation parameters;
- foundational mesh facts.

Do not "learn artistic strategy" from this page. Use it for Blender truth.

### Blender Manual — Mesh Editing

https://docs.blender.org/manual/en/latest/modeling/meshes/editing/index.html

Use as the canonical map of mesh-editing operations.

For every typed command implemented in the modeler bridge:

1. inspect the corresponding manual section;
2. record Blender mode/preconditions;
3. identify operator parameters;
4. test actual behavior in current Blender;
5. encode typed command semantics.

### Blender Manual — Bevel Edges

https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bevel.html

Study:

- edge requirements;
- bevel width behavior;
- segments;
- geometry consequences.

Then create controlled tests.

### Blender Manual — Subdivision Surface Modifier

https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html

Study:

- Catmull-Clark;
- Simple subdivision;
- modifier order;
- creases;
- boundary behavior.

Use this as technical truth, then pair it with expert topology tutorials for artistic judgment.

### Blender Manual — Boolean Modifier

https://docs.blender.org/manual/en/dev/modeling/modifiers/generate/booleans.html

Study:

- Union;
- Difference;
- Intersect;
- solver behavior;
- manifold assumptions;
- known limitations.

Do not infer that a successful Boolean automatically produces production-quality final topology.

### Blender Manual — Modifier Index

https://docs.blender.org/manual/en/latest/modeling/modifiers/index.html

Use as a discovery/index source.

When Claude considers a modifier:

```text
modeling need
→ inspect modifier documentation
→ understand exact behavior
→ test in minimal Blender scene
→ decide whether it belongs in workflow
```

### Blender Manual — Selection Mirror

https://docs.blender.org/manual/en/latest/modeling/meshes/selecting/mirror.html

Useful for symmetry-selection behavior.

---

## 26.2 Blender Studio — Official Training

### Blender Studio

https://studio.blender.org/

Use Blender Studio as a high-trust source for:

- official production workflows;
- artist reasoning;
- Blender-native practices;
- production assets and breakdowns where available.

### Blender Fundamentals — Interface / Modeling Course

https://studio.blender.org/training/blender-2-8-fundamentals/interface-overview/

Although created for an older Blender version, the course provides a structured official foundation including:

- interface;
- object/edit mode;
- selection;
- extrude;
- loop cut;
- bevel;
- knife.

Important rule:

```text
OLD UI DETAIL
→ verify against current manual

MODELING CONCEPT
→ may remain useful
```

Do not discard high-quality older instruction merely because UI buttons moved.

---

## 26.3 Blender Guru — Structured General Blender Foundation

### Blender 5.0 Donut Tutorial Part 1

https://www.youtube.com/watch?v=-tbSCMbJA6o

Use as a CURRENT baseline for:

- Blender 5 interface;
- navigation;
- Edit Mode;
- selections;
- modifiers;
- subdivision;
- loop cuts;
- inset;
- basic form construction.

Do NOT simply follow the tutorial and store notes.

Study using the video-analysis protocol later in this document.

### Blender 4 Complete Beginner Course

https://www.youtube.com/watch?v=4haAdmHqGOw

Older than the Blender 5 course but useful because it covers a broad end-to-end pipeline and includes:

- modeling;
- subdivision;
- proportional editing;
- extrusion;
- solidify;
- reference-image modeling;
- technical checks;
- materials;
- rendering;
- production organization.

Version-specific UI instructions must be checked against current Blender.

---

## 26.4 CG Cookie — Modeling Fundamentals / Topology Judgment

CG Cookie is especially useful because its curriculum explicitly distinguishes tool usage from modeling judgment.

### CORE — Fundamentals of 3D Mesh Modeling

https://cgcookie.mavenseed.com/courses/core-fundamentals-mesh-modeling

Study the curriculum structure:

```text
general mesh modeling
→ hard surface
→ subdivision surface
```

Extract principles rather than copying one asset.

### What Is Good Topology?

https://www.youtube.com/watch?v=HKMGVMplGhE

This is a high-priority source because the project's Mug experience proved that:

```text
valid mesh != good topology
```

Extract its criteria for topology that serves:

- subdivision;
- deformation;
- editability;
- clarity;
- intended purpose.

Test those principles on multiple held-out shapes.

### Important Topology Tools

https://www.youtube.com/watch?v=Yh2zwe4tN24

Study how adding/removing/controlling geometry affects edge flow and future editability.

Do not only record shortcuts.

### Introduction to Retopology

https://cgcookie.com/courses/introduction-to-retopology

Use when the system reaches:

```text
sculpt/high-density source
→ need clean production mesh
```

Extract:

- edge-flow reasoning;
- loops;
- optimization;
- purpose-driven topology.

---

## 26.5 Blender Secrets — Focused Topology/Workflow Techniques

### 5 Minutes of Topology Tips

https://www.youtube.com/watch?v=V7Y-Il-7JFE

Useful for candidate micro-skills around:

- triangle rotation;
- reducing unnecessary quads;
- loop placement;
- loop straightening;
- smoothing/flattening.

Important:

Do NOT promote a short-tip video directly to production knowledge.

For each technique:

```text
observe exact technique
→ define preconditions
→ reproduce
→ test good case
→ test failure case
→ measure
→ promote or narrow
```

### Topology Secrets companion page

https://www.3dsecrets.com/secrets/topology-tips

Useful as a secondary text reference for the same topic.

### Double-Subdivision / Base-Mesh Technique

https://www.youtube.com/watch?v=13UN1Lju5Hs

Treat this as a candidate modeling strategy, not a universal solution.

Test:

- what types of shapes it handles well;
- what it handles poorly;
- topology quality;
- density;
- editability;
- subdivision behavior.

---

# 27. COMMUNITY SOURCES — USE FOR PROBLEMS, CONTRADICTIONS, AND EDGE CASES

---

## 27.1 Blender Stack Exchange

### Frequent Topology Questions

https://blender.stackexchange.com/questions/tagged/topology?tab=Frequent

High-value use:

```text
current topology problem
→ search relevant Stack Exchange question
→ inspect accepted/high-vote answers
→ identify assumptions
→ compare multiple answers
→ reproduce candidate technique
```

Do not blindly use the highest-voted answer.

### Active Subdivision Surface Questions

https://blender.stackexchange.com/questions/tagged/subdivision-surface?tab=active

Use when the modeler hits:

- pinching;
- topology artifacts;
- unexpected smoothing;
- modifier interaction issues.

### Topology Tag

https://blender.stackexchange.com/questions/tagged/topology

Use as a problem-driven search corpus.

Do not bulk-ingest every question.

---

## 27.2 Blender Artists

### Modeling Support Category

https://blenderartists.org/c/support/modeling/37

High-value because it contains:

- topology critique;
- workflow debate;
- troubleshooting;
- examples of context-dependent advice.

When using a thread:

1. inspect original mesh/problem;
2. inspect multiple responses;
3. identify agreements/disagreements;
4. identify responder evidence;
5. convert claims into hypotheses;
6. test them.

### Learning and Understanding Topology / Modeling discussions

Use the Modeling category search rather than trusting random isolated threads.

Example useful topic:

https://blenderartists.org/t/does-good-topology-matter-for-hard-surface-modeling/1543151

This is useful specifically because it demonstrates contextual reasoning:

```text
topology requirement
depends on
surface
lighting
deformation
workflow
final use
```

Another useful technical discussion:

https://blenderartists.org/t/how-to-create-this-kind-of-side-cut-in-hard-surface-modeling-with-good-topology/1482837

Use this kind of source to study:

- problem framing;
- multiple topology solutions;
- subdivision failure;
- local vs global topology decisions.

Do not copy one user's mesh verbatim into a skill.

---

## 27.3 Polycount

Polycount is valuable for production-oriented topology discussions across software packages.

The key principle:

> Polygonal modeling principles are often transferable even when the tutorial uses software other than Blender.

Claude should not reject a strong topology explanation only because it was demonstrated in another DCC.

However:

```text
DCC-specific controls
→ translate/test in Blender

general topology principle
→ test for Blender workflow applicability
```

Search Polycount problem-first rather than scraping the forum broadly.

---

# 28. Hard-Surface Learning Strategy

Do not learn "hard surface" as one trick.

Build skills across these families:

```text
primary-form blockout
component separation
bevel strategy
boolean strategy
subdivision strategy
support topology
hard/soft edge control
normal/shading management
panel/detail construction
curved hard-surface transitions
holes/cutouts
cylindrical topology
symmetry
repetition
retopology
density control
final cleanup
```

For each family maintain:

```text
principles
good examples
failure examples
Blender experiments
executable skills
runtime evidence
```

---

# 29. Subdivision-Surface Learning Strategy

The system must understand more than:

```text
add subdivision modifier
```

It must learn:

- control cage design;
- support-loop placement;
- pole placement;
- transitions;
- curvature continuity;
- cylindrical forms;
- corner behavior;
- holes/cutouts;
- where triangles/ngons are harmless vs harmful;
- density management;
- modifier stack effects.

Use a combination of:

```text
Blender Manual
+
CG Cookie topology curriculum
+
Blender Secrets micro-techniques
+
Stack Exchange/Blender Artists edge cases
+
controlled experiments
```

No one source should dominate.

---

# 30. Organic / Sculpt / Retopology Path

Professional generalization eventually requires non-hard-surface workflows too.

Do not build this before the core modeler is reliable, but preserve the path:

```text
basic mesh modeling
→ subdivision organic forms
→ sculpting
→ retopology
→ production topology
```

When this phase begins:

- prioritize official Blender sculpt documentation;
- use established structured sculpting courses;
- use CG Cookie retopology as a foundation;
- add deformation-aware topology resources;
- evaluate on held-out organic forms.

Do not mix deformation-topology requirements with static hard-surface rules.

---

# 31. SOURCE DISCOVERY POLICY

Claude may use web/browser search when:

- an unfamiliar problem appears;
- two skills conflict;
- repeated fixes fail;
- confidence is low;
- a new workflow is required;
- Blender behavior is unclear;
- a held-out asset exposes a knowledge gap.

Research query should describe the real problem.

Example:

```text
current defect:
subdivision pinching at curved corner

queries:
"Blender subdivision curved corner pinching topology"
"Blender support loops curved corner pinching"
site:blender.stackexchange.com subdivision pinching curved corner
site:blenderartists.org subdivision topology curved corner
```

Search multiple source classes:

```text
official docs
expert education
technical Q&A
community forum
video
```

Do not search only YouTube.

---

# 32. SOURCE DIVERSITY RULE

For an important new technique, prefer evidence from at least two different source classes where available.

Example:

```text
Blender Manual
+
expert tutorial

or

expert tutorial
+
Stack Exchange discussion

or

Blender Studio
+
controlled experiment
```

If all sources simply repeat one unsupported claim, confidence should remain low.

---

# 33. VIDEO STUDY PROTOCOL — CRITICAL

A video is not learned because Claude read its title or transcript.

Before claiming a video was studied, record available modalities:

```json
{
  "playback_access": true,
  "frames_available": true,
  "audio_available": true,
  "captions_available": true,
  "transcript_available": true
}
```

Never say:

```text
"watched"
"observed visually"
"heard"
```

unless the actual modality was accessed.

---

# 34. Video Analysis Pass 1 — Coarse Segmentation

Process at coarse intervals or chapters.

Goal:

- find actual modeling sections;
- skip intros/sponsors/render-only sections when irrelevant;
- identify technique changes;
- identify failures/rework;
- identify final review.

Typical coarse interval:

```text
5–15 seconds
```

or chapter boundaries.

Output:

```json
{
  "start": 210.0,
  "end": 355.0,
  "episode": "constructing curved transition",
  "priority": "HIGH"
}
```

---

# 35. Video Analysis Pass 2 — Fine Action Study

For high-priority modeling segments, inspect at much finer intervals.

Typical:

```text
0.25–1 second
```

when exact actions matter.

For each atomic action capture where observable:

```text
timestamp
mode
view
selection
active object
tool/operator
transform
modifier
visible geometry change
spoken explanation
inspection afterward
```

Example:

```json
{
  "time": 422.8,
  "mode": "EDIT_MESH",
  "selection": "edge_loop",
  "action": "move support loop outward",
  "visible_effect": "corner transition broadens",
  "speech_relation": "explains_current_action"
}
```

---

# 36. Speech ↔ Action Alignment

Classify spoken statements:

```text
predicts_next_action
explains_current_action
explains_previous_action
general_advice
self_correction
tradeoff
uncertain
```

Important distinction:

```text
"Press Ctrl+B"
```

is tool use.

```text
"I moved this support edge away because the corner was pinching"
```

contains transferable modeling reasoning.

Prioritize the second.

---

# 37. Learn Human Judgment From Videos

Capture moments where the artist:

- stops to inspect;
- rotates the view;
- checks silhouette;
- toggles subdivision;
- switches wireframe;
- undoes;
- rejects a result;
- moves topology;
- chooses separate geometry;
- changes strategy;
- simplifies a region;
- says something is "good enough";
- identifies a shading problem.

These are often more valuable than shortcut sequences.

Professional modeling is decision making.

---

# 38. Capture Mistakes and Recovery

Do not sanitize tutorials into only successful actions.

Record:

```text
attempt
→ defect
→ diagnosis
→ undo/rebuild/repair
→ new result
```

Example candidate skill:

```text
If support topology produces visible pinching near a curved transition,
inspect loop proximity before increasing subdivision density.
```

But do not promote until tested.

---

# 39. Modeling Episode Format

Group video actions into episodes.

Example:

```json
{
  "episode_id": "ep_014",
  "goal": "create clean curved hard-surface transition",

  "initial_state": {},

  "actions": [],

  "spoken_explanations": [],

  "inspection_behavior": [],

  "mistakes": [],

  "recovery": [],

  "final_state": {},

  "candidate_principles": [],

  "uncertainties": []
}
```

---

# 40. Four Knowledge Layers — NEVER MIX

## 1. Source Observation

What was actually observed.

Example:

```text
The instructor moved the support loop farther from the corner.
```

## 2. Interpretation

```text
Increasing support-loop distance may reduce the observed pinching.
```

## 3. Experimental Evidence

```text
On three test meshes, increasing distance reduced measured curvature distortion.
```

## 4. Executable Skill

```text
Under these preconditions, inspect support-loop spacing and adjust locally according to this policy.
```

A video statement does not automatically become layer 4.

---

# 41. CONTROLLED BLENDER EXPERIMENTS

Before promoting important modeling knowledge:

```text
candidate principle
→ minimal test scene
→ controlled variants
→ measurements
→ failure case
→ conclusion
```

Example:

Hypothesis:

```text
support loops placed too close to a curved corner intensify pinching
```

Experiment:

```text
A: no support loop
B: moderate distance
C: extremely close distance
```

Measure:

- curvature;
- silhouette;
- normal variation;
- edge density;
- topology complexity.

Save:

- initial `.blend`;
- variant `.blend`s;
- parameters;
- metrics;
- screenshots/Blender-native visual artifacts if useful;
- conclusion.

---

# 42. SKILL FORMAT

Promoted skills must be executable and contextual.

Example:

```json
{
  "skill_id": "subd.curved_transition.support_loop_spacing",

  "applicability": {
    "workflow": "subdivision",
    "surface": "curved",
    "defect": "pinching"
  },

  "preconditions": [],

  "required_observations": [],

  "action_policy": [],

  "expected_effects": [],

  "success_predicates": [],

  "failure_predicates": [],

  "recovery": [],

  "sources": [],

  "experiments": [],

  "runtime_usage": [],

  "status": "EXPERIMENTALLY_TESTED"
}
```

No promoted skill should exist only as prose.

---

# 43. SKILL PROMOTION LIFECYCLE

```text
CAPTURED
→ INTERPRETED
→ CANDIDATE
→ EXPERIMENTALLY_TESTED
→ BENCHMARK_SUPPORTED
→ RUNTIME_VALIDATED
→ PROMOTED
```

Also:

```text
CONTRADICTED
DEPRECATED
VERSION_LIMITED
INSUFFICIENT_EVIDENCE
```

Never erase contradictory evidence.

Refine applicability.

---

# 44. CONTRADICTION HANDLING

Modeling advice often appears contradictory:

```text
"always use quads"

vs

"triangles are fine"
```

Do not choose a side from popularity.

Ask:

```text
static?
deforming?
subdivision?
flat surface?
curved surface?
game low-poly?
high-poly?
boolean intermediate?
final topology?
visible silhouette?
```

Knowledge should become conditional.

---

# 45. KNOWLEDGE MUST RETURN TO LIVE MODELING

A learning episode is incomplete until the skill is used.

Required:

```text
problem on real model
→ research
→ experiment
→ skill
→ return to model
→ retrieve skill
→ apply skill
→ verify result
```

Store runtime usage:

```json
{
  "skill_id": "...",
  "decision_id": "...",
  "scene_revision_before": 811,
  "scene_revision_after": 812,
  "successful": true,
  "measured_effect": {}
}
```

---

# 46. LEARN FROM OWN SESSIONS

After every meaningful modeling run, mine:

- successful decisions;
- failed decisions;
- undos;
- repairs;
- rejected skill retrievals;
- successful skill retrievals;
- topology regressions;
- visual regressions;
- inefficient workflows;
- repeated mistakes;
- human corrections;
- unexpected external edits.

Human corrections are evidence, not automatically truth.

Form a hypothesis.

Replay/test before changing a promoted skill.

---

# 47. CURRICULUM ORDER

Do not attempt every modeling domain simultaneously.

Recommended learning progression:

```text
A. Blender operation fundamentals
B. topology fundamentals
C. simple hard-surface forms
D. subdivision-surface modeling
E. reference-based hard-surface props
F. topology repair/retopology
G. complex stylized props
H. sculpting/organic fundamentals
I. sculpt → retopology
J. materials/UV/production preparation
K. broader asset classes
```

Within hard-surface/stylized prop modeling, expand gradually:

```text
simple boxy prop
→ cylindrical prop
→ multi-component prop
→ curved hard-surface prop
→ complex transition topology
→ stylized design
→ unseen held-out prop
```

---

# 48. DO NOT OVERFIT TO ONE EDUCATOR

No YouTube channel becomes "the truth."

For major workflows compare:

```text
official technical documentation
+
one or more established educators
+
community edge cases
+
own Blender experiments
```

The final skill belongs to the system's evidence base, not to an influencer.

---

# 49. DO NOT MASS-INGEST BEFORE RUNTIME CAN USE KNOWLEDGE

Bad sequence:

```text
download 500 videos
→ create 100,000 notes
→ runtime still cannot use one skill
```

Correct sequence:

```text
closed-loop modeler
→ small validated skill library
→ runtime retrieves/uses skills
→ problem-driven browser research
→ video understanding
→ experiments
→ self-learning
→ larger curriculum
```

---

# 50. NEXT MODELING BENCHMARK

The immediate current benchmark is now:

```text
smooth rounded soap dish
```

This is the project's first genuine subdivision-surface control-cage task.

Its purpose is not "make a soap dish."

Its purpose is to prove:

```text
base control cage reasoning
+
modifier-evaluated surface reasoning
+
support-loop / pole / edge-flow judgment
+
smooth basin transition
+
adaptive correction of real SubD defects
```

Use the current `reference/soap_dish/notes.md` as the held-out brief.

Do not pre-specify the exact topology.

If the task exposes an unresolved real SubD problem, allow the first genuine problem-driven research episode using the vetted source policy in this document.

After the soap dish, the next benchmark must use an **actual image reference**, not only structured text notes.

Then require:

```text
reference image
→ visual decomposition
→ blockout
→ Blender-native silhouette comparison
→ local correction
→ topology/surface review
→ independent final verification
```

Do not return to previous benchmark assets for the next capability claim.

# 51. PROFESSIONAL BENCHMARK LADDER

## Stage 1 — Reliable Blender Operator

Can reliably mutate one persistent Blender session.

## Stage 2 — Closed-Loop Modeler

```text
observe
→ decide
→ edit
→ evaluate
→ adapt
```

## Stage 3 — Reference-Based Modeler

Can model unseen simple references.

## Stage 4 — Competent Stylized / Hard-Surface Modeler

Repeatedly completes clean unseen props.

## Stage 5 — Knowledge-Adaptive Modeler

Can:

```text
unknown problem
→ research
→ experiment
→ learn
→ return
→ continue
```

## Stage 6 — Proficient Specialist

Produces strong editable assets in a focused modeling domain with limited intervention.

## Stage 7 — Broader Professional Modeler

Generalizes across multiple workflows and asset classes.

Do not call one successful prop "professional-level."

---

# 52. HELD-OUT EVALUATION

Never evaluate a capability using assets whose:

- dimensions;
- topology;
- action sequence;
- decomposition;
- special helper functions;
- repair recipe

were developed specifically for that evaluation.

Maintain hidden/held-out references.

The modeler should encounter them only at evaluation time.

---

# 53. PROFESSIONAL METRICS

Track separately:

## Technical validity

- non-manifold count;
- loose geometry;
- degenerate faces;
- normals;
- zero-length edges.

## Topology quality

- valence distribution;
- pole placement by region;
- triangle/ngon placement by region;
- face-area ratio;
- edge-length ratio;
- density;
- subdivision behavior;
- editability.

## Visual quality

- silhouette IoU;
- contour error;
- landmarks;
- proportions;
- component relationships;
- visual hierarchy.

## Process quality

- decisions;
- accepted;
- rejected;
- undone;
- repaired;
- human interventions;
- stale-command attempts;
- Blender restarts;
- recovery success.

## Learning quality

- skills retrieved;
- skills actually used;
- successful reuse;
- cross-asset reuse;
- research episodes;
- experiments;
- contradicted skills;
- promoted skills.

---

# 54. STRICT ANTI-FAKE-PROGRESS RULES

Never count as professional-modeler progress:

```text
complete asset generated by one bpy/BMesh script

asset-specific builder

100 precomputed operations presented as 100 decisions

helper that encodes substantial artistic design

manual revision bump used as proof that Blender changed

technical validity presented as professional topology

desktop screenshot used for facts Blender can expose directly

tutorial summary marked as learned skill

forum advice promoted without testing

human correction attributed to the agent

benchmark threshold changed after seeing result

result accepted only because no exception occurred
```

Keep failures visible.

---

# 55. IMMEDIATE IMPLEMENTATION ORDER FROM CURRENT MAIN

As of commit `a0332746c2cfb39527ad4e74115af3e073f74714`, many older directive items are already implemented.

Do not repeat them.

Proceed roughly in this order:

```text
1. verify current live modeler protocol and soap-dish starting state

2. implement transaction-owned rollback for typed artistic decisions

3. improve external-edit fingerprints beyond persistent-ID set changes

4. ensure decision logs are written immediately per decision

5. keep reconnect / command idempotency / persistent-ID invariants passing

6. begin soap-dish SubD benchmark

7. use evaluated_mesh_health / evaluated_surface_quality throughout

8. add only the typed operation(s) the real SubD task proves necessary

9. localize evaluated-surface defects to actionable control-cage regions

10. if a real unresolved SubD problem occurs:
    trigger targeted external research
    → source selection
    → experiment
    → skill
    → return to soap dish

11. independently evaluate the soap dish:
    base cage
    evaluated surface
    technical validity

12. build Blender-native visual passes

13. ingest an actual held-out image reference

14. implement silhouette/landmark comparison

15. add modeling-stage controller

16. model the first image-reference asset adaptively

17. activate regular problem-driven research-to-skill behavior

18. validate learned skills on second held-out shapes

19. expand toward professional proficiency across:
    hard surface
    subdivision
    retopology
    sculpt/organic
    production prep
```

The objective is no longer to maximize infrastructure completeness.

The objective is to continuously remove the largest gap between the current system and a proficient professional modeler.

# 56. NEXT-SESSION ENGINEERING TESTS

Required:

## Edit Mode truth

```text
Edit Mode mutation
→ no mode exit
→ direct query sees true topology
```

## External GUI edit

```text
agent observes revision N
→ user edits Blender
→ bridge emits revision N+1
→ stale agent command rejected
```

## Persistent IDs

```text
remember region A
→ edit unrelated B
→ surviving A identities stable
```

## Duplicate custom IDs

```text
topology-generating operator
→ verify uniqueness
→ repair if needed
```

## Duplicate command retry

```text
command X executes
→ response lost
→ X retried
→ no duplicate mutation
```

## Reconnect

```text
client disconnects
→ Blender remains running
→ reconnect same PID/session
→ continue
```

---

# 57. REQUIRED END-OF-SESSION REPORT

```text
STATUS: PASS / PARTIAL / FAIL

Git commits:

Blender PID:
Blender session:
Blender restarts:

Protocol version:

Implemented:

Mode-correct live state:
Persistent-ID selection:
Blender-originated revision:
Push events:
External GUI edit detection:
Typed commands:
Idempotent commands:
Heartbeat:
Reconnect:
User/agent ownership:

Tests:

Edit Mode truth:
External GUI mutation:
Stale command rejection:
Persistent-ID stability:
Duplicate-ID repair:
Duplicate command retry:
Reconnect without restart:

Arbitrary execute_blender_code calls:
Reasons:

Human interventions:

Known limitations:

Evidence paths:

Next recommended milestone:
```

Do not mark undocumented/unverified code PASS.

---

# 58. RESEARCH SESSION REPORT

When a research-learning episode is performed, report:

```text
Problem:

Why internal knowledge was insufficient:

Search queries:

Sources considered:

Sources rejected:
- source
- reason

Sources selected:

Source trust tier:

Video modalities actually available:

Direct observations:

Interpretations:

Contradictions:

Candidate hypotheses:

Blender experiments:

Measured results:

Skill created/updated:

Promotion status:

Returned to original asset:
YES / NO

Runtime skill used:
YES / NO

Measured effect on original task:

Remaining uncertainty:
```

---

# 59. FINAL BEHAVIOR TARGET

The eventual interaction should resemble:

```text
USER
provides unseen digital reference

CLAUDE
studies design and decomposes forms

BLENDER
reports exact state and viewport

CLAUDE
chooses primary-form operation

BLENDER
performs typed operation
emits revision/delta

CLAUDE
evaluates result
compares reference

...

CLAUDE
encounters topology problem
internal retrieval confidence low

CLAUDE
searches official docs + expert tutorial + technical forum discussion

CLAUDE
studies actual visual/audio tutorial segment
extracts candidate principle

CLAUDE
creates temporary Blender experiment
tests variants
measures result

CLAUDE
creates candidate skill

CLAUDE
returns to original model
retrieves skill
applies it

BLENDER
reports improvement

CLAUDE
continues

...

independent verifier
checks topology/validity

visual evaluator
checks reference quality

editable .blend delivered
```

That is the end goal.

---

# 60. FINAL RULE

The project must become a MODELING SYSTEM, not a tutorial collector.

External resources matter because professionals build expertise from:

```text
documentation
demonstration
practice
critique
failure
experimentation
experience
```

The autonomous system must reproduce that learning process.

Every new source must answer:

> Is this source authoritative, clear, relevant, reproducible, and useful for a real modeling decision?

Every new piece of knowledge must answer:

> Was it observed, tested, used, and verified?

Every new feature must answer:

> Does it make the system better at continuously observing, understanding, deciding, modeling, verifying, recovering, researching, or learning in Blender?

If not, do not build it yet.




# 61. CURRENT PROFESSIONAL-LEVEL EXIT CRITERIA

The system should not be called "pro-level" based on a single good-looking asset.

A credible proficient-specialist claim requires repeated held-out evidence.

Minimum direction for a future professional benchmark suite:

```text
MULTIPLE UNSEEN REFERENCES
different topology families
different proportions
different component structures

NO PREBUILT ACTION RECIPES

LOW HUMAN INTERVENTION

STRONG VISUAL MATCH

CONTEXTUALLY GOOD TOPOLOGY

EDITABLE / ORGANIZED .BLEND

RECOVERY FROM REAL FAILURES

EFFICIENT DECISION COUNT

KNOWLEDGE REUSE

AT LEAST ONE UNKNOWN PROBLEM
researched
experimentally solved
applied back to original asset
```

Evaluation should include both machine metrics and independent review criteria modeled after professional concerns:

```text
silhouette
proportion
form hierarchy
surface quality
topology appropriateness
editability
modifier organization
scene organization
reference fidelity
unnecessary complexity
production readiness
```

The benchmark must include several assets rather than one.

---

# 62. FINAL DEVELOPMENT QUESTION

At every milestone, ask:

> What is the biggest thing a proficient professional modeler would notice, understand, or do here that this system still cannot?

Examples:

```text
Would a pro notice the primary form is wrong before adding detail?

Would a pro choose a different modeling strategy entirely?

Would a pro recognize that technically valid topology is ugly?

Would a pro rotate the view and inspect highlight flow?

Would a pro stop patching and rebuild the region?

Would a pro know what to search for when uncertain?

Would a pro judge a tutorial source as weak?

Would a pro transfer a technique from one asset to another?

Would a pro avoid wasting ten edits on a problem that needs one strategic change?
```

Use the answer to choose the next development task.

That is the guiding principle from this point forward.

The repository already has substantial control infrastructure.

The remaining journey is increasingly about **modeling intelligence, visual judgment, topology judgment, strategic choice, recovery, and validated learning**.

Do not let infrastructure work become a comfortable substitute for teaching the system to actually model well.
