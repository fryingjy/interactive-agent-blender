# Curriculum card: Modeler-relevant Blender Python and BMesh API

**Status:** DOCS ✓ (current Blender Python API) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ ✓ | RUNTIME_USE ✓ | SECOND_SHAPE ✓

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

## Live Edit Mode and current custom-data transfer (2026-08-16)

Evidence: `runs/2026-08-16_bmesh-editmode-customdata/`

The current official API distinguishes a Python-owned standalone `BMesh` from the live Edit Mode
mesh returned by `bmesh.from_edit_mesh()`. A Blender 5.2.0 LTS fixture now exercises the previously
open live path instead of inferring it from the standalone lab:

- two calls to `from_edit_mesh(mesh)` returned the same live BMesh while the object stayed in Edit
  Mode;
- `bmesh.ops.subdivide_edges(..., cuts=1, use_grid_fill=True)` changed a closed cube from 8/12/6
  vertices/edges/faces to 26/48/24, with every resulting face a quad;
- after adding topology, `bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)`
  persisted the mutation and produced 48 loop triangles, matching the API requirement to mark
  destructive updates when geometry was added or removed;
- `select_flush(True)` converted one selected face into the valid dependent selection of one face,
  four edges, and four vertices;
- generic current attributes persisted through BMesh layers: eight nonzero
  `bevel_weight_edge` floats, twelve `crease_edge` floats, four face-domain
  `semantic_region` integers, and a loop-domain `UVMap`;
- a fresh Blender process opened the saved `.blend` without importing the builder and independently
  verified exact counts, layer values, closure, nondegeneracy, and all-quad topology.

This closes live Edit Mode access and representative custom-data persistence, not systematic
coverage of every BMesh operator or arbitrary layer migration. The current API also documents that
some custom-data management helpers and walkers remain TODO; do not invent support around those
gaps.

## Runtime API lifecycle

Evidence: `runs/2026-08-10_blender-runtime-api/`

- `bpy.context` reports active/view-layer state; `bpy.data` resolves persistent datablocks. The
  fixture confirms both references point to the same active object while preserving the conceptual
  distinction.
- `evaluated_get(depsgraph).to_mesh()` exposed a 56-vertex Bevel result while the base stayed at 8.
- Handler, timer, and message-bus registrations require explicit cleanup. Message-bus `notify`
  rejected a built-in bound method and accepted a Python wrapper.
- A blocking background script does not yield Blender's event loop, so queued timer/message
  delivery is not inferred from successful registration. Use a persistent GUI session for that
  integration claim.
