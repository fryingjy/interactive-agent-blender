# Modeling capability correction — 2026-08-16

## Honest diagnosis

The current system is materially stronger at *technical execution* than at
*visual modeling judgment*. It can make reproducible `.blend` files, retain
live modifiers, collect references, render solid diagnostics, and reject an
obvious failure. Those are necessary safeguards. They have not yet produced
consistent reference-faithful props, which is why the rejected Panasonic,
Seiko, Smeg, and DEKAD exercises must not be presented as capability gains.

The recurring failure is specific: a reference package was converted too
quickly into a generic arrangement of broad volumes. Local contour, clearance,
transition, and negative-space facts were not sufficiently measured before
secondary detail, modifiers, or packaging. A globally plausible bounding box,
clean quads, live SubD, and a passing render do not fix that mistake.

## Evidence inspected

Three user-owned Blender studies were inspected read-only with Blender 5.2:

| Study | Directly useful pattern | What not to infer |
| --- | --- | --- |
| `axe.blend` | Purposeful quad cages; Mirror + live SubD; creases on sharp design lines; Auto Smooth. | A crease attribute is not proof that every contour is correct. |
| `butcher knife.blend` | Explicit `model`, `highpoly`, `lowpoly`, and `textured` stages; live weighted Bevel, Mirror, SubD, and intentional low-poly shading. | High polygon counts or every modifier in a stack are not a quality target. |
| `adventure time sword.blend` | Reference image inside the scene, layered construction stages, controlled mirrored forms. | Stylized reference cannot be treated like a complete orthographic blueprint. |

The raw inventories are retained in
`runs/2026-08-16_capability-diagnosis/`. They are descriptive evidence, not a
license to copy geometry from the source files.

## Corrected working method

1. Gather same-target evidence first: a declared front view and at least one
   depth-resolving view. Label perspective images as perspective; do not force
   them into an orthographic interpretation.
2. Before creating detail, write a concise constraint sheet for the high-
   salience silhouette: outer envelope, local profile breaks, negative spaces,
   clearances, depth order, and true separate assemblies.
3. For each continuous manufactured shell, start with one editable cage and
   develop it with loops, insets, extrusions, bridge/fill operations, or an
   authored profile/revolve. A cube or 12–16-sided circle is a seed, not a
   finished component. Separate objects are reserved for physically separate
   parts.
4. Render the cage in solid/MatCap front, side, and three-quarter views before
   allowing details, materials, broad beveling, or packaging. Record one visual
   observation per declared view, including explicit acceptance or repair work.
5. Use surface tools only after the silhouette is credible: creases for sharp
   SubD design lines, weighted bevels for specifically beveled edges, and
   Smooth by Angle/marked sharps for the required shading discontinuities.
   Keep modifiers live.
6. If a high-salience mismatch remains, rebuild the local cage in place or
   stop the target. Do not disguise it with primitive accumulation, technical
   checks, or a field-report page.

## Enforced change

`PROPORTION_SILHOUETTE` now fails closed unless it contains:

- at least two unique declared reference views;
- a passing `LOCAL_REFERENCE_CONSTRAINT_EVALUATION` with no blocking
  high-salience constraint;
- a written mismatch ledger covering every declared view; and
- no unresolved high-salience visual mismatch.

This is deliberately a provenance/completeness gate, not an automated claim
that a model looks professional. It prevents a good IoU number from advancing
an asset when the written visual inspection still identifies a major issue.

## Available tools and what is actually needed

LoopTools is already installed, as are EdgeFlow, Auto Mirror, F2, Bool Tool,
MeasureIt, Magic UV, and other useful modeling utilities. Installing more
add-ons is not currently the bottleneck. The needed improvement is disciplined
use of the native Edit Mode workflow and direct visual comparison. Blender's
documented loop-cut, edge-crease, edge-bevel-weight, and sharp-edge tools are
the correct foundation for that work.

Sources: [Loop Cut and Slide](https://docs.blender.org/manual/en/5.0/modeling/meshes/editing/edge/loopcut_slide.html),
[Edge Data](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html),
and [Bevel Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html).
