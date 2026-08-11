# Strategy-choice benchmark

**Date:** 2026-08-10  
**Status:** PASS for declared cases; policy-level evidence only

## Purpose

Convert early workflow choices into inspectable decisions: box mesh vs SubD cage vs curve,
separate vs continuous components, nondestructive vs destructive editing, and patch vs rebuild.

## Result

Ten context-diverse declared cases produced all ten expected decisions. The report records every
input, per-option score, winning reason, runner-up, margin, and confidence. Cases cover a
mechanical enclosure, organic shell, cable, hinged lid, watertight print shell, vent array, baked
export, localized defect, repeatedly failed unstable region, and smooth watertight body.

## Preserved failure

The first command-line run failed with `ModuleNotFoundError: knowledge_engine` because Python set
the script directory, not the repository root, on `sys.path`. The runner now resolves and inserts
its own repository root before importing. Unit imports had passed, so keeping this distinct failure
prevents test-run context from being mistaken for CLI usability.

## Limits

The benchmark cases are declared beside the runner and are therefore not held-out. Passing proves
deterministic policy behavior and explanation quality, not professional strategy judgment. The
policy does not author geometry and intentionally reports low margins instead of inventing
certainty. Held-out modeling must test whether these choices improve actual assets.
