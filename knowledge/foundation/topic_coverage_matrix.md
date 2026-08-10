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
| Topology fundamentals | ~ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Subdivision Surface | ✓ | — | ✓ | ✓ | ✓ | ✓ | ~ |
| Boolean modifier | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mirror modifier | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Solidify modifier | ✓ | — | ✓ | ✓ | ~ | ~ | ✓ |
| Modifier stack order | ~ | — | ✓ | ✓ | ✓ | ~ | ~ |
| Retopology fundamentals | — | — | ~ | ✓ | — | ✓ | — |
| Reference blockout | ✓ | — | ~ | ✓ | ✓ | ✓ | ~ |
| Curve objects | ~ | — | ✓ | ✓ | — | ✓ | ~ |
| Sculpting | — | — | — | — | — | — | — |
| UVs | — | — | ~ | ~ | — | ~ | — |
| Materials / shading | — | — | ~ | ✓ | — | ~ | — |
| Blender Python / BMesh | ~ | — | ✓ | ✓ | ~ | ✓ | ~ |

## Current interpretation

The strongest evidence is concentrated in closed-loop runtime behavior, core mesh operations, SubD, topology diagnosis, and selected hard-surface workflows. Standalone Bevel, Mirror, Boolean, and Solidify now have documentation plus controlled Blender 5.2 experiments. Boolean has genuine runtime/cross-asset transfer evidence; Solidify, Bevel, and Mirror now have controlled curved second-shape transfer. Modifier-order transfer remains partial because the curved Mirror/Subdivision result narrowed the earlier flat-seam rule and still lacks controlled visual comparison.

The weakest breadth remains sculpting, UV/material production, structured retopology, systematic API study, video-based learning, repeated retrieval, and transfer validation.

Video remains `—` because no source has been processed with honest access to instructional frames/audio/captions. This is an evidence state, not a claim that video is unnecessary.
