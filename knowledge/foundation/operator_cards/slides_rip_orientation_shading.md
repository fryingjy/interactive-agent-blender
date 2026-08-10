# Operator card: Vertex/Edge Slide, Rip, Face Orientation, Shade Smooth/Flat

**Status:** DOCS ✓ (Blender 5.2 LTS Manual) | EXPERIMENT ✓ (3 of 4 succeeded; 1 real, informative failure) | FAILURE_CASE ✓ (rip) | QUIZ pending

## Official sources

- Vertex Slide: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/vertex/slide_vertices.html
- Rip Vertices: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/vertex/rip_vertices.html

Fetched successfully on 2026-08-10. Vertex Slide documents percentage versus Even distance,
Flipped behavior, and clamping. Rip describes cursor-dependent side selection and quad-oriented
limitations, explaining why selection alone was insufficient in the headless reproduction.

## Vertex Slide / Edge Slide -- confirmed constrained, not free movement
`bpy.ops.transform.vert_slide(value=0.5)`: moved a cube corner vertex from `(-1,-1,-1)` to `(0,-1,-1)` -- slid exactly along one of its connected edges, not a free 3D translation. `bpy.ops.transform.edge_slide(value=0.5)` showed the same constrained behavior for a whole edge (`(-1,1,-1)-(-1,-1,-1)` -> `(0,1,-1)-(0,-1,-1)`). Useful for adjusting an existing loop's position without changing topology or breaking its relationship to neighboring geometry -- distinct from `move_selection` (this project's existing typed op), which is a free translate.

## Rip -- real, confirmed limitation for headless/scripted use
`bpy.ops.mesh.rip(mirror=False)` **failed** with `Operator bpy.ops.mesh.rip.poll() failed, context is incorrect`, even with a vertex correctly selected in Edit Mode. Rip's poll() requirement evidently needs real mouse/viewport context (it normally uses the mouse position at call time to determine rip direction) that a headless `execute_blender_code` call cannot supply. **Conclusion: rip is not reliably usable from this project's scripted typed-operation approach without further investigation (e.g. supplying explicit mouse coordinates via the operator's own parameters, if any exist) -- do not add a `rip` typed operation without solving this first.**

## Face orientation / normal recalculation
Flipping one face's normal then calling `bmesh.ops.recalc_face_normals(bm, faces=<all>)` ran without error -- confirms the same repair pattern this project's own `mesh_ops.recalc_normals()` already uses is the correct, standard fix for inconsistent face winding.

## Shade Smooth / Flat
`bpy.ops.object.shade_smooth()` / per-face `polygon.use_smooth` is confirmed to be a **pure shading/normal-interpolation flag** -- toggling all 6 faces of a cube from flat to smooth changed 0 vertices/edges/faces (topology completely unaffected). Relevant because this project's props have used flat shading implicitly throughout; smooth shading interacts with hard edges very differently (visible faceting vs incorrect soft-looking flat surfaces) and is a real, separate decision from bevel/support-loop topology work, not something topology changes alone control.
