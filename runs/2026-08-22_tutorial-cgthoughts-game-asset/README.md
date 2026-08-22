# CG Thoughts complete game-asset workflow reproduction

Stage 7 follows CG Thoughts' 24:36 hard-surface game-asset tutorial from high-poly modeling through
low-poly derivation, UVs, baking, export, and engine-facing normal-map decisions. The modeled subject
is the tutorial's red-and-white stylized medical case.

## Asset structure

`medical_case_production.blend` contains independent `HIGH_POLY` and `LOW_POLY` collections. The red
case shell is one primary object. Two white wrap bands, two moving latches, and one connected swept
handle are separate because the reference shows genuine assembly/material boundaries. Bevel,
Weighted Normal, and Solidify modifiers remain live and unapplied in the source.

The low variant has UVs on all six meshes and delivers saved 512px BaseColor, Roughness, Metallic,
and tangent Normal maps. The selected-to-active normal bake uses Cycles, a positive margin, an active
target node, Non-Color data, external save, image packing, and a connected Normal Map node.
`medical_case_low.glb` imports successfully in a fresh Blender process with six UV-bearing meshes,
five materials/images, and 204 evaluated faces.

## Verification and boundary

High/low silhouette IoU is `0.9984` front, `0.9980` side, and `0.9985` top. The full bake/material
render is `low_material_render.png`; MatCap and base-wire views remain available independently.

This is a simplified workflow reproduction, not a pixel-identical copy. It is boxier than the
tutorial thumbnail and omits recessed side-panel depth, the medical cross, labels, and tertiary
wear. Those limitations remain visible and documented rather than hidden behind the completed
pipeline checks.
