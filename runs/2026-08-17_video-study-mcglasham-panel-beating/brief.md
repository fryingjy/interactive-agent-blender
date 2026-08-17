# Ian McGlasham -- "Panel Beating" (Loop Tools Curve tool), #21 Subdivision Surface Modelling

Direct follow-on from `runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/`, same
channel and series. That batch already established Ian McGlasham as a trusted, transcript-verified
source for this project's Blender technique study. This single video (goJ4LVHXkC4, 23:11) was pulled
because "panel beating" -- building subtle, controlled, stamped/pressed sheet-metal-style surface
curvature with a curve-fitting tool rather than by freehand vertex pushing -- is a genuinely new
capability category this project has not captured before. It is directly relevant to any future
automotive body panel, appliance shell, or other hard-surface prop where a smoothly domed or creased
surface needs to stay quad-topology-safe and SubD-ready. Transcript-only extraction, no video-
understanding pass.

## Why this video, specifically

The channel's own framing (a "heavily misunderstood and mostly unused tool") matched a real gap: this
project had no prior sourced technique for building controlled, non-random surface curvature on a flat
or curved base mesh, only ad hoc vertex pushing and (from the prior McGlasham batch) Shrinkwrap-based
surface-tracing for joins. This video gives the actual mechanism -- Loop Tools' Curve operator, its
selected-vs-unselected control semantics, and how that mechanism is reused across several distinct
tasks (adding curvature, repairing mistakes, adding sharp creases, flattening) -- rather than just a
finished result.

## The most important finding: Curve's control mechanic, and what it unlocks

The single fact underlying everything in this video is stated plainly partway through: "the curve tool
works only on unselected vertices." Selected vertices are fixed control points; everything left
unselected gets recalculated into a cubic curve between them. That one mechanic, combined with Loop
Tools operating on whole loops (not just individual vertices), produces four distinct reusable
capabilities captured here: (1) spreading a single-loop ridge across a full surface while keeping its
boundary exactly fixed, (2) repairing a bad local region of a mesh -- even a heavily modifier-distorted
one -- by inverting the selection onto the problem vertices and letting the surrounding geometry define
the correction, with a stated real example of this working after "hundreds of other modeling changes"
had already happened since the mistake, (3) building sharp, tapered panel-line creases via Bevel+Curve,
and (4) the tool's hard prerequisite that the mesh be clean all-quad topology with no booleans, n-gons,
triangles, or extraordinary poles -- which independently reinforces the boolean-avoidance principle
already captured from this channel's "Connecting Cylinders" episode, this time from the angle of "a
boolean costs you access to Curve," not just bad topology in the abstract.

## Items captured (9)

1. PROCEDURE -- the core selected/unselected control mechanic; building a single-loop ridge from one
   moved peak vertex plus two fixed endpoint vertices.
2. PROCEDURE -- propagating a ridge loop across a whole surface by selecting two boundary loops plus
   the ridge loop together, with the boundary staying exactly fixed.
3. PROCEDURE -- the invert-selection repair workflow (select the bad vertices, Ctrl+I, Curve) plus the
   Influence slider for partial rather than total correction.
4. FAILURE -- a concrete narrated example of the repair workflow recovering an old, unnoticed
   accidental vertex move on a heavily modifier-distorted torus, without needing to undo intervening
   work.
5. PROCEDURE -- Bevel-to-three-loops plus Curve for a sharp, tapered panel-line crease that still blends
   into the surrounding curved surface.
6. PRINCIPLE -- Curve's hard topology prerequisites (no booleans, no n-gons/triangles/extraordinary
   poles).
7. PRINCIPLE -- the Boundary checkbox caveat when curving a partial loop selection.
8. DECISION -- Curve over Proportional Editing for controlled surface curvature, with the specific
   circular-falloff and boundary-vertex-drift problems Proportional Editing has that Curve does not.
9. PRINCIPLE -- the "framework mesh" discipline: one all-quad master mesh, with triangulated/n-gon
   derivatives generated from it per destination rather than edited directly.

## Not captured as formal items

The video's opening demo of the simplest possible Curve use (select three points on one edge, press
Curve once) was read but folded into item 1 as the "naive stopping point" the transcript itself calls
out, rather than captured as its own item -- it has no mechanic beyond what item 1 already states.
The later door-panel build (separating window/door geometry into new objects with P, "select loop inner
region" for a one-sided selection, extruding the two door panels apart) was read but not captured --
it's object/selection housekeeping around the panel-beating technique, not the deformation technique
itself, and none of it is specific to Curve. A passing mention of using a Shrinkwrap modifier against a
copy of the base mesh when cutting window holes ("this is where I would normally use a shrink wrap
modifier... but I've not done that here") was not captured either -- it is named but not demonstrated,
and the Shrinkwrap-for-surface-tracing mechanism itself is already captured in more complete, narrated
form from the prior "Connecting Cylinders" episode. The video's closing anecdotal references to the
narrator's own sunglasses and toy-train-engine models were not captured -- they are testimonial
(portfolio) claims with no described construction steps.
