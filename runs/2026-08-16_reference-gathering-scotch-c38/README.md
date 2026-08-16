# Scotch C38 reference-gathering run

This run is evidence collection for benchmark prop 2. `reference_manifest.json` is audited by
`tools/verify_reference_set_gate.py`; `reference_plan.md` translates only supported observations
into a reversible connected-cage strategy. Direct user instruction on 2026-08-16 removed the
pre-model HTML board/approval step and authorizes modeling from this evidence package. Human review
still evaluates the produced model afterward.

Re-run the media retrieval only when a source changes:

```powershell
python tools/gather_scotch_c38_reference_media.py
python tools/verify_reference_set_gate.py runs/2026-08-16_reference-gathering-scotch-c38/reference_manifest.json --output runs/2026-08-16_reference-gathering-scotch-c38/audit_report.json
```
