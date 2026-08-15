# Independent video-episode review gate

**Status:** mechanism PASS on a project-owned fixture; public tutorial review remains PENDING.

The new gate requires a verified source identity, an independent reviewer, existing before/during/
after frames that bracket the episode, overlapping transcript evidence, an observed visible action,
and explicit speech/action alignment. Missing evidence stays `PENDING_REVIEW`; an observed source,
visual-action, or speech/action contradiction becomes `REJECTED`.

The six-second project-owned fixture was sampled at 1.833s, 2.167s, and 4.167s. Direct frame review
found an angular `BASE` diagram before the episode, a rounded `EVALUATED` diagram during it, and the
next front/side/top comparison afterward. The authored VTT overlaps 2.0–4.0 with “inspect the
evaluated surface.” All nine review predicates pass. Six controls correctly cover model-only
claims, a missing after frame, non-overlapping speech, a source mismatch, an explicit visual
mismatch, and public-page identity without decoded media.

`apply_independent_episode_reviews` now prevents Gemini extraction from self-verifying. Review video
ID and timestamps must match the requested episode; complete matching reviews can advance extraction
provenance to `INDEPENDENTLY_FRAME_VERIFIED`, while partial and contradicted sets remain explicitly
partial or rejected. Knowledge promotion is unchanged and still requires reproduction and transfer.

The actual YouTube check for `yi87Dap_WOc` did **not** pass. The normal page exposed the correct title
and 11:19 duration label but the media element stayed at current time 0, unknown duration, and ready
state 0. The embed fallback showed YouTube error 153. No decoded frame was observed, so the claimed
307–400s Blender action remains `PENDING_EXTERNAL_FRAME_REVIEW`. No public video was downloaded or
archived.
