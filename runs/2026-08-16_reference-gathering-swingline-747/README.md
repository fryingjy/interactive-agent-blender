# Swingline 747 reference-board gate

This run retains the machine-audited reference set and the still-pending human authorization gate
for the first progressive prop. Machine readiness does not authorize Blender modeling.

## Current artifacts

- `reference_manifest.json` and `audit_report.json` retain the structured evidence and machine
  `READY_TO_MODEL` result.
- `reference_plan.md` defines the exact connected-cage/separate-assembly blockout scope.
- `human_review_gate.json` binds the human gate to the exact audit and plan by SHA-256.
- `human_review_gate_validation.json` proves that the pending contract is internally current; it is
  explicitly not a human decision.
- `docs/field-report/swingline-747-review.html` is the visual board. It emits a decision compatible
  with `tools/record_reference_board_review.py` and can copy or download the JSON.

An approval authorizes only a reversible primary blockout. No `human_reference_board_decision.json`
is retained yet because no human decision has been submitted through this contract.

## Reproduce the pending-gate check

```powershell
python tools/verify_reference_board_gate.py runs/2026-08-16_reference-gathering-swingline-747/human_review_gate.json --audit runs/2026-08-16_reference-gathering-swingline-747/audit_report.json --reference-plan runs/2026-08-16_reference-gathering-swingline-747/reference_plan.md --output runs/2026-08-16_reference-gathering-swingline-747/human_review_gate_validation.json
```
