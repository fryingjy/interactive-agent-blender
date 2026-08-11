# Session learning and replay gate

## Pipeline

1. Parse append-only decision logs with source file and line provenance.
2. Group outcomes by operation and asset/session.
3. Require repeated success across multiple assets before creating a candidate.
4. Keep the candidate unpromoted until a separately declared replay exists.
5. Require a different asset, expected result, observed result, pass/fail, and evidence path.
6. A failed replay contradicts; same-asset replay still requires transfer.

## Evidence

`runs/2026-08-10_learning-system/` mined 165 historical events, created two candidates without
automatic promotion, and replay-validated the repeated bevel operation on a different clean cube.

## Limit

Operation-name frequency is coarse. A production learner must also cluster modeling stage,
topology, surface, defect, parameters, unexpected effects, and visual outcome before encoding a
context-aware executable skill.
