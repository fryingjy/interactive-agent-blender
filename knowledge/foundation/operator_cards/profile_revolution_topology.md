# Operator card: Profile revolution for connected manufactured rings

**Status:** DOCS ✓ | EXPERIMENT ✓ | FAILURE CASE ✓ | RUNTIME USE ✓ | SECOND SHAPE ✓

## Purpose

Use one authored radius/height section and revolve it around an axis when an asset's visible form is
predominantly rotational: bottles, drums, rims, turned handles, collars, and similar manufactured
parts. Raised ribs, rolled seams, and corrugations that are stamped into one skin belong in the same
profile whenever they are physically continuous with that skin.

## Preconditions and selection

- Establish the revolution axis, silhouette aspect, profile landmarks, and required segment count.
- Order profile points monotonically along the section except where the closed wall returns along its
  inner surface.
- Use a closed positive-radius section for a manifold thin-walled shell.
- Keep physically separate assemblies, such as a lid or threaded bung, as separate semantic objects.

## Topology effects

Each adjacent profile pair becomes a circumferential quad strip. A closed profile revolved through
96 segments therefore remains one connected all-quad shell with predictable density and continuous
loops around every integrated rib. This is preferable to intersecting ring objects when the rings are
part of the same stamped body.

## Failure modes learned

- Separate intersecting hoop meshes can reproduce the silhouette but fail the intended continuous
  production topology.
- A blanket angle-bevel modifier on already-supported tight profile loops produced 96 evaluated
  zero-area faces. Removing the redundant modifier restored a clean evaluated mesh.
- A visually plausible top fitting placement was still wrong after camera-orientation conversion;
  image-space circular-landmark measurement exposed and corrected it.
- All-quads is not a universal rule for every asset. It is the correct requirement here because the
  main drum skin is a regular revolved surface with continuous manufactured rings.

## Evidence

- `blender_ops/profile_mesh.py`
- `runs/2026-08-11_multiview-barrel/verify/body_topology.json`
- `runs/2026-08-11_multiview-barrel/verify/collection_mesh_health.json`
- `runs/2026-08-11_multiview-barrel/verify/multiview_silhouette.json`
- `runs/2026-08-11_multiview-barrel/verify/top_fitting_landmarks.json`

The final barrel body has 5,376/5,376 quad faces, zero non-manifold edges, one connected component,
and no evaluated degenerates. This is corrective multi-view development evidence, not held-out proof.
