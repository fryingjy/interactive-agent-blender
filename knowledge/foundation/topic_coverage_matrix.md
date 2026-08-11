# Topic coverage matrix

Updated 2026-08-11. `✓` means substantial evidence, `~` partial evidence, and `—` no demonstrated evidence. A topic is not mature until runtime use and second-shape transfer are represented, even when documentation and a controlled experiment exist.

| Topic | Docs | Video | Experiment | Failure case | Quiz | Runtime use | Second shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mesh fundamentals | ~ | ~ | ~ | ~ | ✓ | ✓ | ~ |
| Extrude | ~ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ |
| Inset | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Bevel operation | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ |
| Bevel modifier | ✓ | ~ | ✓ | ✓ | — | ~ | ✓ |
| Loop cut / Subdivide | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Knife / Bisect | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ |
| Merge / Merge by Distance | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Dissolve / Delete | ✓ | — | ✓ | ~ | ✓ | ~ | — |
| Bridge Edge Loops | ✓ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Fill / Grid Fill | ✓ | — | ✓ | ✓ | ✓ | ~ | — |
| Bisect | ✓ | — | ✓ | ✓ | — | ~ | — |
| Spin | ✓ | — | ✓ | ✓ | — | ✓ | ✓ |
| Split / Separate | ✓ | — | ✓ | ~ | ✓ | ~ | — |
| Symmetrize | ✓ | — | ✓ | ✓ | — | ~ | — |
| Vertex / Edge Slide | ✓ | — | ✓ | — | — | ~ | — |
| Rip | ✓ | — | attempted | ✓ | ✓ | — | — |
| Normals / orientation | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Smooth / Flat shading | — | — | ✓ | — | — | ✓ | ~ |
| Topology fundamentals | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Subdivision Surface | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Boolean modifier | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mirror modifier | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Solidify modifier | ✓ | — | ✓ | ✓ | ~ | ~ | ✓ |
| Array modifier | ✓ | — | ✓ | ✓ | — | — | — |
| Shrinkwrap modifier | ✓ | — | ✓ | ✓ | — | ~ | ✓ |
| Simple Deform modifier | ✓ | — | ✓ | ✓ | — | — | — |
| Screw modifier | ~ | — | ✓ | ~ | — | — | — |
| Remesh modifier | ~ | — | ✓ | ~ | — | — | ~ |
| Decimate modifier | ~ | — | ✓ | ~ | — | — | — |
| Triangulate modifier | ~ | — | ✓ | ~ | — | ~ | — |
| Smooth modifiers | ~ | — | ✓ | ~ | — | — | — |
| Curve modifier | ~ | — | ✓ | ~ | — | ✓ | ~ |
| Lattice modifier | ~ | — | ✓ | ~ | — | — | — |
| Modifier stack order | ~ | — | ✓ | ✓ | ✓ | ~ | ~ |
| Retopology fundamentals | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Corrective shape keys / drivers | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reference blockout | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multi-view visual comparison | ~ | — | ✓ | ✓ | — | ~ | — |
| Diagnostic visual passes | ~ | — | ✓ | ✓ | — | ~ | — |
| Semantic region rendering | ~ | — | ✓ | ✓ | — | ~ | — |
| Localized reference tickets | ~ | — | ✓ | ✓ | — | ~ | — |
| Evaluated surface diagnostics | ~ | — | ✓ | ✓ | — | ✓ | ✓ |
| Surface review lighting | ~ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Machine-enforced stage gates | ~ | — | ✓ | ✓ | — | ~ | — |
| Professional review aggregation | ~ | — | ✓ | ✓ | — | ~ | — |
| Curve objects | ~ | — | ✓ | ✓ | — | ✓ | ~ |
| Sculpting | ✓ | ✓ | ✓ | ✓ | — | ~ | ~ |
| UVs | ✓ | ✓ | ✓ | ✓ | — | ~ | ✓ |
| Materials / shading | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Production organization | ~ | — | ✓ | ✓ | — | ~ | — |
| Export round-trip | ~ | — | ✓ | ✓ | — | ~ | — |
| Blender Python / BMesh | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Blender runtime events/depsgraph | ✓ | — | ✓ | ✓ | — | ~ | — |
| Typed modeling operation surface | ~ | — | ✓ | ✓ | — | ✓ | ~ |
| Scoped transaction rollback | ~ | — | ✓ | ✓ | — | ✓ | — |
| Structured knowledge retrieval | ✓ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Documentation crawl tracking | ✓ | — | ✓ | ✓ | — | ~ | — |
| Self-session learning/replay | ~ | — | ✓ | ✓ | — | ~ | ✓ |
| Modeling strategy selection | ~ | — | ✓ | ✓ | — | — | — |

## Current interpretation

The strongest evidence is concentrated in closed-loop runtime behavior, core mesh operations, SubD, topology diagnosis, and selected hard-surface workflows. Standalone Bevel, Mirror, Boolean, Solidify, Array, Shrinkwrap, and Simple Deform now have documentation plus controlled Blender 5.2 experiments. Boolean has genuine runtime/cross-asset transfer evidence; Solidify, Bevel, Mirror, and Shrinkwrap now have controlled second-shape transfer. Modifier-order transfer remains partial because the curved Mirror/Subdivision result narrowed the earlier flat-seam rule. A fixed-frame synthetic front/side/top loop measures silhouette, bounds, centroid, and contour regression. Same-reference profile modeling transferred from a fantasy sword to a tactical axe, then to a real multi-view rotational prop: the barrel body uses one connected 5,376-quad revolved shell with integrated hoops/corrugations and reaches 0.983 mean normalized three-view IoU. The barrel was tuned against its source and is corrective evidence, not held-out professional-quality proof.

The official-head facial transfer now gives second-shape corrective evidence with independent saved-rig
verification, but its expression is subtle and does not establish production acting. The weakest breadth remains production-quality organic sculpting, full-character/facial articulation,
unknown real-production surface diagnosis, independent/long-horizon retrieval retention,
professional visual judgment, and broader transfer validation.

Video evidence is credited only for eleven Blender-authored/Studio lessons actually decoded,
captioned or locally transcribed, and cross-checked on 2026-08-10. The Modeling Introduction lesson gives partial
mesh-fundamentals coverage; dedicated Extrude and Bevel lessons give substantial operator coverage;
the UV, Sculpt, facial-planning, pole-placement, and lighting lessons now have different-shape experiments. The older Blender 2.80 UI is
version-limited, and machine transcript wording is not treated as authoritative. All unrelated
Video cells remain `—`.

The connected-barrel mixed-cause run provides second-shape runtime evidence for intervention-based
surface diagnosis and review lighting: five simultaneous known faults are selected and repaired by
an adaptive ablation matrix under fixed-seed Cycles, with exact clean-state recovery and independent
mesh verification. It does not establish diagnosis of unknown production defects.

The seam-authored UV bake now has named-engine transfer evidence in Godot 4.7.1. Direct GLB parsing
and a fresh engine import verify UVs, explicit package tangents, normal-texture binding, PBR factors,
unit scale, and axis-converted dimensions. A Base-Color miswiring control proves that successful
import alone does not preserve tangent-normal semantics. This strengthens export/runtime evidence,
but does not establish production texture quality across compression, mip levels, or engines.
