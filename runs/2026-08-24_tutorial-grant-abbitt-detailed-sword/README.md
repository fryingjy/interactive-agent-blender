# Grant Abbitt detailed-sword tutorial reproduction

This bounded I0 lesson studies Grant Abbitt's 40:35 sword workflow. Gemini inspected the full
video/audio/captions and produced 18 timestamped candidate episodes; browser review independently
confirmed the exact source identity, duration, channel and creator-authored final/wireframe
thumbnail. Because ads blocked representative timestamp-frame checks and no independent transcript
was available, the Gemini episode details remain explicitly model-extracted and unverified.

## Result

The reproduction uses two functionally justified objects rather than primitive stacking. The blade
is one connected front/rear all-quad shell whose silhouette and center ridge are authored in the
cage. The hilt is one connected 12-sided revolved profile. A first solid render showed a blade that
was too broad and short, so the connected cage was lengthened and slimmed, its ridge and physical
outline received semantic creases, and one live Subdivision Surface modifier was added. The
modifier remains unapplied.

Fresh Blender 5.2 inspection reports 72 base vertices, 70 base quads, no non-manifold edges, no
n-gons and no degenerate faces. The evaluated blade has 280 quads and no diagnostic pinch
candidates. The result is recognizable and structurally sound, but the shoulder, long arc, upswept
tip and subtly curved hilt do not match the creator target closely enough. It is retained at
**7.2/10 — not an I0 pass**.

The different-geometry transfer builds a leaf spearhead with the same connected silhouette/ridge
principle. Its first tip collapsed three vertices into one location and created two degenerate
quads; that attempt was rejected and corrected to a small three-vertex termination. The accepted
transfer is manifold and all-quad with zero degenerates. This promotes one bounded topology rule,
not general weapon-modeling mastery.
