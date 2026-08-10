# Topic coverage matrix

Updated 2026-08-10. `✓` means substantial evidence, `~` partial evidence, and `—` no demonstrated evidence. A topic is not mature until runtime use and second-shape transfer are represented, even when documentation and a controlled experiment exist.

| Topic | Docs | Video | Experiment | Failure case | Quiz | Runtime use | Second shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mesh fundamentals | ~ | — | ~ | ~ | ✓ | ✓ | ~ |
| Extrude | ~ | — | ✓ | ✓ | ~ | ✓ | ✓ |
| Inset | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Bevel operation | ✓ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Bevel modifier | ✓ | — | ✓ | ✓ | — | ~ | ✓ |
| Loop cut / Subdivide | ~ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Merge / Merge by Distance | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |
| Dissolve / Delete | — | — | ✓ | ~ | ✓ | ~ | — |
| Bridge Edge Loops | — | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Fill / Grid Fill | — | — | ✓ | ✓ | ✓ | ~ | — |
| Bisect | — | — | ~ | — | — | ~ | — |
| Spin | — | — | ✓ | — | — | ~ | — |
| Split / Separate | — | — | ✓ | ~ | ✓ | ~ | — |
| Symmetrize | — | — | ✓ | ✓ | — | ~ | — |
| Vertex / Edge Slide | — | — | ✓ | — | — | ~ | — |
| Rip | — | — | attempted | ✓ | ✓ | — | — |
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
| Modifier stack order | ~ | — | ✓ | ✓ | ✓ | ~ | ~ |
| Retopology fundamentals | ✓ | — | ✓ | ✓ | — | ✓ | ~ |
| Reference blockout | ✓ | — | ~ | ✓ | ✓ | ✓ | ~ |
| Multi-view visual comparison | ~ | — | ✓ | ✓ | — | ~ | — |
| Curve objects | ~ | — | ✓ | ✓ | — | ✓ | ~ |
| Sculpting | ✓ | — | ✓ | ~ | — | — | ~ |
| UVs | ✓ | — | ✓ | ✓ | — | ~ | ✓ |
| Materials / shading | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Production organization | ~ | — | ✓ | ✓ | — | ~ | — |
| Blender Python / BMesh | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Structured knowledge retrieval | ✓ | — | ✓ | ✓ | ✓ | ✓ | ~ |

## Current interpretation

The strongest evidence is concentrated in closed-loop runtime behavior, core mesh operations, SubD, topology diagnosis, and selected hard-surface workflows. Standalone Bevel, Mirror, Boolean, Solidify, Array, Shrinkwrap, and Simple Deform now have documentation plus controlled Blender 5.2 experiments. Boolean has genuine runtime/cross-asset transfer evidence; Solidify, Bevel, Mirror, and Shrinkwrap now have controlled second-shape transfer. Modifier-order transfer remains partial because the curved Mirror/Subdivision result narrowed the earlier flat-seam rule. A fixed-frame synthetic front/side/top comparison loop now measures silhouette, bounds, centroid, and contour regression, but it has not yet been used on a held-out or photoreal reference.

The weakest breadth remains real brush-based sculpting, export validation, external video-based learning, multi-day retrieval retention, held-out visual judgment, and broader transfer validation.

Topic Video cells remain `—` because no external curriculum source has been studied. The local ingestion subsystem itself has processed and visually checked a project-owned MP4 with video, audio, captions, transcript, and timestamped frames; that fixture validates access mechanics but is not credited as subject-matter instruction.
