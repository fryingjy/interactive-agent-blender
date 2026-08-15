# Session report — scoped Shrinkwrap Project attachment

## Modeling question

Can a secondary part's mounting footprint conform to a curved host while its upper structure stays
unchanged, and does the technique transfer across different curvature families?

## Controlled fixtures

- scoped 25-vertex footprint projected onto a sphere;
- unscoped sphere control;
- scoped sphere control using the wrong projection direction;
- scoped transfer onto a cylinder.

Every mount starts as the same closed 50-vertex/48-quad object. The footprint and upper structure
contain 25 vertices each. Host radial resolution is 16 segments: enough to expose faceted geometric
projection without wasting density on the controlled target.

## Result

- Scoped sphere: all 25 footprint vertices moved, all 25 upper vertices stayed exactly fixed,
  maximum analytic-surface error 0.02357, zero degenerates.
- Unscoped sphere: all 50 vertices moved, the part collapsed to nearly zero signed volume, and 12
  degenerate faces formed. A technically valid modifier setup was destructively wrong in scope.
- Wrong direction: zero vertices moved. The modifier existed and evaluated without exception but
  did no modeling work.
- Scoped cylinder transfer: all 25 footprint vertices moved, all upper vertices stayed fixed,
  maximum analytic-surface error 0.01927, zero degenerates.

The fixed MatCap frame visibly confirms footprint conformance, whole-part collapse, no-op floating
geometry, and cylindrical transfer. A fresh Blender process independently checks the saved modifier
settings, vertex-group scope, expected failed control, topology, and image content.

## Reproduction

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 2 --python tools\run_shrinkwrap_footprint_transfer_lab.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background runs\2026-08-15_shrinkwrap-footprint-transfer\shrinkwrap_footprint_transfer.blend --python-exit-code 2 --python tools\verify_shrinkwrap_footprint_transfer.py -- runs\2026-08-15_shrinkwrap-footprint-transfer
```

## Applicability boundary

This is appropriate for a separate movable, bolted, or assembled secondary part. It does not weld
the part to the host and must not be used to hide an inability to construct a genuinely continuous
cast or welded transition. For continuous geometry, use connected topology or a deliberate
boolean/retopology strategy.
