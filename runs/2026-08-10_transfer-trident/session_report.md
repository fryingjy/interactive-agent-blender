# Transfer benchmark D: stylized trident

**Date:** 2026-08-10
**Reference:** `C:\Users\odane\Downloads\blender\ref\f4fb9a354f6b40482eb243c49caec5b9.png` (left trident crop)
**Result:** PASS

## Locked gate and result

Before modeling, `reference_analysis.json` fixed the normalized front-silhouette IoU target at
0.65 and required clean independent verification of every intended visible solid. The final score
is **0.6765773552290406**. The initial blockout scored 0.41448895166986177; measured corrections
improved it through 0.5473, 0.5833, 0.6089, and 0.6493 without changing the gate or comparison
method.

## Closed-loop modeling record

- Geometry was created and changed through the typed modeler protocol in one persistent Blender
  session, ending at decision revision 77.
- The initial box-segment prongs failed the silhouette audit. They remain hidden and editable in
  the `.blend`; measured curve-to-mesh crescents became the evaluated representation.
- Materials, collection assignment, camera/light setup, visibility of superseded components,
  rendering, and saving used the generic Blender fallback. It was not used to generate or mutate
  evaluated modeling geometry.
- The visible asset contains 14 independently editable mesh components grouped under semantic
  head and shaft collections.

## Independent verification

Each visible component was reopened and checked in a separate Blender 5.2 background process with
`tools/verify_mesh.py --evaluated --max-ngons 0 --max-non-manifold 0`. All **14/14** passed with
zero non-manifold edges, n-gons, loose geometry, or degenerate faces and positive signed volume.
The timestamped reports are in `independent_verify/`.

## Scope of the claim

This is one cross-family transfer pass after the held-out fantasy sword. It demonstrates successful
transfer from a broad hard-surface sword to a slender ornamental multi-component prop without an
asset-specific builder. It does not replace later-calendar-day retention evidence or independent
experienced-modeler qualitative acceptance.
