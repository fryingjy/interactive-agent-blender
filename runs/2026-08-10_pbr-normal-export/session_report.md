# PBR normal-map GLB round trip

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS for delivery invariants; imported editable topology intentionally not credited clean

## Result

A clean beveled source uses an `EngineUV` map, packed 32×32 tangent-space normal texture in
Non-Color space, Image Texture → Normal Map → Principled Normal chain, metallic 0.2, and roughness
0.38. The exported 9,368-byte GLB re-imports as exactly one mesh with matching world bounds and 108
surface triangles, a UV map, material, packed 32×32 normal image, Non-Color interpretation, normal
node links, and roughness 0.38. All 11 declared round-trip assertions pass.

The original editable source independently verifies clean: 56 vertices, 54 faces, no n-gons,
non-manifold edges, loose geometry, or degenerates, with outward normals.

## Preserved limitation/failure

The re-imported GLB has 216 vertices and 216 non-manifold edges under the editable-mesh verifier.
glTF split vertices at UV/normal boundaries while preserving the triangulated surface, bounds,
normals, UVs, material, and texture semantics. The result is acceptable as a delivery round-trip
for these declared invariants, but it is not relabeled as a clean editable Blender source mesh.

Blender 5.2 also warns that `Material.use_nodes` is expected to be removed in Blender 6.0. The one
creation-time assignment is retained for current-version compatibility and recorded as version-
limited API behavior.

## Limits

The normal texture is a controlled tangent-vector pattern, not a high-to-low baked production map.
This validates packaging and shader/export semantics, not bake cage quality, mip behavior, channel
conventions in a named external engine, or compression artifacts.
