# Blender-native diagnostic visual passes

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS after two preserved wireframe failures

## Result

`render_diagnostic_pass` now produces fixed-camera solid, wireframe, world-normal, depth, and
component-mask PNGs from Blender's Workbench renderer. Every record includes scene revision,
camera location, orthographic projection, resolution, target objects, frame objects, and scale.
Normal/depth/wireframe passes operate on temporary copies of the modifier-evaluated meshes and
restore source objects and scene settings.

The controlled body-plus-ring scene passed eight assertions. Normal output contained 322 quantized
foreground colors, depth contained eight levels, component masks distinguished both parts, and
wireframe coverage was nonzero and lower than solid coverage. Both evaluated source components
independently verified closed and clean.

## Preserved failures

1. `failed_attempt_empty_workbench_wireframe.json`: Workbench `WIREFRAME` shading saved a PNG but
   produced zero foreground pixels in background rendering. The original assertion only required
   it to be sparser than solid and would have accepted the blank output.
2. `failed_attempt_wireframe_kept_faces.json`: a temporary Wireframe modifier with
   `use_replace=False` retained all faces, making coverage larger than the solid pass.

The final implementation requires visible pixels and uses `use_replace=True`.

## Limits

Normal/depth images are diagnostic color visualizations rather than raw floating-point EXR render
passes. Component colors are categorical and cycle after four objects. Selected semantic-region
rendering and highlight-flow classification remain separate open capabilities.
