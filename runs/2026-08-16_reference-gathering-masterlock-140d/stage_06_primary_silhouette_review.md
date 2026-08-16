# Master Lock 140D — front silhouette review, stage 06

## Validated reference mask

The local front product photograph was segmented with anchored GrabCut (`rect: 175,25,660,940`, eight iterations, holes preserved). Visual inspection of the preview confirms that the body, shackle, and arch opening are present; it is suitable for a front silhouette comparison but remains perspective photography, not an engineering drawing.

An initial comparison used alpha extraction on the opaque black/white mask. That incorrectly treated the whole image as foreground, so its 0.434 IoU result is invalid and is retained only as a mask-mode failure observation. The accepted comparison explicitly uses the binary mask's `128..255` luminance range.

## Accepted normalized comparison

The accepted comparison removes translation and uniform global scale only. It does not remove aspect-ratio or contour differences.

| Metric | Result | Interpretation |
| --- | ---: | --- |
| Silhouette IoU | 0.834 | Primary outer envelope is plausibly aligned for a perspective reference blockout. |
| Bounding-box error | 0.0083 | After normalization, overall proportions are close. |
| Symmetric contour error | 0.0096 | Outer contour discrepancy is low at this scale. |
| Negative-space IoU | 0.703 | The shackle opening remains the material localized mismatch. |

## Decision

Do **not** add the front seam or wordmark yet. They would add surface complexity while the dominant remaining reference error is the arch opening. The next geometric decision must revise the existing single editable shackle path and compare it again. The brass body remains one 8-vertex connected cage with its live, unapplied edge-radius modifier.
