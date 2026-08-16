# Westclox 70010 — Stage 02 decision

**Decision: reject and stop this asset.** The stage is retained as a failed, reproducible construction and comparison record; it is not a model to refine or present as a pass.

## Evidence

- The front normalized comparison has silhouette IoU `0.7593`, but negative-space IoU is only `0.4538`. The latter exposes the missing pressed-metal bell/handle/strut relationships that the global fill score hides.
- Direct solid-view inspection shows a generic octagonal clock body, ellipsoid bells, straight legs, and no credible bell mounting structure. Those are primary-form failures, not surface-detail gaps.
- The primary-form construction audit fails: `ClockShell_BLOCKOUT` was only a primitive plus shading. No committed topology edit established a connected manufactured cage.

## What was learned and changed

1. A generic primitive-plus-shading blockout cannot be promoted for a continuous product form.
2. Component and negative-space diagnostics must veto a plausible global silhouette score.
3. The Bézier curve factory was repaired while making the handle candidate: Bézier splines require `bezier_points`, not `points`. The successful typed Stage 02 run is runtime evidence of that fix.

The next prop attempt must begin with a reference-derived connected cage or a profile construction that can be edited through topology decisions before any modifiers or detail work.
