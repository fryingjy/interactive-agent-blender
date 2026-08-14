# Video extraction protocol

Adopted 2026-08-14 (user-authored, superseding the informal extraction approach used earlier this
session). Governs how every video in `docs/BLENDER_MODELING_CURRICULUM_V2.md` is studied. This is
not a "watch and summarize" pass -- these videos are training sources for a professional-modeling
agent, and the objective is never "the AI knows a bevel exists." The objective is "the AI understands
when, where, why, and how a professional modeler would use a bevel, what can go wrong, how to
diagnose the failure, and what alternative strategies exist."

## Per-video procedure

1. Obtain the actual video/audio whenever legally and technically possible (currently: Gemini
   video-understanding on the real video, not transcript-only -- see `.env` / `GEMINI_API_KEY`).
2. Listen to the instructor's spoken explanation.
3. Analyze what is visibly happening in Blender.
4. Align speech with the actual modeling action.
5. Record: starting state, selected object/component, modeling stage, operation, parameters,
   resulting geometry, topology change, modifier change, visual result, reason for the decision,
   alternatives considered, mistakes, corrections, shortcuts, professional heuristics.
6. Separate four categories explicitly, never blur them:
   - **OBSERVED FACT** -- what is actually visible on screen.
   - **INSTRUCTOR CLAIM** -- what the instructor says is true or why.
   - **INTERPRETATION** -- my own reading of why the technique works, when observed fact and
     instructor claim don't fully explain it.
   - **HYPOTHESIS** -- an untested extrapolation to a case not shown in the video.
7. Do not convert "the artist pressed X" into "X is the correct modeling technique." Instead
   determine WHY the artist used X here.
8. Extract transferable principles, not asset-specific steps.
9. Compare extracted principles against the Blender Manual, the Blender Python API docs, other
   professional tutorials, Blender Stack Exchange, Blender Artists, or other credible sources where
   practical.
10. If sources disagree, preserve the contradiction -- do not silently pick a side. (Matches the
    existing practice in `runs/2026-08-14_video-curriculum/synthesis.md`, e.g. the
    booleans-are-finger-painting-vs-recommended-for-beginners reconciliation.)
11. For important claims, design a controlled Blender experiment.
12. Test the technique on DIFFERENT geometry from the tutorial's own asset.
13. Only promote a technique to reusable/trusted knowledge if it survives that transfer test.
14. Record: source, Blender version, timestamps, claim, evidence, experiment, transfer result,
    limitations, confidence.
15. The resulting knowledge must be retrievable by the modeling planner and must actually influence
    future modeling decisions -- not sit inert in a JSON file.

## How this maps onto the existing implementation

- Steps 1-8 map onto `knowledge_engine/video_knowledge.py`'s `KnowledgeItem` schema: `knowledge_type`
  (PROCEDURE/PRINCIPLE/DECISION/VISUAL_CUE/FAILURE), `claim`, `source` (timestamped),
  `supporting_evidence`, `rejected_alternative`, `reason`, `confidence`.
- Step 6 (OBSERVED FACT / INSTRUCTOR CLAIM / INTERPRETATION / HYPOTHESIS) is a genuinely new
  discipline not yet formally encoded in the schema -- items captured before 2026-08-14 (via this
  protocol's adoption) do not carry this separation explicitly, though `supporting_evidence` already
  distinguishes direct quotes/transcript from paraphrase in most of them. Going forward, new items
  should make this separation explicit in the claim or supporting_evidence text.
- Steps 11-14 (controlled experiment, transfer test on different geometry, promotion gate) map
  directly onto `apply_transfer_test()` in `video_knowledge.py`, which already enforces: a transfer
  test must target a genuinely different asset than the one the knowledge was captured from, and
  status only advances to `TRANSFER_VALIDATED` on a real recorded pass.

## The current real gap

As of 2026-08-14, **106 knowledge items exist across 22 processed videos, and zero have completed
steps 11-14.** All remain at status `CAPTURED` (a few `PROMOTED`-adjacent via strong cross-source
convergence, but convergence across sources is not the same thing as a transfer test on new
geometry, and the schema doesn't conflate them). Steps 11-14 require actually building something in
Blender -- which is blocked while modeling work is paused per direct user instruction ("scrap this
and all the other models for the time being"). This is the single most important unresolved
tension in applying this protocol and is flagged to the user directly, not resolved unilaterally.

## Explicit warning (user's own words, preserved verbatim as the standing rule)

> Don't make Claude watch 100 videos and then declare the AI "trained." That's exactly the failure
> mode we've been trying to avoid with this project. The valuable loop is: watch → understand →
> extract principle → verify against other sources → reproduce → test on different geometry → apply
> to a real reference → measure result → retain knowledge.
