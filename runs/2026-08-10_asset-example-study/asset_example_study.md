# Supplied weapon `.blend` example study

Date: 2026-08-10

Blender: 5.2.0 LTS

Purpose: learn production structure from the user's supplied examples before authoring a new weapon. This is a read-only study, not an assertion that every supplied file is a professional-quality target.

## Method

Each source was opened in background Blender and inspected with `tools/inspect_blend_asset.py`. Selected low meshes were then linked into a fresh scene and rendered with `tools/render_blend_asset_review.py`. The review script replaces materials with one diffuse clay and uses a consistent orthographic three-light setup. It never saves the source `.blend`.

The first Z-sword review failed observability: a metallic override and size-independent lamp power produced an almost black silhouette. That result is retained as `z-sword-low-review.png`. The corrected render, `z-sword-low-review-corrected.png`, uses diffuse clay and lamp power scaled to asset extent. This is a review-tool correction, not a change to the source asset.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `adventure time sword.blend` | 3,876,196 | `A6F7B1BF4232BF9B680A9159208AC9D7B5EB3515847D9B46D0202DEAB7CB4531` |
| `battle axe.blend` | 1,515,914 | `E40A71CADE87DFA4B2D442220BC3E4DC2133717857FED9D63D169D5EFF04B5AE` |
| `dagger.blend` | 48,893,684 | `C70BE38131A96A78AB47C0EDB8DD69B702A0ADBD56183701C5B3AAA3D37C41AA` |
| `Dragon Slayer.blend` | 9,316,552 | `3F72129EA448A42F6EE4D4AD85B49C49790F9DD2AE8D605BE758786EE481298D` |
| `gladius.blend` | 15,936,211 | `39583A56F7A2B33CBE36794D957C5199189D6F0545CFDDCEC0BCB4CA4677C7AE` |
| `z_sword.blend` | 51,334,600 | `5D1824952082D40A6AAE2F933B0013A498E97197316DED34DADA757EE0D20AB2` |

## Measured observations

| Asset | Structure that transfers | Important limitation or rejection |
|---|---|---|
| Adventure Time sword | Five explicit low components and corresponding high components; the low silhouette preserves authored tip, blade notches, guard, grip, and pommel; Mirror/Bevel/Subdivision are retained on construction meshes. | The low blade contains four n-gons. They may be acceptable on planar, non-deforming regions, but this does not make n-gons a default topology strategy. |
| Battle axe | Eleven mesh components; Array, Screw, Shrinkwrap, Solidify, Mirror, and Subdivision indicate procedural treatment of wraps/repeated details and symmetric forms. | Aggregate non-manifold count is high because several objects are open shells. Asset-wide totals cannot distinguish intentional sheet construction from defects; inspect per component before judging. |
| Dagger | An explicit 461,369-vertex / 922,746-triangle high and a closed 348-vertex / 406-face low. The low preserves the leaf blade, waist, curved guard, and three negative-space cutouts. | The high has six degenerate faces and no UV layer. It is suitable as a high-frequency bake source, not as evidence of clean low-poly topology. |
| Dragon Slayer | Twenty-seven mesh objects with named high, low, and construction variants; repeated Subdivision, Mirror, and Bevel stacks show non-destructive component development. | The selected eight low components render as a horizontal assembly and include 107 degenerate faces in the full file. Naming and orientation are inconsistent enough that an automated reviewer must not infer semantic front/up axes. |
| Gladius | Seventy-eight mesh objects and many high/low component pairs show granular decomposition. | The controlled render is visually basic and object naming makes assembly selection ambiguous. High object count alone is not evidence of quality or efficient organization. |
| Z-sword | Explicit blade/guard/hilt/handle/wrap/pommel separation, each with low/high or construction variants. The wrap construction uses Array → Shrinkwrap → Solidify; major forms use Mirror → Bevel → Subdivision. | The full file is dominated by triangulated highs and includes non-manifold geometry. The low review proves silhouette and plane hierarchy, not bake quality or texture quality. |

## Transferable rules

1. Author the weapon silhouette as purpose-built profile geometry. Do not approximate the blade or guard by stacking generic cubes.
2. Establish semantic components at blockout: blade, guard, hilt/handle, wrap, pommel, and optional inlay. Component separation must support editing, UVs, materials, and high/low correspondence.
3. Plan high/low correspondence before detail. A low must retain silhouette, negative spaces, major plane breaks, and bake-compatible closure; the high carries small bevels and secondary surface transitions.
4. Use modifiers because they express a design operation: Mirror for true bilateral forms, Bevel/Subdivision for controlled edge hierarchy, and Array/Shrinkwrap/Solidify for repeated wraps. Modifier count is never a quality metric by itself.
5. Treat guard cutouts and blade/guard junctions as authored negative-space design. The dagger example demonstrates that a 348-vertex low can preserve a distinctive silhouette without brute-force density.
6. Review silhouette and surface separately. Use an unlit or flat mask for contour, then a diffuse clay with grazing key/fill/rim lighting for plane continuity. Scale lamp power with scene extent.
7. Reject file-wide topology totals as a standalone acceptance test. Verify each production output mesh in context; high-poly bake sources and intentional open construction sheets have different contracts from final lows.

## Evidence

- Structural reports: `adventure-time-sword.json`, `battle-axe.json`, `dagger.json`, `dragon-slayer.json`, `gladius.json`, `z_sword.json`
- Controlled low reviews: `adventure-low-review.png`, `dagger-low-review.png`, `dragon-slayer-low-review.png`, `z-sword-low-review-corrected.png`
- Additional controlled reviews: `battle-axe-review.png`, `dagger-high-review.png`, `gladius-review.png`
- Retained failed review: `z-sword-low-review.png`

## Reproduction

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background SOURCE.blend --python-exit-code 1 --python tools/inspect_blend_asset.py -- REPORT.json
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background SOURCE.blend --python-exit-code 1 --python tools/render_blend_asset_review.py -- REVIEW.png OBJECT_NAME [OBJECT_NAME ...]
```

The next modeling benchmark must demonstrate these rules on a new shape and pass fresh-reopen verification. This study alone does not prove modeling competence.
