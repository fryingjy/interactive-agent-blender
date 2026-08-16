# Seam-directed UV production transfer

This Blender 5.2 run returns the independently reviewed official UV lesson to a reproducible
production test. It does not model the externally gated Swingline target.

Two one-object, one-component, all-quad tube cages are tested:

- a 12-sided radial low cage against a denser radial high cage;
- a bent rounded-rectangular low cage against a denser different-shape high cage.

Each low cage receives one authored longitudinal seam, Unwrap, Average Island Scale, and Pack
Islands. A matched duplicate with no seam is the failure control. High and low sources live in
separate `HIGH_POLY` and `LOW_POLY` collections, keep independent cages and unapplied
Solidify→Bevel stacks, and produce real tangent normal bakes plus low-only GLB exports.

Measured mean corner-angle error falls from `15.00°` to `1.87°` on the radial cage and from
`14.82°` to `0.66°` on the bent rounded-rectangle. Both production audits and all fresh-process
source/export checks pass. These are controlled tube-like surfaces, not a universal seam recipe.

## Reproduce

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools/run_uv_seam_production_transfer.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background runs/2026-08-16_uv-seam-production-transfer/uv_seam_production_transfer.blend --python tools/verify_uv_seam_production_transfer.py
```

Primary evidence:

- `uv_seam_production_transfer_report.json`
- `fresh_verification.json`
- `uv_seam_production_transfer.blend`
- `*_high_matcap.png`, `*_low_wireframe.png`, and `*_tangent_normal.png`
- `*_low.glb`
