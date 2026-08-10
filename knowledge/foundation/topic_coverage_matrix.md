# Topic coverage matrix

Updated 2026-08-10. `✓` means substantial evidence, `~` partial evidence, and `—` no demonstrated evidence. A topic is not mature until runtime use and second-shape transfer are represented, even when documentation and a controlled experiment exist.

| Topic | Docs | Video | Experiment | Failure case | Quiz | Runtime use | Second shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mesh fundamentals | ~ | ~ | ~ | ~ | ✓ | ✓ | ~ |
| Extrude | ~ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ |
| Inset | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Bevel operation | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ |
| Bevel modifier | ✓ | ~ | ✓ | ✓ | — | ~ | ✓ |
| Loop cut / Subdivide | ~ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Merge / Merge by Distance | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Dissolve / Delete | ✓ | — | ✓ | ~ | ✓ | ~ | — |
| Bridge Edge Loops | ✓ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Fill / Grid Fill | ✓ | — | ✓ | ✓ | ✓ | ~ | — |
| Bisect | ✓ | — | ✓ | ✓ | — | ~ | — |
| Spin | ✓ | — | ✓ | — | — | ~ | — |
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
| Retopology fundamentals | ✓ | — | ✓ | ✓ | — | ✓ | ✓ |
| Reference blockout | ✓ | — | ~ | ✓ | ✓ | ✓ | ~ |
| Multi-view visual comparison | ~ | — | ✓ | ✓ | — | ~ | — |
| Diagnostic visual passes | ~ | — | ✓ | ✓ | — | ~ | — |
| Semantic region rendering | ~ | — | ✓ | ✓ | — | ~ | — |
| Localized reference tickets | ~ | — | ✓ | ✓ | — | ~ | — |
| Evaluated surface diagnostics | ~ | — | ✓ | ✓ | — | ~ | ~ |
| Machine-enforced stage gates | ~ | — | ✓ | ✓ | — | ~ | — |
| Professional review aggregation | ~ | — | ✓ | ✓ | — | ~ | — |
| Curve objects | ~ | — | ✓ | ✓ | — | ✓ | ~ |
| Sculpting | ✓ | — | ✓ | ~ | — | ~ | ~ |
| UVs | ✓ | — | ✓ | ✓ | — | ~ | ✓ |
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

The strongest evidence is concentrated in closed-loop runtime behavior, core mesh operations, SubD, topology diagnosis, and selected hard-surface workflows. Standalone Bevel, Mirror, Boolean, Solidify, Array, Shrinkwrap, and Simple Deform now have documentation plus controlled Blender 5.2 experiments. Boolean has genuine runtime/cross-asset transfer evidence; Solidify, Bevel, Mirror, and Shrinkwrap now have controlled second-shape transfer. Modifier-order transfer remains partial because the curved Mirror/Subdivision result narrowed the earlier flat-seam rule. A fixed-frame synthetic front/side/top comparison loop now measures silhouette, bounds, centroid, and contour regression, but it has not yet been used on a held-out or photoreal reference.

The weakest breadth remains multi-stroke sculpting, production articulation/retopology, complex
seam-authored UV/baking work, advanced external video instruction, multi-day retrieval retention,
professional visual judgment, and broader transfer validation.

Video evidence is credited only for three Blender-authored Fundamentals lessons actually decoded,
locally transcribed, and cross-checked on 2026-08-10. The Modeling Introduction lesson gives partial
mesh-fundamentals coverage; dedicated Extrude and Bevel lessons give substantial operator coverage;
the Bevel modifier section is partial. The older Blender 2.80 UI is version-limited, and machine
transcript wording is not treated as authoritative. All unrelated Video cells remain `—`.
