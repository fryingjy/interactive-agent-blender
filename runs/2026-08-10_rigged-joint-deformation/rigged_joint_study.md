# Rigged joint density transfer

## Learned rule under test

The Blender Studio facial-planning and Snow retopology lessons both allocate topology according to deformation demand rather than uniform density. This experiment transfers that reasoning from facial patches and an analytic hose to a real armature-driven, non-face organic joint.

## Authored specimen and rig

- Shape: stylized tapered upper/lower limb with authored muscle bulges and elbow narrowing
- Construction: explicit 16-sided cross-section profiles; no mesh primitive operators
- Rig: two connected bones (`Upper`, `Lower`) with smooth vertex-group weights across the joint
- Stack: Subdivision Surface level 1, then Armature
- Pose: 82 degrees on the lower bone
- Dense reference: 47 axial rings
- Purposeful cage: 21 rings, concentrated around articulation plus end support
- Sparse failure: 11 rings with the same profile/weights/pose and end support
- Visual mapping: white = dense reference, green = purposeful joint loops, coral = sparse failure

## Measured result

Nearest-surface error was measured on the posed evaluated meshes against the posed dense rigged reference:

| Metric | Purposeful | Sparse |
| --- | ---: | ---: |
| all-face mean | 0.00376301 | 0.01137237 |
| all-face max | 0.01843780 | 0.06306881 |
| joint-zone mean | 0.00300313 | 0.01887370 |
| joint-zone max | 0.01436530 | 0.06306881 |

The sparse joint-zone mean error is 6.28467x the purposeful cage's error. Both use actual Armature modifiers and both carry `Upper`/`Lower` weight groups, so the comparison is not a static analytic bend.

Fresh Blender 5.2 verification passed 3/3 posed evaluated meshes: closed manifold, zero n-gons/loose/degenerate geometry, positive signed volume, and UVs.

## Retained failures

Three presentation attempts were rejected: clipped perspective framing, an end-on orthographic view that hid longitudinal form, and a labeled view with avoidable end-cap star pinching. End support rings, a readable three-quarter orthographic camera, and clean framing corrected those issues. See `failed_presentation_iterations.json`.

## Bounded conclusion

Purposeful deformation density materially improves fidelity under a real weighted armature pose on this shape. This does not prove a full character rig, facial expressions, twist behavior, corrective shape keys, muscle simulation, or professional animation appeal. Those remain separate gates.
