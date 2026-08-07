# Session note: SoapDish (subdivision-surface milestone, curriculum step D)

Reference: `reference/soap_dish/notes.md` — genuinely unseen before this session, deliberately
the first prop in this project requiring subdivision-surface workflow (control cage != final
surface) rather than flat-panel hard-surface bevels (Bottle/Flashlight/Mug/SpeakerEnclosure).

## Honest logging-discipline gap, stated up front

This directory's `decision_log.jsonl` does **not** cover the full session decision-by-decision
the way `runs/2026-08-07_speaker-typed-protocol/` does. The build-up portion of this session
(primitive creation, proportion scaling, basin inset, initial subdivision) was driven live
through the typed `begin_decision`/`perform_decision`/`verify_decision`/`commit_decision`
protocol — same guarantees, same real verification at each step — but a context-window
compaction happened mid-session, and per-decision JSON records for that early portion were
never written to disk before the compaction, so they cannot be reconstructed with real fidelity.
There is no server-side decision history API to recover exact before/after states or operation
parameters for that stretch after the fact (checked: `modeler_server.py`'s `_command_journal`
is an in-memory idempotency cache keyed by caller-supplied `command_id`, not a persisted audit
trail, and doesn't survive past the calls that used it).

Rather than invent plausible-looking JSON entries with fabricated revision numbers or
parameters for that stretch — which this project's own conventions treat as worse than an
honest gap — `decision_log.jsonl` here only contains entries for the portion of the session
with real, verifiable data: the n-gon problem, its fix, the live human/agent collision, and the
final verified state. This is a process failure to fix going forward (the decision log should be
written incrementally, immediately, from decision 1 of every session — the earlier sessions in
this project got this right), not something to paper over.

## What actually happened (narrative, backed by the logged entries below)

1. Built up a rounded rectangular dish control cage and a concave basin via inset + extrude,
   then subdivided the basin's interior (`cuts=3`) without matching the surrounding rim faces'
   resolution — produced 4 seven-sided n-gons on the rim (5 verts along the new-resolution
   shared edge + 2 original corners each), a real and expected consequence of resolution
   mismatch at a subdivision boundary, not a random defect.
2. Fixed it the fast way: `triangulate_ngons` on the affected rim faces. Reasoned this was
   low-risk since the rim was still flat at the time (the directive's own "context matters"
   guidance on when triangulation is acceptable vs. risky).
3. Separately, while building `evaluated_probe.py` to actually read the Subdivision-Surface-
   evaluated mesh (not just the control cage), found the Subsurf modifier's effect wasn't
   showing up at all — root-caused to `object_ops.add_modifier` never setting
   `show_viewport`/`show_render` (Blender's Python API does not default these True). Fixed,
   documented, committed (`bd4648b`).
4. Mid-diagnosis, `begin_decision` failed with a genuine external-edit detection (not a test):
   vertex count had doubled, n-gons had reappeared, several elements showed `agent_id: null`,
   mode was `EDIT`. Stopped immediately, reported the exact symptoms, and asked directly whether
   the user was editing live. **User confirmed**: "yes im fixing the topology to be all quads."
   Set `control_mode` to `USER_CONTROL` (first real deployment of that mechanism, built earlier
   this session, now exercised for real) and stood down.
5. User completed the manual fix ("fixed"). `control_mode` set back to `AGENT_CONTROL`.
   Re-observed via `get_full_state`: base control cage 66v/128e/64f, `valence_distribution
   {3: 8, 4: 58}` — clean, all-quad rim now properly matching the basin's resolution, revision
   168.
6. Verified the thing that actually matters — the Subdivision-Surface-**evaluated** result, via
   `get_evaluated_state` (the new `evaluated_probe.py` capability): 258v/512e/256f,
   `valence_distribution {3: 8, 4: 250}`, `area_outlier_count: 0`, `max_adjacent_face_angle_radians:
   0.802` (~46°). The 8 valence-3 poles are exactly the 8 original box corners — none clustered
   at the scoop/rim transition, and no area-outlier faces anywhere. Real evidence the manual fix
   avoided introducing new poles at the curved transition, which is the classic pinching failure
   mode this whole milestone exists to watch for.

No genuine unresolvable topology problem has shown up in this session — the n-gon issue was
real but resolved with existing project knowledge (triangulation, then the user's own
resolution-matching correction). Per `docs/RESEARCH_ROADMAP.md`, that means no research episode
is triggered yet. This is being watched honestly, not manufactured.

## Final closure check (new master directive, section 8: local + silhouette diagnosis)

Added `evaluated_probe.bounding_box_comparison()` -- base-cage vs evaluated-surface dimensions,
specifically to check for a real, different failure mode than pinching: Catmull-Clark shrinkage
("beach-ball" erosion) from missing corner support loops, which every other clean signal (0
non-manifold, 0 area outliers, moderate max adjacent-face angle) can miss entirely, since a
shape can be technically clean AND have quietly lost its intended silhouette proportions.

Result on the finished SoapDish: base cage 2.6 x 1.8 x 0.6 (exactly the reference's target
dimensions), evaluated surface 2.5573 x 1.7656 x 0.5967 -- `shrinkage_ratio_xyz`
`[0.9836, 0.9809, 0.9944]`. 1.6-1.9% shrinkage on X/Y, 0.6% on Z: minor and expected for a prop
whose own brief explicitly calls for a "soft and rounded" silhouette, not a sign of eroded
proportions or a missing support loop.

Combined with the earlier evaluated-surface check (0 area outliers, poles only at the 8 original
corners, max adjacent-face angle ~46 deg) and the independent `verify_mesh.py` pass (0
non-manifold/ngons/degenerate, consistent normals), this milestone's own success criteria
(smooth rounded outer form + shallow continuous basin + clean support/control topology + no
visible pinching + good pole placement + good evaluated surface) are met with real, measured
evidence at every layer -- base cage, evaluated surface, and now silhouette/bounding-box. No
further decisions are being added just to raise the count (directive section 15: decision
quality, not action count, is the metric) -- the milestone is judged complete here.
