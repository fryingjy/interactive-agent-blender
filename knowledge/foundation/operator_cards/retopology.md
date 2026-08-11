# Curriculum card: Retopology and remeshing

**Status:** DOCS ✓ (Blender 5.2 Manual generation) | VIDEO ✓ (Blender Studio) | EXPERIMENT ✓ | FAILURE_CASE ✓ | QUIZ ✓ | RUNTIME_USE ✓ | SECOND_SHAPE ✓

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

`runs/2026-08-10_rigged-joint-deformation/` advances the articulation test from analytic mapping to
a real two-bone Armature modifier with smooth `Upper`/`Lower` weights. On a manually authored
organic limb under an 82-degree pose, 21 purposefully distributed rings reduce joint-zone mean
deviation from the 11-ring cage's `0.01887370` to `0.00300313` against a 47-ring rigged reference
(6.28467x), and joint maximum from `0.06306881` to `0.01436530`. Three posed meshes independently
verify clean. This validates joint-density allocation on one weighted shape, not full-character or
facial expression topology.

`runs/2026-08-11_multi-axis-corrective/` adds a real three-bone flex/splay/twist pose and a relative
shape key driven from explicit local bone-rotation variables. The corrective is inactive at rest,
flex-only, and twist-only, but reaches 1.0 for 72° flex + 18° splay + 58° twist. It reduces low-cage
joint mean error from `0.05805965` to `0.01494744` (3.88425×), joint maximum from `0.12682819` to
`0.02697982`, and relative volume error from 12.3923% to 5.1967%. This closes the controlled
multi-axis/corrective mechanism gap, not facial expression or production-character quality.

`runs/2026-08-11_facial-expression-transfer/` uses Blender's official CC0 animation head to test
the next transfer. The source is closed and predominantly quad, but it contains 18 triangles and
10 n-gons, so the run does not relabel it all-quad. Instead, the jaw mask was rebuilt after an
over-broad 733-vertex failure so its final 123 weighted vertices touch only quad faces. The saved
Jaw + bilateral-smile rig and driven corrective pass an independent fresh-process topology/driver
review. This validates localized deformation-region topology and corrective wiring on a facial
shape; the subtle expression does not establish authored facial retopology or production acting.

`runs/2026-08-11_expressive-facial-articulation/` demonstrates why topology acceptance must be
regional and task-dependent. The official source is predominantly quad but not all-quad; the
expression region contains 2,916 quads and 20 non-quads across 2,936 faces (99.3188% quads), while
remaining closed and nondegenerate before and after Subdivision Surface evaluation. The failed
absolute-quad gate is preserved. This supports contextual topology judgment, not autonomous
retopology authorship. Under the current priority override, retopology fundamentals remain active
for general prop repair and flow, while sculpt-heavy organic pipelines are deferred.

## Decision rule

Retopology is goal-dependent. Preserve silhouette and important curvature first, then allocate density, route loops, isolate detail, and place unavoidable poles where deformation and highlights tolerate them. Use Shrinkwrap/snapping as projection aids; never credit them with solving edge flow automatically.
