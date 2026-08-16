# User blend-library construction study

This records direct, read-only scene facts from the user's local `.blend` examples. It is not a claim that every source file is production-ready or that file inventory alone proves visual quality.

## Observed patterns

- `broken sword.blend` separates editable work, high-poly (`hp`), low-poly (`lp`), and sculpt (`zbrush hp`) collections.
- The editable `blade`, `hilt`, and `handle` meshes in that file are quad-only in the inspected state and retain live Mirror, Subdivision Surface, and Smooth-by-Angle modifier stacks.
- Low-poly counterparts use a separate collection and triangulate only as an explicit downstream/export step, not as the editable high-poly construction surface.
- Edge-crease attributes are present on the editable blade, hilt, and handle cages. This supports crease/SubD as the primary sharpness tool when it matches the form, with bevel reserved for a required physical radius.

## Operational rule added after the Westclox failure

A primitive is only a starting cage. A continuous primary form may not advance beyond `BLOCKOUT` from placement, scale, shading, or modifier changes alone. It needs one of the following recorded forms of evidence:

1. an authored connected revolved profile cage; or
2. a committed topology-changing decision on that exact primary object (for example loop cut, extrude, inset, bridge, or edge-controlled rebuild).

`tools/audit_command_sequence_construction.py` makes this rule reproducible for typed command sequences. It is deliberately narrow: it verifies construction evidence, not resemblance or artistic quality.

## Source records

- [broken sword inventory](../runs/2026-08-16_user-blend-library-audit/deep-study/broken%20sword.json)
- [battle axe inventory](../runs/2026-08-16_user-blend-library-audit/deep-study/battle%20axe.json)
- [dragon radar inventory](../runs/2026-08-16_user-blend-library-audit/deep-study/dragon%20radar.json)
