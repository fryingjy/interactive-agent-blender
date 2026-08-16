# Double-curvature semantic Bevel/SubD transfer

This run separates an edge-selection decision from the weight assignment that implements it.
Four live Blender 5.2 variants use one connected, closed, 98-vertex/96-quad cage each:

- `CROWN_COMPLETE` and `SADDLE_COMPLETE` declare and weight all 48 top/bottom rim segments;
- `CROWN_INCOMPLETE` and `SADDLE_INCOMPLETE` retain the same declaration but deliberately omit
  eight distributed segments from the weight map.

Every variant remains closed, nondegenerate, and all-quad after live Bevel → Subdivision evaluation.
That technical success does not hide the negative controls: the explicit semantic audit reports the
exact eight missing persistent IDs, and fixed-frame MatCap comparisons change 7,012 crown pixels
and 8,339 saddle pixels. The visible failures are local bumps, pinches, and broken rim highlights.

`double_curvature_base_cage_wire.png` shows the modifier-disabled connected quad cages.
`double_curvature_bevel_subd_matcap.png` shows both passing complete forms and both retained failure
controls. The isolated complete/incomplete images hold camera and material constant.

The first passing rerun experienced an Intel graphics-driver crash during Blender shutdown after
saving. It is not counted as clean evidence. A subsequent builder run exited 0, and a separate
fresh Blender process passed all 11 saved-state checks in `fresh_verification.json`.

This proves auditable selection completeness on two controlled double-curvature families. It does
not infer reference-defined sharp intent or establish professional quality on an unfamiliar prop.
