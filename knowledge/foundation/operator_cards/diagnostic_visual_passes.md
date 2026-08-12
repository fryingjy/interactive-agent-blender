# Blender-native diagnostic visual passes

## Passes

- **Solid:** lit/cavity form inspection.
- **MatCap:** fast Solid-mode highlight inspection for bevel continuity, unintended softness, faceting,
  and waviness without material, light, or renderer setup. It is a review pass rather than beauty
  output and must be read alongside evaluated geometry.
- **Wireframe:** evaluated topology density and routing, rendered as temporary edge tubes.
- **World normal:** direction color for discontinuities and faceting.
- **Depth:** view-axis depth gradient for overlap and placement.
- **Component mask:** categorical object separation for per-component comparison.
- **Semantic region:** one persistent-ID base-cage face region against context, with stale-ID rejection.
- **Grazing highlight review:** asymmetric key, restrained fill, and rim under fixed camera/material/
  exposure to expose curved-surface dents or waviness that broad frontal light can hide.

Every image must remain attached to scene revision, target/frame objects, camera, projection,
resolution, and view. A saved file or successful render operator is insufficient; require nonblank
content and pass-specific variation.

## Evidence

`runs/2026-08-10_visual-passes/` contains Solid, MatCap, wireframe, normal, depth, and component
mask images with metadata, two preserved wireframe failures, a saved `.blend`, and independent
evaluated-mesh verification. The Blender 5.2 MatCap pass reports 87 quantized foreground colors,
compared with three required by its non-flatness assertion.

`runs/2026-08-10_semantic-region-render/` adds selected-region rendering, dominant-color content
validation, an isometric view, and a preserved edge-on false positive.

`runs/2026-08-10_surface-lighting-judgment/` controls clean/defective topology, material, camera,
engine, and exposure. The corrected grazing review rig raises defect image difference 2.57× over
flat frontal lighting. Two failed verification/lighting assumptions are retained.

## Limits

These are 8-bit diagnostic PNGs, not raw EXR data. They support inspection but do not yet classify
pinching, waviness, or highlight flow automatically.
