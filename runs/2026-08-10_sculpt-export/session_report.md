# Interactive sculpt and export round-trip lab

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS after one preserved verifier correction

## Actual Sculpt Mode mutation

The lab ran Blender with a real hidden GUI context because `bpy.ops.sculpt.brush_stroke` requires a
`VIEW_3D` area. It selected Blender's Draw sculpt brush and submitted a two-sample stroke to a
2,562-vertex icosphere. The operator returned `FINISHED`; 248 vertices moved, maximum displacement
was 0.252191, and mean displacement among moved vertices was 0.071387. This is an actual Sculpt
Mode brush operation, not direct coordinate editing. Independent verification found the saved
result closed and clean with 5,120 triangle faces.

## Export round trips

A beveled, UV-unwrapped, one-material asset was exported to OBJ and binary glTF, then both files
were imported into the same comparison scene. OBJ and GLB preserved world bounds, 108 triangles
of surface coverage, at least one UV layer, and at least one material. Both files are non-empty,
and both imports produced exactly one mesh. The source independently verified clean.

## Preserved failed verifier assumption

`failed_attempt_raw_count_verifier.json` records the first run. It incorrectly demanded identical
raw vertex and polygon counts from GLB. glTF triangulated 54 source polygons into 108 triangles and
split vertices at attribute boundaries (56 to 216), while preserving bounds, triangle coverage,
UVs, and material. Verification was corrected to compare format-invariant evidence. The failed run
remains in the repository instead of being overwritten silently.

## Limits

One Draw stroke proves operator access and measurable geometry change, not sculpting artistry,
anatomy, masks, Face Sets, or coarse-to-fine form judgment. Round-trip checks cover geometry
bounds/surface count plus material/UV presence, not texture-image packaging, tangent parity,
animation, rigging, or target-engine rendering.
