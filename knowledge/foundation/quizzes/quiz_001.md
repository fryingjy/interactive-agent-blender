# Knowledge retrieval quiz 1

Answered from understanding, without re-reading the operator cards while composing -- this is the
actual retrieval test the directive asks for ("query the knowledge engine without pasting the
notes directly... the goal is retrievable modeling judgment, not memorization"). Confidence noted
per answer; low-confidence answers are stated as such, not smoothed over.

## Directive's example questions

**1. Why can technically valid topology still be poor?**
Because "valid" checks (manifold, 0 n-gons, 0 non-manifold edges, 0 degenerate faces) only verify
the mesh has no *structural* errors -- they say nothing about whether edge flow, pole placement,
and density actually serve the mesh's purpose (clean deformation, predictable subdivision,
editability, good shading). This project's own Mug session is the direct evidence: a mesh that
passed every validity check was still real, correctly-judged bad topology because its poles were
scattered irregularly rather than concentrated only where geometrically necessary.
*Confidence: high -- this is core to the project's whole premise, not a fresh guess.*

**2. When should dissolve be preferred to delete?**
When the goal is removing an element while keeping the mesh closed/watertight -- dissolve merges
the surrounding faces into an n-gon rather than opening a hole. Delete (with a hole-creating
context) is for when an actual opening is wanted, e.g. before extruding a cavity or before
bridge/fill needs a boundary to attach to. Directly measured this session: dissolving 1 vertex of
a cube gave 7v/9e/4f (merged, closed); deleting that same vertex with VERTS context gave 7v/9e/3f
(a genuine hole, 3 faces gone entirely, not merged).
*Confidence: high -- fresh, direct, numeric evidence from this session.*

**3. How does support-loop spacing alter a SubD surface?**
A support loop placed close to a sharp feature pins the Catmull-Clark surface tighter there
(sharper, less rounded); moving it away lets the surface curve more broadly. Too-close spacing is
the classic cause of pinching. *Lower confidence on the detection side*: this session's own
attempt to build a numeric pinch-vs-healthy-curvature classifier (`evaluated_defect_regions`)
found this genuinely hard -- SoapDish's healthy rounded corners showed a smooth, continuous angle
gradient (median 3.7deg up to ~46deg with no discontinuity), and a local-neighbor-ratio heuristic
produced false positives on that healthy geometry while NOT clearly discriminating a deliberately
built bad case either (similar severity scores for both). I understand the *concept* correctly;
I do not yet have a reliable automated way to detect it, and said so honestly in the code.
*Confidence: high on the concept, explicitly low/unsolved on automated detection.*

**4. Why does modifier order matter?**
Each modifier operates on the output of whatever ran above it, not the original base mesh
independently. This session measured three distinct consequences directly, not the same lesson
repeated: Mirror-before-Subdivision breaks the mesh (16 non-manifold edges, Subsurf trips on the
merged seam); Mirror-before-Bevel carves the seam (Bevel treats former seam edges as ordinary);
Bevel-before-Solidify is a near-total no-op (a flat single-face plane has no dihedral angle to
bevel).
*Confidence: high -- three separate controlled experiments this session, matched-pair geometry.*

**5. When may a triangle be harmless?**
On a flat, unsubdivided surface with no deformation requirement -- flat is flat regardless of
triangulation, so no shading or curvature artifact results. This project has used
`triangulate_ngons` on flat regions specifically for this reason (SpeakerEnclosure, and the first
SoapDish rim fix before the user's superior all-quad correction).
*Confidence: high -- established, repeated project practice.*

**6. When is an n-gon especially risky?**
On or near a surface that will be subdivided or deformed -- Catmull-Clark's handling of an n-gon
is less predictable and can pinch or read non-planar. The SoapDish rim n-gons (from a mismatched
subdivision resolution at a basin/rim transition) are the project's own direct example.
*Confidence: high.*

**7. How should Mirror influence topology planning?**
Model only half the form with the cut edge exactly on the mirror plane so the halves weld
seamlessly, and -- per this session's fresh finding -- place Mirror deliberately relative to
Bevel/Subdivision in the stack, since the wrong order either breaks the mesh outright or visibly
carves the seam.
*Confidence: high, and specifically improved this session (the stack-order part was not known
before today).*

**8. What makes Boolean a useful intermediate workflow but not necessarily good final topology?**
Boolean reliably produces the geometrically correct shape/volume quickly, but the seam's actual
edge flow is whatever the solver's algorithm produces, not deliberate artistic design -- it
routinely leaves slivers, near-coincident verts, and irregular n-gon/triangle patterns needing
cleanup. This project's own `boolean-groove-cut-topology-cleanup` skill exists specifically
because merge_by_distance + recalc_normals + triangulate_ngons was needed after every tested
boolean cut, and even after cleanup the seam's edge flow isn't deliberately designed the way a
hand-built support loop would be.
*Confidence: high -- an actual promoted skill in this project, generalized across DIFFERENCE and
UNION operations already.*

**9. When should separate geometry be preferred?**
When a component is conceptually and physically distinct enough to benefit from its own
transforms/materials/modifiers, or will eventually be independently adjustable/replaceable. Fresh
finding this session: `bpy.ops.mesh.separate` creates a genuinely new Blender object, while
`bmesh.ops.split` (similar name, easy to conflate) only creates a disconnected island within the
SAME object. This project's own gadget blockout used separate objects for the dome/band/buttons
correctly, for exactly this reason.
*Confidence: high, and the split-vs-separate distinction specifically is new this session.*

**10. What evidence suggests a region should be rebuilt rather than patched?**
When the problem is structural -- the wrong strategy or primitive entirely, not a local, isolated
defect. The gadget blockout v1-to-v2 rebuild is the project's own direct example: the wristband
wasn't just proportioned wrong, it was built on the wrong PRIMITIVE (a symmetric torus for an
asymmetric, overlapping, tapering wrapped strap that a torus cannot represent at all) -- no amount
of proportion-patching would have fixed that; the fix required a genuine strategy change
(curve_ops, built specifically because the existing primitive vocabulary couldn't do it).
*Confidence: high -- this is the most recent, most vivid example in the whole project's history.*

## Session-specific questions (testing retrieval of this session's less "obvious" findings, not just the directive's given questions)

**11. Why did `bridge_edge_loops` silently produce 0 new faces on a pair of bare wire-edge rings?**
`BMEdge.is_boundary` means "exactly one linked face." A wire edge (created via
`fill_type='NOTHING'`, zero linked faces) never satisfies that, so filtering `bm.edges` by
`is_boundary` silently excludes every edge, leaving `bridge_loops` nothing to act on. Fix: pass
the raw edge list, or filter by `is_wire`, when the source loops have no faces at all.
*Confidence: high -- root-caused via direct return-value inspection this session, not guessed.*

**12. Why does `grid_fill` fail on a multi-segment grid hole even with the correct boundary edge count selected?**
Its automatic corner/pairing detection can't unambiguously resolve which edges are the "corners"
when every boundary segment is equal length, with no additional disambiguation available (the
low-level `bmesh.ops.grid_fill` has no `span`/`offset` parameters at all -- those exist only on
the higher-level `bpy.ops.mesh.fill_grid`). Confirmed directly via Blender's own reported error,
"Connecting edge loops overlap" -- an explained failure, not a silent one.
*Confidence: high -- reproduced cleanly with step-by-step verification, and cross-referenced
against the real API signature via WebSearch.*

**13. Why can't `bpy.ops.mesh.rip` be used reliably from this project's scripted typed-operation approach?**
Its `poll()` requires real mouse/viewport context (rip direction is normally inferred from mouse
position at call time) that a headless `execute_blender_code` call cannot supply -- confirmed
directly: `Operator bpy.ops.mesh.rip.poll() failed, context is incorrect`, even with a vertex
correctly selected in Edit Mode.
*Confidence: high -- a real, reproduced, explained failure, not assumed.*

## Honest self-assessment

Strong, evidence-backed retrieval on: dissolve/delete distinction, modifier stack-order rules (now
the strongest-evidenced topic in this whole foundation phase), n-gon/triangle risk context,
boolean's real limitation, separate-vs-split. Genuinely weak, and said so above rather than
hidden: automated pinch/curvature-defect detection (question 3) -- correct conceptual
understanding, no reliable detector. This is consistent with `evaluated_defect_regions`'s own
docstring, which already states this limitation in the code, not just here.
