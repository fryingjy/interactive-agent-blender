# Connected camera corrective rebuild

## Evidence boundary

This is a post-review corrective run and is **not new held-out evidence**. The earlier camera
candidate passed its predeclared automated gates, but experienced user review rejected its broad
interpretation of separate assemblies. The correction therefore tests the stronger construction
rule after it was known: grow compatible forms from one base cage through routed loops, inset, and
extrusion; do not disguise disconnected primitive-like shells by joining them into one object.

## Accepted result

- One Blender mesh object and one connected mesh component.
- 258 base vertices, 256/256 base quads, closed manifold, no degenerate faces or loose vertices.
- 8,706 evaluated vertices and 8,704/8,704 evaluated quads after weighted Bevel and two SubD levels.
- Sixteen authored radial control vertices for the lens; evaluated smoothness comes from SubD.
- Lens and both top controls are welded extensions of the camera cage, not added cylinders.
- 144 lens-ring edges carry bevel weight 1.0; `Bevel (Weight, 0.028, 2 segments)` precedes SubD.
  The shell uses 0.04-unit authored perimeter support-loop spacing because beveling its front/back
  star-transition loops failed evaluated manifold checks.
- Populated UV layer and four integrated node-material regions.
- Normalized held-out-source silhouette IoU: front `0.902752`, side `0.852748`, top `0.727913`,
  mean `0.828676`; all original thresholds pass.
- Fresh-process saved-file verification passes 19/19 assertions.
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
