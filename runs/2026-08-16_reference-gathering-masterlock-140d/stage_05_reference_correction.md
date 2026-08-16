# Master Lock 140D — reference interpretation correction

## Trigger

The retained local file `masterlock_140d_front.jpg` was visually re-inspected while preparing the secondary-form step. It plainly shows a shallow horizontal front seam and the `Master` wordmark. It does **not** show a circular keyway on that face.

## Correction

The prior `front_keyway` hypothesis was downgraded from `STRONGLY_INFERRED` (0.75) to `UNKNOWN` (0.05). The scene decomposition now identifies `front_seam_and_wordmark` as a connected body-surface feature, not a separate front component. No Blender object or geometry had been made from the false hypothesis, so no scene rollback was necessary.

## Retained learning

An oblique product image must not promote a barely resolved dark feature into a component claim when a clearer retained view contradicts it. Before secondary modeling, re-open the strongest available view and test whether the proposed feature has independent silhouette, boundary, material, or occlusion evidence.
