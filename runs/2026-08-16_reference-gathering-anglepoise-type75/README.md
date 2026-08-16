# Anglepoise Type 75 reference evidence

This run defines the exact benchmark target as the standard desk-base Anglepoise Type 75 in Slate Grey. It uses manufacturer cut-outs and technical specifications, not a downloaded CAD mesh. Local media is ignored; URLs, file hashes, observations, dimensions, uncertainties, and modeling constraints remain tracked.

The selected evidence establishes the full articulated silhouette, paired arm construction, front/rear linkage, base profile, shade profile, rear shade pivot, spring placement, and primary dimensions. The product is a real assembly, so separate objects are appropriate for physically separate parts. Each major formed part should still be built as a coherent connected cage rather than a stack of decorative primitives.

Validation:

```powershell
python tools/verify_reference_set_gate.py runs/2026-08-16_reference-gathering-anglepoise-type75/reference_manifest.json --output runs/2026-08-16_reference-gathering-anglepoise-type75/audit_report.json
```

No HTML board or pre-model human approval gate is used.
