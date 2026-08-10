# Curriculum card: Sculpt, remesh, Multires, and retopology handoff

**Status:** DOCS ✓ (Blender 4.1/5.0 Manual generations) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ~ | QUIZ pending | RUNTIME_USE ~ | SECOND_SHAPE ~

Official sources:

- <https://docs.blender.org/manual/en/5.0/sculpt_paint/sculpting/index.html>
- <https://docs.blender.org/manual/en/5.0/modeling/meshes/retopology.html>

## Foundations

- Sculpting prioritizes form through brushes, masking/Face Sets, symmetry, filters, and changing resolution.
- Voxel Remesh rebuilds a uniform volume-based mesh; voxel size trades detail against density.
- Multires supports multiple subdivision levels for non-destructive coarse-to-fine sculpt detail.
- Automatic remesh does not create intentional deformation flow; animation/production handoff may require manual retopology and projection.

## Blender 5.2 findings

Evidence: `runs/2026-08-10_uv-material-sculpt/`

- Two Multires subdivisions changed an 8-vertex cube to a clean 98-vertex evaluated surface.
- Voxel Remesh combined two overlapping icosphere masses from 324 vertices/640 faces into one clean 484-vertex/482-face manifold result.
- A meaningful nonzero UV layer still existed after this Blender 5.2 remesh (1,928 nonzero loops), contradicting an unconditional “all data layers are always lost” claim from older documentation. Layer/value presence does not prove semantic UV correspondence, so UVs must still be revalidated after remesh.

Evidence: `runs/2026-08-10_sculpt-export/`

- A real Draw-brush Sculpt Mode operator stroke moved 248 of 2,562 vertices; maximum displacement
  was 0.252191. The saved result independently verified closed and clean.
- The brush required a real `VIEW_3D` context, so the lab ran Blender in a hidden GUI process rather
  than pretending a headless geometry mutation was a brush test.

## Limitation

This validates resolution mechanics and actual brush access, not organic sculpting judgment. A
single stroke is not primary/secondary form design; anatomy/form evaluation and a
sculpt-to-purposeful-retopology asset remain required.
