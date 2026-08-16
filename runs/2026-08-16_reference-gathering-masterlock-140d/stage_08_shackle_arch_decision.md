# Master Lock 140D — accepted shackle-path correction

## Observation

The stage-04 shackle used two upper control points at `x = -10` and `x = 10`, producing a visibly over-wide flat crown. The retained front reference has a much shorter crown before the arch turns downward.

## Controlled trial

The same six-point, one-spline BEZIER shackle was tested with only the two upper controls moved inward to `x = -4` and `x = 4`. Its profile, bevel depth, point count, separate assembly status, and official 6 mm / 21 mm / 22 mm constraint targets were unchanged.

| Accepted normalized comparison | Stage 04 | Trial | Direction |
| --- | ---: | ---: | --- |
| Silhouette IoU | 0.8338 | 0.8618 | improved |
| Negative-space IoU | 0.7032 | 0.7190 | improved |
| Bounding-box error | 0.00831 | 0.00371 | improved |
| Symmetric contour error | 0.00961 | 0.00740 | improved |

## Decision

Accept the narrowed crown. This is one editable curve-coordinate revision, not a replacement assembly. The current transaction system has mesh-owned rollback; curve-point mutation is a typed direct curve command and is therefore explicitly outside mesh persistent-ID/transaction claims. The saved scene and post-change curve-state report are the verification boundary for this decision.
