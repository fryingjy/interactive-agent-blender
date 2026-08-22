# Blender Bros tricky SubD detail tutorial reproduction

This is the complete-asset half of Stage 4. The source is Josh - Blender Bros' 18:53 tutorial on
dealing with a detail that fades into a curved SubD host. Gemini inspected the complete audiovisual
range in two bounded calls; YouTube oEmbed and the retained source thumbnail independently verify
the title, creator, duration family, and target form. The video itself is not archived.

## What was modeled

- `failure.blend`: a 16-segment, one-object all-quad shell whose relief starts at full depth on one
  ring. The fixed MatCap view exposes the resulting horizontal pinch.
- `corrected.blend`: the same 224-vertex/208-quad cage, but the relief is eased through three rings
  before reaching full depth. The shell remains connected and uses live Solidify then Subdivision;
  Smooth by Angle is used instead of blanket smooth shading.
- `transfer.blend`: a different 14-segment, squat oval cuff with a diagonal relief. An initial
  column-jumping transfer was rejected for visible waviness; the retained transfer blends the
  influence across neighboring radial columns and evaluates to 4,928 quads with no non-manifold
  edges or automated pinch candidates.

All `.blend` files retain unapplied modifiers. The host and relief are not separate visible
primitives. The 32 base non-manifold edges in the source-like pair and 28 in the transfer are the
two intentional open rims before live Solidify; evaluated geometry is manifold.

## Result and boundary

The promoted result is narrow: detail depth and lateral routing must fade continuously into a
curved host. The abrupt branch has a worse maximum robust curvature outlier (`8.5756`) than the
gradual branch (`7.2550`), while raw pinch-candidate count moves in the opposite direction
(`26` to `32`); this is retained as proof that the candidate count alone cannot decide visual
quality. Fixed MatCap review is decisive here.

This is a bounded reproduction of the tutorial's outer shell and integrated fading detail, not an
exact recreation of its HardOps/BoxCutter/Mesh Machine command history. The companion Stage-4
topology sheet separately reproduces perimeter rerouting and convex loop termination. Exact local
triangle termination inside this asset remains a limitation and is not claimed.
