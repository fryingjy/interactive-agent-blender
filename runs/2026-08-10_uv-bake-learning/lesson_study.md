# UV seam and high/low bake learning episode

**Status: PASS (candidate skill evidence, not held-out promotion)**

## Source observation

Official Blender Fundamentals, *UV Unwrapping* (CC BY 3.0 mirror):
https://commons.wikimedia.org/wiki/File:UV_Unwrapping_-_Blender_2.80_Fundamentals.webm

Actual modalities processed: 385.021 seconds of video/audio, 13 decoded frames, and 70 local
machine-transcript segments. Full media/transcript remain local and ignored by Git.

Key timestamped observations:

- 03:21-04:24: standard Unwrap uses authored seams, while Smart UV and projection methods are
  strategy alternatives with different tradeoffs.
- 04:09-04:48: Project from View can look correct from one viewpoint and stretch perpendicular
  faces because they receive insufficient UV area.
- 05:08-06:24: seams specify the cut graph; the instructor explains each cut by the intended island
  connectivity rather than marking edges arbitrarily.

## Interpretation

Seam placement is a topology/production decision. Start from the islands needed for continuous
texture flow and hidden discontinuities, then choose the minimum cut graph that opens those islands.
Automatic packing does not repair poor seams, distortion, or inconsistent texel density.

Current official documentation corroborated the lesson and added production requirements:

- Average Island Scale and Minimize Stretch target scale/distortion, while Pack Islands targets
  texture-space use.
- Selected-to-Active baking needs an active UV-mapped low mesh and selected high source; cage/ray
  settings control projection misses.
- Tangent normal textures must use the matching UV map and Non-Color interpretation.

## Different-shape reproduction

`tools/run_uv_bake_learning_lab.py` authored a flared 12-sided low-poly housing (50 vertices,
60 faces) and a 64-sided detailed high source (1,602 vertices, 1,664 faces). This is not an asset
benchmark; it is a neutral controlled transfer fixture.

The low mesh uses 27 deliberate seams: both cap boundaries plus one longitudinal side cut. Unwrap,
Average Island Scale, and packing produced zero degenerate UV faces, all coordinates inside the
0-1 tile, and world texel-ratio coefficient of variation `0.12050`.

## Failure and recovery

1. The first run used the remembered `BLENDER_EEVEE_NEXT` enum. Blender 5.2 rejected it; the valid
   enum is `BLENDER_EEVEE`, and the bake path correctly changed to `CYCLES` CPU.
2. Selected-to-Active with no selected high source was intentionally tested and rejected with
   `No valid selected objects`.
3. With the high source selected and low mesh active, the tangent bake finished. The 256x256 map
   contains 27,552 non-neutral pixels and measurable RGB variation.

Fresh Blender processes independently verified both high and low meshes manifold, non-degenerate,
normal-consistent, with no n-gons or loose geometry.

## Candidate skill

For production UV/bake work: author seams from intended island continuity; apply scale; unwrap;
average island scale; inspect distortion and padding; select high source(s) and make UV-mapped low
target active; use Cycles Selected-to-Active with measured cage/ray distance; bake tangent normals;
interpret the image as Non-Color; verify visible projection artifacts and mesh validity.

Status remains **EXPERIMENTALLY_TESTED** until reused on a genuinely different production asset.
