# UV, material, sculpt, and production foundation lab

**Status:** PASS (12/12 assertions after one API correction).

## Results

- UV: applying non-uniform scale before seam unwrap improved world texel-ratio consistency from CV `0.5345` to `0.2778`; Smart Project packed inside 0–1.
- Materials: reproduced diffuse-metadata/Principled-node divergence, verified connected PBR inputs, detected an orphan slot, and confirmed a fully assigned two-slot case.
- Sculpt foundations: two Multires levels evaluated cleanly; Voxel Remesh unified overlapping masses and changed topology while remaining manifold.
- Production: a semantically named object/collection/modifier with applied scale and no hidden items passed the local audit.

## Preserved correction

The first remesh attempt failed because `bmesh.ops.create_icosphere` requires an explicit `mathutils.Matrix` in Blender 5.2. Replacing `None` with `Matrix.Identity(4)` satisfied the documented API contract; no other assertions were changed.

## Version-sensitive observations

Blender warned that unwrap on non-uniform object scale uses an unscaled mesh. The lab quantified the consequence rather than relying on the warning alone.

Voxel Remesh retained a populated UV layer in Blender 5.2. This does not prove the mapping still corresponds usefully to the new topology; production code must re-check distortion/semantic placement. Material `use_nodes` also emitted a Blender 6.0 deprecation warning, so future compatibility should inspect the then-current API.

## Independent verification

Fresh evaluated checks passed the applied-scale UV cube, Multires object, final voxel-remeshed object, and production object. Machine-readable reports are under `verification/`.

## Largest remaining gaps

Real sculpt-brush form judgment, purposeful sculpt-to-retopo transfer, texture baking/normal maps, and export validation remain incomplete.
