# Hard-surface and ornamental prop curriculum (v3)

Updated: 2026-08-16. This is the operational merge of the two user-supplied
hard-surface/stylized-prop curricula. It supersedes their duplicated queues while retaining
the evidence history in `BLENDER_MODELING_CURRICULUM_V2.md` and the distinct-source mapping in
`VIDEO_CURRICULUM_2026_ADDITIONS.md`.

## Decision

The general curriculum has the broader production coverage. The ornamental/elongated-prop
curriculum correctly changes the immediate priority: a convincing elongated prop cannot be
rescued by bevels, material, or ornament if its silhouette, landmarks, and depth were inferred
from one view. Therefore the next learning sequence is **multi-view interpretation -> primary
blockout -> surface diagnosis -> topology/representation -> production finish**.

This is a priority change, not a claim that the existing videos are fully learned. Existing
extractions are candidates unless their claims have passed independent review, a controlled
reproduction, a different-geometry transfer, and (where useful) runtime use.

## Source de-duplication and study queue

| Priority | Source / curriculum role | Existing status | Required evidence before it changes modeling policy |
| --- | --- | --- | --- |
| P0 | `xHJzDpijPqg` — robot from front/side references | **Unavailable:** direct YouTube check on 2026-08-16 reports “Private video”; no analysis was made | Obtain a user-authorized/public replacement that visibly models from matched front/side references, then review shared landmarks and front/side correction; reproduce on a non-robot reference; measure localized errors in both views |
| P0 | User-provided same-object reference sets | Available locally, but current sword work is front-view constrained | Reference-set audit, landmarks, projection uncertainty, and a human-approved reference plan before blockout |
| P1 | `CdHXpHPWKYo` — BornCG “Smoothing & Hard Edges” | Source correction: the supplied `HH7InXu7ZdU` URL is actually an Edit Mode lesson. Correct source has a duration-bounded Gemini candidate extraction, still unverified | Independently inspect before/during/after frames and speech; cross-check current Blender behavior; then run a controlled classification test separating geometry, normal, SubD, and edge-radius causes |
| P1 | `2Gg5QY5h9pQ` — cylinders / circular forms | Listed; no verified episode in the current curriculum record | Scale- and silhouette-aware radial-density transfer, not a fixed segment-count rule |
| P1 | `_bpsEd_5IW4` — clean hard-surface topology | Listed; no verified episode in the current curriculum record | Curved/highlight-critical versus flat/hidden surface comparison on different geometry |
| P1 | `seFDI4pqnOo` — Boolean topology | Listed; no verified episode in the current curriculum record | Boolean-versus-native/inset representation decision with evaluated-surface review |
| P2 | `46XJ6_V5PN0` — carabiner / elongated curved form | Listed; no verified episode in the current curriculum record | Compare curve, profile, and polygon construction on an unrelated ornamental support |
| P2 | `nsTjnQ067sw`, `vPeeybzxfLI`, `Ml2t8uxPAQU` | Earlier captures exist | Re-study only for a named unresolved decision; do not create duplicate summaries |
| P2 | UV, PBR, normal/displacement lessons | Earlier captures exist; asset application is shallow | Apply seam, packing, roughness, and geometry-vs-normal decisions to a validated asset |

The broad fundamentals, modifier overview, materials, UVs, and stylized-process sources stay in
the curriculum as retrieval material. They do not displace P0 reference interpretation merely
because they are easier to process.

## Modeling contract derived from both curricula

For every unfamiliar ornamental or hard-surface prop:

1. Establish source identity, projection uncertainty, all useful views, primary silhouette,
   landmarks, overlaps, negative spaces, and material boundaries.
2. Decide component boundaries from form/function and visible seams. Use a continuous editable
   cage where the reference shows one continuous surface; use separate meshes only for genuine
   manufactured/layered components. Do not equate "single object" with automatic quality.
3. Build primary mass first, using edit-mode extrusion/loop placement/insets where that gives the
   cleanest cage. Do not add ornament to conceal an unresolved silhouette or depth error.
4. Compare front, side, and applicable perspective/three-quarter views before secondary form.
   Localize the largest mismatch instead of accepting a global score.
5. Diagnose edge defects before acting: base geometry, normals, edge radius, SubD control, or
   modifier order are different causes. Keep finishing modifiers live and inspect cage and
   evaluated surface separately.
6. Choose curves, booleans, mirrored geometry, insets, separate overlays, material detail, or
   normal/displacement according to silhouette impact, thickness, repetition, symmetry, shadow,
   and editability.
7. Only after proportion and surface approval, prepare UVs/materials and package independent
   high/low collections with unapplied modifier stacks.

## Evidence gate for each video

Use `VIDEO_EXTRACTION_PROTOCOL.md`. Gemini video input is a candidate extractor, never a
validator. Each source must retain only permitted derived evidence, then pass:

`source identity -> actual audio/video candidate extraction -> independent before/during/after
frame + speech alignment -> controlled reproduction -> different-geometry transfer -> runtime
use (when a planner policy is claimed) -> reference-driven application`.

Identity binding is required before extraction: use a ranked discovery candidate or an independent
direct-source record containing the exact URL, title, creator, and duration. This guards both
Gemini endpoints against accidental near-match tutorial substitution; it does not validate the
technique itself.

Current Gemini prerequisite: install `requirements-video-learning.txt`. A denied API credential is
an external-access failure, not evidence that a source was watched. The 2026-08-16 attempt against
the P0 robot lesson was denied by the currently configured credential. A direct browser check then
found that the source itself is private in the available session. No analysis file, source media,
or modeling claim was created; see
`runs/2026-08-16_video-study-multiview-reference-robot/source_availability.json`.

## Acceptance before another sword-like attempt

An elongated ornamental candidate is eligible for review only when it has an approved multi-view
reference plan (or explicitly bounded single-view interpretation), a landmark/proportion table,
front and side silhouette comparison, stated continuous-versus-separate component rationale,
live modifier report, cage/evaluated/solid visual evidence, and an honest unresolved-depth list.
It is not acceptable merely because it has a clean technical audit, UV layers, or a high/low
collection split.
