# Interactive Agent Blender

A fresh project to develop a reference-driven Blender modeling tool for editable, commission-quality game props.

**Status: initial Blender editing loop implemented. Professional modeling capability has not been demonstrated.**

Start with [the feasibility report and development plan](docs/FEASIBILITY_AND_PLAN.md). It defines the first supported asset class, architecture, experiments, delivery requirements, and release criteria.

Important market constraint: HiddenDevs currently prohibits AI-generated, AI-modified, and automated examples in skill-role applications. Eligibility for AI-assisted commissions is not established. Tool development and marketplace permission are separate questions.

The first implementation target is an editable hard-surface prop workflow with reference comparison, scoped repairs, and a verified Roblox export. Not unrestricted image-to-3D generation, a tutorial archive, or a universal professional-modeler claim.

## Current runtime

Runs one decision in a separate Blender process. Supports mesh inspection, single-face extrusion, selected-vertex movement, and temporary orthographic Workbench previews. Edits require a snapshot fingerprint and a new output file. Failed mesh edits restore their source data; successful operations are never labeled artistic acceptance.

```powershell
python -m modeler --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --input work/source.blend --request work/request.json --report work/inspection.json
```

Inspection request:

```json
{"action": "inspect", "object": "Cube"}
```

Edit request (replace the fingerprint with the latest inspection value; add `--output work/edited.blend`):

```json
{"action": "move_vertices", "object": "Cube", "expected_fingerprint": "FROM_INSPECTION", "vertices": [0], "delta": [0.1, 0, 0]}
```

`extrude_face` takes `face` and `delta` instead of `vertices`. Indices are snapshot-local. Coordinates and deltas are object-local. The fingerprint covers geometry, numerical mesh attributes, world transform, and scalar modifier settings, not the entire scene or external modifier dependencies.

Render request (no `--output`; the image path must be new):

```json
{"action": "render", "object": "Cube", "eye": [4, -6, 3], "target": [0, 0, 0], "scale": 4, "path": "work/preview.png"}
```

Only single-user meshes in Object Mode without shape keys are supported. Selection and rendered visibility follow the loaded object. Mesh-health checks do not detect all intersections, flipped faces, bad proportions, or poor shading. Source modifiers remain live; editing their settings is not exposed yet. This is a local trusted-user tool, not a sandbox. Checkpoint files and reports are not published automatically.

## Verification

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup --disable-autoexec --python-exit-code 1 --python tests/blender_smoke.py
$env:BLENDER_EXECUTABLE = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
python -m unittest discover -s tests -p "test_*.py" -v
```

Tests use synthetic fixtures and temporary media, not commission examples. Next: one permitted-reference prop, measured proportions, and visible repair; then expand operations only as that exercise requires. UV/material delivery, reference comparison, and Roblox validation remain unimplemented.
