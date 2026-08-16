# Session report — seam-directed UV transfer

**Status:** PASS within the controlled scope.

The previously verified official lesson established the source observation: seams define intended
UV cut boundaries. The older project reproduction was no longer retained, while the current
production fixture used Smart Project. This run closes that reproducibility gap with an authored
seam graph and a different-shape transfer under Blender 5.2.

Both source families use one connected all-quad base cage rather than joined primitive shells.
Solidify and Bevel remain live on high and low objects. The low cages have 48 and 60 base faces
versus 192 and 224 on their high counterparts. Three-view silhouette minima are above the frozen
0.90 gate, evaluated shells are closed and nondegenerate, UVs are packed in the unit tile, tangent
bakes contain surface signal, and fresh GLB imports contain exactly one low mesh with UVs and its
material.

The decisive controls are the same low cages unwrapped without the longitudinal seam. Their mean
corner-angle error is `15.00°` and `14.82°`; the authored layouts reduce this to `1.87°` and
`0.66°`. A UV layer's existence therefore does not establish layout quality.

No modifiers were applied, no reference target was modeled, and no human visual approval is
claimed. The resulting skill is `TRANSFER_VALIDATED`, not runtime-validated on an unfamiliar prop.
