# Scotch C60 reference-to-form study

This run is the first post-audit non-rotational reference target. It tests whether independent
observations and competing 3D interpretations actually change construction, rather than merely
populating a reference checklist.

## What the references changed

- Opposing product views and the opened-hub view reject two independent rail primitives on a solid
  top. The upper housing is authored as one connected all-quad U-plan shell with a real center
  channel and front/rear bridges.
- Highlight and silhouette evidence reject a circular swept-tube rail. The selected cross-section
  is a broad molded band whose shoulders are controlled by a live SubD/partial-crease strategy.
- The visible lower boundary cannot distinguish a separate molding from a cosmetic groove. The
  blockout therefore keeps the lower base separate and reversible without claiming the ambiguity is
  solved.

## Reproducible path

1. `reference_manifest.json` and `visual_reconstruction.json` bind identity, authority, eleven
   observation passes, competing hypotheses, cross-view predictions, and uncertainty.
2. `typed_blockout_sequence.json` creates five functionally justified components. The upper shell
   is one connected nine-section cage; the roll and hub are 16-segment revolved cages.
3. `typed_surface_sequence.json` adds semantic edge creases and a live, unapplied Subdivision
   Surface modifier to the shell. The base uses a separately declared complete physical-radius edge
   set and a live weight-limited Bevel. It does not blanket-smooth the hard parts.
4. `visual_revision_log.json` records why the five-section result was rejected, what changed, and
   what remains visibly incomplete.
5. `fresh_asset_inspection.json` is a clean Blender 5.2 process report: 240 base vertices, 234/234
   quad faces, zero triangles, n-gons, non-manifold edges, or degenerate faces, with all three
   modifiers still live.

The retained third-party photographs live under ignored `media/`; the manifest preserves their
URLs and provenance. Human review rejected the reconstruction after the attached-hub correction:
the overall form remains inaccurate and some separately authored shapes should instead be connected
topology. Work on the prop stopped. This run is retained only as failure evidence and must not be
cited as a finished, accepted, or capability-proving asset.
