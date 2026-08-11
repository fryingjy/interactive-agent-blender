# Bevel and Mirror cylindrical transfer report

**Runtime:** Blender 5.2.0 LTS (`fbe6228777e7`)

**Result:** PASS (7/7 assertions). The intentionally open Mirror seam also failed the independent verifier as expected.

## Scope

This second-shape lab transferred standalone Bevel and Mirror findings from boxes to cylindrical geometry. It separated editable base meshes, evaluated modifier results, and independent checks of the saved `.blend` file.

## Mirror findings

| Variant | Merge distance | Evaluated verts | Non-manifold edges | Result |
| --- | ---: | ---: | ---: | --- |
| Exact curved seam | 0.001 | 26 | 0 | closed |
| Curved seam at X=0.002 | 0.001 | 32 | 12 | open, expected failure |
| Same gap, repaired threshold | 0.010 | 26 | 0 | closed |

The seam-distance result transferred from a planar half-box to a half-cylinder. Raising the threshold repaired this deliberately small gap, but this is not permission to use broad merge distances without checking for unintended welding.

Both `Mirror -> Subdivision` and `Subdivision -> Mirror` were closed and all-quad on this exact-seam half-cylinder (482 vertices, 480 faces, zero non-manifold edges). This does not prove visual equivalence, and it contradicts any universal claim that one order must always fail. The earlier flat-seam failure remains valid for its tested geometry; the transferable rule is to test the evaluated seam on the actual topology.

## Bevel findings

The same closed cylinder was tested with Bevel width 0.1 and one segment after stretching it to world height 4.

| Variant | Object Z scale | Measured top bevel band | Non-manifold edges |
| --- | ---: | ---: | ---: |
| Scale applied | 1.0 | 0.1000 | 0 |
| Scale unapplied | 2.0 | 0.2000 | 0 |

Unapplied Z scale doubled the world-space bevel band while the modifier width remained 0.1. Both outputs were manifold, showing why topology health alone cannot validate world-space bevel consistency.

## Independent verification

`tools/verify_mesh.py --evaluated` was run against all seven saved objects. Exact seam, repaired seam, both stack orders, and both Bevel variants passed. `Mirror_Cylinder_Gap` failed exactly as intended with 12 non-manifold edges. Machine-readable verifier records are in `verification/`.

## Artifacts

- `bevel_mirror_transfer_lab.blend`
- `bevel_mirror_transfer_report.json`
- `verification/*.json`
- `tools/run_bevel_mirror_transfer_lab.py`

