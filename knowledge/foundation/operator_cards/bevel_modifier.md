# Operator card: Bevel modifier

**Status:** DOCS ✓ (Blender Manual 4.5 LTS) | EXPERIMENT ✓ (Blender 5.2.0 LTS) | FAILURE_CASE ✓ | QUIZ pending | RUNTIME_USE ~ | SECOND_SHAPE ✓

## Purpose

Use the Bevel modifier as a non-destructive alternative to the Edit Mode bevel operation. It changes evaluated geometry while preserving the base cage until applied.

## Official behavior studied

Source: <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html>

- `Affect` selects edge or vertex beveling.
- Width methods (`OFFSET`, `WIDTH`, `DEPTH`, `PERCENT`, `ABSOLUTE`) interpret the same numeric width differently.
- `Segments` controls loops added across the bevel profile.
- Limit methods can target all edges, an angle threshold, bevel-weight attributes, or a vertex group.
- `Clamp Overlap` restricts width when neighboring bevels would overlap.
- Miter and intersection modes change corner topology; shading options can harden normals and propagate seam/sharp attributes.

The accessible Manual page is labeled Blender 4.5 LTS. Runtime findings below were reproduced independently in installed Blender 5.2.0 LTS; do not silently treat the version gap as proof that every option is unchanged.

## Controlled Blender 5.2 findings

Evidence: `runs/2026-08-10_modifier-foundation/`

| Variant | Evaluated verts | Faces | Non-manifold |
| --- | ---: | ---: | ---: |
| Triangulated cube, limit `NONE`, width 0.2, segments 2 | 80 | 84 | 0 |
| Same cube, limit `ANGLE` at 30°, width 0.2, segments 2 | 56 | 60 | 0 |
| Cube, segments 1 | 24 | 26 | 0 |
| Cube, segments 3 | 96 | 98 | 0 |

Angle limiting excluded coplanar triangulation edges in this test. Unrestricted beveling processed those internal diagonals and created substantially more geometry.

Increasing segments from 1 to 3 quadrupled evaluated vertex count on the test cube (24 to 96). Choose segment count from silhouette/highlight requirements rather than treating more segments as automatically better.

## Failure case: excessive width

On a 2×2×2 cube with width 2.0 and three segments:

- Clamp enabled: minimum evaluated edge length was approximately `2.38e-7`.
- Clamp disabled: minimum evaluated edge length was approximately `0.731`.

Both results remained manifold, but Clamp produced nearly collapsed edges. Therefore:

> Clamp Overlap prevents a class of overlap; it does not guarantee healthy topology or a visually useful bevel at excessive width.

Inspect evaluated edge lengths, corner topology, and highlights after large bevels. Manifoldness alone is insufficient.

## Cylindrical second-shape transfer

Evidence: `runs/2026-08-10_bevel-mirror-transfer/`

A closed cylinder stretched to world height 4 was beveled at width 0.1 with one segment. Applying the Z scale before Bevel produced a measured world-space top band of 0.1. Leaving object Z scale at 2.0 produced a 0.2 band. Both evaluated meshes were closed and independently verified clean (allowing their two intentional cap n-gons).

The scale warning therefore transferred beyond the original box-like cases: a manifold result can still have inconsistent world-space bevel width.

## Normal-policy comparison

Evidence: `runs/2026-08-16_bevel-normal-policy/`

The Manual documents two distinct ways to keep surrounding flat faces visually flat after Bevel:
enable Harden Normals directly, or set Bevel Face Strength and place a Weighted Normal modifier
after Bevel with Face Influence enabled. On matched Blender 5.2 cubes, plain smooth Bevel produced
a 10.5605° maximum corner-normal deviation across the six large panels; both documented policies
reduced it to 0° while preserving identical evaluated topology. The solid Workbench comparison and
fresh-process verifier are retained with the run.

### Curved manufactured transfer

Evidence: `runs/2026-08-16_curved-bevel-normal-policy/`

Twelve live, unapplied variants add an unbeveled semantic baseline and transfer the comparison to a
uniform 12-sided cylinder, an equal-count uneven 12-sided cylinder, and a uniform 16-sided taper.
Plain smooth Bevel bends cap normals by `8.4464°–8.4823°`. Harden Normals restores every side to
its unbeveled baseline and makes cap error `0°`. Face Strength followed by Weighted Normal also
flattens caps and stays below `0.024°` side error on the uniform cylinder/taper.

The equal-count uneven cylinder is the important rejection: its baseline is already `5.0°` away
from the intended radial normal. Harden Normals preserves that error; it cannot repair the cage.
Weighted Normal increases the side error to `9.9988°`, worse than plain smooth Bevel at `9.0773°`,
because face-area weighting responds to the uneven panel distribution.

Decision rule: compare against an unbeveled semantic baseline; use Harden Normals when preserving
the surrounding curved faces is the goal; use Weighted Normal only after checking its weighting on
the actual curved region. If the restored baseline is wrong, redistribute topology before adding
segments or normal tricks. Equal vertex count does not imply equal curvature quality.

Actual silhouette, arbitrary double curvature, SubD, and reference fidelity still require separate
diagnosis; custom normals cannot repair geometry.

## Weighted-edge production transfer

Evidence: `runs/2026-08-11_connected-camera-corrective/`

Experienced review identified excessive softness after a clean one-component camera already passed
silhouette and topology gates. A live user example demonstrated `Bevel` limited by edge weight before
two SubD levels. The first correction was itself overturned because lens-only weighting did not cover
the object's intended hard edges. On the final corrective camera:

- Weighting all 198 lens/front/back candidate edges sharpened the image but created 48 Bevel-stage
  and 192 post-SubD non-manifold edges.
- Reducing width from `0.028` to `0.004` did not change those counts, disproving excessive width as
  the cause.
- Scope probes isolated the cause: 14 front-perimeter weighted edges produced 12 Bevel-stage
  non-manifold edges; 24 back/star-cap edges produced 36; 144 lens-ring edges produced zero before
  and after SubD.
- Rebuilt topology and consistent face winding permit all 492 semantically intended hard edges to
  carry weight `1.0`: body perimeters (96), four three-segment longitudinal corner rails (12), lens
  steps (216), and both control loop systems (84 each).
- Bevel width `0.018`, two segments, then two SubD levels remains manifold at the isolated Bevel
  stage and after SubD. A winding error in the assembled front annulus reproduced the earlier failure
  independently of width; recalculating consistent outward normals repaired the root cause.
- Tight support loops remain unweighted when their job is transition control rather than representing
  a hard design edge. “Complete weighting” means every intended sharp edge, not every mesh edge.
- Weight placement is a visual-semantic decision. A clean probe that weighted four cardinal midline
  rails produced an unwanted side seam; fixed-view Solid review moved them to the four diagonal
  rounded-body corner chains while retaining clean evaluated topology.
- Bevel cannot reverse an overly soft base silhouette. The user's live camera used width `0.002`
  over a `0.28047` minimum cage dimension (ratio `0.00713`), comparable to the candidate's ratio.
  Its sharper result came from a literal box cage. Replacing n=6 with n=16 improved the candidate
  but still pre-rounded it; the accepted revision removes the superellipse entirely. Four flat sides
  and exact 90-degree rails now feed the same `0.018` weighted Bevel, which authors the full radius.

Weighted bevel is a fast sharpness control, not a blanket license. Probe edge scope separately from
width, audit face winding, and verify the evaluated mesh after every downstream modifier.

## Hard-surface shading policy

Evidence: `runs/2026-08-12_hard-surface-shading-policy/`

For Blender 5.2 hard-surface work, blanket `polygon.use_smooth=True` is not an acceptable surface
strategy. It can visually erase a missing edge radius, make a flat transition look melted, and hide
the absence of semantic edge selection. The tested default sequence is:

1. classify design edges as sharp, curved, or intentionally smooth;
2. assign edge weights only to sharp design edges;
3. apply a scoped `BEVEL` before `SUBSURF` where a real radius and controlled curvature are both
   needed;
4. invoke `bpy.ops.object.shade_smooth_by_angle(angle, keep_sharp_edges=True)` for normals;
5. inspect Solid/MatCap highlights and the evaluated mesh.

Smooth by Angle does not repair wrong topology or missing bevels. It is a normal-interpolation
policy after geometric edge intent has been authored.

Step 3's `BEVEL` limit method is usually `WEIGHT` with edge weights from `set_bevel_weight_by_ids`,
the only method that maps to inspectable persistent edge IDs. `ANGLE` and `VGROUP` limiting are also
legitimate (see the cylindrical/production transfer sections above) and have their own typed,
intent-recording path: `set_bevel_scoping(name, method, angle_deg=..., vertex_group=..., width=..., segments=...)`,
documented in `smooth_by_angle.md`. Configuring `limit_method` directly through `bpy` without calling
it leaves the object's intent unrecorded and `get_hard_surface_shading_audit` correctly returns
`REVIEW_REQUIRED` for it, regardless of whether the resulting geometry is otherwise clean.

## Preconditions and verification

- Apply or account for non-uniform object scale before judging world-space bevel consistency.
- Confirm the limit method targets the intended edges.
- Inspect both base cage and evaluated surface.
- Check density, minimum edge lengths, corner intersections, shading, and silhouette.
- Test modifier order whenever another modifier creates or removes edges relevant to the bevel.
