# Current development state

## Shield body study

Reference: [Wood shield by hatalar205](https://commons.wikimedia.org/wiki/File:Wood_shield.svg), released under CC0 through Open Clipart. This is an illustration-driven exercise, not a reconstruction of a documented physical shield. Its back, thickness, and physical dimensions are unknown.

Observed locally with Blender 5.2.1 LTS. The source image is 960 pixels wide; SHA-256 `b7d56a560dcad187e4d6e2f64e5b2d90d454cae5e8d1b2e8a4d01910d1b96aab`. Downloads, request logs, scenes, and previews live in ignored `work/shield/`, not Git.

Mechanical setup created one cube. Subsequent geometry changes used fingerprint-checked runtime commands: subdivide the connected cube cage, then reposition vertices using a reference-outline mapping. The mapping is study-specific; it is not an autonomous reference-understanding subsystem. Alpha segmentation is unusually easy on this transparent illustration.

The retained starting body is `work/shield/02-body.blend`: 218 vertices and 216 quads. It has one connected component, no nonmanifold edges, and no detected degenerate faces. It is a flat body with assumed thickness 0.08 Blender units, not a completed shield. No modifiers were applied.

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

## Next modeling work

The dominant missing feature is the oval recessed panel and its surrounding rim. Design loops around that panel rather than decorating the existing flat grid with separate primitives. Then inspect the front and oblique surface before adding fasteners or materials. Thickness and the back must continue to be labeled assumptions unless another suitable reference resolves them.

The body is not a finished prop or commission candidate. No UV, material, game-engine import, independent review, or generalized modeling claim has been completed. HIGH_POLY/LOW_POLY production packaging should follow a credible surface, not precede it.

## Runtime verification

Seven native Blender tests pass, including connected subdivision/repositioning. Four Python tests pass with Blender enabled, covering CLI save/reload and overwrite/stale-state rejection plus mask comparison behavior. Runtime commands now include connected subdivision and vertex-position edits. Checks remain limited: intersections, winding problems, n-gon suitability, and reference accuracy are not automatically accepted or rejected by the basic mesh-health guard.

No private client data, reference images, renders, or binary scenes are pushed to GitHub. Local study artifacts remain available for continuation; the experiment is not reproducible from this compact report alone.
