# Operator card: Spin, Split vs Separate, Symmetrize

**Status:** DOCS ✓ (Blender 5.2 LTS Manual plus BMesh API) | EXPERIMENT ✓ all four | FAILURE_CASE partial (one real enum-value mistake caught and fixed live) | QUIZ pending

## Official sources

- Split: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/split.html
- Separate: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/separate.html
- Symmetrize: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/symmetrize.html
- BMesh operators (`spin`): https://docs.blender.org/api/current/bmesh.ops.html

The current Manual pages were fetched successfully on 2026-08-10. Split disconnects selected
elements in the same object; Separate creates objects by Selection, Material, or Loose Parts.

## Spin
`bmesh.ops.spin(bm, geom=<verts+edges>, angle=radians, steps=N, axis=(x,y,z), cent=(x,y,z), use_duplicate=False)` -- a lathe/revolve operation: sweeps input geometry around an axis, generating new geometry at each step.

Reproduction: an 8-vert circle (radius 0.3, offset +1 on X so it doesn't sit on the spin axis) spun 360 degrees around Z in 12 steps -> 104v/200e/96f. Sanity check: 8 verts x 13 rings (12 steps + the starting ring) = 104, matches exactly. Confirms this is the correct mechanism for lathe-style revolved forms -- relevant to this project's own Bottle prop, which was instead built via primitive scaling/bevels, not spin; spin would have been a legitimate alternative strategy worth having known about.

## Split vs Separate -- a real, easy-to-conflate distinction
- **`bmesh.ops.split(bm, geom=<selected>)`**: duplicates the selected geometry into a disconnected island **within the same object/mesh**. Reproduction: cube 8v/12e/6f, split the top face -> 12v/16e/6f (4 new duplicate verts + 4 new duplicate edges for the split-off face; face count unchanged since the original top face is still there too, now just topologically disconnected from it).
- **`bpy.ops.mesh.separate(type='SELECTED')`**: genuinely creates a **new, separate Blender object**. Reproduction: selecting the top face and calling separate confirmed a second object (`Exp_Separate.001`) appeared in `bpy.data.objects`.
- These are NOT interchangeable despite similar names -- `split` is a low-level bmesh topology operation (still one object), `separate` is a scene-level operation (produces two objects). This project's `object_ops.py` currently has no wrapper for either; if a future prop genuinely needs a detached component (e.g. a removable cap, a separate small part), `separate` is the one that matches that intent, not `split`.

## Symmetrize
`bpy.ops.mesh.symmetrize(direction='POSITIVE_X')` -- direction names in this Blender version's enum are `NEGATIVE_X`/`POSITIVE_X`/`NEGATIVE_Y`/`POSITIVE_Y`/`NEGATIVE_Z`/`POSITIVE_Z`, **not** `POSITIVE_X_TO_NEGATIVE_X` as first guessed (caught immediately by a clear Python enum error, not a silent failure).

Reproduction: cube deliberately made asymmetric (one +X+Y+Z corner pushed from (1,1,1) to (3,1,1)). `direction='POSITIVE_X'` confirmed to mean **positive-X side is the source/master**: the negative-X side was overwritten to mirror the (including deliberately-broken) positive side, producing a matching vertex at (-3,1,1). Also added a new seam of verts exactly at X=0 to cleanly split the mesh along the mirror plane, rather than just moving existing verts. Useful for enforcing bilateral symmetry after an asymmetric edit was made to only one side (e.g. fixing a slip during freeform sculpting/adjustment) -- distinct from the Mirror *modifier* (non-destructive, live) which this project has not yet used either.
