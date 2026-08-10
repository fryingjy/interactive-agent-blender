# Blender modeling documentation walk

**Audit date:** 2026-08-10  
**Target runtime:** Blender 5.2.0 LTS  
**Rule:** an index page is orientation, not proof that every child page was studied.

This is the systematic map between official documentation and repository evidence. `TESTED` means
a controlled Blender artifact exists; `USED` means a technique also appears in a real modeling
session; `INDEXED` means the branch and its boundaries were mapped but child-page study is
incomplete; `OPEN` means no adequate evidence exists.

| Documentation branch | Primary official source | Status | Repository evidence | Remaining work |
| --- | --- | --- | --- | --- |
| Mesh editing overview | Mesh Editing operator index | INDEXED | mandatory operator inventory plus prior labs/cards | child pages are not exhaustively studied |
| Extrude / inset | Mesh Editing branch | USED | speaker, soap-dish, operator runs | formal parameter sweep is incomplete |
| Bevel operation | Bevel Manual | TESTED/USED | operator card and prior runs | profile/custom-profile breadth |
| Delete / dissolve | Mesh Editing branch | TESTED | operator and BMesh labs | complete child-page notes |
| Merge by Distance | Mesh Editing + BMesh API | TESTED | BMesh lab | edit-mode operator parameter sweep |
| Bridge / fill / grid fill | Mesh Editing branch | TESTED/USED | operator runs and failure records | more incompatible-loop shapes |
| Bisect / spin / symmetrize | Mesh Editing branch | TESTED | operator runs | second-shape transfer is sparse |
| Slides / rip | Mesh Editing branch | PARTIAL | operator run; headless rip failure | interactive-context rip evidence |
| Normals / shading | Mesh Editing + BMesh API | TESTED/USED | BMesh normals and production sessions | custom normals/weighted normals |
| Subdivision Surface | Subdivision Surface Manual | TESTED/USED | soap dish and topology/SubD lab | broader crease and boundary modes |
| Bevel modifier | Bevel modifier Manual | TESTED | modifier and curved-transfer labs | custom profile and weight/vgroup limits |
| Mirror modifier | Mirror modifier Manual | TESTED | modifier and curved-transfer labs | clipping/bisect combinations across axes |
| Boolean modifier | Boolean modifier Manual | USED | foundation lab plus cross-asset use | exact/manifold solver transfer breadth |
| Solidify modifier | Solidify modifier Manual | TESTED | planar and curved transfer labs | complex-boundary/non-manifold inputs |
| Array modifier | Array modifier Manual | TESTED | array/deform lab | object offset, caps, fit modes |
| Shrinkwrap modifier | Shrinkwrap modifier Manual | TESTED | retopology lab | deformation-ready retopo transfer |
| Simple Deform modifier | Simple Deform Manual | TESTED | deform lab and preserved API pitfall | bend/taper/stretch second shapes |
| Screw/Remesh/Decimate/Triangulate | modifier index and official indexed excerpts | TESTED | secondary-modifier lab | exhaustive child pages and second shapes |
| Smooth/Corrective/Laplacian Smooth | modifier index and official indexed excerpts | TESTED | secondary-modifier noisy-sphere controls | armature correction and second shapes |
| Curve/Lattice modifiers | modifier index and official indexed excerpts | TESTED | segmented-strip and cage-deformation controls | cross-asset production transfer |
| Retopology/remeshing | Retopology Manual | TESTED | low-cage conformance, actual sculpt handoff, deformation-density lab | production articulation and animation weighting |
| Sculpting | Sculpting index | PARTIAL | Multires, voxel remesh, actual Draw stroke and retopo handoff | masks, Face Sets, filters, multi-stroke form development |
| UV layout/editing | UV workflow/editing Manual | TESTED | UV/material/sculpt and PBR GLB labs | seams on complex asset and engine-specific conventions |
| Materials | Materials introduction + Principled BSDF | USED | node/slot repair and packed normal-map GLB transfer | color management and named-engine transfer |
| BMesh ownership/layers | BMesh module API | TESTED | BMesh API lab | edit-mode live BMesh and more custom-data layers |
| BMesh operators | BMesh operators API | TESTED | nine-operation lab | systematic signatures beyond modeler-critical subset |
| Reference images | Empties Manual | USED | reference blockouts | perspective/camera calibration |

## Version discipline

The source registry records the documentation version actually visible at study time. Manual
pages labeled 4.5 or 5.0 are not silently presented as 5.2 documentation; relevant claims were
reproduced in installed Blender 5.2.0 where the status says `TESTED`.

## Exit interpretation

The high-value modeling surface is now mapped and each major branch has at least orientation.
This does **not** mean every Manual child page or API function was read. The remaining gaps are
named above so future work can target them without converting an index visit into false breadth.
