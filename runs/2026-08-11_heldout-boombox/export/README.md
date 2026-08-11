# Boombox production GLB export

The accepted connected-cage scene exports to `heldout_boombox.glb` with evaluated modifiers. A
fresh Blender 5.2 factory process re-imports the package and direct GLB parsing inspects primitive
attributes.

Passing invariants:

- 41 mesh objects and 15,292 evaluated triangles preserved;
- combined XYZ dimensions preserved after Blender converts the Y-up package back to Z-up;
- UVs, material assignment, and all seven material families preserved;
- every primitive declares POSITION, NORMAL, and TEXCOORD_0;
- at least the primitives whose UVs support tangent calculation carry TANGENT.

`failed_axis_expectation.json` preserves the rejected verifier rule. Tangents are not present on
every radial primitive because the asset has no tangent-normal texture and current smart UVs do not
support tangent calculation everywhere. A future normal-map version must author those UVs and make
per-primitive tangent presence a hard gate.
