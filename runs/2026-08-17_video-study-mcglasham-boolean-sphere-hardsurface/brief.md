# Ian McGlasham -- "Boolean Sphere Hard Surface" (#18, Subdivision Surface Modelling series)

Direct follow-on from `runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/`, same
creator and series. That earlier batch captured "Connecting Cylinders," whose narration states plainly
that "a boolean will destroy your topology instantly with zero chance of recovery." This episode was
picked specifically because its title -- "Boolean Sphere Hard Surface," from a source already on record
as boolean-averse -- promised a direct test of that stance against a curved cutter, which this project's
own boolean workflow has never had a real answer for (no Weld-modifier step, no post-boolean-bevel
cleanup step exists anywhere in this project's typed op surface). Transcript-only extraction, no
video-understanding pass.

## The most important finding: not a safe exception, and not a simple reinforcement either -- a third thing

The framing question going in was: does this video show a genuinely safe way to boolean a curved
surface (a controlled exception to "never boolean"), or does it actually demonstrate why not to, or is
it a cleanup technique after the fact? Per the transcript, the honest answer is closest to the third
option, but sharper than "cleanup after the fact" suggests -- it's closer to **boolean-as-disposable-reference,
never boolean-as-final-geometry**.

The video does not apply the Boolean modifier to the model that ships. It duplicates the target mesh
into three copies -- "final cube" (explicitly named as the one that will become the finished
subdivision-surface model), "patch," and "sphere" (the cutter) -- and the Boolean modifier is applied
only to "patch," immediately, with the cutter hidden right after. The narration's own assessment of the
raw boolean result matches this project's existing findings almost exactly: "we'll see a lot of
problems, there are a lot of n-gons and a lot of stray vertices, and that's the nature of the boolean
modifier, that's what it does." Nothing about that raw output is kept. What follows is roughly nine
minutes of manual reconstruction: dissolving the boolean's own stray two-edge vertices, re-insetting and
straightening the patch boundary by hand (Edge Rail inset, scale-to-zero per axis with an active-element
pivot), building matching loop cuts on the real "final cube" via vertex snapping, joining the two
objects, and running Merge by Distance with the result checked against a known expected vertex count. Even
after all of that, the video finds and has to separately fix a residual light-pinching artifact around a
boolean-origin pole using a Laplacian Smooth modifier. The closing line makes the framing explicit: "this
is one of the main methods i use when i'm given boolean sketches of objects and i start remaking them
properly" -- the boolean output is treated as a sketch, not a deliverable.

So: this does **not** contradict the "never boolean curved surfaces" stance already in this project's
knowledge base -- it agrees with it, and goes further, by showing that even in the one case where a
boolean is used at all, its output is never trusted past the moment it's used to measure an intersection
profile. The status of every item below is CAPTURED, not CONTRADICTED, because there is no genuine
conflict: both sources treat raw boolean output as unusable, and this video does not claim otherwise. Where
it adds something new is procedural detail this project didn't have before -- concrete, exploitable
patterns in *how* boolean damage is shaped (defect vertices cluster at exactly two edges each; damage
scales with cutter density) and concrete techniques for the manual reconstruction step this project's own
boolean workflow currently has no answer for at all.

## Items captured (8)

1. DECISION -- the core boolean-as-disposable-reference workflow: three duplicates, boolean only on the
   throwaway "patch," cutter hidden immediately, raw output never kept.
2. PROCEDURE -- exploit the two-edges-per-defect-vertex signature of boolean n-gon damage: Select
   Similar > Amount of Connecting Edges, then Dissolve Vertices, in one pass.
3. PROCEDURE -- turn a cleaned boolean patch into a reusable insert: double inset (second with Edge
   Rail), delete the outer ring, then hand-straighten the boundary loop with active-element scale-to-zero
   per side.
4. PROCEDURE -- graft the patch back in: vertex-snapped loop cuts on the target mesh to match the patch
   boundary, join, then Merge by Distance verified against a known expected vertex count rather than
   trusted at default settings.
5. VISUAL_CUE -- a residual boolean-origin pole can still pinch light under Subdivision Surface even
   after clean quad topology; diagnosable via orbit-dependent highlight size and confirmable under a
   zebra-stripe matcap.
6. PROCEDURE -- the Laplacian Smooth fix for that pinch: vertex-group-scoped, placed before Subsurf in
   the stack, Repeat tuned by eye (~130 of a possible 200 here).
7. PRINCIPLE -- keep the boolean cutter's own geometry deliberately low-resolution (subdivided-cube-cast-
   to-sphere, not a dense UV Sphere), since damage scales with cutter density.
8. PRINCIPLE -- Subdivision Surface should always be the last modifier in the stack (stated in passing,
   in an unrelated animated-bonus-object segment, but explicit and general).

## Not captured as formal items

The video's closing "purple thing" segment (a separate sphere given random individual-face extrusions,
three Wave modifiers, and a rotation animation) is a stylistic flourish unrelated to the boolean/topology
technique and was not captured beyond the one general Subsurf-ordering statement it happened to contain
(item 8). The video's passing mention that "we would now be free to use shrink wrapping to make things
even more precise but this is normally fine" was not captured as a separate item -- it is a one-line aside
with no procedural detail, and this project already has a fuller Shrinkwrap-based technique captured from
the "Connecting Cylinders" video in the prior batch.
