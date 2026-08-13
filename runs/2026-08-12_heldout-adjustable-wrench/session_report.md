# Held-out benchmark: vintage adjustable (pipe) wrench

Contract frozen before download: `benchmark_brief.md`. Source: Poly Haven CC0
`adjustable_wrench` (Mateusz Sadek, donated). Source geometry was isolated to
neutral reference renders only; construction used measured pixel data alone,
never the source topology, object names, modifiers, or materials.

## Step 0: orientation check (prospective, not retroactive)

Per the frozen contract, `tools/verify_reference_view_orientation.py` was run
against the neutral reference BEFORE any landmark measurement or construction --
its first genuinely prospective use (its only prior validation was retroactive,
against the already-known desk-lamp bug).

```
--in-plane-axis X --wide-view front
```

Result: **consistent** (exit 0). The reference's own measured aspect ratios
(front 0.269 vs. side 0.120 -- front genuinely wider) matched the X-axis probe's
empirical front/side pattern. Construction proceeded with front width -> world X,
side width -> world Y, height -> world Z, without the axis inversion that cost the
desk lamp a full failed construction cycle. This is the first real evidence the
tool changes workflow behavior, not just documents a past lesson.

## Construction method

`tools/run_heldout_adjustable_wrench.py`. Every cross-section station along the
body's height is read directly from `tools/measure_reference.py`'s row-profile
output for both the front and side masks: front row width -> world-X half-extent,
side row width -> world-Y half-extent, row position -> world-Z, and each view's
own centerline (measured from the confirmed round shaft/handle region, where
front width in px == side width in px) -> the station's X/Y center offset. An
ellipse is swept through 78 such measured stations and lofted into one
continuous, closed-cap, all-quad body (`Wrench_Body`) -- no primitive assembly,
no by-eye placement, no hard-coded shape template for this object.

This is a deliberately different construction strategy from the revolve-based
watering can and the skeleton-frame desk lamp: neither a body of revolution
(the jaw region is confirmed non-round, see below) nor a multi-segment armature,
but a single asymmetric profile loft driven by two independent orthographic
measurements at once.

## Investigated and reverted: the jaw-mouth fork

Direct run-length analysis of `reference_front_mask.png`'s alpha channel (not
assumed) confirmed rows y_px 108-132 contain two disjoint foreground spans, not
one -- a real gap between the fixed jaw/teeth and the movable jaw, not merely a
narrow silhouette. A second candidate split the loft there: `Wrench_Body` kept
only the fixed-jaw/right-lobe extents, and a separate `Movable_Jaw` object
covered the left-lobe span, mirroring this project's existing precedent for
genuinely distinct mechanical parts (watering-can handle, telephone handset).

Measured effect: front IoU **0.916856 -> 0.911423**, front recall **0.982389 ->
0.973345**. The sudden single-lobe radius at the split stations, next to
full-span radius at the immediately adjacent stations, made the loft taper more
sharply through that band and lose more true-reference coverage than the
gap-carving recovered. Reverted. `Wrench_Body` is the single-loft version; the
fork investigation is kept here as evidence, not hidden, and is the concrete next
gap to close (with a genuinely better local topology, not a blanket retry of the
same split) if this asset is revisited.

## Result

Normalized silhouette IoU vs. the isolated reference
(`tools/compare_alpha_multiview.py`, this project's standing 0.97 front/side/top/
mean gates -- not adjusted after seeing results):

| View | IoU | Recall | Precision | Gate 0.97 |
| --- | --- | --- | --- | --- |
| front | 0.916856 | 0.982389 | 0.932177 | fail |
| side | 0.973018 | 0.977776 | 0.995023 | **pass** |
| top | 0.883142 | 0.966318 | 0.911191 | fail |
| **mean** | **0.924339** | | | fail |

This is the highest silhouette agreement of any held-out asset in this project
to date (prior best automated pass: boombox 0.816 mean IoU, later rejected on
visual review; prior best still-open case: telephone 0.840, watering can 0.901;
worst case: desk lamp 0.417). It still does not clear the frozen gate on two of
three views and **is not claimed as a pass**. Front/top recall is consistently
higher than precision (0.98/0.97 vs. 0.93/0.91) -- the candidate over-covers
rather than misses, concentrated in the jaw region's un-carved fork and the
un-modeled fine tooth serration, both accepted primary-form-level
simplifications documented above and in the construction script's own comments,
not silent gaps.

Independent fresh-process verification (`tools/verify_mesh.py`, a new Blender
invocation, no shared code with the generator):

```
vertices: 2936, edges: 5868, faces: 2934
non_manifold_edges: 0, ngons: 0, loose_verts: 0, loose_edges: 0, degenerate_faces: 0
signed_volume: 0.2513 (positive -> normals consistently outward)
clean: true
```

Renders: `candidate/candidate_{front,side,top,isometric}_mask.png`,
`.blend` at `candidate/heldout_adjustable_wrench.blend`.

## What this does and does not establish

- Establishes: the orientation-check tool works prospectively on a genuinely new
  reference, not just retroactively on a known bug. Establishes: a
  single-object, all-quad, dual-view-measured elliptical loft is a viable
  primary-form strategy for an asymmetric hand tool, reaching mean IoU well
  above every prior held-out family without any primitive assembly.
- Does not establish: professional quality, tooth-level surface detail, human
  acceptance, or that the fork/mouth gap is solved -- it is an open, honestly
  quantified gap with a documented failed first attempt at closing it.
- Automated gate pass/fail here should not be read as the final word either way,
  consistent with this project's own boombox lesson (automated pass, rejected on
  visual review) and camera lesson (automated pass, rejected on experienced
  review) -- this candidate is offered for the same human visual check before any
  status is upgraded to a pass.
