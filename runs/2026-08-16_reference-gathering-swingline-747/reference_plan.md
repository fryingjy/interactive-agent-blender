# Swingline 747 Classic — reference and construction plan

## Target boundary

Target: current Swingline 747 Classic 74718 lipstick-red geometry family. The color is a surface
variant; the primary target is the current 747 Classic construction and envelope. This is a
reference-only phase. The manifest intentionally remains `TARGETED_RESEARCH`; no Blender blockout
is authorized yet.

## Local source board

Ignored third-party media is organized by use, with URLs and limitations preserved in
`reference_manifest.json`:

- `media/primary/74718_product_elevation.jpeg` — exact red product elevation; primary silhouette
  and visible nose/anvil relationship only.
- `media/construction/747_open_mechanism.jpg` — current red 747-family open mechanism; supports
  separate magazine, hinge, and spring reasoning, not closed-state dimensions.
- `media/uncertain/747_vintage_underside.jpg` — rejected vintage underside lead; never use it as
  current-product geometry until the revision is independently established.

## What is already observable

- The top lever is one continuous formed-metal cover: begin from one box-shaped cage, add loops
  where the silhouette changes, and extrude/shape the integrated rear transition. Do not assemble it
  from cylinders or unrelated bevelled blocks.
- The low base is a separate structural casting/shell, not a continuation of the top cover.
- The staple magazine/rail, anvil plate, hinge/latch, spring, and rubber feet are distinct physical
  assemblies. Keep them separate only because the reference shows a material, motion, or assembly
  boundary.
- The visible cover/base throat is a critical negative space. It must survive every blockout and
  SubD test.

## Planned editable topology

1. `TopLeverShell_HIGH`: one connected low-density quad cage from a box, with longitudinal loops at
   the front nose, visible crown break, rear hinge transition, and the cover/base gap. Add loops
   only where the actual profile changes.
2. `BaseShell_HIGH`: a separate connected box-derived cage for the cast base, its front anvil recess,
   and rear hinge housing. The anvil recess should be cut/recessed in edit mode, not simulated with
   a loose block.
3. `MagazineRail`, `AnvilPlate`, `HingePin`, `Latch`, `Spring`, and `Feet`: separate only where
   the real mechanism confirms a separate manufactured or moving piece.
4. Create `HIGH_POLY` and `LOW_POLY` collections only after the primary construction is approved.
   Both keep live, unapplied modifier stacks and independent editable cages.

## Shading and modifier policy

- Start from sharp box-derived cages; do not round every corner before the proportions are correct.
- Use `Shade Auto Smooth` after face/edge intent is established. Smooth shading alone is not a
  substitute for support geometry.
- Assign bevel weight to every deliberately sharp design edge, including the four longitudinal cover
  edges, base perimeter breaks, front nose boundary, and the anvil recess where the reference
  requires a hard highlight. Do not rely on a handful of selected edges.
- Choose the Bevel/SubD order only after a solid-mode highlight check on the closed cage. Preserve
  broad manufactured radii with loop placement; use weighted bevels for tight chamfers. Never apply
  modifiers in either high or low collection.

## Blocking unknowns

Top/right/rear and current underside evidence are still missing. Until those high-impact questions
are resolved, no dimensions beyond the provisional overall envelope, no exact rear curvature, and no
underside feature should be modeled as fact.
