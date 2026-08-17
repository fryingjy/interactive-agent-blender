# Ian McGlasham -- Subdivision Surface Modelling series (primitives + connecting cylinders)

Direct follow-on from `runs/2026-08-17_video-study-mcglasham-cylinder-subd/`, per the user's explicit
instruction to stop building new product models for now and focus on actually learning reusable
skills from video study. The cylinder video (#5 in this creator's numbered series) turned out to be
one part of a systematic "fix every SubD-unsafe primitive, then connect them" curriculum -- checked
the channel's upload list and pulled the four most directly complementary episodes: "A better cone"
(#6), "A better cube" (#7), "Fixing the UV Sphere" (#13), and "Connecting Cylinders" (#15).
Transcript-only extraction for all four (no video-understanding pass).

## Why these four, specifically

Not a broad sweep of the whole channel -- each one was picked for a specific reason tied to either
an active project gap or a direct extension of what the cylinder video already taught:
- **Cone**: same construction family as the cylinder fix already applied to the flashlight (now
  deleted, but the technique is what's being kept); extends the "control loop" mental model to a
  primitive that pinches to a genuine point rather than a flat cap.
- **Cube**: the bevel-segment-parity rule (even segments only) is an immediately actionable,
  zero-cost rule for every future `bevel_selection` call in this project's typed op surface.
- **UV Sphere**: this project's own knowledge base already has one fix for sphere-pole-pinching
  (the Quad Sphere construction, from CG Boost's 100+ Tips). This gives a second, different-mechanism
  fix, with an explicit and important caveat about industry-standard compliance that the first
  source didn't need to address.
- **Connecting Cylinders**: the single most valuable video in this batch. Directly answers a
  question this project has hit repeatedly and never actually solved: how to join two intersecting
  curved hard-surface forms without a boolean and without the resulting T-junction/ngon mess.

## The most important finding: a complete, reproducible boolean-free join technique

"Connecting Cylinders" gives a full, precise, step-by-step method: loop-cut near the intersection on
each cylinder, Shrinkwrap (Project mode, small negative offset) each loop onto the OTHER cylinder so
it traces that surface's exact profile, delete the interpenetrating faces, join the two objects,
Bridge Edge Loops across the two exposed boundaries, then Subdivision Surface. Zero booleans, zero
manual point-pushing, a stated 142-vertex result that then accepts Array/SimpleDeform modifiers
cleanly. This is a real, complete answer to a class of problem this project's own knowledge base has
only ever partially addressed (the T-junction ngon bug from subdivide/bisect; the still-open
boolean-cleanup gap flagged from CG Boost's Modifiers chapter). It is not yet transfer-tested on an
actual build in this project -- that is the natural next step once modeling resumes.

## Items captured (6)

1. PROCEDURE -- the full Shrinkwrap+Bridge boolean-free curved-surface join technique.
2. PROCEDURE -- Linear-interpolation loop-cut smoothing (up to ~8) for sharpening a bridged seam
   without creasing.
3. PRINCIPLE -- always inset before extruding on any flat/mostly-flat face, with the pole-count
   reasoning for why.
4. PRINCIPLE -- Normal Edit modifier fix for UV Sphere pole pinching and curved-surface extrusion
   light-bending, explicitly flagged as shading-only and non-industry-standard (use the already-known
   Quad Sphere construction as the default; this is a documented fallback, not a replacement).
5. PRINCIPLE -- Bevel segments must be even, or a triangle appears at every corner meeting point.
6. PROCEDURE -- Merge by Distance after scaling a ring to a point (for lathed/revolved cone-like tips)
   fixes an over-sharp spike caused by unmerged coincident vertices, plus the dissolve-every-other-
   edge technique for converting the resulting triangle fan to quads.

## Not captured as formal items

The cube video's precision "prism-style" construction (inset top/bottom, then scale cross-section
control loops by a factor of 2.7 to eliminate corner poles entirely) was read but not captured as a
separate item -- the video itself frames it as a rare-need precision technique ("there are going to
be very few circumstances in which you need a cube this precise... mostly cubes are made with the
bevel modifier"), and its value is fully covered by items 3 and 5 above for this project's current
priorities. The chess-piece build episodes referenced as following this primitives series (rook,
bishop, queen, king, pawn, board) were not pulled -- they're applied case studies of the same
primitive-fixing techniques already captured here, not new technique sources.
