# Profile-authored tactical axe study

## Source and intent

The supplied single-view source is
`C:\Users\odane\Downloads\blender\ref\tactical_axe.png`. This run tests whether the modeling
system can transfer profile-authored hard-surface construction to a different shape family after
the sword quality rebuild. It is corrective transfer evidence, not a new held-out benchmark.

## Reference analysis

- Thresholded source bounds: `[6, 63, 553, 249]`.
- Measured outer-profile area: 37,833 pixels.
- Measured head-aperture area: 1,768 pixels.
- Measured grip-region area: 18,907 pixels.
- The source supports side silhouette, negative space, fastener placement, and broad material
  separation. It does not establish hidden construction, absolute dimensions, thickness, bevel
  depth, or the far-side grip shape.

## Construction decisions

- The full tang and axe head come from a simplified 35-point measured contour extrusion.
- The head opening is a real through-aperture made by an exact Boolean, not a dark decal.
- Raised grip scales are separate closed meshes derived from an eroded semantic grip mask and use
  procedural bump for controlled surface breakup.
- The exposed cutting edge is a separate authored strip so its bevel/material response can differ
  from the dark body.
- Four fasteners are separate authored cylinders at measured source landmarks.
- The hierarchy uses restrained bevels, explicit UV layers, semantic names, and a final
  triangulation stage for deterministic evaluated verification.
- No `bpy.ops.mesh.primitive_*` operator is used. The asset contains seven semantic mesh objects.

## Visual and technical result

- Normalized side-silhouette IoU: **0.942380**.
- Aperture/negative-space IoU: **0.771739**.
- Normalized centroid error: **0.001314**.
- Normalized symmetric contour error: **0.001523**.
- Fresh-process evaluated verification: **7/7 clean meshes**; every component is closed manifold,
  outward-positive, UV-bearing, and free of n-gons, loose geometry, and degenerate faces.

Artifacts include `profile_authored_axe.blend`, `axe_beauty.png`, `axe_front_mask.png`, the
`silhouette_eval/` masks/overlay/metrics, `reference_profile.json`, and
`fresh_collection_verify.json`.

## Retained failures and limits

The first tessellator adapter assumed the wrong Blender 5.2 return shape; the first camera cropped
the head; and a threshold of 240 incorrectly included the gray background, yielding a meaningless
0.269494 IoU. All are retained in `failed_attempts.json` with their corrections.

The strong profile score does not validate unseen depth, ergonomics, material realism, mechanical
construction, multi-view consistency, or professional acceptance. The same supplied image drove
profile extraction and evaluation, so this is measured same-reference transfer rather than unseen
human judgment.
