# Anglepoise Type 75 editable benchmark stage

This run models the Slate Grey standard desk-base Anglepoise Type 75 from the audited official reference package in `../2026-08-16_reference-gathering-anglepoise-type75/`. It is a typed-runtime, incrementally rendered benchmark stage—not a downloaded CAD reconstruction and not a final production approval.

## Construction

- The base, shank, shade, and shade cap are connected 16-segment revolved profile cages with quad flow. The base and shade are not stacks of cylinders or cones.
- Each paired arm is a box-derived connected cage. Live edge creases retain its manufactured rectangular section under live Subdivision Surface.
- Pins, washers, springs, diffuser, and switch are separate only where the physical articulated lamp is assembled from separate parts.
- The three lower springs and elbow tension loop were created as curves, evaluated into editable manifold meshes, and then retained as ordinary mesh components.
- Small Bevel modifiers are used only on machined circular parts that need a physical edge radius. Formed shells use profile topology and SubD; box-derived bars use creases.
- Smooth by Angle is applied after topology and edge-control decisions.

## Evidence and boundary

`anglepoise_type75_editable_candidate.blend` contains independent editable source cages in separate `HIGH_POLY` and `LOW_POLY` collections. Modifiers remain live and unapplied. Low objects use level-0 SubD where applicable; they are editable low-SubD variants, not purpose-authored production retopology.

The current evidence covers reference audit, primary envelope, linkage, secondary visible assemblies, solid/MatCap/wire renders, and fresh saved-file verification. It does not claim final human acceptance, production UVs/materials, exact hidden internals, underside detail, or final low-poly optimization.
