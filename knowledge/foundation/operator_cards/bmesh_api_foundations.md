# Curriculum card: Modeler-relevant Blender Python and BMesh API

**Status:** DOCS ✓ (current Blender Python API) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ✓ | SECOND_SHAPE ✓

Official sources:

- <https://docs.blender.org/api/current/bmesh.html>
- <https://docs.blender.org/api/current/bmesh.ops.html>

## State model

- A standalone `BMesh` is Python-owned: load with `from_mesh`, write back with `to_mesh`, and free it explicitly.
- Edit-mode BMesh access uses `from_edit_mesh` and should call `update_edit_mesh`; tessellation updates are explicit.
- Connectivity and custom data live on BMesh element/layer structures.
- Blender does not enforce every selection or mesh-validity convention while a script edits; scripts must leave a valid state and flush selection dependencies.
- Element index lookup tables can become stale or absent after topology creation/change. Call `ensure_lookup_table()` before indexed access and `index_update()` when stable indices are required.

## Blender 5.2 controlled findings

Evidence: `runs/2026-08-10_bmesh-api/`

- `remove_doubles` reduced four vertices to three but returned `None`, so post-state—not an assumed `targetmap`—was the reliable authority in this runtime.
- `dissolve_degenerate` removed a near-zero triangle; `triangulate` converted a hexagon into four faces and returned four face mappings.
- Broad `dissolve_limit` with boundary dissolving erased an open two-triangle region (zero faces). Directly dissolving only the shared edge produced one four-sided face. Selection scope is part of operator semantics.
- Recalculating reversed cube normals changed signed volume from -8 to +8.
- A 24-loop UV custom-data layer survived `to_mesh` with all values populated.
- `select_flush(True)` preserved face→edge→vertex selection dependencies.
- Copying/freeing a BMesh copy left the original valid and unchanged.

## Failure discipline

Never assume an operator's return dictionary, target scope, or successful call proves the intended mutation. Measure element counts/data, validate normals and topology, then write back and independently inspect the saved mesh.
