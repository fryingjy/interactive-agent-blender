# Ian McGlasham -- "Insetting and softbodies" (#16, Subdivision Surface Modelling series)

Continues the same-channel video-study work started in
`runs/2026-08-17_video-study-mcglasham-subd-primitives-and-connections/` (cylinder/cone/cube/UV-sphere
primitives, connecting cylinders). This episode was picked deliberately, not swept in with the rest of
the series: "Insetting" is the mechanism behind a principle this project already holds as a habit
(always inset before extruding a detail feature) but had only captured at the level of "do this, it
avoids poles" -- this video is the creator's own dedicated explainer for *why* that rule exists, with a
level of mechanical detail (the Inset-operator's O/Outset toggle, a live loop-cut-redirection demo, a
paired before/after vertex count) the earlier captures didn't have. "Softbodies" is a genuinely new
topic for this project -- nothing in the knowledge base touches cloth/soft-body simulation, modifier
stack ordering under simulation, or how topology choices affect deformation. Transcript-only extraction
(no video-understanding pass); source video ID `K5VJYlUV23I`, 26:33 long.

## The most important finding: bad pole placement is invisible at rest and visible in motion

The video's real payoff isn't a new modeling trick -- it's a demonstration, with a controlled A/B
comparison, of *why* the inset-before-extrude habit matters beyond looking tidy in Edit Mode. The
creator builds two near-identical spiked cube shapes: one by extruding faces directly (no inset), one
by insetting-then-outsetting each face first. Both get identical Cloth physics settings and are dropped
on a floor. The non-inset version needs loop cuts that run across the *entire* mesh just to control the
softness of each connection point (there's no local loop to select otherwise); at rest it looks only
mildly worse, but per the narration, under actual cloth simulation those loops show up as visible
ridges that distort the object's structure as it deforms -- "those edges are changing the actual
structure of our shape." The inset-first version, with the exact same physics settings, "distorts
perfectly... there are no ridges." The video also puts a real number on the topology cost of skipping
the inset: 104 vertices (inset-first) versus 176 vertices (direct extrude) on the same shape, "about 70
percent heavier" and correspondingly slower to simulate. That combination -- a static-mesh problem that
was already suspected, now shown to also be a deformation-time problem, with a measured vertex-count
delta attached -- is new information for this project, not a restatement of the existing inset rule.

## Items captured (7)

1. PRINCIPLE -- five-spoked poles aren't inherently bad; the problem is unpredictable loop-cut behavior
   and pull near curvature/corners, so the real rule is pole *placement*, not pole avoidance.
2. FAILURE -- extruding a face directly (no inset) plants a pole at the extrusion's base, forcing
   mesh-wide tightening loops to control the connection afterward, since there's no local loop to grab.
3. PROCEDURE -- Inset then press O (Outset) while the operator is live: preserves the extrusion's
   original footprint size (matches a reference feature) while relocating the pole ring onto flat mesh,
   leaving a local control loop that doesn't touch the rest of the mesh.
4. VISUAL_CUE -- mesh-wide tightening loops read as fine at rest but show up as hard ridges once the
   mesh actually deforms under cloth/soft-body simulation; topology correctness includes deformation
   behavior, not just static shading.
5. PRINCIPLE -- the inset-first version of the same shape came in at 104 vertices vs. 176 for the
   direct-extrude version (~70% heavier), with a matching cloth-simulation speed cost -- a quantified,
   not just aesthetic, argument for the habit.
6. PRINCIPLE -- Subdivision Surface must always be the last modifier in the stack; stated as an
   unconditional rule, required for correct cloth/soft-body results, GPU subdivision acceleration
   (Blender 3.1+), and Array-modifier-generated duplicates.
7. DECISION -- use Cloth physics (Bending stiffness/damping as the shape controls, Structural/Shear
   maxed out to remove them) rather than the dedicated Soft Body system for soft-body-style
   deformation; Cloth is described as more stable, faster, and interruptable.

## Not captured as formal items

The back half of the video (roughly 10:00 onward) is mostly softbody/cloth *setup mechanics* rather
than modeling or topology technique, and per the task's own guidance this is intentionally not padded
out into items: specific parameter walk-throughs (vertex mass 20kg, speed multiplier 2.5, quality
steps, self-collision distance 0.01, impulse clamping left at zero, cache-to-bake workflow), the
extrude-individual-faces-then-scale-by-individual-origins technique used to build the two demo spike
shapes (a general Blender technique, but organic/spike-array in character, not hard-surface), using the
Array modifier to multiply soft-body objects instead of duplicating geometry in Edit Mode, and the
closing lighting/HDRI/material/render-preview segment (Poly Haven HDRI, mapping/texture-coordinate
nodes, Eevee screen-space reflections) were all read but skipped -- none of it is modeling/topology
technique transferable to this project's hard-surface work, it's scene-dressing and simulation-tuning
specific to this one demo. The creator's own closing aside ("i think this one was really just about
topology and it's got away from me a bit... i really should get on with the queen for our chess set")
confirms the softbody material was a tangent even by the source's own framing, which matches this
project's expectation going in that the softbody portion would be lower-value than the insetting half.
