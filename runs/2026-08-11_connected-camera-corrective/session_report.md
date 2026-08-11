# Connected camera corrective rebuild

## Evidence boundary

This is a post-review corrective run and is **not new held-out evidence**. The earlier camera
candidate passed its predeclared automated gates, but experienced user review rejected its broad
interpretation of separate assemblies. The correction therefore tests the stronger construction
rule after it was known: grow compatible forms from one base cage through routed loops, inset, and
extrusion; do not disguise disconnected primitive-like shells by joining them into one object.

## Accepted result

- One Blender mesh object and one connected mesh component.
- 532 base vertices, 530/530 base quads, closed manifold, consistent winding, no degenerate faces or loose vertices.
- The housing starts from a literal box perimeter: four flat sides and four exact 90-degree corner
  rails. Intermediate edge-loop vertices support Edit Mode routing but do not pre-round the body.
- 25,122 evaluated vertices and 25,120/25,120 evaluated quads after weighted Bevel and two SubD levels.
- Each top control is a measured regular 12-vertex circle. Its rectangular 12-edge shell opening is
  bridged one-to-one into that circle and extruded as welded loops; it is not a rounded square.
- The lens uses 24 radial edges because its loop must match the locally refined body perimeter for
  a direct all-quad bridge. The top controls retain the user-requested sparse 12-edge density.
- Lens and both top controls are welded extensions of the camera cage, not added cylinders.
- All 492 intended hard edges carry bevel weight 1.0: 96 body-perimeter, 12 longitudinal body-corner
  rail, 216 lens-step, and 84 edges on each top control. Each visible corner rail consists of three
  connected segments split by support loops. `Bevel (Weight, 0.018, 2 segments)` precedes SubD. Tight authored support
  loops remain unweighted because they control transition width rather than represent hard edges.
- A semantic scope probe independently isolates every sharpness category. Base, Bevel-only, and
  final SubD stages are all closed, consistently wound, all-quad, and manifold.
- Populated UV layer and four integrated node-material regions.
- Normalized held-out-source silhouette IoU: front `0.888246`, side `0.846788`, top `0.730301`,
  mean `0.821778`; all original thresholds pass.
- Fresh-process saved-file verification passes 24/24 assertions, including a literal-box profile gate.
- GLB round trip passes 6/6 assertions as one mesh with exact evaluated dimensions, UVs, four
  material regions, and evaluated geometry.

## Rejected iterations

1. `failed_square_lens/`: one-component/all-quad but the four-sided lens cap visibly read square.
2. `failed_32_vertex_overdense/`: circular result but an unnecessarily dense 32-vertex radial cage;
   reduced to 16 after user review.
3. `failed_soft_edges/`: clean 16-vertex result rejected by experienced review for insufficient
   hard-surface sharpness.
4. `failed_overweighted_bevel/`: broad 198-edge weighting looked sharper but created 192 evaluated
   non-manifold edges. Width and scope probes isolated the safe 144-edge lens-only selection.
5. `failed_incomplete_weighting_square_controls/`: the first accepted correction is preserved after
   user review overturned it: lens-only weighting omitted intended hard edges, and four-sided top
   extrusions merely looked rounded under SubD. The replacement uses true 12-edge circles and a
   complete semantic 480-edge weight map.
6. `failed_missing_corner_rails/`: true circular controls and 480 clean weighted edges still omitted
   the four visible longitudinal corner rails identified by user review.
7. `failed_cardinal_midline_weights/`: the first rail interpretation weighted top/right/bottom/left
   midlines. It stayed manifold but created an unwanted side seam in Solid view. The accepted map
   instead weights the four diagonal rounded-rectangle corner chains.
8. `failed_broad_superellipse_corners/`: all 492 correct semantic edges were weighted, but the n=6
   base superellipse itself encoded a broad pill-shaped radius. Live-scene comparison showed the
   user's bevel ratio was comparable, proving width was not the softness cause. The accepted body
   next attempt used an n=16 profile that kept panels flatter and confined curvature to narrow corners.
9. `failed_pre_rounded_n16_body/`: n=16 still encoded curvature before Bevel. The accepted cage
   removes the superellipse entirely and begins from exact box sides/corners; weighted Bevel creates
   the complete visible corner radius.

## Live-scene transfer

Read-only inspection of the user's unsaved Blender scene found one selected planar 18-edge loop
with zero measured radial variation: a genuine circle rather than a subdivided square. Its base
half-cage has 20 expected Mirror-seam boundary edges; Mirror closes them, and the Mirror, Bevel,
SubD, and Smooth-by-Angle evaluated stages are all manifold. The same inspection found 219 edges
above a 25-degree dihedral threshold but only 153 weighted, confirming the user's warning that
visual sharpness coverage must be audited semantically rather than inferred from modifier presence.

Official operation study: Blender core **To Sphere** (`Shift-Alt-S`) can circularize a planar loop
around its pivot; the official LoopTools add-on's **Circle** operation adds best-fit, fit-inside,
regular spacing, flattening, radius, and influence controls. This scripted specimen generates the
same regular angular/radial result deterministically and verifies both radius and angle-gap error.

## Commands

```text
blender --background --factory-startup --python tools/run_connected_camera_corrective.py -- runs/2026-08-11_connected-camera-corrective
python tools/compare_alpha_multiview.py runs/2026-08-11_heldout-camera-subd/reference runs/2026-08-11_connected-camera-corrective runs/2026-08-11_connected-camera-corrective/normalized_silhouette_report.json --candidate-prefix connected --front-min 0.80 --side-min 0.68 --top-min 0.70 --mean-min 0.76
blender --background --factory-startup --python tools/verify_connected_camera_corrective.py -- runs/2026-08-11_connected-camera-corrective/connected_camera_corrective.blend runs/2026-08-11_connected-camera-corrective/connected_camera_verify.json
blender --background --factory-startup --python tools/run_connected_camera_export.py -- runs/2026-08-11_connected-camera-corrective/connected_camera_corrective.blend runs/2026-08-11_connected-camera-corrective/export/connected_camera.glb runs/2026-08-11_connected-camera-corrective/export/glb_roundtrip_report.json
```

## Remaining limitation

This is a deliberately stylized topology-transfer specimen, not a finished photoreal vintage
camera. Exact aperture hardware, engravings, leather microtexture, wear, and independent expert
acceptance remain open.
