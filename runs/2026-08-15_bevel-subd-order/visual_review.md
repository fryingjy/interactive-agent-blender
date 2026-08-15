# Fixed-frame visual review

Reviewed against `bevel_subd_order_matcap.png` and `bevel_subd_order_wire.png` after the clean
factory-startup run. Left to right: pre-Subdivision Bevel, crease-protected post-Subdivision
Bevel, and unprotected post-Subdivision Bevel.

## Observed result

- **Pre-Subdivision Bevel:** broadest and most continuous corner highlight on this fixture. The
  rounded edge becomes part of the form Subdivision smooths. It has no localized pinch candidates
  in the measured diagnostic, but costs 2,400 evaluated quad faces and retains less perfectly
  axis-planar area than the crease-protected variant.
- **Crease-protected post-Subdivision Bevel:** preserves the flattest panels and a tighter,
  manufactured chamfer at 1,176 evaluated quad faces. The tight three-edge corners show visibly
  concentrated highlights and 16 localized curvature candidates. On this fixture it is crisper
  and cheaper, not categorically "less pinched."
- **Unprotected post-Subdivision Bevel:** the base design lines move during Subdivision before the
  Bevel evaluates. The result is visibly over-rounded and no longer reads as the same crisp box
  design, despite matching the protected variant's face count and bounding box.

## Conditional decision rule

Use Bevel before Subdivision when a broad physical radius should participate in the smoothed form
and the resulting topology/highlight flow is acceptable. Use crease/support protection followed by
a post-Subdivision Bevel when the reference calls for flatter panels and a final tight chamfer,
but inspect multi-edge corners for concentrated highlights or pinching. Do not place weighted
Bevel after Subdivision without preserving the intended design lines first.

This is one supported box fixture, not transfer validation. A curved hull and a real prop still need
their own comparison before either workflow is promoted as broadly preferred.
