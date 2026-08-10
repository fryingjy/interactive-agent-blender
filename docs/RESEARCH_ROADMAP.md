# Autonomous Research & Expertise Acquisition — Mandatory Future Subsystem

**Status: active foundation phase. The closed-loop runtime has substantial demonstrated evidence,
and controlled documentation/experiment work has begun. Legal local video/document ingestion,
structured retrieval, usage telemetry, uncertainty, and rebuild-decision foundations are now
implemented and tested; external curriculum breadth and cross-asset promotion remain incomplete.
Research should stay problem-driven and should not outrun the runtime's ability to apply and
verify what it learns.**

## Why this exists

`docs/EXPERIENCED_MODELER_TARGET.md`-style ambition (from the project's own history) keeps
running into the same wall: a fixed internal skill library cannot cover every modeling problem
the system will eventually face. The long-term system must be able to recognize "I don't
currently know enough to solve this confidently" and independently go acquire that knowledge —
then close the loop by actually applying it to the task that triggered the search.

## Sequencing rule (binding)

```
demonstrated base: observe -> decide -> act -> verify -> adapt
                   (see runs/2026-08-07_decision-cycles/, tools/decision_log.py)
        |
        v
strengthen runtime reliability + foundation breadth
        |
        v
problem-driven research + controlled experiments
        |
        v
structured retrieval, legal video ingestion, and cross-asset validation
```

Do not mass-ingest sources merely to increase counts. Add research capabilities only when the
closed-loop runtime can apply, verify, reject, and retain their output. See "Research breadth
should grow with modeling ability" below.

## Target behavior

```
modeling problem encountered
  -> search existing internal knowledge (knowledge/skill_store.py)
  -> sufficient? YES -> use it
                  NO  -> research externally (docs, tutorials, forums, video)
                         -> compare claims across sources
                         -> form candidate techniques
                         -> test techniques inside Blender (controlled experiment)
                         -> measure results
                         -> encode successful technique as executable knowledge
                         -> return to the original modeling task
                         -> apply the newly learned technique
                         -> verify whether it actually solved the problem
```

Research is **problem-driven**, not breadth-driven. It should normally originate from: an
unknown modeling problem, a failed action, a repeated repair failure, a low-confidence decision,
conflicting retrieved skills, a new technique requirement, a benchmark weakness, or a new asset
class. Never "crawl N videos to grow the knowledge base" for its own sake.

Search queries are generated from the actual modeling state and defect (e.g. "subdivision
pinching around a curved hard-surface corner" -> `"Blender subdivision pinching curved corner
topology"`, `site:blender.stackexchange.com subdivision corner pinching`,
`site:blenderartists.org subdivision topology pinching`), not a static source list.

## Source hierarchy

- **Tier A — primary/authoritative**: Blender Manual, Blender Python API docs, Blender Studio,
  official developer info. Use for operator/modifier/API behavior, version differences,
  technical definitions.
- **Tier B — established expert education**: experienced modeling educators, professional
  workflows. Use for strategy, topology decisions, workflow efficiency, artistic reasoning.
- **Tier C — technical community discussion**: Blender Stack Exchange, Blender Artists,
  Polycount, developer forums. Valuable for unusual problems and competing approaches, but
  claims must not automatically become facts.
- **Tier D — weak/unverified**: isolated comments, short posts, unsourced claims. Can generate
  hypotheses only, with low initial confidence.

## Video understanding is mandatory (once built)

Title/description/thumbnail/transcript-alone is not equivalent to watching the tutorial. Combine
visual frames + audio/captions/transcript + timestamps to learn what operation happened, what was
selected, what mode was active, what changed, *why* the artist did it, what they rejected/undid,
how they repaired it, what tradeoff they discussed. The WHY matters as much as the shortcut.

Pipeline: video discovery -> metadata -> audio/caption/transcript -> coarse segmentation ->
detect important episodes -> fine frame analysis -> align speech with visible actions -> extract
decisions/mistakes/recovery -> derive hypotheses -> Blender experiments -> validated executable
skills. Example candidate record:

```json
{
  "source": "...", "time_range": [412.3, 438.8],
  "problem": "subdivision corner pinching",
  "observed_state": {"workflow": "subdivision", "region": "corner"},
  "observed_actions": ["move support loop farther from corner"],
  "spoken_reason": "the loop is too close and is creating pinching",
  "visible_result": "surface transition becomes smoother",
  "candidate_principle": "support-loop proximity affects transition width and can intensify corner pinching",
  "confidence": 0.82
}
```
Remains a candidate until experimentally tested.

Implemented foundation: `knowledge_engine/ingest/video_ingest.py` accepts only explicitly
approved local roots, probes real video/audio streams through PyAV, parses local VTT/SRT
captions, and extracts timestamped frames. `runs/2026-08-10_video-ingestion/` exercises the full
path on a project-owned MP4 with audio and captions. This proves modality access and extraction,
not outside tutorial expertise. The module deliberately contains no platform downloader.

`knowledge_engine/ingest/document_ingest.py` restricts local reads to approved roots, extracts
headings/parameter-warning candidates/links, fingerprints content, and emits a normalized source
record. Approved web fetches require a hostname allowlist and reject redirects outside it.

## Structured retrieval and learning state

`knowledge_engine/retrieval.py` ranks both historical and promoted skill schemas using query,
modeling stage, workflow, surface, defect, local topology, modifier state, reference issue,
runtime success, and Blender-version relevance. Ranking exposes a score breakdown for audit.
`knowledge/skill_store.py search-structured` is the CLI entry point.

`knowledge_engine/telemetry.py` stores append-only skill usage with decision/asset IDs, scene
revision change, action, result, measured effect, and unexpected effects. `reasoning.py` adds
explicit diagnosis confidence, evidence-based region rebuild pressure, multi-view regression
checks, and component-graph validation. Unit tests cover these mechanisms; real cross-session
runtime use remains required before broad promotion claims. A first controlled use now exists in
`runs/2026-08-10_knowledge-use/`: structured retrieval selected the historical material-slot
skill, one revision-linked mutation reduced orphan slots from one to zero, and telemetry fed the
measured success back into future ranking. This is one narrow use, not general runtime maturity.

## Four knowledge layers — never mix

1. **Source Observation** — what was actually seen/read/heard ("the presenter moved this edge
   loop outward").
2. **Interpretation** — what the system thinks that means ("moving the loop outward may reduce
   pinching").
3. **Experimental Evidence** — what happened when reproduced ("three test meshes showed lower
   curvature distortion").
4. **Executable Skill** — the actual behavior available to the live modeler ("when these
   preconditions exist, inspect support-loop distance and adjust per this policy").

## Skill promotion lifecycle

```
CAPTURED -> INTERPRETED -> CANDIDATE -> EXPERIMENTALLY_TESTED -> BENCHMARK_SUPPORTED
         -> RUNTIME_VALIDATED -> PROMOTED
```
Also: `CONTRADICTED`, `DEPRECATED`, `VERSION_LIMITED`, `INSUFFICIENT_EVIDENCE`. Never silently
overwrite conflicting evidence — represent knowledge conditionally (subdivision vs. static vs.
deforming vs. game mesh vs. boolean intermediate vs. final topology, etc.) rather than forcing
one universal answer when sources disagree (e.g. "always quads" vs. "triangles are fine here").

## Controlled Blender experiments

Before promoting a technique: form a hypothesis, build variants (e.g. no support loop / moderate
distance / extremely close), measure (surface curvature, min edge ratio, normal variation,
silhouette difference, topology complexity), and store the starting `.blend`, ending `.blend`,
parameters, measurements, conclusion, and source links — this is the evidence trail the same way
`runs/*/verify_reports/` already works for Proof 7.

## Must return to the original task

Research -> notes -> abandon the model is the failure mode to avoid. Required:
`problem -> research -> experiment -> skill acquired -> return to the original Blender
session/model -> apply skill -> measure improvement -> continue modeling`. This mirrors the same
discipline already enforced for decision cycles by `blender_ops/decision_state.py`/
`tools/decision_log.py`: no batching, no abandoning the loop, always close the cycle.

## Learn from its own sessions too

External sources aren't the only source of expertise. Learn from the project's own successful
actions, failed actions, undo sequences, repair attempts, wrong skill retrievals, unexpected
topology changes, visual regressions, successful topology patterns, inefficient workflows, and
repeated mistakes. Example: a repair skill succeeds on 3 assets and fails on a 4th at a mirror
boundary -> hypothesis: "works normally but needs different behavior at mirror seams" -> test
that hypothesis before modifying the skill, don't just patch blindly.

## Professional-level end goal (not just "control Blender" or "produce valid meshes")

Given an unseen reference or brief, autonomously produce work approaching a proficient
professional's judgment, cleanliness, adaptability, and efficiency — form judgment (primary/
secondary/tertiary forms, proportion, silhouette, shape language), modeling strategy (box/surface/
subdivision/boolean/bevel/mirror/manual-topology/retopology/separate-components, chosen
appropriately), topology judgment (edge flow, support topology, poles, density, deformation,
subdivision behavior, shading), workflow judgment (what to solve now vs. postpone vs. simplify vs.
separate vs. rebuild vs. accept as good enough), self-critique (recognizing bad proportions, weak
silhouette, pinching, shading artifacts, over-density, bad relationships, reference mismatch), and
recovery (a professional doesn't avoid every mistake, but recognizes and recovers from them
quickly — same spirit as this project's mistake-detect-and-repair proofs).

### Benchmark ladder (each stage demonstrated with held-out tasks)

1. Reliable Blender operator
2. Closed-loop modeler (observe -> decide -> edit -> evaluate -> adapt) — **current milestone**
3. Reference-based modeler (unseen simple reference)
4. Competent hard-surface/stylized modeler (clean unseen props)
5. Knowledge-adaptive modeler (research + learn + continue on an unfamiliar problem)
6. Proficient specialist (strong editable assets in a chosen domain, little intervention)
7. Broader professional modeler (generalizes across asset categories/workflows)

**Held-out evaluation is mandatory**: never evaluate a stage using objects whose actions,
dimensions, topology, decomposition, or helper code were touched during development of that
stage's capability. Maintain references the agent only sees at evaluation time — this is what
stops benchmark-specific engineering from masquerading as modeling intelligence. (Directly
relevant to this project's own Proof 6 "unseen prop" discipline — no prep files staged in
advance.)

### Research breadth grows with modeling ability, in this order — do not reverse

```
closed-loop runtime works -> small internal skill library works -> problem-driven browser
research -> documentation ingestion -> forum research -> video understanding -> controlled
experimentation -> self-session learning -> cross-asset skill generalization
```

## Final target architecture

```
External Knowledge (Docs/Web/YouTube/Forums/Training)
        v
Research/Learning (observe -> hypothesize -> experiment -> validate)
        v
Knowledge/Skills  <---- Reference
        v
Modeling Planner
        v
OBSERVE / DECIDE  <-----------------------------.
        v                                        |
Modeler Runtime (transactions, verification,     |
                 recovery)                       |
        v                                        |
Blender Direct Add-on / MCP Layer                |
        v                                        |
Persistent Blender Session                       |
        v                                        |
      result  ------------------------------------
```

The learning system and the modeling system are meant to eventually operate as one continuous
system, not two separate projects bolted together.
