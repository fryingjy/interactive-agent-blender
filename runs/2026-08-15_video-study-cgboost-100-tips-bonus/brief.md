# CG Boost -- 100+ Tips to Boost Modeling in Blender (Bonus chapter)

Final chapter of curriculum item #4's first pass (see
[[../2026-08-15_video-study-cgboost-100-tips-meshmodeling/brief.md]] and
[[../2026-08-15_video-study-cgboost-100-tips-modifiers/brief.md]] for the earlier chapters and the
overall video's scope). This run covers **Bonus** (1:49:27-1:56:03, tips #101-102 of 101, plus the
outro), the last unprocessed section of the video. Unlike the Modifiers-chapter run, no video/frame
analysis was available here -- this pass is transcript-only, working from auto-generated captions
with `[M:SS]` timestamps and no visual confirmation. Confidence on every item is capped accordingly
(0.45-0.5); claims are phrased as "per the transcript" / "per the narration," never as something
observed on screen.

## Scope: genuinely small

This is a short, niche chapter and it is treated that way. Tip #101 (Draw Cables) is a real
technique for a category of part this project has never built (cables/hoses/wires routed between
objects). Tip #102 (3D Sticky Notes) is a workflow-annotation prop for the video's own presentation,
not a construction technique this project is likely to need soon, but its underlying
Shrinkwrap-plus-weight-paint conforming mechanism is worth recording because it is a materially
different variant of a technique already captured from the Modifiers chapter. Four items were
captured; nothing was padded to hit a target count.

## Items captured (4)

1. Draw Cables base setup -- bevelled curve (Bevel Depth ~0.25, resolution 64) drawn freehand with
   the Draw tool, after clearing the curve's default control points. First captured technique for
   cable/hose/wire-type geometry; this project's current construction approach is entirely
   mesh/edge-loop based and has no analogue for this.
2. Draw Cables surface Offset = 1 (not the default 0) when drawing directly onto a mesh surface, so
   the cable sits flush on top of the surface instead of half-buried in it. Recorded as a `DECISION`
   because the failure mode at the default value is a real, silent-looking defect the narration
   explicitly calls out.
3. 3D Sticky Note base construction -- plane, subdivide, proportional-edit bend, Shade Smooth,
   Subdivision Surface (level 2) with Mean Crease = 1 on the outer boundary for a sharp silhouette
   with a smoothed interior, Solidify (~0.03) for thickness, Auto Smooth to avoid shading artifacts.
   Low priority (sticky notes are not a part type this project is likely to build), captured because
   it was cheap to record while already reading this chapter.
4. Shrinkwrap Project scoped by an initially-empty Vertex Group, built up with graduated (0-1)
   Weight Paint values rather than binary group membership, so only part of a flat object's surface
   conforms to a curved host and by a continuously adjustable amount. This is the same underlying
   mechanism as the vertex-group-scoped Shrinkwrap Project item already captured from the Modifiers
   chapter (tip #93, the sensor-mount-footprint case) and from
   [[video-curriculum-mug-diagnosis]]'s untested handle-attachment hypothesis, but that earlier case
   used a fixed (already-populated) vertex group for a binary in/out footprint. Here the group starts
   empty and gets its membership and strength from weight-painting, which is a genuinely different,
   softer control scheme (graduated blending vs. hard boundary) -- recorded as a separate item rather
   than merged with the earlier one.

## Not captured as formal items

The outro / sign-off itself (approximately 1:56:01 onward, "so you will never forget any of the
tips you have learned in this video") carries no modeling content. The face-snapping /
"project individual elements" snapping-option setup used to drag sticky notes around interactively
(per the transcript, ~1:53:05-1:53:23) is folded into item 4's claim rather than split out, since it
is a supporting UI step for the same workflow, not an independent technique. The specific choice of
target object (water gallon vs. head, per the transcript ~1:55:35-1:55:48) is an example, not a
generalizable claim on its own.

## Curriculum item #4: first pass now complete across all chapters

This closes out curriculum item #4's first pass. All seven chapters of the video have now been
processed: User Interface, Selection, Mesh Modeling, Transformation, Modifiers, Organization, and
Bonus. The two standing follow-ups flagged during this pass remain open and are not resolved by this
chapter: (1) the Modifiers-chapter contradiction between this project's Bevel-before-SubD policy and
the video's demonstrated Bevel-after-SubD "Clean Hard-Surface Sub-D Modeling" order (needs a
controlled test, not a documentation edit), and (2) the vertex-group-scoped Shrinkwrap Project
technique (now confirmed a third time, across Modifiers tip #93 and this chapter's sticky-note case)
as an untested hypothesis for the mug's unresolved handle-attachment failure -- still worth actually
trying on the mug, not just noting as plausible again. The curriculum item itself would benefit from
a second, differently-focused pass later (the curriculum's own framing: "why would a professional
choose this tool here"), but that is future work, not part of this pass.
