# Documentation crawl and guarded session learning

**Date:** 2026-08-10  
**Status:** PASS

## Documentation reader

The local approved-root crawler followed links from an index to three unique documents, extracted
headings/parameters/warnings, deduplicated an exact content copy, and ended with
`QUEUE_EXHAUSTED`. A second run capped at one page ended explicitly with `MAX_PAGES_REACHED` and a
nonempty remaining queue. Canonical IDs and hashes prevent repeated pages from inflating coverage.

This validates local-document traversal mechanics. The fixture is project-owned and does not count
as external curriculum knowledge.

## Self-session learning

Five historical decision logs supplied 165 real events. Mining found two patterns meeting the
declared multi-session threshold: `DecisionTransaction.perform(mesh_ops.bevel_edges)` (7 successes,
2 assets, 0 failures) and property writes (19 successes, 2 assets, 0 failures). Both remained
`CANDIDATE_REQUIRES_REPLAY`; none was automatically promoted.

The bevel pattern was replayed on the different controlled `Typed_Bevel` cube. It produced
32v/60e/30f and independently verified clean, advancing that candidate to `REPLAY_VALIDATED` with
an evidence path. This does not promote a universal bevel strategy; context/applicability still
belong in a structured skill.

## Preserved failure

The first replay API compared prose `expected` and richer measured `observed` values for literal
equality, falsely marking a passing replay contradicted. The failed report is preserved. Replay now
stores both separately and uses the declared pass plus required evidence path; different-asset
transfer remains mandatory.
