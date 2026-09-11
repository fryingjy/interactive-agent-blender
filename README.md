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

Only single-user meshes in Object Mode without shape keys are supported. Mesh-health checks do not detect all intersections, flipped faces, bad proportions, or poor shading. Source modifiers remain live. This is a local trusted-user tool, not a sandbox. Checkpoint files and reports are not published automatically.

On this workstation, Workbench intermittently crashes inside the Intel graphics driver at process shutdown. A saved PNG is not evidence of a clean process exit. Add `"engine": "CYCLES"` to a render request for the tested CPU clay-render alternative (8 samples, 512 square). It leaves source materials untouched. Workbench remains available, not proven stable.

## Verification

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup --disable-autoexec --python-exit-code 1 --python tests/blender_smoke.py
$env:BLENDER_EXECUTABLE = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
python -m unittest discover -s tests -p "test_*.py" -v
```

Tests use synthetic fixtures and temporary media, not commission examples. [Current shield study and next work](docs/CURRENT.md) records the first reference-driven exercise, including a rejected topology tradeoff. UV/material delivery and Roblox validation remain unimplemented.

The editor also supports `subdivide_edges` (`edges`, `cuts`) and `set_vertex_positions` (`positions`: vertex-index/coordinate pairs). Selective edge subdivision may introduce triangles and n-gons; manifoldness is not a sufficient topology-quality check.

Surface operations use the same fingerprint requirement:

| Action | Additional request fields | Scope |
| --- | --- | --- |
| `inset_region` | `faces`, positive `thickness`, signed `depth` | Connected selected face region; no intersection guarantee |
| `set_edge_crease` | `edges`, `weight` in 0–1 | Selected edge attribute |
| `set_vertex_crease` | `vertices`, `weight` in 0–1 | Selected vertex attribute |
| `set_face_smoothing` | `faces`, boolean `smooth` | Selected faces only; does not fix geometry |
| `set_subdivision` | integer `levels` in 0–3 | Creates/updates one live `Modeler_Subdivision` modifier |

Inspection reports triangle/quad/n-gon counts. Mesh edits warn when they introduce n-gons; the warning is a review signal, not a blanket prohibition. The managed subdivision operation restores its prior settings if post-edit inspection fails.

Optional image comparison dependencies are listed in `requirements.txt`. `python -m modeler.compare --help` describes alpha-mask comparison with an explicit scale and offset. Same-view silhouette overlap is not proof of depth, surface quality, or professional acceptance.
