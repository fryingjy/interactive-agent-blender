# Connect Vertex Path lab

This controlled Blender 5.2 experiment validates a bounded typed equivalent of Edit Mode Connect
Vertex Path: exactly two visible selected endpoint vertices.

Evidence:

- `connect_vertex_path_lab_report.json`: 6/6 live transaction cases, including live Edit Mode;
- `connect_vertex_path_fresh_verification.json`: 5/5 checks after reopening the saved file in a
  separate Blender process;
- `connect_vertex_path_solid.png`: Workbench solid/cavity topology evidence;
- `connect_vertex_path_lab.blend`: saved fixtures with persistent element identities.

Observed results:

- one convex six-sided face split into two quads with one new edge and no new vertices;
- a diagonal route across three quads inserted two crossed-boundary vertices and produced four
  quads plus two endpoint triangles, with no n-gons, degenerates, loose geometry, or disconnected
  path pieces;
- already-connected and disconnected endpoint selections raised before acceptance, triggered
  transaction-owned rollback, preserved all fingerprint layers, and did not advance revision;
- created vertices, edges, and faces retained unique positive IDs after save/reload.

Boundary: this does not validate ordered three-plus endpoint selection, curved surfaces, arbitrary
SubD suitability, or real-prop visual quality. The operation prevents a T-junction; it does not
guarantee all-quad topology.
