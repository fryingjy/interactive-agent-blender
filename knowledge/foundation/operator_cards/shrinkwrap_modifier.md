# Operator card: Shrinkwrap modifier

**Status:** DOCS ✓ (Blender 5.0 Manual generation) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ~ | SECOND_SHAPE ✓

## Official behavior studied

Source: <https://docs.blender.org/manual/en/5.0/modeling/modifiers/deform/shrinkwrap.html>

- Nearest Surface Point chooses the closest target-surface point.
- Project casts along selected local axes and allowed positive/negative directions; vertices with no hit remain unchanged.
- Offset and snap/wrap mode determine where points sit relative to the selected target point.
- Projection limit, face culling, auxiliary targets, and vertex groups can restrict the result.

## Blender 5.2 controlled findings

Evidence: `runs/2026-08-10_array-deform-retopology/`

A 7×7 quad grid above a UV sphere reached mean target radius 0.9980 with Nearest Surface Point. Offset 0.2 moved it to mean radius 1.1977. The same grid using Project with only the wrong (+Z) direction enabled moved exactly 0 vertices: Blender returned a valid evaluated open mesh, but the intended operation was a complete no-op.

A 42-vertex icosphere cage starting at radius 1.25 shrinkwrapped onto a 1,984-vertex target sphere at mean radius 0.9989 and independently verified clean. This demonstrates geometric conformance and density reduction, not deformation-ready edge flow.

## Decision rule

Choose the wrap method from the modeling intent. Verify displacement magnitude, projection direction/local axes, missed vertices, offset, and silhouette. For retopology, Shrinkwrap helps conformance but does not design loop flow, pole placement, or deformation topology.

## Vertex-group-scoped mounting footprint (transfer validated, 2026-08-15)

`runs/2026-08-15_shrinkwrap-footprint-transfer/` tests the secondary-part attachment case directly.
On the same closed 50-vertex/48-quad mount, Project limited to a 25-vertex footprint group conformed
all footprint vertices to a sphere while leaving all 25 upper structure vertices exactly fixed. The
same setup transferred to a cylinder with maximum analytic-surface error below 0.020 and remained
closed, manifold, and non-degenerate. The unscoped control moved the entire part, collapsed its
signed volume nearly to zero, and created 12 degenerate faces; the wrong-direction control moved
zero vertices.

Use this only when component-boundary evidence supports a separate assembled/movable/bolted part.
It does not join the component to the host and is not a substitute for connected topology where the
reference implies a continuous transition.
