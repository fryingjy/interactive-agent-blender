# Curriculum card: Materials and production organization

**Status:** DOCS ✓ | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ✓ | SECOND_SHAPE ✓

Official sources:

- <https://docs.blender.org/manual/en/latest/render/materials/introduction.html>
- <https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html>

## Material findings

Materials are data-blocks; node connections determine rendered surface behavior. The Principled BSDF provides physically based controls such as Base Color, Metallic, Roughness, transmission, coat, and emission.

Evidence: `runs/2026-08-10_uv-material-sculpt/`

- Changing `Material.diffuse_color` to red left the connected Principled Base Color at its default gray. Metadata and render-affecting node state can diverge.
- Setting Base Color, Roughness `0.32`, and Metallic `0.85` directly on the connected Principled node was recovered exactly from the saved material state.
- A second material slot unused by any polygon was detected as an orphan; assigning alternating faces made both slots reproducibly used.

Evidence: `runs/2026-08-10_pbr-normal-export/`

- A packed tangent normal image in Non-Color space survived GLB export/re-import with the Image
  Texture → Normal Map → Principled Normal chain intact.
- Principled roughness `0.38`, UV presence, 32×32 image dimensions, bounds, and triangulated surface
  count survived the round trip. This proves transport semantics for the fixture, not normal baking.

## Production audit

The lab's `Production_Ready` collection passed checks for semantic object naming, applied scale, descriptive modifier naming, and no hidden objects. Its evaluated mesh independently verified clean.

For final assets also check collection hierarchy, no accidental orphan geometry/data, modifier order and visibility, reproducible material assignments, checkpoints, export axes/units, and final saved `.blend`. A tidy one-object fixture proves audit mechanics, not full multi-component export readiness.
