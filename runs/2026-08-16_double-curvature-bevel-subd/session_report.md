# Session report

- Blender: 5.2.0 LTS
- Builder: `tools/run_double_curvature_bevel_subd_lab.py`
- Independent verifier: `tools/verify_double_curvature_bevel_subd.py`
- Builder result: 10/10 assertions, exit code 0 on the retained clean run
- Fresh-process result: 11/11 checks, exit code 0
- Source meshes: one connected, closed, all-quad cage per variant
- Modifiers: live WEIGHT Bevel → Catmull-Clark Subdivision → Smooth by Angle
- Typed decisions per object: explicit declaration, weight assignment, shading policy

Retained failures:

1. The first experiment report failed because expected and actual persistent-ID sets had different
   ordering despite equal membership. The assertion now compares sorted sets.
2. The initial base-cage image relied on a viewport-only `show_wire` flag and did not render the
   wires. It was replaced by temporary Wireframe geometry that is removed before save.
3. One passing builder invocation crashed during Intel GPU-driver teardown after saving; it was
   discarded as execution evidence and replaced by a clean exit-0 rerun.

Claim boundary: controlled semantic completeness and visual-consequence evidence only; no automatic
sharp-edge inference, held-out reference match, or human acceptance.
