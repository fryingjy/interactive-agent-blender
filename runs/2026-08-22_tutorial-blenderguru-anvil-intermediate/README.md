# I0: Blender Guru anvil (4-part intermediate modelling tutorial)

First intermediate-tier (I0) tutorial attempted after B1/B4 unblocked it (see
`docs/TUTORIAL_REPRODUCTION_TRACK.md`). I0 asks for a complete reference-driven
hard-surface tutorial: full object, proportion correction, booleans/continuous
topology chosen by context. Source: Blender Guru / Andrew Price's 4-part
"Blender Intermediate Modelling Tutorial" (anvil), `source_metadata.json`.

Construction reused this project's own prior transcript research from
2026-08-14/15 (`runs/2026-08-14_video-study-blenderguru-anvil/`,
`runs/2026-08-15_video-study-blenderguru-anvil-part{2,3,4}/`) rather than
re-fetching video access -- TubeAlfred credits are very low (12 remaining
after one `video_get` call this run) and were spent only on confirming
identity/duration and fetching Part 1's own thumbnail, which turned out to be
a wireframe render of the tutorial's actual finished anvil
(`media/part1_thumbnail.jpg`) -- real creator-authored visual evidence of the
target result, used as the shape reference throughout this run.

## What was built

`anvil_tutorial_v4.blend`, one connected mesh (`Anvil`):

- **Table**: the tutorial's own starting point -- the simplest unambiguous
  primitive (Part 1), a flat rectangular block.
- **Body (waist/base)**: extruded from the table's bottom face through six
  rings, each independently tapered on the locked XY plane -- approximating
  the video's Shift+Z proportional-edit taper (bmesh doesn't expose
  proportional-editing falloff curves directly, so this is a per-ring scale
  approximation, not a literal reproduction of the tool). Proportions were
  tuned against the Part 1 thumbnail wireframe: a pinched waist narrowing to
  ~40% of the table width, then flaring back out to a foot wider than the
  table itself, matching the reference's stable-looking base.
- **Horn**: extruded from the table's own flat -X wall through four
  progressively narrowing segments, merged to a point at the tip
  (`bmesh.ops.pointmerge`, not an oversized-tolerance `remove_doubles` --
  that was tried first and left broken face references).
- **Boolean cut** (Part 2): the concave curve under the horn/table junction
  is cut with a Boolean Difference against a cylinder operand, followed by
  Remove Doubles at the seam (Part 2's own stated cleanup method -- no Weld
  modifier, matching the source's technique exactly) and an attempted
  tris-to-quads requad, since a live Subdivision Surface follows.
- **Support loop** (Part 3): one loop cut added near the table's top
  perimeter, slid close to the edge, to keep that edge reading sharper under
  SubD -- Part 3's own technique (not a Bevel modifier, not edge crease).
- **Live Subdivision Surface modifier** (Part 4's principle: keep the base
  mesh lean, use SubD for roundness rather than hand-modeling curvature),
  left unapplied so the base cage stays editable.

## Real bugs found and fixed during construction

- An initial attempt used manual `bmesh.ops.extrude_face_region` chaining
  and repeatedly produced non-manifold geometry: cap-face identification by
  Z-coordinate matching broke because the waist's ring sequence revisits the
  same Z twice (narrows then widens back through it), and extruding a face
  that was already an *exterior* wall of a closed solid (the horn's
  attachment point) left the original face behind as a redundant internal
  partition, which is correct behavior for extruding a *fresh* face but
  wrong for extruding an *existing* solid's wall. Both are documented as
  `v1` was abandoned in favor of `v2`'s `bpy.ops` Edit Mode approach, which
  lets Blender resolve topology bookkeeping instead of manual face-tracking.
- `bpy.ops.object.transform_apply(location=False, ...)` on the initial table
  cube left the object's position as a separate transform instead of baking
  it into the mesh data, so every subsequent Z-target in Edit Mode was
  computed in the wrong coordinate space -- the body extruded *into* the
  table's own volume instead of below it. Fixed by using `location=True`.
- The first lit render showed what looked like a disconnected floating
  base -- checked directly with a flood-fill connectivity walk over the
  bmesh graph (not assumed): the mesh is one single 41-vertex island, fully
  connected. The apparent gap was the waist section rendering as pure black
  against a pure-black world background with no fill light -- a lighting
  problem, not a topology one. Confirmed by adding world/fill lighting,
  which made the connection immediately visible.

## Honest status: base cage clean, SubD result not yet crisp -- not scored

Fresh-process structural verification of the base cage: 101 vertices, 73
faces, 0 loose vertices, 0 non-manifold edges, 0 degenerate faces. The
boolean cleanup left 14 non-quad faces at the seam despite the requad
attempt -- a disclosed limitation, not hidden.

The rendered SubD result (`anvil_v4_solid.png`) does not yet read as a crisp
hard-surface anvil -- it looks over-smoothed, almost blob-like, with the
table edge, waist facets, and base foot all rounding into each other rather
than staying visually distinct. This is a real, specific, correctly
diagnosed problem, not a mystery: only one support loop was added (near the
table top), while Part 3's own transcript notes state the exact symptom this
produces -- "a mesh region that looks noticeably more rounded/blobby than
its neighbors is the signal that a support loop is missing there." One loop
is not nearly enough density for a shape with this many independent
transitions (waist pinch, base shoulder, horn/table junction, boolean seam).

**This run is not scored against any fidelity gate.** It is retained as a
real first I0 attempt: the base proportions were tuned against genuine
creator-authored reference evidence (the Part 1 wireframe) and hold up
reasonably well in the flat-shaded, pre-SubD view (`anvil_v2_iso.png`); the
boolean and support-loop *techniques* were both genuinely applied, not
skipped; but the finished SubD result needs substantially more support-loop
coverage before it is presentable, let alone comparable to the reference.

## v5: systematic support loops added -- real improvement, real limitation found

Added support loops at every horizontal ring-boundary edge (66 candidate
edges) via `bmesh.ops.bevel` at small offset/2 segments -- a robust way to
place two closely-spaced parallel loops flanking each transition, the same
topological outcome as manually sliding loops close to an edge, without the
error-prone per-edge index tracking that broke once in v4. This is not the
Bevel modifier and not bevel weight (both explicitly avoided by the source
tutorial); it's the edit-mode bevel operator used purely to place support
loops accurately. Base cage grew from 101 to 313 vertices, structurally
clean throughout (0 loose/non-manifold/degenerate).

The SubD-evaluated render (`anvil_v5_solid.png`) is a real, visible
improvement over v4 -- distinct segment bands are now visible at the waist
and horn instead of one melted blob -- but doubling the bevel offset
(0.012 to 0.025) produced no visible change at all, which is the signal
that support-loop density was never the limiting factor here. **The real
limitation, found by checking rather than guessing further: every
cross-section in this build (table, waist, base, horn) is 4-sided.** A
4-vertex cage under Subdivision Surface smooths into a rounded *square*,
not a circle, no matter how many support loops flank it -- an anvil's waist
and horn are much closer to round/oval in cross-section. This is an
architectural limitation of the construction, not a parameter to keep
tuning.

**Still not scored.** v5 is retained as correctly-diagnosed evidence of what
would actually need to change: a higher-sided cross-section for the
waist/horn, not more support-loop iteration on the current 4-sided cage.

## v6-v7: fixed the diagnosed cross-section limitation

First attempt fixed it the hard way and broke: tried rounding the existing
4-sided table's boundary in place (subdivide the bottom face into a grid,
round just the outer loop with To Sphere, extrude from there). This cascaded
real problems -- rounding the bottom boundary forces the four adjacent side
walls to re-triangulate to match the new vertex count, so "the one flat -X
wall face" the horn was supposed to extrude from no longer existed as a
single face at all, and repeated attempts to re-locate it by position broke
the same way v1's Z-collision bug did (a rounding transform moves vertices
off the exact plane being searched for). Abandoned this approach rather than
keep patching it.

**v6** rebuilt from scratch using a 12-sided cylinder as the starting
primitive instead of a cube -- every ring (table, waist, base, horn) is
consistently round from the first vertex, with no square-to-round
transition topology needed anywhere. The table's edge is now slightly
faceted/rounded rather than sharp-cornered-rectangular versus the
reference -- a real, disclosed simplification, traded because the
diagnosis found the horn/waist reading as round matters more for
silhouette recognizability than the table's exact corner sharpness. This
also fixed an unexplained side effect from v4/v5: the material had rendered
washed-out white despite a near-black base color, which turned out to be
the blocky 4-sided geometry catching specular highlights across its whole
faceted silhouette; the properly round v6 geometry renders as correct dark
steel with a normal, localized specular highlight.

**v7** reapplied v5's validated support-loop technique (`bmesh.ops.bevel`
on all 108 horizontal ring-boundary edges) to v6's round cage. Structurally
clean throughout (0 loose/non-manifold/degenerate). The result
(`anvil_v7_solid.png`) is real, visible progress on both fronts at once:
the table now reads as a distinct flat disc with a real edge instead of
melting into the waist, and the waist/horn genuinely read as round/oval
rather than a smoothed square.

**Remaining rough spots, disclosed rather than hidden:** the horn's
attachment to the table shows some jagged/uneven geometry where the two
meet (visible as a rough notch in the render) -- likely the support-loop
bevel interacting awkwardly with the horn's own tapering segments right at
the junction. The base foot is still underdeveloped, reading as a short
thin stem rather than the reference's visibly wide, stable-looking flare.

**Still not scored against the reference.** This is the current best state
of the run: the specific limitation identified last session (4-sided
cross-section) is fixed and confirmed working, table definition is real
progress, and two remaining specific problems (horn-junction roughness,
underweighted base foot) are named precisely rather than left as a vague
"needs polish."
