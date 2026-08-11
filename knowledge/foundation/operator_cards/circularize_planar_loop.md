# Operator card: circularizing a planar loop

**Status:** DOCS ✓ (Blender Manual / official LoopTools documentation) | EXPERIMENT ✓ (Blender 5.2 LTS) | FAILURE_CASE ✓ | RUNTIME_USE ✓ | SECOND_SHAPE ~

## Purpose

Turn an existing Edit Mode loop into a genuine circle without replacing the modeled region with a
separate cylinder. Use only enough vertices for the silhouette and downstream connections.

## Official operations

- Blender core **To Sphere**: Mesh ‣ Transform ‣ To Sphere, shortcut `Shift-Alt-S`. On a planar
  loop with the pivot at its center, factor 1 gives the selection a circular/spherical radius.
  More selected elements produce a smoother result.
- Official LoopTools add-on **Circle**: accepts open or closed selected loops and supports Best Fit,
  Fit Inside, Flatten, Radius, Regular, and Influence controls. `Regular` equalizes spacing.

Sources:

- <https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/transform/to_sphere.html>
- <https://docs.blender.org/manual/en/3.6/addons/mesh/looptools.html>

The accessible LoopTools page is version 3.6 documentation; runtime behavior should be confirmed
against the installed extension/version before automation depends on its operator identifier.

## Camera correction experiment

Evidence: `runs/2026-08-11_connected-camera-corrective/`

- Rejected state: four-sided top-control extrusions only appeared rounded after SubD.
- Corrected state: each control uses seven welded 12-vertex rings grown from a 12-edge opening in
  the body, with no added cylinder object.
- Independent checks measure every ring's radial relative span below `2e-7` and angular-gap relative
  span below `6e-7`, well inside the `1e-5` gate.
- All 530 base faces and all 25,120 evaluated faces are quads; base, Bevel-only, and final stages are
  one-component closed manifolds.

## Workflow rule

1. Add or route enough vertices in the surrounding topology to support the intended loop count.
2. Select the planar loop and place the pivot at its intended center.
3. Use To Sphere at factor 1, or LoopTools Circle with Flatten and Regular when best-fit/radius
   controls are useful.
4. Check radius variation, spacing, planarity, surrounding face flow, and the evaluated silhouette.
5. Extrude or bridge the resulting loop so the feature remains connected to the base object.

Do not call a four-sided loop circular merely because subdivision rounds its corners.
