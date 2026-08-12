# Held-out articulated desk-lamp benchmark — rejected

## Source boundary and contract

The CC0 Poly Haven `desk_lamp_arm_01` GLTF was selected before download and was used only to render
neutral reference pixels. Source geometry was not inspected or copied. The contract predeclared a
multi-component mechanical assembly: arms, hubs, clamp, and shade may be separate because they
articulate or are serviceable; rails and tension paths must still be continuous members.

## Technical result

The generated candidates use closed all-quad path lofts for arm rails, tension paths, hubs, clamp,
shade, and bulb. Their technical assertions pass: source absent, continuous primary members,
UV/material presence, articulated assemblies, sparse radial shade control, and clean evaluated
meshes. Planner checkpoints were recorded at reference analysis and primary blockout, but this
procedural fallback does **not** count as proof of typed runtime execution.

## Rejected visual result

The predeclared IoU gates were front 0.68, side 0.70, top 0.58, mean 0.66. Candidate v1 scored
0.423875 / 0.004494 / 0.298890 (mean 0.242420). It placed paired arm rails across depth, which
collapsed them in the side view. Candidate v2 corrected the Z-shaped pose but scored mean 0.372787.
Candidate v3 made the rails visible in the articulation plane but scored mean 0.358021. Candidate
v5 used normalized mask row landmarks to compress the clamp/shade span around the elbow and improved
to 0.446008 front, 0.222600 side, 0.548928 top, mean 0.405845. It still fails every frozen gate.

Two bootstrap failures are also retained: missing repository-root import for the planner, and an
output path initialized inside the invalid-argument branch. Neither produced an accepted candidate.

## Conclusion

**REJECTED.** This is useful failure evidence about articulated multi-component proportion and
projected-frame reasoning. It cannot support a held-out capability claim, production handoff, or
professional quality claim. The next attempt must begin with explicit side-view rail/frame
landmarks and component proportions rather than broad manual span adjustments.
