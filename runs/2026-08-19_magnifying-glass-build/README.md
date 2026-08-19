# Magnifying glass, blockout stage — the first build where knowledge fired on a real problem

Executes the frozen contract in `runs/2026-08-18_magnifying-glass-reference/contract.md`. This is the
first reference-driven build in the repo since the 2026-08-17 deletion of all prior model attempts,
and the first time a validated skill has been retrieved for a problem that arose during actual
modeling rather than from a ticket written to trigger it.

Built live over the typed decision protocol (`begin -> perform -> verify -> commit`), one meaningful
decision at a time, with observation between each. No object-specific generator: there is no
`build_magnifying_glass.py`. Every shape decision below is an individual typed transaction against
live state.

## The milestone: knowledge retrieved for a genuine, unprompted modeling problem

At the point of growing the neck out of the handle, the real question was *how to add a narrower
collar to the flat end cap of a coarse cylinder without the new form drooping into the surrounding
surface*. Querying the skill store with that problem — not with a ticket type, not with the skill's
name — returned:

```
 14.861  TRANSFER_VALIDATED   extrude.inset_first.local_containment
  7.334  TRANSFER_VALIDATED   topology.connect_vertex_path.subd_safe_quads
  7.085  TRANSFER_VALIDATED   hard-surface.explicit_semantic_bevel_edge_intent
```

The top skill's conditional rule applied directly and correctly: its validated boundary says the
benefit is *small on an already-fine grid but real on a coarse surrounding surface*. Here the
surrounding surface was a single 24-gon cap — squarely the coarse case — so inset-before-extrude was
the right call, and the knowledge said so for the right reason rather than as a blanket rule.

This is materially different from the circular runtime evidence withdrawn by the 2026-08-19 audit:
the problem existed first, the query described the problem in the modeler's own words, and the
retrieval had to earn the match.

**Honest scope of the claim:** the skill informed *the decision*. It did not execute autonomously —
this was retrieval-informed manual authoring, not planner-driven execution, because
`extrude.inset_first.local_containment` still has `trigger_vocabulary_status: NOT_YET_OBSERVABLE`
(no classifier can emit `local_feature_extrusion_on_coarse_surface`). So this is one honest step
beyond "retrieval works in a lab" and one step short of "the planner drove a real build".

## Decisions taken

| # | decision | result |
| --- | --- | --- |
| 1 | `create_primitive` cylinder — handle primary form (Ø1.7 × 10, 24-sided) | 48v, 0 non-manifold |
| 2 | `inset_selection` on the top cap, thickness 0.30 — **knowledge-informed** | 72v, 0 non-manifold |
| 3 | `extrude_selection` 2.0 — neck grown from the handle's own mesh | 96v, 0 non-manifold |
| 4 | `create_primitive` torus — ring/bezel, OD 9.0, rotated into the handle's plane | separate component |
| 5 | `scale_selection` ×1.465 in XY — **reference-driven proportion correction** | 96v, 0 non-manifold |

## Reference comparison drove a real correction

The contract's own review gate required measuring proportions against the reference before
advancing. Measuring `ref_front_oblique_round_lens.jpg` by pixel extents (not by eye):

```
REFERENCE px: ring_d=740  handle_len=877  handle_d=205  neck=199
```

| ratio | reference | model (before) | error |
| --- | --- | --- | --- |
| ring_d / handle_d | 3.61 | 5.29 | **+47%** |
| ring_d / handle_len | 0.84 | 0.90 | +7% |

The handle was **47% too thin** relative to the ring — the dominant proportion error, and one the
contract's frozen mm estimates had actually encoded (90mm ring / 100mm handle implies 0.90, while
the same paragraph's measured 0.81 pixel ratio implies otherwise; the contract was internally
inconsistent and anticipated this, permitting revision of the mm estimates while keeping ratios
frozen). Decision 5 corrected it.

Re-measuring the corrected render with the **same method applied to the model's own alpha
silhouette**:

| ratio | reference | model (after) | error |
| --- | --- | --- | --- |
| ring_d / handle_d | 3.61 | **3.60** | **-0%** |
| ring_d / handle_len | 0.84 | 0.72 | -14% |

The remaining -14% on the length ratio was checked rather than assumed to be an error: the reference
handle recedes from camera, so its measured length is a projection. A true ratio of 0.84 at ~30° of
tilt projects to 0.73 — essentially the model's 0.72, and ~30° matches the visibly oblique pose in
the photo. So the width ratio (perspective-robust, both measurements normal to the recession axis)
is the trustworthy check, and it is now exact.

A measurement bug was caught and fixed en route: the first pass converted the RGBA render to
grayscale, turning the *transparent* background black and making the threshold select the entire
frame (reported handle_d = ring_d = 699px on a 700px image). Using the alpha channel as the
silhouette mask fixed it. Recorded because a silently wrong measurement would have "verified" a
wrong model.

## Blockout review gate

Against the contract's frozen criteria:

- **Silhouette / proportion** — PASS (measured; exact on the robust ratio, consistent on the other)
- **Ring circular and open, negative space intact** — PASS (`eval_top.png`, `stage3_corrected_front.png`)
- **Neck is a real distinct transition** — PASS (visible as a separate narrower collar)
- **Handle length/diameter plausible for a held object** — PASS (Ø2.5 × 10cm)
- **No visible topology defect** — PASS for each component individually (0 non-manifold throughout)

**Known and deliberately deferred:** the ring and neck are still separate touching objects, clearly
visible in `eval_iso.png`. The contract requires them joined as one continuous mesh (not a Boolean).
That is secondary-form work and correctly does not belong at blockout — but it is exactly the
failure mode this project has hit repeatedly, so it is named here rather than left to be discovered
later.

## Status

Blockout complete and awaiting the human review the contract requires **before** any detail work.
Per the standing rule, no topology or detail work proceeds while primary form is unreviewed.
