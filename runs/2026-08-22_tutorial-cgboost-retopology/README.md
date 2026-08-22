# CG Boost retopology tutorial reproduction

Stage 5 uses CG Boost's 14:14 beginner retopology tutorial. Gemini inspected the complete video,
audio, captions, and UI in two bounded ranges. YouTube oEmbed, indexed chapters/caption text, and
the retained thumbnail independently confirm the identity and lesson structure. The video is not
archived.

## Modeled evidence

- `failure.blend` contains a dense curved eye/brow target and a 96-face retopo patch whose radial
  rows deliberately change correspondence. It is manifold and all-quad, but the wire view exposes
  spiraling/twisted landmark flow. This is the important failure: technical validity and a smooth
  render do not prove deformation-aware topology.
- `corrected.blend` contains an independently authored 448-face high target in `HIGH_POLY`, a
  96-face low cage in `LOW_POLY`, an eye globe as a legitimate separate anatomical assembly, and a
  bend probe in `DEFORMATION_TESTS`. The eye-opening loops align before the surrounding patch is
  filled. Shrinkwrap, SubD, final conforming Shrinkwrap, and Bend remain live and unapplied.
- `transfer.blend` moves the same loop-first strategy to a different pointed mouth landmark using
  a 392-face high target, an 80-face low cage, and a separate bend probe.

The first generic oval iteration was rejected because it did not read as the tutorial's eye/brow
landmark. A second iteration added an almond opening, asymmetric brow/cheek envelope, and eye
context. A later fixed-frame audit found post-projection SubD shrinkage; the retained stack adds a
second live Shrinkwrap after SubD and compensates the authored low boundary without applying any
modifier.

## Verification and boundary

The corrected eye cage has zero n-gons, loose vertices, degenerates, or non-manifold edges in base
and evaluated geometry. The twisted failure has 24 automated pinch candidates and maximum robust
outlier `11.9293`; the aligned correction has 9 and `7.5798`; its bent probe remains manifold with
7 candidates. The low/high base-face ratio is `0.214286`. Fixed-frame silhouette IoU is `0.877153`
front, `0.892811` side, and `0.885763` top, passing the explicitly bounded Stage-5 minimum of
`0.85` but not the later production target of `0.90`.

This is a bounded eye/brow and mouth landmark-patch reproduction, not a claim that the complete
dragon head from the tutorial was rebuilt. BSurfaces/F2/Slide Relax UI gestures are represented by
their resulting connected cages and controlled failure/correction, not falsely claimed as direct
interactive tool replay. The user's live-modifier requirement overrides the tutorial's final
modifier-application step.
