# Current development state

## Shield body study

**Current working scene: `work/shield/15-tip-shading.blend`.** Connected oval panel and rounded rim, 290 base vertices / 288 quads, one live level-2 subdivision modifier (4,610 evaluated vertices / 4,608 evaluated faces). It remains an unfinished surface study, not an accepted prop.

Reference: [Wood shield by hatalar205](https://commons.wikimedia.org/wiki/File:Wood_shield.svg), released under CC0 through Open Clipart. This is an illustration-driven exercise, not a reconstruction of a documented physical shield. Its back, thickness, and physical dimensions are unknown.

Observed locally with Blender 5.2.1 LTS. The source image is 960 pixels wide; SHA-256 `b7d56a560dcad187e4d6e2f64e5b2d90d454cae5e8d1b2e8a4d01910d1b96aab`. Downloads, request logs, scenes, and previews live in ignored `work/shield/`, not Git.

Mechanical setup created one cube. Subsequent geometry changes used fingerprint-checked runtime commands: subdivide the connected cube cage, then reposition vertices using a reference-outline mapping. The mapping is study-specific; it is not an autonomous reference-understanding subsystem. Alpha segmentation is unusually easy on this transparent illustration.

The initial all-quad starting body was `work/shield/02-body.blend`: 218 vertices and 216 quads. It has one connected component, no nonmanifold edges, and no detected degenerate faces. It is a flat body with assumed thickness 0.08 Blender units, not a completed shield. No modifiers were applied.

An observed silhouette repair added cuts only along the outer boundary and conformed the new points to the reference. The resulting `work/shield/04-refined.blend` has 266 vertices, 128 quads, eight triangles, and 88 pentagons. Despite a better outline, this is **not promoted as the working subdivision cage**. The original all-quad body remains the starting point for the next construction decision.

| Diagnostic | Initial body | Boundary experiment |
| --- | --- | --- |
| Same-view silhouette IoU | 0.987843 | 0.994209 |
| Missing silhouette pixels | 1,228 | 578 |
| Extra silhouette pixels | 0 | 7 |
| Connected components | 1 | 1 |
| Nonmanifold edges | 0 | 0 |
| N-gons | 0 | 88 |

Both comparisons used the same 512-square orthographic render frame, scale 2.4, and reference-to-frame scale 0.3555555556 with offset (85.3333333333, 17.0666666667). There was no per-candidate alignment optimization. This is a fitted same-view contour test, not held-out validation. The oblique view verifies thickness visually but has no independent reference counterpart.

## Retained lesson

Selective boundary refinement can improve an outline while damaging a useful quad layout. Review topology after local subdivision; reject the tradeoff when the planned surface workflow needs better loop structure. A silhouette score cannot authorize that decision by itself.

## Connected panel and surface pass

Starting from the all-quad body, inset the front face region and reposition its grid to a provisional oval centered at source pixel (474,562), with radii (306,407). These are approximate measurements of the illustration, not independent ground truth. A second inset creates a narrow recessed transition. Rim and panel remain part of the same mesh.

Live subdivision plus edge creases smoothed the oval but shrank the outer silhouette. A targeted vertex crease recovered a less rounded tip. One bounded correction of the outer cage, derived from the observed evaluated contour, improved same-view IoU from 0.975518 to 0.992794 under the same CPU renderer and fixed camera. This does not validate unseen depth or hidden construction.

For rim relief, split its opposite radial edges to add one continuous middle loop, then raise that loop. Unlike the earlier isolated boundary splits, this preserved all quads. The assumed rim height is 0.045 units above the outer front surface. The outline score remained 0.992794: 437 missing pixels and 293 extra pixels. No geometry modifiers were applied.

Final base checks: one component, zero nonmanifold edges, zero detected degenerate faces, zero triangles/n-gons. Front surface smoothing was deliberately scoped. A dark tip artifact appeared under smooth shading; flattening the terminal faces reduces that artifact but introduces visible local faceting. The final tip is provisional and needs better surface-flow treatment. This is not a completed shading repair.

The front image shows the recessed oval and broad rounded rim. An oblique CPU render was visually inspected; it confirms the modeled relief, not fidelity to an unavailable side reference. Panel proportions still need a more precise component-boundary comparison. Fasteners, planks, materials, back construction, and delivery preparation are absent.

## Runtime findings

Creating a new BMesh custom-data layer invalidated cached edge handles. Crease editing now creates the layer first, then reacquires elements. Native tests exercise edge and vertex crease operations.

Workbench intermittently wrote a preview and then crashed during shutdown in `igxelpicd64.dll`. The CPU Cycles inspection option completed the subsequent study renders and native tests with clean exits. The Intel driver issue is not fixed; this is an alternative execution path. CPU preview noise is expected at eight samples. Source materials are not changed.

Inspection now explicitly reports polygon-type counts, and mesh edits warn on introduced n-gons. Malformed position requests and failed managed-modifier inspections are tested for rollback. These safeguards address concrete failures; they are not artistic acceptance checks.

## Next modeling work

Resolve the terminal rim's surface flow, compare the oval boundary with the illustration, then add its remaining assembly details and materials. Do not chase a perfect silhouette score while those larger features are missing. Thickness and the back must continue to be labeled assumptions unless another suitable reference resolves them.

The body is not a finished prop or commission candidate. No UV, material, game-engine import, independent review, or generalized modeling claim has been completed. HIGH_POLY/LOW_POLY production packaging should follow a credible surface, not precede it.

## Runtime verification

Thirteen native Blender tests pass, including connected inset, crease/subdivision, scoped smoothing, CPU rendering cleanup, n-gon warnings, and rollback. Four Python tests pass with Blender enabled, covering CLI save/reload and overwrite/stale-state rejection plus mask comparison behavior. Checks remain limited: intersections, winding problems, n-gon suitability, and reference accuracy are not automatically accepted or rejected by the basic mesh-health guard.

No private client data, reference images, renders, or binary scenes are pushed to GitHub. Local study artifacts remain available for continuation; the experiment is not reproducible from this compact report alone.
