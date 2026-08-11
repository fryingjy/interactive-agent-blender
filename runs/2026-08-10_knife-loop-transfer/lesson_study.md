# Knife and Loop Cut lesson-to-system study

## Sources actually processed

- Blender / Dillon Gu, *Knife Tool - Blender 2.80 Fundamentals*, 119.201 seconds, 12 decoded
  checkpoints, audio, and 23 local machine-transcript segments.
- Blender / Dillon Gu, *Loop Cut - Blender 2.80 Fundamentals*, 190.321 seconds, 17 decoded
  checkpoints, audio, and 27 local machine-transcript segments.
- Current Blender 5.2 LTS Manual pages for Knife Topology Tool, Loop Cut and Slide, and Bisect.

The two Blender Secrets links supplied by the user were also attempted, but YouTube returned HTTP
429 and a bot-confirmation challenge. They are not counted as learned.

## Extracted reasoning

- Knife adds a deliberate path of vertices and edges through faces. Confirmation/cancellation and
  visible-vs-cut-through scope are part of the operation, not incidental UI details.
- Bisect is the deterministic planar-cross-section member of the same family. Clear Inner/Outer
  creates a boundary that Fill can cap; Fill without clearing a side is not a meaningful request.
- Loop Cut is not generic “add polygons.” It follows a compatible face ring, then optionally slides
  the inserted loop. Density should be added where a later form, support transition, or component
  extraction needs it.
- Blender 5.2 adds important current controls: Even/Flipped slide spacing, Clamp, Correct UVs,
  Knife occlusion/cut-through, angle snapping, and multi-object cutting.

## Different-shape transfer

The controlled transfer uses authored rounded equipment housings rather than the lesson cube/chair.
On a valid eight-edge quad ring, the typed operation creates three complete rings: 24 vertices, 48
edges, and 24 faces, while preserving a closed manifold. A triangulated interruption initially
revealed that the typed helper was only subdividing selected edges; it created 27 vertices and
falsely reported success. The operation contract now rejects that selection before mutation.

The Bisect case clears one side at `x=0.65`, creates eight boundary vertices, fills one cap, and
remains closed. A Fill request with neither side cleared is deliberately rejected. All three saved
evaluated specimens pass fresh-process verification; the cap specimen explicitly allows its one
planar n-gon.

## Boundary

This promotes continuous-quad-ring validation and exact Bisect behavior into the executable system.
It does not prove freehand modal Knife judgment, arbitrary local rerouting quality, or professional
prop modeling.
