# Blender Bros beginner hard-surface tutorial reproduction

Stage 3 follows the complete 39:53 mechanical-enclosure tutorial rather than extracting isolated
tool slogans. The study must identify the asset's component hierarchy, symmetry, Boolean and bevel
stack decisions, shading policy, and visible correction points; reproduce a cohesive layered asset;
retain at least one failed visual/technical branch; and transfer the surviving construction rule to
different geometry. Source video is inspected in place and is not downloaded or archived.

## Result

The bounded Stage 3 lesson is complete. Gemini inspected the actual audiovisual source in two
source-bound ranges; YouTube identity, duration, captions, and the apply-scale correction were
independently checked in the browser. The Blender reproduction uses one connected all-quad primary
cage, one legitimate separate lower service panel, live mirrored construction cutters, live
Boolean-before-Bevel modifiers, and Smooth by Angle. Construction cutters remain recoverable in a
hidden collection and no modifier is applied.

The rejected branch places Bevel before Boolean and leaves the generated aperture as a visibly
polygonal, unchamfered cut. The retained branch places two Booleans before Bevel and renders rounded
aperture edges in MatCap. A wide horizontal control module transfers the same ordering and
symmetry-plane rule to different geometry. This run also exposed and fixed a generic system defect:
counter-clockwise `create_profile_extrusion` outlines previously produced inward normals and could
silently break Boolean cutters. The operation now normalizes winding and its Blender lab verifies
outward cap and side normals.

This is training evidence, not a production-topology claim. The base cages are connected,
all-quad, manifold, and deliberately sparse; the live Boolean/Bevel evaluated meshes still report
boundary/non-manifold and n-gon diagnostics around cuts. Visual results are retained, but those
evaluated diagnostics must be resolved in later topology-cleanup lessons before using the method as
a production delivery recipe.
