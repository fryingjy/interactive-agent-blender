# Principal-axis reference Image Empty transfer

This Blender 5.2 run reproduces the verified orthographic reference-card correction through the
typed `create_reference_image` operation and transfers it to distinct front/right project-owned
cards.

Four controlled states are retained:

- a CUSTOM free-view card that correctly fails construction calibration;
- a FRONT Image Empty reproduction with 0° axis error;
- distinct FRONT and RIGHT cards that both measure 0° and pass fresh verification;
- a duplicated-single-image front/right control that is axis-aligned but rejected as distinct
  multi-view evidence.

The first builder run failed because the audit measured stale `matrix_world` values immediately
after object-property writes. The audit now forces a view-layer update before measuring normals;
the failed result is described in `session_report.md` instead of being hidden.

This is scene-setup evidence, not a reference-fidelity benchmark or authorization to bypass the
Swingline human gate.
