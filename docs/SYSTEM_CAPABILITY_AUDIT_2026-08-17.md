# System capability audit — 2026-08-17

## Verified toolchain

- Blender 5.2 LTS is available locally.
- Python 3.12.10, FFmpeg 9.0, and yt-dlp 2026.07.04 are installed.
- Local-video ingestion and Gemini range-analysis commands load and validate.
- The Gemini API key is **not** configured in the current process. Public
  YouTube analysis therefore cannot run until the user configures a key; no
  credential was requested, printed, or persisted by this audit.

No additional local tool installation is currently the limiting factor.

## Root causes

1. **Visual capture integrity was not enforced.** A blank side render could
   enter a written review. `tools/verify_multiview_render_evidence.py` now
   rejects missing, blank, and byte-identical views, and the
   `PROPORTION_SILHOUETTE` gate requires its passing report. This is a
   capture-integrity gate, not an automated likeness claim.
2. **Closed-manifold bias distorted open manufactured forms.** The reusable
   open quad-surface operation and live-Solidify workflow correct this. The
   KUPONG closed-shell failures remain retained negative evidence.
3. **Research evidence is partially non-reproducible.** The source audit
   reports 62 historical/missing artifacts, all classified rather than
   silently counted as local proof. Recovery is not automatically justified;
   future claims must cite currently reproducible evidence or stay bounded.
4. **The real bottleneck is visual judgment transfer.** The directive matrix
   remains 13/20 PARTIAL: no amount of primitive/operator expansion proves
   repeated reviewer-accepted reference resemblance. The next gains must
   couple multi-view references, small connected-cage decisions, and
   independent review.
5. **Video-learning infrastructure exists but needs live source use.** The
   Gemini/local pipeline is available, but the missing API key blocks a new
   public-video study in this process. Existing video records cannot be
   relabeled as new learning.

## Correct development rule

For the next authorized prop, do not advance on topology or IoU alone. Require
a nonblank/distinct view preflight, local constraints, a per-view mismatch
ledger, and visual inspection of base cage, evaluated modifier result, and
solid/MatCap render. Research a tutorial only for a named local failure, then
reproduce and transfer it before promotion.
