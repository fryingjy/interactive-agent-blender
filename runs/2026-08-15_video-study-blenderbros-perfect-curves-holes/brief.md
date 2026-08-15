# Josh - Blender Bros -- "PERFECT curves with holes in Blender"

Video `FjWrEccXREY`, 9:24, channel `@JoshGambrell` (now "Josh - Blender Bros"). Transcript-only
extraction (auto-generated captions, no frames reviewed). Second of three videos processed in this
project's first survey pass on curriculum item #14.

## Why this video

Two independent angles made it worth reading: it's a curve-based construction method for tubular
objects with holes -- a genuinely different technique from this project's repeated manual
extrude-and-rotate-chain approach that caused three separate bugs this session (teapot spout x3,
teapot handle bridge-twist, padlock shackle) -- and it uses Loop Tools' Circle operator, which was
also flagged today from an unrelated source (CG Boost 100+ Tips) as the standard way to get perfect
circular holes/bosses.

## Most important finding

The video's real technique is not really about curves -- it's a specific Data Transfer sequencing
recipe for preserving shading when cutting holes into a mesh: duplicate and hide the clean source
BEFORE cutting, transfer custom normals from the hidden duplicate afterward, and get the Solidify +
Auto Smooth steps done BEFORE the Data Transfer (not after, which destroys it). None of this is
about the curve tool specifically -- it would apply to holes cut into any shading-sensitive mesh,
curve-derived or not. This project doesn't have a Data Transfer modifier in its typed op surface
yet, so nothing here is immediately actionable, but it's a real, sourced recipe for the next time
holes need to be cut into an already-shaded curved surface without visible artifacts.

## Items captured (4)

1. PROCEDURE -- duplicate-and-hide-before-cutting, then Data Transfer custom normals from the clean
   copy.
2. DECISION -- scope Data Transfer to a matching-thickness Vertex Group when source/target shell
   thickness differs.
3. PROCEDURE -- Loop Tools Circle for perfect circular loops (independent confirmation of today's
   CG Boost finding).
4. DECISION -- Solidify + Auto Smooth must precede Data Transfer in the modifier stack, not follow
   it.

## Not captured as formal items

The alternative texture-based "hollow look" technique using the channel's own MaterialWorks addon
(alpha channel + seam-mode UV unwrap, ~7:01-8:44) achieves a similar visual result without any
geometry changes at all, but it's a paid-addon-specific workflow this project has no access to and
no plan to depend on -- noted for completeness, not captured as a reusable technique. The opening
curve-creation basics (0:00-1:04, adding a Path curve, Bevel Depth, resolution) are generic curve
setup already implicitly covered by this project's own curve-tool capability
(`create_curve`/`set_curve_bevel_depth`), not new information.
