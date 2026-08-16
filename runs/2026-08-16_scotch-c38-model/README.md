# Scotch C38 editable modeling run

This run contains the directly authorized benchmark-prop-2 attempt. Modeling proceeded without a
pre-model approval page. The source package is retained in
`../2026-08-16_reference-gathering-scotch-c38/`; visual judgment applies to the produced views.

## Result

- `scotch_c38_editable_candidate.blend` is the current editable candidate.
- `final_*_matcap.png` and `final_front_wire.png` are controlled Workbench review views.
- `independent_verification.json` is a fresh Blender 5.2 saved-file inspection driven by
  `verification_contract.json`.
- `stage_*_sequence.json` and `stage_*_report.json` retain the typed ModelerServer decisions and
  intermediate evidence.

The upper shell begins as one box-derived cage. Seven longitudinal cuts establish sparse profile
stations; moving those loops creates the side silhouette. Inset and inward extrusion create the
top cavity within the same connected mesh. The saved upper source has 60 vertices, 116 edges, and
58 quad faces, with one connected component and no loose or non-manifold edges. Separate objects
are reserved for real assemblies: weighted base, tape roll, removable hub, and cutter blade.

## Crease correction

The first shading pass used weighted Bevel before Subdivision. Direct feedback preferred creases
for the shell and base. Stage `06b` assigns crease 0.82 to 71 semantic upper-shell edges and all 12
base edges, then disables the broad Bevel modifiers in viewport and render. Subdivision remains
live and unapplied. The cutter retains a small live Bevel because a narrow manufactured blade edge
benefits from an actual radius.

A read-only comparison with the user's saved `C:/Users/odane/Downloads/feed.blend` is retained as
`user_scene_crease_inspection.json`. That saved example contains no crease layer: it uses a very
narrow weighted Bevel on comprehensively selected edges before level-2 Subdivision and Smooth by
Angle. This is recorded as a distinct valid strategy, not mislabeled as crease control. The user's
visible open scene had unsaved changes, so it was not saved or altered by this run.

## Editable variants and boundary

All five components have independent source cages in separate `HIGH_POLY` and `LOW_POLY`
collections. Modifier stacks are live; no modifier was applied. Low variants use level-0
Subdivision. These lows are editable internal variants, not production retopology. The artifact
does not yet include final UVs, materials, underside detail, or an accepted final likeness. The
current form is a technically verified proportion/silhouette candidate whose remaining quality is
judged from the rendered views.

One stage-6 Blender process saved successfully and produced its reports/renders before an Intel
graphics-driver teardown fault (`igxelpicd64.dll`). The later crease and final-package processes
completed cleanly; the crash is retained as a runtime limitation rather than counted as proof.
