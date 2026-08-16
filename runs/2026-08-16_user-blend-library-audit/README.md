# Read-only user blend-library audit

Six saved examples from `C:\Users\odane\Downloads\blender\blend` were opened read-only in Blender 5.2 and inventoried with `tools/inspect_blend_file.py`. No source `.blend` was modified or saved.

## What the examples demonstrate

| Source | Mesh objects | Notable construction evidence |
| --- | ---: | --- |
| `alien force watch.blend` | 52 | Explicit high/low collections; substantial all-quad SubD component cages; recurring Mirror, Bevel, Subdivision, and Smooth by Angle stacks. |
| `dragon radar.blend` | 2 | A 594-vertex all-quad radar cage with live Subdivision; a separate wire component. |
| `batarang.blend` | 3 | Separate high/low assets, with the editable construction plane retaining Mirror, Bevel, Subdivision, and Smooth by Angle. |
| `broken sword.blend` | 31 | High/low and ZBrush-support collections; complex multi-object production scene. |
| `battle axe.blend` | 5 | Compact assembly with mirror-assisted SubD components. |
| `adventure time sword.blend` | 15 | High/low/model separation with live modifier use across the editable forms. |

## Corrective conclusion

The problem in the rejected kettle was not that primitives are inherently forbidden. It was that I did not commit early enough to a reference-specific connected cage, check component silhouettes against the source, then rebuild the wrong cage before adding secondary features. The examples reinforce a better default: use an editable box/profile/mirror cage for a continuous manufactured surface; use separate objects only for genuine assemblies; keep SubD/crease/bevel intent live; and inspect form in solid/MatCap before moving on.

The inventory cannot judge visual quality or infer exactly how the meshes were created. It is evidence of the saved scene structure only.
