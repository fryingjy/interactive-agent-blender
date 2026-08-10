# Curriculum card: Retopology and remeshing

**Status:** DOCS ✓ (Blender 5.0 Manual generation) | VIDEO ✓ (Blender Studio) | EXPERIMENT ✓ | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ✓ | SECOND_SHAPE ~

## Official behavior studied

Source: <https://docs.blender.org/manual/en/5.0/modeling/meshes/retopology.html>

Video: <https://studio.blender.org/training/stylized-character-workflow/5e5407ec8faf011a381510d7/>

Advanced live study: <https://www.youtube.com/watch?v=tRqCeWZLqQo>

- Voxel remesh rebuilds uniform volume-based topology; lower voxel size preserves more detail at higher density.
- Voxel remesh is unsuitable as final deformation topology and is not the preferred route for Subdivision/Multires cages.
- Quad remesh can better suit Subdivision, but automatic remesh still does not replace intentional deformation flow.
- Manual retopology creates an overlapping mesh and uses overlay, Poly Build, snapping, and projection to match the source.
- Plan loops from articulation, compression, and creases before drawing polygons. Put redirection
  poles on flatter, lower-motion, or hidden surfaces rather than in hard creases or deformation arcs.
- Attached deforming components should carry compatible flow when they must move in unison.

## Project evidence

The mug repair (`runs/2026-08-07_mug-retopo/`) demonstrated that validity metrics can pass while pole placement and junction flow remain poor, and that comparing a bad junction against a clean analogous region can guide a rebuild.

The controlled sphere transfer (`runs/2026-08-10_array-deform-retopology/`) reduced 1,984 target vertices to a 42-vertex conforming cage with mean radial error about 0.0011. That is a useful conformance baseline, but an icosphere's triangles do not establish deformation-ready loop routing.

The actual sculpt handoff (`runs/2026-08-10_sculpt-retopo-deformation/`) projects a 114-vertex cage
onto the 2,562-vertex mesh changed by a recorded Sculpt Draw stroke. The independently clean cage
has mean face-center surface error 0.0280. In a separate shared 70-degree bend, a 17-ring quad cage
cut mean surface error from the sparse 5-ring cage's 0.02958 to 0.01131 and maximum error from
0.09754 to 0.03182. Density should therefore be allocated where deformation and changing radius
need samples, not distributed uniformly by habit.

The official planning lesson was inspected through 15 decoded frames and 140 authored-caption
segments. The tube bend is a different-shape transfer of its articulation-density rule: the sparse
failure has 2.62× the adequate cage's mean error and 3.07× its maximum error. This does not yet
validate facial patch/pole routing, mouth interiors, or expression shape keys.

The 2h12m Blender Studio live retopology lesson was inspected through 27 decoded checkpoints and
4,595 automatic-caption segments. It adds concrete patch-routing rules: trace where loops actually
lead, use three/five-pole redirections to delimit patches, avoid high-valence clusters, reduce loops
before low-demand regions, keep poles out of proximity-loop creases and major articulation, and
build eyelids/inner mouth as functional structures. A controlled different-shape transfer placed
the same five-pole pair either away from or inside a 92-degree hose bend. Bend-zone mean deviation
from the all-quad control rose from `4.13698e-08` to `1.42220e-04` when the poles were in the bend,
a 3,437.77x ratio. The result is mechanism evidence, not a claim of facial animation quality.

## Decision rule

Retopology is goal-dependent. Preserve silhouette and important curvature first, then allocate density, route loops, isolate detail, and place unavoidable poles where deformation and highlights tolerate them. Use Shrinkwrap/snapping as projection aids; never credit them with solving edge flow automatically.
