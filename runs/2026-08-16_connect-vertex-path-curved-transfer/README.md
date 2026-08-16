# Connect Vertex Path: curved/SubD transfer

This controlled Blender 5.2 fixture tests a bounded, two-endpoint `connect_vertex_path` on
nonplanar open patches. `Crown_Hex_Repair` and `Twisted_Hex_Repair` begin as six-sided faces and
become two all-quad base faces through the typed transaction path. Each retains a live, unapplied
Catmull-Clark Subdivision modifier.

`Curved_Strip_Diagonal_Control` demonstrates the boundary: a diagonal across three quads would
leave endpoint triangles. With `require_all_quads=true`, independent BMesh preflight rejects it
before mutation; the report compares the full fingerprint and scene revision before and after.

Run the builder with Blender's Python executable:

```text
blender --background --factory-startup --python tools/run_connect_vertex_path_curved_transfer.py
blender --background --factory-startup --python tools/verify_connect_vertex_path_curved_transfer.py
```

The retained builder report has 6/6 assertions; the independent verifier has 9/9 checks. The solid
and wireframe images are controlled topology evidence, not a claim of production-asset fidelity.
