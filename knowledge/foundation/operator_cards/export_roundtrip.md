# Export round-trip verification

## Rule

Do not treat an export operator's `FINISHED` status as proof of a usable deliverable. Re-import the
file and compare format-invariant properties.

## Minimum checks

- non-empty file and exactly the expected mesh count;
- world-space bounds and units/axis orientation;
- triangulated surface count rather than raw polygon count;
- UV and material presence;
- clean source mesh before export;
- target-specific texture, tangent, animation, and engine checks when those data matter.

## Why raw counts can mislead

glTF is triangle-oriented and may split vertices at UV or normal boundaries. In the Blender 5.2
lab, a 56-vertex/54-polygon source re-imported from GLB as 216 vertices/108 triangles while
preserving bounds, 108 source loop triangles, UVs, and a material. Exact raw count equality was a
verifier defect, not an export failure.

## Evidence

`runs/2026-08-10_sculpt-export/` contains OBJ and GLB files, imports saved in the `.blend`, a
machine-readable report, the preserved failed assertion, and independent source verification.
