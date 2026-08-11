# Run evidence

Each dated folder is an empirical record, not a polished showcase. A substantive run should contain
enough information to answer:

- what question or task was tested;
- which source/reference and Blender version were used;
- what changed, failed, was repaired, or was rejected;
- which base/evaluated/visual/technical channels were inspected;
- which thresholds were declared before judging the result;
- which fresh-process verifier checked the saved artifact;
- what the result does **not** prove.

Preferred structure:

```text
runs/YYYY-MM-DD_short-purpose/
├── session_report.md
├── *_report.json
├── *_verify.json or verify/
├── final editable .blend
├── representative visual evidence
├── failed_*/
└── media/                 # ignored third-party/local source media
```

Historical folders predate this convention and remain in place because their paths are cited by
knowledge records and audits. Do not delete or rewrite failed evidence to improve a score.
