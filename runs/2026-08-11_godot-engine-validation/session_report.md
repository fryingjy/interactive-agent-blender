# Godot external-engine tangent-bake validation

**Date:** 2026-08-11

**Blender:** 5.2.0 LTS

**External engine:** Godot 4.7.1 stable, official Windows x86_64 build

**Status:** PASS for the declared UV/tangent/material/scale import invariants

## Result

The seam-authored 256x256 Cycles tangent bake from
`runs/2026-08-10_uv-bake-learning/` was packaged as a binary glTF asset and imported by a real,
portable Godot editor. The valid asset preserves:

- `TEXCOORD_0`, `NORMAL`, and an explicitly exported `TANGENT` attribute in the GLB itself;
- a Godot `StandardMaterial3D` with the embedded PNG bound as an enabled normal texture;
- metallic `0.15` and roughness `0.42`;
- unit node scale and the expected Blender Z-up to glTF/Godot Y-up dimension mapping,
  `[1.8, 1.8, 2.8] -> [1.8, 2.8, 1.8]`.

Godot reported 78 imported vertices/UVs/normals, 312 tangent scalars, 288 indices, and one surface.
All eight runtime assertions pass. A second verifier created a fresh temporary Godot project,
reimported both GLBs, reran the GDScript checks, and directly parsed each GLB 2.0 JSON chunk without
using Blender. All ten independent assertions pass.

## Deliberate failure and recovered export defect

The failure control uses identical mesh data, material factors, UVs, tangents, and embedded tangent-
normal pixels, but wires those pixels to Base Color instead of a tangent Normal Map node. Godot still
imports the file, then correctly exposes `albedo_texture_present=true`,
`normal_enabled=false`, and `normal_texture_present=false`. This demonstrates why successful file
loading is not proof of correct normal-map semantics.

The first supposedly valid export also failed independent inspection: Godot had generated runtime
tangents, but the GLB itself did not declare `TANGENT`. The exporter was corrected with
`export_tangents=True`; the final GLB now carries the attribute and passes both direct package and
runtime checks. A separate first-run GDScript type-inference error was fixed by explicitly typing
the surface-format bitmask.

## Reproduction and provenance

Run:

1. Blender: `tools/run_godot_tangent_bake_validation.py`
2. Godot: `--headless --import --path runs/2026-08-11_godot-engine-validation`
3. Godot: `--headless --path ... --script res://validate_import.gd`
4. Independent check: `python tools/verify_godot_engine_validation.py`

The 84,198,557-byte engine archive is not committed. Its SHA-256 is
`c7a289051eaefb460b0106b60e9cd5bee0ef55fd102dcb2bed1eb356cf3d90a1`; the extracted console
executable SHA-256 is `35dab11e04ece16a2b93035e65204f4a944a3e00b020d43e54409193379d5eef`.

Official sources:

- https://godotengine.org/download/archive/4.7.1-stable/
- https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html
- https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/import_process.html
- https://docs.godotengine.org/en/4.0/tutorials/assets_pipeline/importing_scenes.html

## Limit

This is a controlled headless import and structural/material inspection, not a human-reviewed
render across mip levels, compression settings, multiple graphics APIs, or another engine. It
closes the named-engine import gate for this fixture, not production-wide texture validation.
