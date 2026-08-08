# Operator card: Modifier stack order matters (directive explicitly flagged this as untested)

**Status:** DOCS pending (Manual modifier-stack pages not yet fetched) | EXPERIMENT ✓ 2 of 4 listed pairs | FAILURE_CASE n/a (both orders are "valid," they just produce different, real results -- the finding is that they're NOT interchangeable, not that one errors) | QUIZ pending

Directive: "For important modifier pairs, explicitly test order... Never assume stack order is
interchangeable." Confirmed correct with real, decisive, non-coincidental measurements (a first
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

## Not yet tested
Mirror + Subdivision, Solidify + Bevel -- deferred, real gap, listed explicitly in the directive.
