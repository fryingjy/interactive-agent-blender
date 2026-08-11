# Topology context and Subdivision Surface lab

**Status:** PASS (9/9 assertions, 13 specimens).

## Scope

The lab created valence-3/5/6 pole fans, flat/curved triangle cases, flat/nonplanar n-gons, uniform/uneven quad spacing, tight/wide support geometry, a matched cylindrical quad route, and a valence-5 loop termination. Every record separates editable base topology from Blender's evaluated Catmull-Clark result.

## Strongest findings

- Flat poles and triangles remained flat; topology category alone did not create a surface defect.
- Curvature exposed context: the curved triangle reached a 7.60° adjacent-face change and the nonplanar n-gon 11.88°.
- Uneven all-quad spacing produced nearly five times the evaluated area variation of the uniform control (0.599 versus 0.124).
- Tight support retained 0.9919 of cube span versus 0.9676 for wide support. Both were closed, all-quad, and independently verified clean.
- The open cylindrical side used 32 quads with matched circumferential resolution and evaluated with near-uniform face area.

## Limitations

These metrics characterize controlled geometry; they are not an automatic professional-quality classifier. Open patches legitimately report boundary edges. The current angle/area signals still require controlled visual reflection and silhouette evidence to judge pinching and highlight flow.

## Evidence

- `topology_subd_lab.blend`
- `topology_subd_report.json`
- `verification/Support_Tight_*.json`
- `verification/Support_Wide_*.json`
- `tools/run_topology_subd_lab.py`
