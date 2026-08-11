# Official Blender lesson ingestion

**Date:** 2026-08-10

**Outcome:** multimodal ingestion + local transcription PASS; transcript accuracy remains bounded

Google-indexed Blender Studio pages returned HTTP 402 and YouTube extraction returned a bot-check,
so neither route was bypassed. Wikimedia Commons provided the same official Blender Fundamentals
videos as CC BY 3.0 originals. Three files were downloaded and ingested through the repository's
approved-root video pipeline:

| Lesson | Duration | SHA-256 | Evidence |
|---|---:|---|---|
| Modeling Introduction | 75.401 s | `f6a6fef06ca3b89c133ada732909925af019e95f9306a7834715b885a99473a6` | 4 decoded frames + audio stream |
| Extrude | 286.901 s | `2aa5cd83ce3e0915d55db4649cc1a7eb8629f0dc78c22daea78a267034c163c9` | 9 decoded frames + audio stream |
| Bevel Tool | 211.361 s | `2f52c26b21a3a965770f4def08af32bb9d414895b82f837174d124fbe107d34f` | 8 decoded frames + audio stream |

Direct visual observations include the Modeling workspace/modifier taxonomy, Extrude Region versus
Along Normals/Individual/to Cursor variants, and Bevel modifier width/profile/Clamp Overlap plus
None-versus-Angle limit controls. These reinforce existing tested operator principles.

The files contain video and audio but no creator captions. A local faster-whisper `tiny.en` pass now
provides timestamped machine transcripts (23 + 68 + 35 segments), with English detection probability
reported as 1.0 for each file. Important instructional claims were cross-checked against decoded
frames, current official docs, and existing Blender 5.2 labs in `lesson_study_report.md`; transcript
wording is not treated as authoritative. Downloaded media remain local evidence and are intentionally
not published to GitHub.

Sources: Wikimedia Commons file pages for the Blender-authored CC BY 3.0 originals.
