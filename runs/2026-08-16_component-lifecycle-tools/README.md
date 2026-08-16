# Recoverable component lifecycle lab

This Blender 5.2 runtime lab verifies two missing workflow operations exposed by the rejected
KLF03 attempt:

- replace a failed mesh cage from a candidate while preserving the stable target object name;
- archive a failed component into a hidden collection without deleting it.

Both mutations run through decision-owned transactions. The sequence deliberately rejects each
operation once to prove rollback, then commits it. `report.json` and `result.json` distinguish
source preservation, target identity, mesh/modifier transfer, visibility, and collection ownership.
