# Reference-gathering-only exercise — Bialetti Moka Express 3-cup

## Outcome

This run completes collection and structured analysis without opening Blender or creating a model.
The machine reference gate reports `READY_TO_MODEL`, but the separate roadmap-required human gate is
still `PENDING_USER_REVIEW`; `modeling_authorized` remains false.

## Evidence gathered

- Twelve photographs of one physical pre-owned 3-cup unit from one eBay listing, including four
  exterior orientations, open/interior views, lid underside, hinge, valve, box and manual.
- Official Bialetti product/specification evidence for 155 mm overall height, 72 mm boiler-base
  diameter, 130 ml capacity, aluminum body and thermoplastic handle/knob.
- Official Bialetti construction text identifying boiler, funnel/filter plate, collector, valve and
  gasket.
- A 3-cup retailer exploded image for the visible component stack, with retailer dimensions rejected
  because the page's metadata is internally inconsistent.
- A local ignored 4×3 contact sheet visually reviewed at full resolution. Third-party images remain
  under `media/` and are not redistributed by Git.

## Validation

- Reference schema/audit: 8/8 matching items, 8 required views, 3 provenance sources.
- Readiness checks: 7/7 pass; all 10 critical properties covered.
- Dimensional anchors: 155 mm height, 72 mm base diameter, 130 ml capacity.
- Structured decomposition: 11 components, 10 relationships, 4 primary silhouette components.
- Conflicts: two recorded and resolved without averaging or invention.
- No `.blend`, generated model, or Blender construction script exists in this run.

Reproduction:

```powershell
python tools\verify_reference_set_gate.py runs\2026-08-15_reference-gathering-bialetti\reference_manifest.json --output runs\2026-08-15_reference-gathering-bialetti\audit_report.json
```

## Construction implications if human review authorizes the comparison

- Boiler and collector are separate real cast components, but each shell should be one continuous
  eight-facet cage rather than a stack of cylinders or decorative plates.
- The spout must grow from the collector sector as an integrated open channel.
- The handle, lid, knob, valve, hinge and internal filter stack are legitimately separate
  manufactured parts; the one-object rule must not erase real assembly boundaries.
- Facet planes and designed hard breaks must remain sharp with controlled physical bevel radii.
  Global smooth shading is inappropriate for the defining shell planes.
- The upper chamber must be hollow with its floor and delivery column represented; an exterior-only
  closed shell would be structurally inaccurate.

## Honest unresolved evidence

- No direct boiler-underside view was found. Underside stamps/recesses are prohibited from being
  invented and remain deferred.
- Exact overall width including handle and spout is not authoritatively dimensioned.
- The same-object box looks older than current official product pages; cross-revision geometry
  compatibility is medium confidence pending human review.

## Next gate

The user/human reviewer must accept or reject the board and answer the three questions in
`human_review_gate.json`. Only acceptance authorizes the planned equal-effort target-only versus
structured-reference-set comparison. A machine pass alone cannot satisfy that requirement.
