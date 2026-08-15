# Bridge correspondence control — session report

## Outcome

Protocol 0.3 adds bounded Bridge Edge Loops correspondence control: a read-only candidate analyzer,
an explicit integer `twist_offset`, exactly-two-closed-loop validation, and unequal-density rejection
by default. Two controlled shape families reproduce visible crossed bridges and correct them through
the typed transaction path. A separate Blender process verifies the saved scene and render artifacts.

The run also exposed and fixed an independent recovery defect. If a transaction-owned operation
mutated a mesh and then raised, `perform()` previously propagated the exception before marking the
operation performed, allowing partial state and snapshot-related mesh datablocks to remain. Failed
operations now restore all transaction-owned target channels before re-raising and free their
snapshots.

## Results

- Blender: 5.2.0 LTS.
- Circle: twist `2` corrected to `0`; connector length 19.5538 → 12.8000 (34.5% reduction).
- Rounded rectangle: twist `3` corrected to `0`; connector length 31.5188 → 19.2000 (39.1% reduction).
- Both default and corrected outputs contain only quads, with expected open end boundaries and
  manifold connector edges.
- Unequal 10/12 loops are rejected by analysis and mutation without changing scene state.
- A deliberate vertex mutation followed by `RuntimeError` is restored exactly.
- The saved file contains exactly six intended mesh datablocks; no rollback snapshots or orphans.
- Visual review confirms crossed/pinched default wireframes and clean corrected correspondence.

## Reproducible commands

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools\run_bridge_correspondence_lab.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python tools\verify_bridge_correspondence.py -- runs\2026-08-15_bridge-correspondence-control\bridge_correspondence.blend runs\2026-08-15_bridge-correspondence-control\bridge_correspondence_verify.json
```

## Retained failures

The first lab execution rendered all evidence but failed while serializing a `frozenset` in the
state fingerprint. The report writer was corrected with an explicit JSON-safe conversion. The first
independent verification then correctly failed a stale assertion that expected the corrected offset
itself to be nonzero; the experiment instead injects a nonzero error and corrects it to zero. The
verifier was changed to test that exact error/correction relationship. Neither failure was treated as
a geometry pass until the final report and independent verifier both passed.

## Evidence boundary

This is controlled transfer across two equal-density loop families, not a held-out prop. Minimum
connector length is a geometric heuristic, not proof of artistic correspondence. Symmetry can create
tied offsets, semantic landmarks may override length, and unequal-density bridging still requires
explicit topology planning and review.
