# Ian McGlasham -- "Retopologising Text" (#10, Subdivision Surface Modelling series)

Transcript-only extraction (no video-understanding pass) of `TC-qyGzRyeQ`, 14:08 long, same
channel/series as `runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/`. That run
already established this creator's numbered SubD series as a trusted source for this project; this
episode is #10 in that series, sitting between the primitive-fixing videos already captured and the
chess-piece build episodes that follow it.

## Why this video, and why it's captured as a general technique, not a text tutorial

The episode's own title and premise are about retopologizing text glyphs. It is filed under this
project's video-study process anyway, and extracted with a specific reframing, because the transcript
itself states in its opening seconds that this is not really about text: "before we tackle the bishop
i want to quickly talk about text **or any closed curve like a logo** and how to handle that... i'm
going to quickly show you how to retopologize one letter and from there hopefully you'll see that you
can use the method to **retopologize any text**" -- and later, describing the curve setup step
directly: "that's how you retopologize any **closed curves**" (transcribed as "clause curves," almost
certainly a mis-transcription of "closed curves"). The letter "a" the video works through is used only
because it happens to have "lots of curves, a few pointed parts, a hole in the middle" -- i.e. it's
picked as a stand-in for a generically messy closed outline, not because anything in the method is
specific to font glyphs.

Every technique captured below was checked against this reading and phrased in terms of "a closed
outline" / "an arbitrary closed-curve shape" rather than "text," except where the step is genuinely
about curve-object mechanics (Resolution Preview, Fill) that only makes sense for a curve-derived
outline in the first place -- which itself is not text-specific, since a logo or any traced silhouette
would also start life as a curve object in Blender. Nothing in the eight captured items depends on the
outline being a letterform.

## The most important finding: a complete, reproducible messy-outline-to-clean-quads technique

The video's core sequence (items 4 and 5 below) is a genuine, general answer to a problem this
project's knowledge base didn't have a clean fix for yet: given an arbitrary closed 2D outline with no
useful internal structure (an organic silhouette, not a primitive), how do you get an evenly-spaced,
all-quad border and interior fill without pushing every point by hand? The answer given is mechanical
and repeatable: fill with throwaway n-gons, inset all of them by a tiny amount, delete the original
n-gons to leave a thin evenly-inset border strip, then Edge Slide (G G + Alt, with a typed numeric
factor) each boundary loop to redistribute its vertices evenly -- followed by F2-assisted directional
quad fill for the interior, with vertex-count matching via loop cuts before filling across any gap.
This complements, rather than duplicates, the boolean-free curved-surface join technique captured from
"Connecting Cylinders" in the sibling run above -- that one solves joining two primitives; this one
solves converting one arbitrary flat silhouette into quads. Also captured: the same "control loop"
mental model from the primitives videos, now applied to a flat hand-built mesh (with a new detail, a
Seam-as-visual-label convention distinct from Crease-based sharpening); a named failure mode of the
manual fill workflow (On Cage reveals normal-direction pinching, fixed by Recalculate Normals Outside,
not by re-editing geometry); and a general SubD-cage inspection technique (Wireframe + Optimal Display
off + stepping through modifier Levels 0-3).

## Items captured (8)

1. DECISION -- hand-retopologize a closed outline rather than use the Remesh modifier, which the video
   names explicitly as a commonly-tried but inadequate shortcut for this exact problem.
2. PROCEDURE -- curve prep before mesh conversion: low Resolution Preview, Fill off.
3. PROCEDURE -- match span/vertex counts across boundary segments (Ctrl+R works on curve points too),
   then Loop Tools > Relax exactly once rather than hand-pushing points.
4. PROCEDURE -- the core border-generation technique: fill / inset / delete / per-loop Edge Slide with
   a typed numeric factor, repeated for the outer silhouette and every interior hole.
5. PROCEDURE -- F2-assisted directional quad fill, with a two-vertex pre-selection trick to disambiguate
   fill direction and loop-cut count-matching before filling across an uneven gap.
6. PRINCIPLE -- control loops just inside every boundary, marked Seam as a visual-only label, tuned
   with axis-independent G G sliding.
7. FAILURE -- On Cage display can reveal pinched areas from manual fill work that are a normals-direction
   problem, not a topology problem; fixed by Recalculate Normals Outside, not by re-editing geometry.
8. PROCEDURE -- general SubD base-mesh inspection: Wireframe display + Optimal Display off + stepping
   modifier Levels 0-3 to see the true cage independent of the smoothed render.

## Not captured as formal items

The aside about Ctrl+A (Apply Transform) throwing "fonts can only have scale applied" on a text/curve
object (~65-78s) is a minor Blender quirk the video itself shrugs off ("who knows what that's all
about... it doesn't really matter") -- not a technique, and not confirmed to generalize to curve
objects that aren't text. The extrude-for-thickness step (select all, E, 0.1, shade smooth, ~576-585s)
was read but folded into item 6's supporting context rather than given its own item -- "extrude a flat
shape to give it depth" is generic Blender knowledge already assumed elsewhere in this project, and
nothing about the extrude value or process is specific or novel here. The closing Wave-modifier
deformation test (~686-793s) demonstrates that the resulting mesh deforms and rotates cleanly with no
artifacting, which is a nice confirmation that items 4-7 actually produced clean topology, but it is a
demonstration of already-captured results rather than a new technique, so it wasn't split out on its
own (its one genuinely new piece of content, the Wireframe/Optimal-Display inspection method used
during it, is captured as item 8). The video's closing offer to make a full "retopologizing an entire
font" video was not acted on -- no such video was located or pulled for this run.
