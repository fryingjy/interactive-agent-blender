# Anglepoise Type 75 modeling plan

## Exact target

Anglepoise Type 75 Desk Lamp, Slate Grey, standard circular desk-base variant. The configured pose follows the official full-product Slate Grey cut-out while dimensions come from the official support article and technical sheet.

## Measured anchors

- Configured envelope: approximately 52 cm high, 43 cm wide, and 19.5 cm deep.
- Shade: 14.5 cm diameter and 19.2 cm high.
- Base: 19.5 cm diameter.
- Maximum reach: 71 cm; maximum vertical reach: 90 cm.
- Arm members: technical drawing labels the paired arm spans at approximately 31 cm and 32 cm.

## Component graph

1. Cast-iron circular base with a formed aluminum cover and central vertical shank.
2. Lower pivot yoke, paired lower bars, lower spring pair, and transverse pins.
3. Elbow pivot, paired upper bars, upper tension/cable loop, and transverse pins.
4. Shade fork/pivot, one-piece flared aluminum shade, rolled lower lip, diffuser/bulb region, vented switch cap, and switch button.
5. Flexible cable, modeled only after primary-form acceptance because it must not disguise linkage errors.

## Construction strategy

- Build the base as one sparse 16-segment radial profile cage with purposeful vertical profile loops. Use SubD and crease/support control; use a small bevel only if the physical lower rim requires a real radius.
- Build each arm bar from a box-derived connected cage, shaped in Edit Mode. The four bars remain separate because the real mechanism is articulated and paired.
- Build the shade as one 16-segment connected profile/loft cage, not stacked cones and cylinders. Preserve the straight neck, smooth flare, rolled lower lip, and rear pivot transition.
- Use 12-16 sided radial cages for pins and spacers. Separate fasteners and springs are allowed only because they are real separate components.
- Keep modifiers live and unapplied. Prefer edge creases and support topology for SubD form control; apply Smooth by Angle only after topology and sharp-edge control are correct.
- Maintain separate `HIGH_POLY` and `LOW_POLY` collections with independent editable cages. No modifier is applied on the user's behalf.

## Stage order

1. Scale anchors, base, shank, arm bars, and shade envelope.
2. Linkage spacing and pivot alignment from side and front views.
3. Base and shade profile refinement with connected cages.
4. Yokes, pins, springs, and verified negative spaces.
5. Crease/support-edge and shading pass.
6. Independent topology/modifier verification and controlled solid/wire renders.

## Known uncertainty and constraints

- Product photos are perspective cut-outs, not orthographic blueprints; use official dimensions to prevent image-scale drift.
- Exact hidden fastener lengths, base underside, internal shade wall, and cable routing inside joints are not established.
- Do not invent underside detail or internal hardware during primary-form work.
- Vented cap holes are secondary detail and cannot compensate for an inaccurate shade profile.
- Manufacturer CAD is explicitly excluded so the benchmark remains a genuine modeling exercise.
