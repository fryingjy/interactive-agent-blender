# Scotch C38 Classic Desktop Tape Dispenser — reference and construction plan

## Target boundary

Target: current black Scotch C38 Classic Desktop Tape Dispenser, product family 70005291441.
The exact official listing sets the 6.4 × 2.7 × 2.7 inch overall envelope, replaceable 1-inch hub,
3/4-inch maximum tape width, weighted non-skid base, and one-handed cutter function. The board is
machine ready only for a reversible primary blockout; it is not human-authorized for any Blender geometry.

## Local source board

The downloaded source media is ignored and retained for inspection only. Its URLs and hash inventory
are in `media_inventory.json`; its evidence roles and limits are in `reference_manifest.json`.

- `media/official/c38_product_primary.jpg` — authoritative loaded front-left product oblique.
- `media/retailer/texas_art_white_background.jpg` — unloaded top-right view; exposes cavity, hub,
  bridge, lower seam, and cutter assembly.
- `media/retailer/ofix_clean_profile.jpg` — second loaded oblique that corroborates the long wedge
  silhouette and raised front cutter face.
- `media/retailer/office_depot_replacement_hub.jpg` — compatible removable hub component; it proves
  separateness but not hidden body attachment details.

## Observable construction

- The lower plinth/base and the sloped upper shell are separate visible manufactured regions. The
  upper shell should begin as one box-derived connected cage, with loops/insets only at the cavity,
  shoulder, cutter-face, and side-profile transitions. It must not be assembled from stacked wedges,
  cylinders, or generic rounded primitives.
- The rectangular top cavity is primary negative space. It exposes the tape roll and removable hub and
  needs to remain open through every silhouette review.
- The cutter face, tape bridge, serrated metal blade, tape roll, and removable hub are separate only
  because the references show an assembly/material/function boundary. The front housing itself is part
  of the main outer shell until an exact seam says otherwise.
- Hidden underside feet, ballast fastening, and hub-retention details are unknown. Do not invent them.

## Planned reversible topology (only after human approval)

1. `UpperShell_HIGH`: one box-derived connected cage. Add sparse longitudinal and transverse loops for
   the rear shoulder, rectangular cavity, sloped cheek profiles, front bridge, and front cutter face.
2. `WeightedBase_HIGH`: one separate box-derived low plinth, because the visible perimeter seam and
   distinct weighted base establish an assembly boundary.
3. `Hub`, `TapeRoll`, `CutterBlade`: separate functional assemblies. Use 12–16 radial sides where
   cylindrical, not 32 by habit; keep modifiers unapplied.
4. Create `HIGH_POLY` and `LOW_POLY` collections only after the primary construction is approved.
   Each keeps editable cages and live modifier stacks.

## Surface policy

- Begin with literal box profiles. Do not round the four main body corners before the profile and cavity
  proportions match the board.
- Use Smooth by Angle after face/edge intent is set. Smooth shading alone does not create a controlled
  hard-surface form.
- Use a semantic bevel-weight pass on every edge intended to read as a hard manufactured transition:
  upper-shell perimeter, cavity rim, lower-base perimeter, front-cutter boundaries, and bridge edges.
  Bevel and SubD remain unapplied; their order must be checked in solid/workbench highlights.

## Blocking unknowns

The board deliberately does not establish exact underside feet, hidden ballast, fasteners, or the
hub-retention mechanism. Those are outside the authorized blockout scope and remain absent unless an
exact current-product reference is added.
