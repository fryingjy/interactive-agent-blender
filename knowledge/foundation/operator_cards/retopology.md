# Curriculum card: Retopology and remeshing

**Status:** DOCS ✓ (Blender 5.0 Manual generation) | EXPERIMENT ✓ | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ✓ | SECOND_SHAPE ~

## Official behavior studied

Source: <https://docs.blender.org/manual/en/5.0/modeling/meshes/retopology.html>

- Voxel remesh rebuilds uniform volume-based topology; lower voxel size preserves more detail at higher density.
- Voxel remesh is unsuitable as final deformation topology and is not the preferred route for Subdivision/Multires cages.
- Quad remesh can better suit Subdivision, but automatic remesh still does not replace intentional deformation flow.
- Manual retopology creates an overlapping mesh and uses overlay, Poly Build, snapping, and projection to match the source.

## Project evidence

The mug repair (`runs/2026-08-07_mug-retopo/`) demonstrated that validity metrics can pass while pole placement and junction flow remain poor, and that comparing a bad junction against a clean analogous region can guide a rebuild.

The controlled sphere transfer (`runs/2026-08-10_array-deform-retopology/`) reduced 1,984 target vertices to a 42-vertex conforming cage with mean radial error about 0.0011. That is a useful conformance baseline, but an icosphere's triangles do not establish deformation-ready loop routing.

## Decision rule

Retopology is goal-dependent. Preserve silhouette and important curvature first, then allocate density, route loops, isolate detail, and place unavoidable poles where deformation and highlights tolerate them. Use Shrinkwrap/snapping as projection aids; never credit them with solving edge flow automatically.
