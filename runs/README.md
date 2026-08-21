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

**Status correction (2026-08-14):** per explicit user instruction, every historical run folder was
removed except `2026-08-13_blend-file-study` (the ten-professional-file `.blend` study), to clear
the accumulated 1.7GB of build/render evidence. This directly contradicts the "historical folders
remain in place" guidance above, which held until this date -- that guidance describes this
project's default policy, not what actually happened here. Any `Evidence: runs/...` citation in
`knowledge/foundation/operator_cards/*.md`, `docs/BENCHMARK_HISTORY.md`, or elsewhere pointing at a
path other than `2026-08-13_blend-file-study` is now a dangling reference: the written finding
still stands, but the raw reproducible artifact backing it no longer exists on disk (recoverable
from git history prior to this date if ever needed). Do not silently rewrite those citations to hide
this; if a citation is corrected, note that the underlying evidence was removed, not that it never
existed.

**Status correction (2026-08-20):** the magnifying-glass build was purged for overclaiming --
`2026-08-18_magnifying-glass-reference/`, `2026-08-19_magnifying-glass-build/`, and the root-level
`directive-coverage-audit.json` / `directive-coverage-audit-current.json` were removed. The
object-specific generator script it left behind (`tools/apply_authored_bezel_profile.py`) was
deleted for the same reason as the 2026-08-17 purge precedent: it has no purpose once its target
model is gone. As with the 2026-08-14 correction, any citation to these paths elsewhere in the repo
is now a dangling reference to evidence removed from disk, not evidence that never existed. The
mallet (`2026-08-20_mallet-build/`) and mug-handle-join (`2026-08-20_mug-handle-join/`) runs are the
current trust-rebuild work.
