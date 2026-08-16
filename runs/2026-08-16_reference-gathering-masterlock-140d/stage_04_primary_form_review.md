# Master Lock 140D — primary-form review, stage 04

## Decision and evidence

The initial 8 mm body depth was a placeholder, not a specification.  The official product page establishes 40 mm body width and a 6 mm shackle with a 21 mm by 22 mm clearance, but does not publish body thickness.  The retained official oblique photo shows a substantially deeper body than the initial cage.

One reversible, low-confidence correction was therefore made: the connected brass-body cage depth changed from 8 mm to **16 mm**.  This remains a visual hypothesis, not a manufacturing claim; rear and underside fidelity remain out of scope until a dimensioned side/rear source is available.

## Live-state verification

| Channel | Observed state | Result |
| --- | --- | --- |
| Editable base cage | `brass_body`: 8 vertices, 12 edges, 6 quad faces; 0 non-manifold edges, n-gons, loose vertices, or degenerates | PASS |
| Body envelope | 40 x 16 x 32 mm base bounds | Width is official; height/depth remain image-derived hypotheses |
| Evaluated body | Live `Body_Edge_Radius_Unapplied` Bevel, 1.0 mm width, 3 segments, angle scope; 96 evaluated vertices / 98 faces; no probe pinch candidates | PASS as a surface-control check, not a reference-quality verdict |
| Normal policy | Typed `Smooth by Angle`, 30 degrees, preserving sharp edges | PASS |
| Shackle construction | One editable 6-point BEZIER path with 3.0 mm bevel depth; no disconnected cylinder assembly | PASS |
| Shackle constraints | 6 mm diameter; authored leg centerlines at +/-13.5 mm give 21 mm clear width; evaluated inner crown is approximately 22 mm above the body top | PASS against official shackle values |
| Visual review | Front and isometric solid renders show the corrected depth and restrained physical body radii | Plausible primary blockout only |

## Diagnosis

The primary-form error was not a lack of subdivisions or a need to add objects. It was an unresolved dimension being treated as if it were harmless. The correction keeps the body as one manipulable cube-derived cage and uses an unapplied modifier only for the manufactured edge radius visible in the reference.

## Gate

**Primary blockout: conditionally advanceable.** The front envelope and shackle constraints are coherent, but the body depth is still low confidence and the reference is perspective-only. Do not call this a finished or production-accurate asset. The next justified work is a narrowly sourced secondary front insert and top-socket treatment, after obtaining a more direct front/side view if available. Do not add logo engraving, key geometry, rear detail, materials, or dense support topology first.
