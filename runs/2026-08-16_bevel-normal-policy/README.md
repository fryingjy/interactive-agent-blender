# Bevel normal-policy comparison

This Blender 5.2.0 LTS lab reproduces the current Manual's flat-panel shading claims for Bevel
Harden Normals and for Bevel Face Strength consumed by a following Weighted Normal modifier. It is
a matched technical fixture, not a universal hard-surface rule or an asset-quality claim.

Left to right in `bevel_normal_policy_solid.png`:

1. plain smooth Bevel;
2. Bevel with Harden Normals;
3. Bevel Face Strength `AFFECTED`, then Weighted Normal with Face Influence.

All variants evaluate to 96 vertices, 192 edges, and 98 faces. The maximum corner-normal error on
the six large panels is 10.5605° for plain smooth Bevel and 0° for both documented normal policies.

## Reproduce

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools\run_bevel_normal_policy_lab.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools\verify_bevel_normal_policy.py -- runs\2026-08-16_bevel-normal-policy\bevel_normal_policy.blend --output runs\2026-08-16_bevel-normal-policy\fresh_verification.json
```

Official sources:

- <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html>
- <https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html>

The result does not establish curved-panel repair, silhouette quality, reference accuracy, or
correct semantic edge selection. Custom normals cannot repair incorrect geometry.
