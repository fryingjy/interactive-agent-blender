# Operator card: Modifier stack order matters

**Status:** DOCS ~ (individual modifier pages studied; no universal order rule exists) | EXPERIMENT ✓ (all 4 planned pairs) | FAILURE_CASE ✓ | QUIZ ✓ | RUNTIME_USE ~ | SECOND_SHAPE pending

Operating rule: for important modifier pairs, test order rather than assuming the stack is
interchangeable. Confirmed with real, decisive, non-coincidental measurements (a first
naive test accidentally produced identical results for both orders because the test geometry
didn't actually make the modifiers interact -- caught and corrected before drawing any
conclusion, see below).

## Mirror + Bevel

**First attempt was a false negative, caught before being trusted**: cube geometry offset so it
didn't touch the mirror plane at all -- both orders produced identical results (112v/108f) simply
because Mirror and Bevel never actually interacted with the same geometry. Redid with the cube's
inner face sitting exactly ON the mirror plane (X=0), so a real seam exists.

| Order | Verts | Faces | Non-manifold |
|---|---|---|---|
| Mirror -> Bevel | 68 | 67 | 12 |
| Bevel -> Mirror | 108 | 107 | 4 |

Root cause, confirmed by inspecting vertex positions directly at X=0 (not just counts):
- **Bevel -> Mirror**: the inner (mirror-plane-touching) face survives as a plain flat shrunk
  square (e.g. verts at (0,+-0.7,+-0.7) -- shrunk from +-1 by the 0.3 bevel width, but NOT
  further chamfered at its own corners, matching completely ordinary single-object bevel
  behavior). The two mirrored halves meet at this flat face with a continuous, seamless
  transition -- reads as one smooth shape.
- **Mirror -> Bevel**: the same seam location instead shows 12 vertices with bevelled/rounded
  profile coordinates (e.g. (0,-1,-0.7), (0,-0.9121,-0.9121)) -- because Bevel now runs on the
  ALREADY-MERGED double-wide shape, and the former seam edges are just ordinary edges in that
  merged mesh, so Bevel's "affect all edges" default rounds them too. This carves a visible
  facet/crease right along what should have been an invisible, flat mirror seam.

**Conclusion, with real evidence behind it, not just repeated folk wisdom: put Bevel BEFORE
Mirror in the stack** for a clean, seamless result, unless the seam itself is deliberately meant
to be treated as a regular edge.

## Boolean + Bevel

| Order | Verts | Faces | Non-manifold | N-gons |
|---|---|---|---|---|
| Boolean -> Bevel | 248 | 216 | 0 | 4 |
| Bevel -> Boolean | 120 | 88 | 0 | 4 |

Both topologically clean (0 non-manifold either way -- this pair doesn't have a "broken" order,
unlike Mirror+Bevel's visible seam artifact). The real difference is what gets rounded:
- **Boolean -> Bevel**: Bevel runs on the post-cut result, so it rounds BOTH the cube's outer
  edges AND the freshly-cut hole's rim. Higher density (roughly 2x the geometry).
- **Bevel -> Boolean**: Bevel runs first on the plain cube (rounding only its 12 original edges),
  then Boolean cuts a hole through the already-rounded shape -- the hole's own rim stays sharp,
  since no bevel treatment is applied after the cut.

**Conclusion**: this is a genuine strategic choice, not a "correct vs wrong" order like
Mirror+Bevel. Boolean->Bevel for a countersunk/rounded-hole look; Bevel->Boolean for a rounded
outer silhouette with a crisp drilled/machined hole. Directly relevant to this project's own
SpeakerEnclosure driver cavity (built via inset+extrude instead, a different strategy entirely --
this is new, complementary knowledge about a boolean-based alternative, not a contradiction of
prior work).

## Mirror + Subdivision

| Order | Verts | Faces | Non-manifold |
|---|---|---|---|
| Mirror -> Subdivision | 171 | 176 | **16** |
| Subdivision -> Mirror | 196 | 192 | **0** |

The most consequential result of the four pairs tested: **Mirror before Subdivision genuinely
breaks the mesh** (16 non-manifold edges -- Subsurf's Catmull-Clark evaluation trips on the
merged seam even though Mirror's own weld/merge succeeded at the base-cage level). **Subdivision
before Mirror is clean** (0 non-manifold) -- Subsurf insets the evaluated surface slightly at an
open boundary (confirmed: no evaluated vertices remain exactly at X=0 in this order, unlike the
seam-sample in the broken order which still shows verts sitting at X=0), and Mirror then
duplicates that already-correct result without issue.

**Conclusion, directly load-bearing for any future prop combining Mirror with Subdivision
Surface: Subdivision must come BEFORE Mirror in the stack**, not after -- this is a correctness
requirement here, not just a stylistic preference like Boolean+Bevel above.

## Solidify + Bevel

| Order | Verts | Faces | Non-manifold |
|---|---|---|---|
| Solidify -> Bevel | 56 | 54 | 0 |
| Bevel -> Solidify | 8 | 6 | 0 |

Tested on a Plane (an open, single-face mesh -- Solidify's real use case is giving a flat/open
shell thickness, which a pre-closed cube barely exercises). **Bevel -> Solidify is effectively a
no-op for Bevel**: a flat single-face plane's boundary edges each have only one adjacent face, so
there is no real dihedral angle for Bevel to round -- the result (8v/6f) is indistinguishable from
a plain thin box with no bevel applied at all. **Solidify -> Bevel works as expected** (56v/54f):
Bevel runs on the now-3D solid shape and correctly rounds its edges.

**Conclusion**: for Solidify + Bevel, this isn't just a preference -- **Solidify must come first
or the Bevel step does essentially nothing.**

## Summary across all 4 listed pairs
Three different KINDS of stack-order consequence found, not the same lesson repeated four times:
1. **Mirror + Bevel**: both orders "work" (no invalid geometry), but only one is visually correct
   (Bevel first avoids carving the seam).
2. **Boolean + Bevel**: both orders are valid AND visually reasonable -- a genuine strategic
   choice (Boolean first if the cut's rim should also be rounded).
3. **Mirror + Subdivision**: only one order is even topologically valid (Subdivision first);
   **Solidify + Bevel**: only one order makes Bevel do anything at all (Solidify first).
Do not generalize "put X before Y" from one pair to another -- each pair was tested independently
because the underlying reason differs each time.
