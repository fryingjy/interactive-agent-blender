# Swingline 747 reference-board gate

This run retains the machine-audited historical reference set and its original pending human
authorization gate for the first progressive prop. Machine readiness did not itself authorize
Blender modeling.

Later on 2026-08-16, a human narrowly approved a reversible blockout, then rejected that blockout.
The target-specific builder, `.blend`, renders, and decision files were removed on direct user
instruction. This retained research run is not a current authorization or accepted model.

## Current artifacts

- `reference_manifest.json` and `audit_report.json` retain the structured evidence and machine
  `READY_TO_MODEL` result.
- `reference_plan.md` defines the exact connected-cage/separate-assembly blockout scope.
- `human_review_gate.json` binds the human gate to the exact audit and plan by SHA-256.
- `human_review_gate_validation.json` proves that the pending contract is internally current; it is
  explicitly not a human decision.
- `docs/field-report/swingline-747-review.html` is the visual board. It emits a decision compatible
  with `tools/record_reference_board_review.py` and can copy or download the JSON.

An approval would authorize only a reversible primary blockout. No
`human_reference_board_decision.json` is retained: the human decision was deliberately removed with
the rejected target-specific attempt, so this historical gate must not be used to resume modeling.

## Reproduce the pending-gate check

```powershell
python tools/verify_reference_board_gate.py runs/2026-08-16_reference-gathering-swingline-747/human_review_gate.json --audit runs/2026-08-16_reference-gathering-swingline-747/audit_report.json --reference-plan runs/2026-08-16_reference-gathering-swingline-747/reference_plan.md --output runs/2026-08-16_reference-gathering-swingline-747/human_review_gate_validation.json
```
