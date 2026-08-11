# Problem-driven research episode: false GLB failure

## 1. Original task and observed problem

The active task was a production export round trip. OBJ passed exact topology counts; GLB returned
the same bounds, UV/material presence, and visible surface, but raw counts changed from 56 vertices
and 54 polygons to 216 vertices and 108 polygons. The initial verifier marked the task failed.

## 2. Insufficient local knowledge

The raw-count assertion assumed interchange formats preserve Blender's editable mesh indexing and
polygon boundaries. The observed exact doubling to 108 faces suggested triangulation, but that
inference alone was not enough to rewrite the verifier.

## 3. Source selection and weak-source rejection

Search-result snippets and unsourced forum-style explanations were not used as authority. The
research went to Blender Foundation's official glTF and OBJ documentation. The glTF page explicitly
describes automatic triangle conversion and vertex separation at discontinuous UVs/flat-shaded
edges. The OBJ page documents its geometry, UV, material, triangulation, modifier, and axis options.
Both sources are registered as trust tier A with their visible documentation versions kept distinct
from the installed 5.2 runtime.

## 4. Hypothesis and controlled retest

Hypothesis: triangle surface count, world bounds, UV presence, and material presence should survive
the round trip even when raw vertices/polygons do not. The failed JSON was preserved, the verifier
was changed to those invariants, and the complete export/import operation was rerun from scratch.

## 5. Skill and return to the task

The resulting `export_roundtrip.md` skill says to verify format invariants and target-specific data,
not operator completion or editable topology identity. Returning to the original task produced a
passing GLB round trip: 108 source loop triangles and 108 imported triangles, identical world
bounds, one UV layer, and one material. The same policy also passed a second format, OBJ, without
special-casing its preserved polygon structure.

## 6. Scope

This is a complete problem -> research -> experiment -> skill -> original-task improvement loop.
Transfer is narrow (two formats on one source asset); target-engine rendering and a second asset are
still required before broad promotion.
