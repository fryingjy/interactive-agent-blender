# Blender-native diagnostic visual passes

## Passes

- **Solid:** lit/cavity form inspection.
- **Wireframe:** evaluated topology density and routing, rendered as temporary edge tubes.
- **World normal:** direction color for discontinuities and faceting.
- **Depth:** view-axis depth gradient for overlap and placement.
- **Component mask:** categorical object separation for per-component comparison.

Every image must remain attached to scene revision, target/frame objects, camera, projection,
resolution, and view. A saved file or successful render operator is insufficient; require nonblank
content and pass-specific variation.

## Evidence

`runs/2026-08-10_visual-passes/` contains five final images, metadata, two preserved wireframe
failures, a saved `.blend`, and independent evaluated-mesh verification.

## Limits

These are 8-bit diagnostic PNGs, not raw EXR data. They support inspection but do not yet classify
pinching, waviness, or highlight flow automatically.
