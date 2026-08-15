# Secondary-view component-strategy experiment

**Status:** PASS (21/21 checks)

A rectangular and a 16-sided radial housing each compare one continuous full-depth body against a narrow body plus a separate full-front faceplate. Both candidates match the front truth, so the planner refuses to choose from that view. The fixed-frame top view reveals the depth error, selects the one-object/one-component continuous strategy, and overrides a generic separate-material prior in the planner.

The saved Blender file and a fresh Blender process independently preserve object counts, connected-component counts, dimensions, collection organization, and masks.

This is controlled synthetic two-family transfer, not photograph inference, a held-out prop, or professional visual acceptance.

## Validation

- Blender experiment analysis: 21/21 checks pass.
- Fresh Blender 5.2 process: 10/10 structural/render checks pass and all 12 canonical alpha-mask
  hashes reproduce without retaining duplicate PNGs.
- Retrieval regression: 13/13 positive and 5/5 abstention cases pass.
- Repository suite: 123 tests and 12 subtests pass.
- Pyflakes, compileall, repository audit (610 files), JSON parsing, and diff checks pass.
