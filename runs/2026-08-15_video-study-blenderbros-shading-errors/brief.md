# Josh - Blender Bros -- "How to fix SHADING ERRORS in Blender"

Video `EdEIUkWzYY0`, 13:07, channel `@JoshGambrell` (now rebranded "Josh - Blender Bros" -- the
channel curriculum item #14 names). Read via transcript only (auto-generated captions, no frames
reviewed) -- claims below are grounded in narration text, not anything "shown on screen." Part of
this project's first survey pass on curriculum item #14 ("identify the highest-value hard-surface
videos specifically... channel not yet surveyed"), alongside two sibling runs processed the same
session (`2026-08-15_video-study-blenderbros-perfect-curves-holes`,
`2026-08-15_video-study-blenderbros-blocky-to-bevels`).

## Why this video, specifically

Picked over the many Hard Ops/Boxcutter/Plasticity/business-content videos on this channel because
its stated subject -- shading errors from booleans and bevels -- lands directly on this project's
existing bevel-weight/Weighted-Normal/Smooth-by-Angle shading policy
([[blender-modeling-technique-corrections]]), which up to now has never had its actual FAILURE
MODES documented, only its intended usage.

## Most important finding: a real boundary condition on the Weighted Normal fix

The project's policy already uses Weighted Normal as part of its bevel-weight approach, but has
never stated where it stops working. This video draws that boundary explicitly and demonstrates it
directly: Weighted Normal fixes flat-surface bevel shading distortion (where a bevel's holding-edge
angles are slightly off the intended value) by forcing those angles to be treated as exact -- but
on a genuinely curved surface, the shading problem is a different thing entirely (an actually bent,
non-planar face), and Weighted Normal does nothing for it. This matters immediately: every
hard-surface asset this project has built so far (teapot body/spout, door handle, the abandoned
stapler) has curved surfaces, so this isn't a hypothetical edge case -- it's the common case. The
ranked fix order for curved-surface distortion (clean quad topology first, denser isolating geometry
second, Data Transfer modifier third as a last resort) is now on file as a real, sourced decision
tree rather than something to rediscover by trial and error next time it comes up.

A second, more mechanical finding: a Mark Sharp edge splits into TWO holding edges when later
beveled, both inheriting the sharp marking -- producing a visible unwanted seam along the bevel.
This is a concrete, previously-undocumented interaction between Mark Sharp and bevel operations.

## Items captured (4)

1. PRINCIPLE -- Weighted Normal fixes flat-surface bevel distortion, not curved-surface distortion
   (a different underlying problem: a bent, non-planar face).
2. PROCEDURE -- the ranked three-fix decision tree for curved-surface shading distortion.
3. PROCEDURE -- Mark Sharp + bevel interaction (splits into two holding edges) and its three fixes.
4. PRINCIPLE -- Mark Sharp's actual purpose: an escape hatch for angle-threshold conflicts Auto
   Smooth's single global angle can't resolve, not a general substitute for it.

## Not captured as formal items

The opening practical demo of the sharp-marking-on-a-bevel problem (0:00-0:24) is folded into item 3
rather than captured separately -- it's the same claim, just narrated before the mechanism was
explained. The closing sales pitch for the channel's paid course (11:20-13:07) is not modeling
content.
