# Video discovery and source-identity validation

## Question

Can the repository find new Blender lessons for current curriculum gaps without archiving videos,
avoid known/held-out contamination, and pass a discovered source into multimodal study without
misattributing another video?

## Discovery result

Three live YouTube metadata searches produced a 15-item ranked study queue. Ten video IDs known at
discovery time were excluded and snapshotted in `known_sources_at_discovery.json`. Held-out asset
terms and explicitly deferred character/sculpt/animation
topics were rejected before queueing. Search used `yt-dlp --flat-playlist`; no media, captions, or
transcripts were downloaded, and discovery promoted zero knowledge.

The ranking is deliberately weak: it measures metadata fit and triage value, not authority,
correctness, or learning. Every candidate remains `DISCOVERED_METADATA_ONLY` with
`MULTIMODAL_EXTRACTION` as its next gate.

## Failure found and fixed

The first Gemini call requested queue rank 1 (`sCdhkLUCV8A`) but reported a different video ID,
title, and creator. The old wrapper rewrote the source URL to the requested URL and accepted the
result. That could silently attach a complete lesson to the wrong source.

The pipeline now fails closed when the model-reported video ID differs or cannot be verified. A
discovery-bound call additionally embeds and validates exact title, creator, and duration metadata.
The earlier 2026-08-15 Gemini validation artifact is retroactively marked rejected for the same
identity defect.

## Strict retry and independent review

The strict retry reported the exact queue source identity and produced five candidate episodes. A
live browser review confirmed the page identity and partially corroborated the Face/Closest snap
discussion at 02:00. It also found that the claimed Grid Fill interval begins too early: at 04:32,
the source was still discussing splitting sections. Browser frame capture repeatedly timed out, so
visible-action verification remains incomplete.

Disposition: `INDEPENDENT_REVIEW_PARTIAL_TIMESTAMP_DEFECT`. No lesson item is promoted and no
runtime skill is created from this run.

## Reproduction

```powershell
python tools/discover_video_lessons.py --query "Blender reference modeling workflow multi view proportion blockout" --query "Blender hard surface subdivision topology curved product workflow" --query "Blender retopology edge flow density poles hard surface" --output runs/2026-08-15_video-discovery-queue/discovery_queue.json --per-query 8 --maximum 15 --exclude-source-file runs/2026-08-15_video-discovery-queue/known_sources_at_discovery.json --heldout-target-term bialetti --heldout-target-term moka --heldout-target-term camera --heldout-target-term telephone --heldout-target-term watering --heldout-target-term lamp --heldout-target-term boombox --heldout-target-term wrench --exclude-topic-term character --exclude-topic-term sculpt --exclude-topic-term zbrush --exclude-topic-term animation --exclude-topic-term rigging
python tools/analyze_video_with_gemini.py --discovery-queue runs/2026-08-15_video-discovery-queue/discovery_queue.json --rank 1 --output runs/2026-08-15_video-discovery-queue/strict_top_candidate_analysis.json
python tools/verify_video_discovery_run.py
```

## Boundary

This closes portable metadata discovery and source-identity enforcement. It does not close visual
action recognition, full speech/action synchronization, reproduction, transfer, or professional
modeling readiness.
