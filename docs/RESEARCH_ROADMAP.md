# Autonomous Research & Expertise Acquisition — Mandatory Future Subsystem

**Status: active foundation phase. The closed-loop runtime has substantial demonstrated evidence,
and controlled documentation/experiment work has begun. Legal local video/document ingestion,
structured retrieval, usage telemetry, uncertainty, and rebuild-decision foundations are now
implemented and tested; external curriculum breadth and cross-asset promotion remain incomplete.
Research should stay problem-driven and should not outrun the runtime's ability to apply and
verify what it learns.**

## Current specialization override (binding)

`docs/DEVELOPMENT_PRIORITIES.md` governs near-term resource allocation. Research and benchmarks
must currently emphasize hard-surface, SubD, topology, reference modeling, modifier strategy,
retopology fundamentals, and production-ready prop workflows. Sculpting remains foundational but
deferred; do not select new character, facial, anatomy, or sculpt-heavy benchmarks unless a minimal
organic technique is strictly required by a higher-priority prop task.

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

## Reference Understanding / Scene Decomposition (implemented 2026-08-13)

A user-directed critique of the current repo state named this as the biggest gap between "the brain"
and genuinely perceptual judgment, citing the adjustable wrench directly: an automated pass can say
"I have a good silhouette" while a human says "you didn't actually model the wrench." Implemented as
`knowledge_engine/scene_decomposition.py` -- see `docs/REFERENCE_COLLECTION_PROTOCOL.md`'s "Scene
decomposition" section for the full description and `runs/2026-08-13_telephone-rebuild/
scene_decomposition.json` for a worked example. This closes one P0 item from that critique with real,
tested code (`tests/test_knowledge_engine.py::SceneDecompositionTests`), not a stub.

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
Remains a candidate until experimentally tested. `observed_actions` should eventually be drawn from
a controlled taxonomy (object create/delete/select, mode switch, extrude, inset, loop cut, bevel,
move/rotate/scale, merge, bridge, dissolve, knife, boolean, mirror, subdivision, support loop, edge
crease, bevel weight, normal edit, shading change) rather than free text, precisely so
`spoken_reason` can be checked against the actual action type instead of just co-occurring in time --
recognizing not just that a Bevel was applied but that "this edge needs a controlled manufactured
radius and highlight" is the reason, which is the part that transfers to a different asset. Not
implemented: this requires the action-recognition and speech/action alignment stages below, neither
of which exist yet.

**Planned, NOT YET IMPLEMENTED, module breakdown** for the day the sequencing rule above actually
reaches "video understanding" (still gated behind documentation ingestion and forum research per
"Research breadth grows with modeling ability" below -- recorded here as architecture, not scaffolded
as empty files, per this project's own standing rule against half-finished implementations):
`research/video_agent/{discovery,source_ranker,acquisition,metadata,audio,transcription,
scene_segmentation,visual_events,blender_ui_understanding,speech_action_alignment,lesson_extractor,
mistake_detector,technique_extractor,experiment_generator,knowledge_promoter,episode_store}.py`.

**Update (2026-08-13): the acquisition/description/segmentation gap above is now substantially closed
by an external connector, not by code in this repo.** A CloudGlue MCP connector
(`mcp__Cloudglue__*`) is connected and confirmed functional (`list_collections` round-tripped
successfully). Its tools cover real pieces of the pipeline directly: `describe_video` accepts YouTube
URLs natively (closing the "nothing in this project's toolset can fetch from a video platform" gap
below), `segment_video_chapters` gives coarse segmentation, `search_video_moments` /
`search_video_summaries` give semantic search across speech/on-screen-text/visual content within a
collection, and `extract_video_entities` / `segment_video_camera_shots` add structured entity and
shot-level detail. This is genuine external infrastructure for `discovery.py`-through-
`scene_segmentation.py`'s job, not a research claim -- confirmed by a real, successful tool call, not
assumed from the connector's description. What CloudGlue does NOT provide, and what still needs
building on top of it if this thread is pursued: `blender_ui_understanding.py` (recognizing Blender-
specific UI actions, not general video description), `speech_action_alignment.py` (tying a spoken
timestamp to a specific modeling action rather than a general video moment), and everything from
`lesson_extractor.py` onward (mistake/technique extraction into this project's own knowledge
schemas). **Update (2026-08-13): now genuinely applied.** `describe_video` against a real, verified
YouTube URL (found via `WebSearch`, not guessed) -- "The MOST IMPORTANT Hard Surface Modeling Tip -
Edge Creasing" -- returned a full, accurate, timestamped scene-by-scene transcript with real
technical argument structure, not a generic summary. Cross-checked against this project's own
already-validated `edge_crease.md` findings (not accepted blindly, per Section "Multiple-video
triangulation" logic even with only one video): the source argues against crease for hard-surface
work, which on inspection is a real, additive mechanistic finding (a fully-sharp, zero-radius edge
lacks the specular highlight a physical Bevel radius gives) rather than a contradiction of the
tested crease-with-support-stays-flat result -- recorded as `SOURCE OBSERVATION` in
`edge_crease.md`'s own "Video source" section, explicitly not promoted past that layer, with one
concrete untested claim (crease values 0.7-1.0 reading identically) flagged for a real experiment
before use. This is the first real instance of the `video observation -> hypothesis -> [pending]
experiment -> transfer -> runtime use` loop Section 61 below describes, still short of the
experiment/transfer/runtime steps.

A second connector (`mcp__Blender__*`, distinct from this project's own `blender_ops/` code and the
existing `mcp__blender__*`/`mcp__modeler__*` tools) is also connected: `search_manual_docs` /
`search_api_docs` do full-text search over the actual bundled Blender user manual and Python API
reference and work standalone (confirmed live, no running Blender instance required) -- a direct,
higher-fidelity replacement for ad hoc web-fetches when grounding a Tier-A documentation claim (see
"Source hierarchy" below). Its live-instance tools (`get_objects_summary`, `execute_blender_code`,
viewport/window screenshots, `get_blendfile_summary_*`) additionally give live introspection of a
running Blender GUI, but require Blender open locally with this connector's own addon active --
confirmed by a live connection attempt that correctly reported "Cannot connect to Blender at
localhost:9876" when no instance was running, the same category of requirement as this project's own
`blender_ops/modeler_server.py`.

`discovery.py`/`acquisition.py` (YouTube search and download) are explicitly the biggest open gap in
this repo's OWN code -- today's `video_ingest.py` deliberately only accepts already-local,
already-permitted video, and nothing in this project's toolset can fetch from a video platform;
standing that up is real infrastructure work with its own permission/security surface, not a natural
extension of the current ingester. CloudGlue's `describe_video` narrows this gap for analysis
(it fetches and analyzes a YouTube URL server-side without this repo needing its own downloader) but
does not replace `video_ingest.py`'s own local-file, provenance-tracked path, and does not by itself
implement the Blender-specific action recognition or knowledge-schema promotion this project needs.

**Update (2026-08-14): CloudGlue's credits ran out mid-session (`describe_video` returned
"Insufficient credits on account for this operation. This operation requires 196 credits."`,
confirmed a real billing limit and not a connection break by immediately re-succeeding on the free
`list_collections` call). Rather than wait, the observed CloudGlue output *schema* --
`## File`/`## Title`/`## Summary`/`## Scenes` with `### Scene [MM:SS - MM:SS]` blocks and timestamped
`**Speech:**` lines, chunked in ~20-second windows -- was reverse-engineered as a local module,
`knowledge_engine/ingest/scene_document.py`, built entirely on this project's own already-existing,
already-approved-roots-gated `video_ingest.py` (no new downloader, no bypass of the YouTube bot-check
that blocked a direct scrape attempt earlier this session).**

`build_scene_document()` buckets local frame extraction + parsed/transcribed speech into the same
scene-window shape, sampling multiple frames per scene (not just one at the window boundary) so a
reviewer has real intra-scene visual coverage. Critically, it does **not** claim CloudGlue's
proprietary visual captioning: each scene's `visual_description` and the document's overall
`summary` are left as an explicit `UNFILLED` placeholder naming the exact frame files to inspect,
filled in only by `fill_visual_descriptions()` -- which is meant to be called by a vision-capable
reviewer (Claude, reading the frame PNGs directly via `Read`) actually looking at the frames, not by
any automated local model, since this project has no local vision-captioning backend. This was
proven end-to-end, not just structurally: run against the existing project-owned fixture
(`runs/2026-08-10_video-ingestion/project_owned_modeling_lesson.mp4`), the extracted frames were read
directly and described from what was actually visible (colored instructional cards reading "STEP 1 /
Inspect the base cage", "STEP 2 / Inspect the evaluated surface", "STEP 3 / Compare front, side, and
top"), matching the parsed speech exactly, and persisted back through `fill_visual_descriptions`.
Tests: `tests/test_ingest.py` (3 tests, approved-roots rejection, schema/frame-coverage shape,
fill-and-persist round trip). The real limitation stands unchanged from the paragraph above: this
reproduces CloudGlue's *orchestration*, not a replacement for its trained visual-understanding model,
and still has no legal way to acquire an actual external YouTube tutorial file -- it requires the
user to supply a local video (screen recording, or a file downloaded through means outside this
project's own tooling) before it can be pointed at real external curriculum content.

**Update (2026-08-14): the acquisition gap above closed, and the first real external tutorial was
studied end to end.** Direct programmatic YouTube access (`fetch`, `XMLHttpRequest`, direct
`/api/timedtext` requests) reproducibly returned HTTP 200 with an empty body regardless of method --
neither confirmed as an extension side effect nor a deliberate platform restriction, and deliberately
not probed further once that ambiguity was clear, per the standing rule against working around
bot-detection. Live browser automation on the user's own authenticated session (not scraping --
literally the same interaction a human doing this manually would perform) hit no restriction at all
and confirmed clean access to the actual video and rendered captions. The user then connected
**TubeAlfred**, a community MCP connector exposing YouTube data including
`youtube_video_transcript`, which returned a complete, real, per-phrase-timestamped transcript
(2,682 segments, 104 minutes) for JL Mussi's "Learn Blender 3D Modeling Under 97 Minutes!" on the
first call -- the project's first successful automated acquisition of real external tutorial
content. Saved to `runs/2026-08-14_video-study-jl-mussi/` (raw JSON + a 20-second-window
consolidated transcript, matching this project's own scene-window convention). As an unverified
community connector, its output is treated the same as any other source: `SOURCE OBSERVATION`,
subject to the same promotion path as everything else, not a verified fact merely because the
connector worked.

**New capability: `knowledge_engine/video_knowledge.py`.** A structured, temporally-grounded
knowledge-extraction schema (`KnowledgeItem`: `PROCEDURE`/`PRINCIPLE`/`DECISION`/`VISUAL_CUE`/
`FAILURE`, each carrying a `SourceTimestamp`, required `supporting_evidence`, and a status following
this project's own knowledge lifecycle) plus `apply_transfer_test`, which enforces the "a technique
counts as learned only if it improves performance on an unseen object" rule directly in code --
a transfer test targeting the same asset the knowledge was captured from is rejected outright,
matching `session_learning.py`'s existing "no promotion without a declared replay" discipline for
session-mined skills. Extraction itself is not automated: five real items were captured from the JL
Mussi transcript by actually reading it (not generated from the title) -- among them, a `DECISION`
that cylindrical segment counts should be divisible by four ("it gives me even symmetry lines across
the X, the Y, and the Z") and a `FAILURE` that closely-spaced beveled verts pinch once Subdivision
Surface is applied even though the base cage looks fine. All five validate cleanly and are saved to
`runs/2026-08-14_video-study-jl-mussi/knowledge_items.json`; none has a transfer test yet, so none
has been promoted past `CAPTURED` -- per the module's own rule, they are not yet trusted runtime
knowledge. 15 new tests in `tests/test_video_knowledge.py`, full suite 50/50.

A curated 20-video curriculum (`docs/VIDEO_LEARNING_CURRICULUM.md`), authored by the user, gives
this pipeline a real backlog beyond this one video -- prioritized reference analysis, topology,
SubD, and decision extraction over shortcut/UI-tour content, with an explicit "ultimate test"
(unseen reference, extracted knowledge must transfer) that is now directly implemented rather than
aspirational.

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

The fixed-frame visual comparator in `knowledge_engine/visual_compare.py` and
`runs/2026-08-10_visual-comparison/` is a prerequisite for stages 3+, not evidence that stage 3
has been passed. It prevents per-candidate camera framing from hiding proportion regressions and
requires improvement across front, side, and top, but currently measures silhouettes only.

Early workflow selection is now inspectable through `knowledge_engine/strategy.py`. Its separate
representation/component/edit/repair decisions expose scores, reasons, runner-up, margin, and
confidence. The 10/10 declared-case benchmark is a regression test, not a held-out stage result.

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

Current implementation and held-out contamination status are audited in
`docs/DIRECTIVE_IMPLEMENTATION_AUDIT.md` and
`knowledge/foundation/benchmark_readiness.json`.

## Update (2026-08-14, continued): curriculum processing in progress

Per direct user instruction ("do EVERY video"), working through all 20 entries in
`docs/VIDEO_LEARNING_CURRICULUM.md`, mapped to real video IDs in
`runs/2026-08-14_video-curriculum/video_manifest.json`. Each processed video gets its own
`runs/2026-08-14_video-study-<slug>/` directory with `transcript_full_text.txt` (or
`transcript_raw.json` + `transcript_consolidated.txt` for the first, longest video) and
`knowledge_items.json` (real, cited `KnowledgeItem` entries per `knowledge_engine/video_knowledge.py`,
validated against the schema before being considered done).

**9 of 20 entries processed as of this session** (entries 2, 3, 4, 7, 8, 9, 11, 12, 14 -- 29
knowledge items total across those 9, all schema-validated, all status CAPTURED / none yet
transfer-tested). Entries 3 (JL Mussi), 9 (Ian McGlasham SubD), 11 (Blender Bros SubD Hard Surface),
and 14 (RileyB3D advanced hard surface / laundry bottle) were the highest-density sources so far --
McGlasham's inset-and-fill boolean-replacement procedure and RileyB3D's lattice-blockout /
vertex-count-matched-boolean / shrinkwrap-reconform / topology-redirect sequence are the strongest
candidates for an eventual transfer test on a new build. Two videos (Grant Abbitt interface basics,
CG Cookie workspace-setup part 1) were confirmed genuinely low-density per the curriculum's own
"avoid overweighting UI-introduction videos" rule and were extracted honestly thin (1 item each)
rather than padded.

**Update (same session, continued): 15 of 20 entries now processed, 63 knowledge items total.**
Per direct user instruction ("keep working but also make sure you are actually learning, and that
goes for the ones already 'captured'"), added a genuine cross-video synthesis pass
(`runs/2026-08-14_video-curriculum/synthesis.md`) rather than only accumulating more isolated
CAPTURED items -- reconciled an apparent contradiction between two sources on boolean workflows,
traced a 5-source convergence on SubD pinching back to its root cause (uneven initial-blockout
quads, per Elementza), resolved a genuine tension between two sources on when topology redirection
is/isn't appropriate, and found two concrete untested hypotheses for the mug build's two unresolved
failures (Screw-modifier revolve instead of baked segment count; Shrinkwrap+vertex-group for
handle attachment -- see memory `video-curriculum-mug-diagnosis.md`). One entry (16, original pick)
was blocked -- no caption track available -- and was swapped for a different video by the same
creator that does have captions, logged honestly in the manifest rather than skipped silently.

**Update (same session, final): all 17 numbered curriculum entries now processed** (entry 1's
modeling portion covered; its texturing/lighting/compositing portion deliberately left unprocessed,
per the curriculum's own "lower priority: rendering tricks" guidance -- see the manifest note on
entry 1). 76 knowledge items total across 17 processed videos. Entries 18-20 remain deferred
categories (not single videos) pending specific selection.

Mid-session, the user pushed back hard on transcript-only extraction ("you are currently only
observing transcripts and not watching the videos") -- correctly, since several `VISUAL_CUE`-type
claims were being inferred from spoken description rather than actually seen. Investigated real
alternatives: yt-dlp direct download hit YouTube's bot-detection wall (declined to bypass via cookie
extraction, per the standing rule against defeating anti-bot measures); the sandboxed in-app Browser
tool initially rendered a black frame for the live video canvas (a real rendering limitation, not a
block) but was later confirmed to render live video correctly once actually displayed. One item
(McGlasham's loop-straightening `VISUAL_CUE`, in `mcglasham-subd`) was visually re-confirmed against
a real frame as a proof of concept. Decision (mine, since the user delegated it): apply visual
spot-checks forward for genuinely appearance-based claims, not a blanket backfill across the 66
items already captured before that point -- most of those are grounded in direct quotes about
spoken reasoning/decisions, which the transcript is solid primary evidence for.

## Update (same session, continued): Gemini video-understanding wired up, extended beyond the 20-video curriculum

User provided a Gemini API key (stored in `.env`, gitignored). Confirmed working via
`models/gemini-3.7-flash-video-understanding-eap`, which genuinely watches a YouTube video rather
than inferring from title/transcript -- validated by cross-checking its description of a specific
timestamp against an actual browser frame grabbed at that same timestamp; they matched.

Used this to backfill visual grounding on the 3 `VISUAL_CUE`-typed items that existed before this
point (all 3 confirmed accurate; the `subd-3dprint` "On Cage" item's confidence rose the most since
its source quote was garbled auto-captioning that the actual on-screen behavior fully vindicated).

Then extended past the original 20-entry curriculum: found and processed 5 new videos spanning a
genuine beginner-to-pro progression (CG Boost tricks -> CG VOICE mistake-correction -> Blender Bros
curvy/organic -> The Gnomon Workshop professional training -> JL Mussi advanced topology), each
analyzed by having Gemini watch the full video and report specific timestamped, visually-grounded
moments (mesh state, modifier stack, exact settings), not narration paraphrase. Manifest:
`runs/2026-08-14_video-curriculum/extended_videos_manifest.json`. This produced markedly denser,
more technically precise items than transcript-only extraction did -- e.g. exact modifier stack
order and settings values that a transcript alone never states clearly.

**106 knowledge items now captured across 22 processed videos total.** None have a recorded transfer
test yet -- per the project's own lifecycle they remain CAPTURED, not TRANSFER_VALIDATED, regardless
of cross-source reinforcement; that requires trying them on an unseen build, which is blocked while
modeling work is paused per direct user instruction. Flagged to the user as an open decision rather
than resumed unilaterally. Full cross-video synthesis (contradictions reconciled, convergent
principles traced to root causes, 2 concrete untested hypotheses for the mug build's unresolved
failures) is in `runs/2026-08-14_video-curriculum/synthesis.md` -- not yet updated with the 5
extended videos' findings.

## Update (2026-08-14, later): curriculum v2 adopted, first transfer test passed, second correction made live

Adopted the user's own pasted curriculum restructuring (`docs/BLENDER_MODELING_CURRICULUM_V2.md`)
and its 16-step extraction protocol (`docs/VIDEO_EXTRACTION_PROTOCOL.md`), which explicitly named
this project's biggest gap: zero transfer-tested items despite 106 captured ones. Resumed modeling
specifically to close that gap.

Ran the first genuine transfer test in the project's history: a 5-vertex profile revolved with a
Screw modifier, segment count changed live from 8 to 16 (40->80 verts, 0 degenerate faces at
either setting) via `apply_transfer_test()` -- **PASS, TRANSFER_VALIDATED**
(`runs/2026-08-14_transfer-test-screw-cylinder/`).

Second attempt (Shrinkwrap + vertex-group for a mug handle) was interrupted mid-build by direct
user correction: "your approach is still wrong stop and watch me do it and learn." The technique
would have technically passed its own narrow claim (position/normal conforming) but was the wrong
tool for a part that needs to read as structurally fused. Ceded control (`set_control_mode`),
observed the user's live fix (join + bridge into one continuous mesh), and corrected the knowledge
base and memory afterward rather than letting the technically-passing test stand unqualified. The
generalized lesson: mechanism-validation is not the same claim as technique-choice-validation.
Retired the mug from the active prop-candidate list per direct instruction; replaced it with a
teapot (two grown appendages instead of one) and a lever door handle (a different base form factor).

Found and fixed two real bugs in the typed protocol surface while building these tests:
`set_modifier_parameter` couldn't resolve object-reference RNA properties (Shrinkwrap.target etc.)
from a string name; `assign_vertex_group` didn't exist at all, so no modifier requiring a vertex
group mask could be configured through the typed surface. Also ran a pyflakes pass across core
modules and fixed the real dead-code hits it found.

Continued the curriculum under "don't stop until it's done": processed 11 more videos (retopology,
Parabox hard-surface, CG Boost 100+ tips, Blender Bash modifiers, JL Mussi cylinders, Blender Guru
Anvil, Josh Gambrell tricks, CG Boost UV unwrapping, normal-vs-displacement, both Blender Guru PBR
videos) without pausing for confirmation between them.

**173 knowledge items now across 33 processed videos; 1 TRANSFER_VALIDATED, 172 CAPTURED.**

Stopped mid-Level-8 (materials/shading) when Gemini's free-tier video-understanding quota
(`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, 20 requests/day for
`models/gemini-3.7-flash-video-understanding-eap`) was exhausted -- confirmed via two retries with
the API's own suggested backoff, both still 429. This is a real external daily cap, not a design
choice; the Default Cube procedural-materials video (Level 8's last item) and anything requiring a
further Gemini call are blocked until the quota resets. Field report republished
(`https://claude.ai/code/artifact/fd49fe3a-a730-46e4-b33a-6b06f7e6f07e`) reflecting all of the above,
including this blocker, rather than silently stalling.

## Update (2026-08-14, later still): second transfer test passed, on a genuinely different asset

With the video pipeline blocked, pivoted to two things the Gemini quota doesn't gate: finished the
pyflakes cleanup pass across `tools/*.py` (17 files, all genuinely-unused imports/locals; one
legitimate re-export in `quality_review.py` fixed via explicit `__all__` instead of a false-positive
finding) -- full 50-test suite still green -- then resumed modeling to close the "most of the base
isn't transfer-tested" gap.

Built a lever door handle (`DoorHandle_Rose`) entirely through the typed decision-transaction
protocol: rose disc, spindle boss grown from the rose's own top face, lever arm grown from the
boss's own outer wall and curved via three extrude+rotate steps -- 300 vertices, 0 non-manifold
edges, 0 ngons, true at every one of 18 intermediate decisions, not just the end state. This
specifically re-tests the connected-topology lesson from the earlier live mug-handle correction, but
on a deliberately different base form (flat disc + bore, not a revolved vessel). Wrote the
correction up as a proper `KnowledgeItem` for the first time (it had only existed as a brief.md and
a memory entry until now) and ran `apply_transfer_test()` against it for real:
`captured_while_building: "mug_handle_join"` correctly blocked reusing the mug itself as the test
asset, and the door handle build passed. Status moved `CAPTURED` -> `TRANSFER_VALIDATED` -- the
project's second genuinely transfer-tested item, and the first tested on an asset type it wasn't
captured on.

One real correction mid-build, handled cleanly rather than forced through: chained two
`perform_decision` calls inside one transaction, which the external-edit detector correctly flagged
as unexpected mid-transaction drift on the second call. Used `reject_decision` for a clean rollback
and redid the two operations as separate transactions -- confirms the protocol wants exactly one
`perform_decision` per begin/verify/commit cycle.

Also reclaimed `AGENT_CONTROL` (left on `USER_CONTROL` since the earlier live correction) only after
confirming, via `poll_events` and `get_full_state`, that the object the user had been live-editing
(`Cylinder.001`, zero persistent-ID coverage, so never touched by the typed protocol) had gone quiet
for ~19 minutes -- left it completely untouched and built the new work on a separate object, per the
"don't resync/overwrite external state" lesson.

One honest limitation: the lever's downward curve landed around 8-9 degrees, short of the
reference spec's 30-40 degree target, because `rotate_selection` pivots around the selection's own
median rather than an external joint further back -- still reads correctly in the silhouette
renders, but the exact angle undershot the plan. Full account, including the transfer-test
JSON payload, in `runs/2026-08-14_transfer-test-doorhandle-grown-lever/brief.md`.

## Update (2026-08-14, later): teapot body built clean; spout attempt reverted with two real bugs caught

Started the teapot (the mug's harder replacement: two grown appendages, not one). Built
`Teapot_Body` via the same validated `spin_selection` revolve mechanism as the first transfer test,
plus `merge_by_distance` to fuse the axis-touching point's duplicate vertices -- 168 verts, 32
non-manifold edges (exactly the intended open mouth), 0 degenerate faces.

Attempting the spout (inset+extrude+curve from the wall's widest-point ring, the same technique
that passed the door-handle transfer test) surfaced two real, previously-undocumented bugs in the
typed protocol, both caught before they caused unrecoverable damage:

1. `commit_decision` reset selection to the whole mesh (195 verts) instead of leaving the just-
   extruded 13-vert tip ring selected, right before a `rotate_selection` call that would have
   deformed the entire body. Caught via `get_selection`, rejected the pending decision before it
   executed. Confirmed `reject_decision` only restores geometry/transform, not selection --
   the identical pattern worked fine three times during the door-handle build, so this isn't
   universal; don't trust selection persistence across a commit without checking.
2. `extrude_selection`'s face-normal-direction assumption failed on the body's tapering shoulder
   region -- the first extrude moved the attach patch inward (measured, not assumed: x went
   2.162 -> 1.581) instead of outward, even though the body's overall normals were confirmed
   correctly oriented elsewhere. Doubly-curved / tapering attachment points need their normal
   checked directly before extruding, not assumed from "select wall faces, extrude."

Recovered cleanly rather than leaving a mangled build: deleted all spout geometry by ID, found and
removed 7 leftover vertices that had escaped the ID-based deletion (they kept their original face's
low ID through `inset_selection`, which reuses rather than reassigns IDs for the shrunk patch), and
closed the resulting hole back to a manifold wall in three incremental `fill_selection` passes.
Final state: 32 non-manifold edges (mouth only), 0 degenerate faces -- genuinely clean, one small
honest cosmetic blemish (a slightly non-planar repair patch, not a manifold defect) left as-is.
Both bugs written up as a proper memory entry
(`decision_transaction_protocol_gotchas.md`) with the exact fix pattern (re-select by ID before
every `perform_decision`; verify normals directly on non-cylindrical attachment points) for the next
attempt. Full account: `runs/2026-08-14_teapot-body-revolve/brief.md`.

## Update (2026-08-14, later still): second spout attempt, three more chained-extrude failures -- real unresolved bug found

The user manually fixed the first attempt's leftover ugly repair patch (3 ngons -> 0) mid-session;
confirmed clean via `get_full_state`'s external-edit detection before continuing.

Reattached the spout at the z=0.51 ring using the directly-measured reliable normal, applying the
"re-select by ID before every `perform_decision`" fix throughout. The first extrude from the
original wall worked correctly (measured: x 2.09 -> 2.591). Every extrude after that failed, three
different ways: an anisotropic taper likely shearing the tilted ring's plane before the next
extrude; an edge-based extrude (no cap face available) using boundary-vertex normals, which
represent a rim's radial direction, not a tube's length direction; and -- most surprisingly -- a
clean face-based extrude of a freshly-`fill_selection`-closed cap, which still went inward despite
having a single well-formed face to compute a normal from.

**This is now a confirmed, unresolved, 3-for-3 bug in chained `extrude_selection` calls specific
to this build** -- not something to keep guessing at live. Reverted fully back to a clean flat
wall (161 verts, exactly matching the pre-spout count; 32 non-manifold edges = mouth only) rather
than shipping a broken or half-built spout. Documented in
`decision_transaction_protocol_gotchas.md` with the recommendation to root-cause it on a controlled
bare-cube test (extrude twice in a row, check direction each time) before attempting the spout a
third time -- the door-handle build's identical-looking 3x extrude+rotate pattern worked correctly,
so whatever differs between that build and the teapot's is the actual thing to isolate.

## Update (2026-08-14, later still): root-caused and fixed the chained-extrude bug; spout complete

Followed through on the recommended controlled repro instead of guessing further live. Built a
bare cube away from the teapot, extruded its +X face once, then directly inspected where the
original face's persistent ID ended up. **Found it immediately:** the ID was reassigned to one of
the new SIDE-WALL faces (center shifted 90 degrees off-axis, normal rotated to match), not deleted
and not kept on the new cap -- the genuine cap got a completely different, freshly-assigned ID.
Confirmed the fix by extruding the correct cap face a second time: direction was right.

This exactly explains all three teapot failures -- each one reused a pre-extrude face ID for a
follow-up extrude, which by then pointed at a side wall roughly perpendicular to the tube's
intended direction. `inset_selection` genuinely does preserve IDs on its shrunk cap (confirmed
separately, still true); `extrude_selection` does not, despite the surface-level similarity.

Rebuilt the spout a third time applying the fix throughout (always read the new cap's IDs from
that step's own `id_delta.faces.added`, filtered to all-new-vertex faces, never reuse a pre-extrude
ID). Measured the new cap's position after every one of the 4 extrude steps to confirm direction
empirically: x went 2.09 -> 2.591 -> 3.021 -> 3.512 -> 4.005, monotonically outward the entire way.
Final body: 211 vertices, 42 non-manifold edges (32 mouth + 10 intentional pour opening), 0
degenerate faces. Front and top silhouette renders both read as a correct, symmetric teapot spout.

Wrote the bug up as a proper `KnowledgeItem`
(`runs/2026-08-14_extrude-id-reassignment-bugfix/knowledge_items.json`), captured on the bare-cube
test and transfer-tested for real on the teapot spout -- status `TRANSFER_VALIDATED`. This is the
project's third genuinely transfer-tested item, and notably the first one about the modeling
tooling itself rather than a modeling technique or principle. Full account:
`runs/2026-08-14_teapot-body-revolve/brief.md`. Remaining teapot work: the C-shaped handle, which
needs a real `bridge_selection` back into the body at a second attachment point -- new territory
even with the extrude bug fixed, since it's a full loop rather than a cantilevered tip.

## Update (2026-08-14, later): reconciled stale curriculum tracking, grew the handle, started an official-documentation/forum track

Reconciled `docs/BLENDER_MODELING_CURRICULUM_V2.md` against actual `runs/` output -- six items (3,
6, 8, 10, 17, 18) were marked "not yet processed" despite having been genuinely processed earlier
in the session; the doc just never got updated back. Fixed each with its real run directory and
item count, and documented ~17 additional videos processed outside the list's exact numbering
(mostly Level 14 professional-judgment material).

Continued the curriculum for real: processed the Default Cube procedural-materials video (Gemini
quota had reset), Blender Guru's Beginner 4.0 tutorial, Josh Gambrell's UV workflow (found via
title search), and Polygon Runway's Winter Café stylized-modeling walkthrough (also found via
title search) -- 20 new items across four videos, closing out Levels 7, 8, and 13 completely.

Grew the teapot handle as a 9-segment curved arm using the now-fixed extrude technique -- every
segment confirmed moving correctly by direct measurement. Attempting to close it into a true
two-point C-loop via `bridge_selection` hit a different, real bug: unequal loop sizes (10 vs 12
vertices) produced a genuinely twisted connection (10 edges with 3 linked faces instead of 2).
Confirmed as real, not a stale-ID repeat: deleting the suspected extra face made non-manifold
edges go up, not down. Reverted cleanly and finished the handle as a capped cantilevered hook
rather than ship broken topology -- attached at one point on the body, not the spec's two.

Per direct instruction, started treating the official Blender manual and community forums as real
sources under the same extraction discipline as the video curriculum (new Level 16, not a
one-time skim). First pass: Bevel, Weighted Normal modifier, and Bridge Edge Loops manual pages,
chosen specifically because they connect to live project work rather than at random -- and this
paid off immediately. The manual's Bridge Edge Loops page documents a `Twist` parameter that
"offsets the choice of target vertex which each source vertex is connected to" and can make the
generated tube twist -- this is the actual, documented root cause of the teapot handle's crossed
bridge, which this project's own `bridge_selection` wrapper never exposed as a parameter. A
Blender Artists forum thread on the same symptom added a practical workaround (inset both end
faces before bridging) as a lower-confidence, community-sourced supplement. Six items captured;
`decision_transaction_protocol_gotchas.md` updated with the confirmed mechanism and a concrete
next step (expose `twist` on `bridge_selection`) instead of leaving the bug as "unresolved, cause
unknown."

## Update -- 2026-08-15

Pivoted from curriculum work to a held-out reference-reconstruction test (per prior explicit
user approval), starting with a padlock. Reference-collection protocol followed genuinely: real
Wikimedia Commons photos, explicit MEDIUM/LOW confidence statements, a written modeling plan
before touching Blender. Body + shackle-hole blockout progressed, but three separate attempts to
cut two discrete shackle-leg holes (`subdivide_selection`, then `bisect_selection` on an isolated
inset face, then `bisect_selection` again) all hit the same T-junction ngon bug: any bmesh
operation that inserts a vertex into a face boundary edge shared with an unselected neighbor face
turns that neighbor into an ngon. Simplified to a single slot as a stated, honest workaround. The
shackle arc (extrude+rotate chain, 2 of 8 planned 22.5-degree segments) was found not to track the
intended analytic circle cleanly on inspection. Direct user feedback: "poorly done job scrap and
try something else" -- the padlock was deleted from the live scene rather than patched.

Restarted the held-out test with a desk stapler instead (no fragile curved-tube appendage,
breaking the failure pattern from three prior curved-appendage attempts: teapot spout x3, teapot
handle bridge-twist, padlock shackle). Per direct user instruction ("you can use my actual browser
this time"), references were gathered from the user's own logged-in Chrome rather than the
sandboxed browser -- this reached real manufacturer-listed dimensions (Swingline 747 Classic,
7.4 x 1.7 x 2.6 inches) instead of photo-estimated proportions, a meaningfully stronger reference
basis than the padlock had. Built the body from real dimensions, shaped a shallow arched top via
`loop_cut_selection` on the length-direction edge ring (a full topological ring cut, not a
per-face subdivide -- deliberately avoids the T-junction bug rather than re-triggering it), added
a hinge-seam bevel and a flared base plate, and began applying the standing bevel-weight policy
(sharp edges on the base plate weighted, Bevel modifier before Subdivision Surface). Mid-sequence,
the user manually added the Subdivision Surface modifier live in the Blender GUI -- correctly
recognized as a collision to observe and continue from, not overwrite (per
[[live-blender-gui-collision-handling]]). The modeler typed server then dropped its connection
mid-operation; before it could be re-established, direct user instruction: "scrap the modelling
tests and continue with the curriculum until you're done." Both `reference/padlock/notes.md` and
`reference/stapler/notes.md` are left in place as honest records; `Stapler_Body` is left as-is in
the live scene (not cleaned up, since no destructive action was requested).

Resumed curriculum work: began the first pass on curriculum item #4 (CG Boost's 100+ Tips to
Boost Modeling in Blender, REQUIRED, previously entirely unprocessed), chapter-by-chapter since the
full video is nearly two hours. Started with the Mesh Modeling chapter specifically (not the
video's first chapter) because it connects directly to live project problems. This paid off
immediately: the video documents Connect Vertex Path (`J`) as splitting an existing face along a
vertex path rather than inserting a vertex into a shared boundary edge -- a genuine, sourced fix
candidate for the T-junction ngon bug hit three times this session. This is now tested and exposed
as a bounded typed two-endpoint operation in `runs/2026-08-16_connect-vertex-path/`: a copy-first
preflight, continuous shared-boundary splitting, transaction rollback, persistent identity, solid
topology evidence, and fresh-process verification pass. Ordered three-plus point paths and
curved/SubD transfer remain open. Two independent
alternative hole-cutting techniques also surfaced (Bridge Edge Loops between matching opposing
faces; Loop Tools Circle). Eight items captured; curriculum doc and this roadmap updated.

## Update -- 2026-08-15 (continued)

Closed out curriculum item #17: processed the remaining 3 parts of Blender Guru's 4-part anvil
modeling series (transcript-only, via TubeAlfred, dispatched to three parallel background agents
since each transcript exceeded the single-call token limit). Part 2 (Boolean) confirms this
project's existing boolean-cleanup gap rather than closing it -- the video uses manual Remove
Doubles plus quad-preserving knife cuts, never a Weld modifier, and defers edge rounding to support
loops rather than a post-boolean bevel at any point. Part 3 (Sharpening Edges) adds a third,
bevel-free technique to the live Bevel-before-vs-after-Subdivision-Surface question found earlier
the same day: support/proximity loops, with Edge Crease explicitly rejected as unreliable except at
maximum value. Part 4 (Final Touches) contributes a real judgment-call principle -- check reference
photos for actual edge sharpness before spending effort solving a topology problem reference may
show does not need solving -- plus an explicit rejection of Ctrl+E Rotate Edge in favor of
delete-face+Alt+M merge for edge-flow redirection. 23 items total across the three parts. Curriculum
doc and the bevel/SubD-contradiction memory note both updated.

## Update -- 2026-08-15 (continued 2)

Surveyed curriculum item #14's target channel (Josh Gambrell, now rebranded "Josh - Blender
Bros") for the first time -- mostly Hard Ops/Boxcutter/Plasticity add-on tutorials and business
content now, not pure technique videos. Selected and processed the 3 highest-value hard-surface
videos (transcript-only). Most valuable: "How to fix SHADING ERRORS in Blender" draws a real,
previously-undocumented boundary on this project's own bevel-weight policy -- Weighted Normal only
fixes flat-surface bevel shading distortion, not curved-surface distortion (a bent/non-planar face
is a different problem entirely, needing clean topology, denser geometry, or a Data Transfer
modifier instead). Every hard-surface asset built this session has curved surfaces, so this is
immediately load-bearing, not hypothetical -- added to the bevel-weight policy memory as a flagged
boundary condition. "PERFECT curves with holes" independently confirms Loop Tools Circle (also
found today via CG Boost) and adds a curve-to-mesh construction path for tubular parts, genuinely
different from this project's repeated extrude-and-rotate-chain approach. "CONVERT your blocky
objects into perfect bevels" is judgment-only (no new mechanics): a third independent source
confirming full-blockout-before-any-bevels sequencing, plus principles about bevel placement and
width as silhouette-design decisions. 11 items total; curriculum doc and the bevel-weight policy
memory both updated.

## Update -- 2026-08-15 (continued 3)

Ran the Level 14 synthesis pass the curriculum doc had been flagging as owed since the extended-
curriculum push: cross-referenced all 87 knowledge items across the 20 "professional breakdown"
video runs against the 9-stage reasoning-chain framework (reference interpretation -> blockout ->
representation choice -> topology -> modifier -> detail -> surface/shading -> mistake ->
correction). No new videos watched -- pure meta-analysis of knowledge already on file.

Honest result, not a rubber-stamp: five stages (topology, modifier, detail, surface/shading,
mistake->correction) are strongly evidenced, several rules cross-validated independently across 3
separate runs (the Bevel-miter-must-be-Arc rule, the Shrinkwrap+Data-Transfer attach combo, the
origin-must-be-reset-before-mirroring failure). Two stages are moderate but narrower than they look
(blockout decision is mostly sequencing rules, not proportion judgment; representation choice has 7
candidate items but only one -- a professional explicitly rejecting boolean-driven geometry in favor
of native topology, with named consequences -- is a real live narrated decision rather than a
retrofitted technique claim). One stage is thin to the point of near-absence: reference
interpretation. Of 87 items, exactly one actually closes the loop from "here is what the reference
shows" to "here is the geometric decision that produced." This independently confirms this
project's own already-flagged capability gap (the 2026-08-14 external assessment: "give it any
reference and get a professional model" remains unmet) rather than being a coincidence of which
videos got processed -- the same gap keeps surfacing from a completely different angle. The
synthesis names concrete next-source types for the thin stages instead of just restating the gap.
Curriculum doc updated with the honest strong/moderate/thin verdict.

## Update -- 2026-08-15 (video principle transferred into planner behavior)

Closed one concrete part of the video-learning loop instead of adding another summary. The anvil
lesson's 05:07-06:40 sequence—manual step extrusion creates uneven spacing; establish full height
and uniform loops before deformation—was reproduced and transferred to a different 12-sided
circular lamp pedestal under a predeclared contract.

At identical 156-vertex/154-quad topology, the uniform candidate reduced profile RMSE by 82.10%
and side-quad aspect-ratio p95 by 54.85%. Both meshes remained one connected manifold object with
24 explicitly selected cap-perimeter bevel edges, Bevel before SubD, and Smooth by Angle. A fresh
Blender process independently reproduced every topology, profile, density, modifier, and shading
gate. The failed 32-edge semantic selection and blank wireframe attempt remain documented rather
than rewritten as success.

The two source items are now `TRANSFER_VALIDATED`; the structured skill is top-ranked for a matching
deformation-density query. A controlled planner proof shows the validated skill changes the same
localized ticket from `INSPECT` to a scoped `loop_cut_selection`, while a merely captured skill does
not act and non-manifold geometry still preempts it. `runtime_usage` remains empty because no real
held-out asset has used the skill through a typed transaction yet; that is the next promotion gate.

## Update -- 2026-08-15 (held-out runtime attempts rejected by human review)

Two attempts tested the next promotion gate, but neither is being counted as successful runtime
validation. The first used one CC0 museum photograph of an opalescent candlestick. It produced a
real typed transaction trace and high normalized silhouette score, but human review correctly
identified the core evidence error: a symmetry-reconstructed single view cannot establish accurate
three-dimensional form. The run is retained with `REJECTED_AS_FULL_FORM_VALIDATION`; its metrics
remain factual but cannot support skill promotion.

The replacement run corrected the sourcing method before modeling: five photos of one specific
Nailsea candlestick were collected from one listing, with a complete elevation, close upper/lower
details, oblique top/bottom evidence, and a direct base view. Published 30.5 x 9 x 9 cm dimensions
became frozen gates. This exposed a second real failure that normalized front IoU had hidden: SubD
shrank the first evaluated build to 7.43 cm wide. A fresh-process cross-view verifier rejected it;
the control cage was then compensated and reproduced 30.5000 x 9.0000 x 9.0000 cm, a circular
hollow socket, one 396-vertex/384-quad cage, closed evaluated geometry, and front IoU 0.8479.

Human review still rejected the corrected asset as insufficiently accurate. Therefore the skill
remains `TRANSFER_VALIDATED`, `runtime_usage` stays empty, and no metric-only promotion is allowed.
The next step is not further tuning of either candlestick: study the user's forthcoming videos on
reference sourcing, selection, interpretation, and modeling-from-reference; reproduce and validate
their methods; then attempt a different held-out prop. This is now the clearest active knowledge
gap, consistent with the Level 14 synthesis finding that reference interpretation was the thinnest
stage in the curriculum.

## Update -- 2026-08-15 (reference-workflow curriculum and executable readiness gate)

Processed all seven user-supplied general reference-workflow videos with actual public-video
audio/visual input through Gemini 3.6 Flash. Every URL was independently resolved to its intended
YouTube title/creator; raw timestamped analyses, source-fitness boundaries, cross-source synthesis,
and seven validated-schema `CAPTURED` items are stored in
`runs/2026-08-15_video-study-reference-workflow/`. None is promoted.

The study resolved an important apparent contradiction: multi-source creative synthesis is useful
for design, but exact reconstruction must converge on same-target/same-variant factual evidence.
Implemented `knowledge_engine/reference_analysis.py` so image count, view count, provenance count,
projection, purpose, dimensional authority, critical-property coverage, and conflicts are distinct.
The planner now returns `TARGETED_REFERENCE_RESEARCH` with no Blender operation when evidence is
insufficient.

Also fixed a runtime enforcement defect discovered during this work: forward stage transitions had
validated the destination gate while the planner validates the stage being completed, and the MCP
command bypassed strict validation. Forward transitions now advance exactly one stage and validate
the current stage; regressions remain explicit and logged. Controlled manifests correctly reject
the single-photo candlestick and a mixed-camera-variant set while accepting the same-object Nailsea
set as ready to begin. That acceptance does not overturn the human rejection of the Nailsea model.
The next required evidence remains a human-reviewed reference-gathering-only exercise, then an
equal-budget target-only versus structured-reference-set comparison on a new prop.

## Update -- 2026-08-15 (bridge correspondence gap closed at controlled-transfer level)

The documented Bridge Edge Loops Twist gap is now implemented through protocol 0.3. A read-only
analyzer simulates candidate offsets on copied BMeshes, typed mutation accepts explicit
`twist_offset`, and unequal loop density is rejected by default. Deliberately twisted circle and
rounded-rectangle tubes were corrected in Blender 5.2, visually reviewed in solid/wireframe passes,
and independently verified in a fresh process. The run also found and fixed automatic rollback after
an operator mutates and then raises, including an orphan-datablock leak.

This promotes only the narrow official-manual Twist claim to `TRANSFER_VALIDATED`. It does not
validate semantic landmark pairing, unequal-density topology, or a held-out production prop. The
roadmap priority therefore remains unchanged: complete the human-reviewed reference-gathering-only
exercise, then compare target-only and structured-reference-set modeling at equal effort on a new
prop before another difficult held-out build is accepted.

## Update -- 2026-08-15 (retrieval now abstains from weak unrelated matches)

An expanded retrieval probe exposed three concrete false positives: camera-perspective, UV-packing,
and armature-deformation tickets retrieved unrelated skills at scores between 1.4142 and 3.3416.
`StructuredSkillStore.search()` now uses a calibrated 4.0 default floor while retaining an explicit
lower-threshold option for exploratory search. A frozen 14-case regression covers eleven direct or
paraphrased positive contexts across all six current skills and three unrelated-ticket abstentions;
all pass, and every positive top result clears a predeclared 1.0 margin.

This improves executable memory safety and closes one wrong-retrieval mode. The set was authored
after inspecting the store and calibrating the threshold, so it is regression evidence rather than
held-out or independent retention. Longer-interval retrieval, broader real-session use, and the
future human reference-review gate remain open.

## Update -- 2026-08-15 (Bevel/SubD source conflict experimentally reconciled)

Ran the controlled comparison owed by curriculum item #4 instead of resolving a source conflict by
editing prose. Three identical 56-vertex/54-quad supported box cages used the same 36 semantic
design-edge segments: weighted Bevel -> Subdivision; crease-protected Subdivision -> weighted
Bevel; and an unprotected post-Subdivision Bevel negative control. All three remained closed,
all-quad, manifold meshes, proving technical validity cannot select the workflow.

The fixed-frame MatCap/evaluated-wire review and fresh-process verifier support a conditional rule.
Pre-Subdivision Bevel produced the smoothest broad radius here (2,400 evaluated faces, zero
localized pinch candidates). Crease-protected post-Subdivision Bevel preserved the flattest panels
and a tighter chamfer at 1,176 faces, but concentrated highlights at box corners and produced 16
localized curvature candidates. The unprotected post-Subdivision control visibly over-rounded the
form even though its face count and bounds exactly matched the protected variant -- a directly
preserved rejection of count-only judgment. Evidence: `runs/2026-08-15_bevel-subd-order/`.

This closes the contradiction as a controlled experiment, not as transfer validation. The next
promotion step is the same comparison on a curved hull or real prop whose reference declares
whether the edge should be a broad radius or tight final chamfer.

## Update -- 2026-08-15 (scoped Shrinkwrap footprint transfer)

Closed the three-source-but-untested Shrinkwrap Project hypothesis with a controlled reproduction
and different-curvature transfer. A closed 50-vertex/48-quad secondary mount was split semantically
into a 25-vertex contact footprint and 25 upper structural vertices. On both a sphere and cylinder,
Project limited to the footprint moved all intended vertices, preserved every upper vertex exactly,
landed within 0.024 of the analytic host surface, and remained closed/manifold/non-degenerate.

The controls establish why the details matter: an empty modifier vertex-group field projected the
whole part, collapsed its volume nearly to zero, and produced 12 degenerate faces; the wrong local-Z
direction moved zero vertices without throwing an error. The visual frame and fresh-process
verifier retain both failures. The skill is `TRANSFER_VALIDATED`, not runtime promoted. It applies
only to a physically separate assembled/movable/bolted component; continuous host transitions still
require connected topology or a deliberate boolean/retopology strategy. Evidence:
`runs/2026-08-15_shrinkwrap-footprint-transfer/`.

## Update -- 2026-08-15 (portable video discovery and fail-closed provenance)

Implemented the repository-owned discovery step without turning “stock up” into an archive.
`knowledge_engine/ingest/video_discovery.py` uses `yt-dlp --flat-playlist` for public metadata only,
ranks triage value with explicit limitations, excludes already registered IDs, blocks held-out
target terms and deferred topics, and emits a queue whose only next state is multimodal extraction.
A three-query live run retained 15 unique candidates, excluded ten known sources, downloaded no
media, and promoted no knowledge.

The first Gemini analysis of queue rank 1 exposed a more important defect: it reported another
video's ID, title, creator, and lesson while the wrapper replaced that URL with the requested URL
and accepted the structure. The pipeline now rejects every unverifiable or different model-reported
ID. Queue-bound analysis also requires exact title/creator and duration-with-tolerance agreement.
The earlier Gemini pipeline-validation artifact is retroactively marked rejected for the same
broken identity chain.

A strict retry passed identity binding, but independent browser review found its Grid Fill range
started too early and could not complete visible-frame checks because capture timed out. The run is
therefore `INDEPENDENT_REVIEW_PARTIAL_TIMESTAMP_DEFECT`, not learned knowledge. This closes
discovery and one provenance failure mode; reliable visible-action review, tight speech/action
alignment, reproduction, transfer, and runtime use remain open. Evidence:
`runs/2026-08-15_video-discovery-queue/`.

## Update -- 2026-08-15 (rejected Nailsea form corrected, still awaiting human review)

Revisited the retained rejected Nailsea candlestick after the user correctly called out its weak
form. The failure was mechanical uniform axial sampling: 33 evenly spaced loops left too little
control at tight transitions, and Subdivision erased important changes in the measured profile. A
reusable bounded sampler now redistributes a 45-loop budget toward measured slope and curvature
while preserving one connected 12-sided all-quad shell.

The work also exposed and fixed two runtime defects. The old generator used a superseded prose-only
stage transition instead of strict structured evidence. More seriously, exact rounded-Z grouping
split BMesh loop-cut rings where one radial edge differed by tiny floating-point amounts, producing
an `11 + 1` helical distortion. Generator and independent verifier now use bounded axial clustering.
The final fresh-process verifier sees exactly 45 planar 12-vertex rings and passes every topology,
modifier, evaluated-health, dimension, circularity, hollow-socket, and render check.

Relative to the rejected baseline, front silhouette IoU rose from 0.848 to 0.955, profile RMSE fell
68.47%, and contour error fell 74.54%. Evaluated dimensions are 8.981 x 8.981 x 30.500 cm against
the documented 9 x 9 x 30.5 cm target. This remains `CORRECTED_PENDING_HUMAN_FORM_REVIEW`: the old
rejection is not erased, multi-view artistic acceptance is not inferred from metrics, and no skill
is promoted. Evidence: `runs/2026-08-15_nailsea-form-correction/`.

## Update -- 2026-08-15 (typed editable high/low packaging and runtime transfer)

Replaced the Nailsea generator's asset-specific duplicate/collection helper with the typed
`package_high_low_variants` operation. It keeps the source as the high variant, creates an
independent editable low mesh, places each in a separate collection, copies the live modifier stack,
sets only the low Subdivision level, and applies no modifiers. Transaction ownership now includes
the target's collection membership and newly created collections as well as object, mesh, transform,
metadata, modifier, and selection state.

The controlled lab commits one package, rejects a second after mutation, and rejects a collection-
name collision before persistent change. A separate Blender process verifies independent cages,
equal base topology, live Subdivision/Solidify stacks, different evaluated density without applying
anything, complete persistent IDs, and removal of every rollback-created object, mesh, and
collection. The real Nailsea artifact was regenerated through the typed operation and passed its
fresh saved-scene verifier with `HIGH_POLY`/`LOW_POLY` isolation and both stacks unapplied.

This closes editable internal variant packaging, not true production retopology. Purpose-authored
low topology, UVs, bake transfer, and export remain separate open work.

## Update -- 2026-08-15 (question-driven reference research policy)

Applied the already completed seven-video reference-workflow synthesis instead of replaying the
videos or collecting more notes. `ReferenceResearchQuestion` and `ResearchCandidate` now retain the
unknown property, trigger, impact, exact queries, every inspected candidate, accept/reject reason,
linked factual reference, resolution, and reversible modeling constraint. An open high-impact
question blocks both the reference audit and Blender's strict `REFERENCE_ANALYSIS` transition.

Controlled positive and negative cases, including a real Blender 5.2 stage transition, confirm that
unaudited question evidence is refused without mutating stage state. This is experimental evidence
for one reference-policy skill, not proof that a resulting model will be more accurate. A fresh
board, human review, and equal-budget target-only versus structured-reference build remain open.

## Update -- 2026-08-15 (secondary-view depth changes construction strategy)

Closed the gap matrix's controlled component/depth reconstruction experiment without bypassing the
required human reference gate. Rectangular and 16-sided radial fixtures each pit one continuous
full-depth body against a narrow body plus separate full-front faceplate. Their front silhouettes
are exactly identical (`1.0` IoU), so the executable policy refuses to choose and the planner emits
`RESOLVE_SECONDARY_VIEW_STRATEGY` with no Blender mutation.

The fixed-frame top view preserves `1.0` IoU for the continuous candidates and reduces the separate
controls to `0.711577` and `0.695574`. Both exceed the frozen `0.15` decision margin. The resolved
evidence overrides a deliberately conflicting generic separate-material prior, and a fresh Blender
process confirms one-object/one-component continuity rather than joined disconnected shells.

This promotes the narrow secondary-view strategy skill to `TRANSFER_VALIDATED` across controlled
shape families. It does not infer depth from photographs, authorize an unreviewed model, or prove
professional fidelity. The next promotion gate is a real unrelated multi-view prop decision with
typed runtime telemetry and human visual comparison.

## Update -- 2026-08-16 (curved Bevel normal-policy boundary reproduced)

`runs/2026-08-16_curved-bevel-normal-policy/` returns the earlier hard-surface video claim to a
direct Blender test. Twelve editable, unapplied variants compare an unbeveled semantic baseline,
plain smooth Bevel, Harden Normals, and Face Strength followed by Weighted Normal across a uniform
12-sided cylinder, an equal-count uneven 12-sided cylinder, and a uniform 16-sided taper.

Plain smooth Bevel bends cap normals by `8.4464°–8.4823°`. Harden Normals restores every curved
side to its unbeveled baseline and makes cap error `0°`; Weighted Normal also flattens caps and is
near-analytic on the uniform cages. The uneven circle is the decisive failure control: its baseline
is already `5.0°` wrong from alternating 20°/40° spacing, Harden Normals preserves that error, and
Weighted Normal increases it to `9.9988°`—worse than plain smooth Bevel at `9.0773°`.

The promoted experimental rule is topology-first: compare against an unbeveled baseline; do not
use flat-panel Weighted Normal success as a blanket curved-skin policy; and repair distribution
when the restored baseline remains wrong. This is controlled radial/taper transfer, not arbitrary
double curvature, SubD transfer, a human-reviewed prop, or runtime validation. Swingline remains
externally gated.

## Update -- 2026-08-16 (official seam lesson returned to current production evidence)

`runs/2026-08-16_uv-seam-production-transfer/` closes a real provenance gap: the official UV
episode had independent frame/speech review, but its older Blender reproduction was no longer
retained and the current high/low fixture used Smart Project. Blender 5.2 now reproduces one
longitudinal cut on a connected 12-sided radial tube and transfers it to a bent rounded-rectangle.

Matched no-seam controls measure `15.00°` and `14.82°` mean corner-angle error; authored layouts
measure `1.87°` and `0.66°`. Both high/low pairs are separate, independent, one-component all-quad
cages with live Solidify→Bevel stacks. Evaluated shells are closed, three-view production audits
pass, tangent bakes are packed Non-Color data connected through Tangent Normal nodes, and fresh GLB
imports contain one low mesh with UVs and material. The retrieval benchmark also exposed and fixed
an over-broad first draft: generic UV overlap-after-pack still abstains. The promoted skill remains
controlled `TRANSFER_VALIDATED`; Swingline production use still requires human authorization.

## Update -- 2026-08-16 (native range-scoped Gemini and reference-card transfer)

The user-supplied TubeAlfred/Gemini account exposed one concrete missing capability: long or
chaptered videos should be narrowed with Gemini's native `video_metadata` offsets instead of always
spending a whole-video request. `knowledge_engine/gemini_video_study.py` and
`tools/analyze_video_with_gemini.py` now accept a complete start/end pair, send those offsets through
`types.VideoMetadata`, require absolute full-source timestamps, reject episodes outside the requested
interval, preserve the range in provenance, and keep the whole-video Interactions path unchanged.
Focused tests cover incomplete/invalid ranges, SDK request shape, endpoint routing, and out-of-range
model output. TubeAlfred itself is not callable in the current Codex environment, so no transcript,
metadata, search, or chapter evidence is falsely attributed to it.

The public 3DTudor reference-setup lesson was then reprocessed. Its whole-video pass produced a
useful first candidate but direct browser playback found later timestamp drift: by roughly 142 s the
video had entered external reference-board discussion. Those later ranges are rejected. A native
24–124 s pass stayed inside scope and returned three absolute-timestamp episodes for the free-view
failure, orthographic re-import, and crossed-card/wireframe setup. Five retained browser frames plus
sampled visible machine captions independently verify the combined correction episode.

`create_reference_image` and `audit_reference_images` return the lesson to Blender 5.2. A CUSTOM
free-view Image Empty fails construction calibration; a FRONT reproduction and distinct FRONT/RIGHT
transfer measure 0° error; and a front/right pair sourced from the same duplicated image is rejected
when distinct multi-view evidence is required. The first audit run failed because newly assigned
rotations had stale `matrix_world` values; a view-layer update repaired the measurement without
changing thresholds. The resulting skill is `TRANSFER_VALIDATED` for scene setup only. It does not
prove photographic orthography, source identity, calibration, model likeness, or authorization to
bypass Swingline's human gate.
