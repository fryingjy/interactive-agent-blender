# Knowledge system

## Purpose

Knowledge must improve a modeling decision. Tutorial collection, transcripts, or notes alone do not
count as learned capability.

```text
task gap
-> retrieve existing knowledge
-> research an allowed source when needed
-> separate observation from interpretation
-> reproduce in a controlled Blender lab
-> retain failures and measure outcomes
-> test on a different shape
-> apply to the task that triggered research
-> log runtime use and revise confidence
```

## Knowledge locations

- `knowledge/foundation/source_registry.json` — normalized source identity, access modalities,
  trust, version, experiments, and limitations.
- `knowledge/foundation/operator_cards/` — concise executable guidance and bounded evidence.
- `knowledge/foundation/topic_coverage_matrix.md` — docs/video/experiment/failure/quiz/runtime/
  second-shape coverage.
- `knowledge/foundation/quizzes/` — retrieval and retention checks performed without copying notes.
- `knowledge/skills/` — runtime-oriented learned skills with applicability boundaries.
- `knowledge/foundation/progressive_prop_benchmark_curriculum.json` — current capability gate;
  [GOAL.md](GOAL.md) is its living execution roadmap.

Structured runtime retrieval uses a calibrated default score floor and may return no skill. That
abstention is intentional: weak lexical overlap must not turn an unrelated ticket into an executable
hint. Use `tools/knowledge_skills.py search-structured --min-score ...` only to lower the floor for
explicit exploratory search, never silently for planner mutations. The frozen positive/negative
regression cases live in `knowledge/foundation/retrieval_benchmark_cases.json`.

## Source hierarchy

1. current Blender Manual, Python API, official training, and developer information;
2. established professional educators;
3. serious technical communities;
4. weak or isolated advice as low-confidence hypotheses only.

Video credit requires actual accessible modalities. Titles, descriptions, thumbnails, or transcripts
alone are not equivalent to visual study. Record whether frames, audio, captions, transcripts, and
chapters were available.

## Promotion lifecycle

```text
CAPTURED
-> INTERPRETED
-> CANDIDATE
-> EXPERIMENTALLY_TESTED
-> TRANSFER_VALIDATED
-> RUNTIME_VALIDATED
-> PROMOTED
```

Also preserve `CONTRADICTED`, `DEPRECATED`, `VERSION_LIMITED`, and `INSUFFICIENT_EVIDENCE` states.
Never overwrite conflicting evidence with a universal slogan.

## Video/document ingestion

Local media ingestion is deliberately legal and bounded:

- only approved local roots and approved web hosts;
- real stream probing, timestamped frame extraction, and VTT/SRT parsing;
- no platform restriction bypass;
- source observations, machine transcription, interpretation, and experiment results remain
  distinct;
- important claims return to current documentation and Blender reproduction.

Public YouTube sources can additionally be passed by URL through Gemini's supported video input.
The repository stores the prompt, source identity, model/access metadata, and timestamped analysis,
not a copy of the video. Audio/visual analysis is still only `CAPTURED`; it must survive
corroboration, controlled reproduction, different-target transfer, and runtime use before promotion.

Independent episode review is a separate gate. `knowledge_engine.video_episode_review` requires
source identity, a reviewer other than the extracting model, before/during/after frames, overlapping
speech, and explicit action alignment. `apply_independent_episode_reviews` binds that evidence to the
same video ID and timestamp range before Gemini provenance can advance. Pending access is not a
contradiction, and frame verification alone never promotes a modeling principle.

The current video evidence is summarized in
`knowledge/foundation/video_learning_curriculum.md`; media files normally remain ignored under
`runs/*/media/`.

## Claim boundary

A technique is not general merely because one controlled fixture passes. Promotion requires useful
transfer, runtime application, measurable effect, and retained applicability limits. Held-out claims
must not use assets whose dimensions, topology, decomposition, thresholds, or helper recipes were
developed while building the capability.
