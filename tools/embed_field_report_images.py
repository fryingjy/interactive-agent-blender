"""One-off: substitute {{IMG_*}} placeholder tokens in the scratchpad field report
with base64-embedded PNG data URIs, read/replace/write without the bytes ever
passing through the calling agent's own context."""
import base64
from pathlib import Path

REPORT = Path(
    r"C:\Users\odane\AppData\Local\Temp\claude\C--Users-odane-Downloads-3d"
    r"\ae23098a-ce76-43f1-9094-0f8038feeec7\scratchpad\field_report.html"
)
ROOT = Path(r"C:\Users\odane\Downloads\3d")

MAP = {
    "{{IMG_WC_REF}}": "runs/2026-08-11_heldout-watering-can/reference/reference_front_beauty.png",
    "{{IMG_WC_MODEL}}": "runs/2026-08-12_watering-can-rounded-parts-bevel-reverted/final_model_front.png",
    "{{IMG_TEL_REF}}": "runs/2026-08-11_heldout-vintage-telephone/reference/reference_isometric_beauty.png",
    "{{IMG_TEL_MODEL}}": "runs/2026-08-12_telephone-handset-bevel-reverted/final_model_iso.png",
    "{{IMG_BA}}": "runs/2026-08-13_blend-file-study/battle_axe/reference_iso.png",
    "{{IMG_BATARANG}}": "runs/2026-08-13_blend-file-study/batarang/reference_iso.png",
    "{{IMG_WATCH}}": "runs/2026-08-13_blend-file-study/alien_force_watch/reference_iso.png",
    "{{IMG_BROKEN}}": "runs/2026-08-13_blend-file-study/broken_sword/reference_iso.png",
    "{{IMG_ATS}}": "runs/2026-08-13_blend-file-study/adventure_time_sword/reference_iso.png",
    "{{IMG_ASTA}}": "runs/2026-08-13_blend-file-study/asta/reference_iso.png",
    "{{IMG_AXE}}": "runs/2026-08-13_blend-file-study/axe/reference_iso.png",
    "{{IMG_BAT}}": "runs/2026-08-13_blend-file-study/bat/reference_iso.png",
    "{{IMG_AP15}}": "runs/2026-08-13_blend-file-study/ap15/reference_iso.png",
    "{{IMG_AK47}}": "runs/2026-08-13_blend-file-study/ak47/reference_iso.png",
    "{{IMG_CREASE_BAD}}": "runs/2026-08-13_blend-file-study/crease_experiment/beauty_compare_ABC_before_support_fix.png",
    "{{IMG_CREASE_GOOD}}": "runs/2026-08-13_blend-file-study/crease_experiment/beauty_compare_ABCD_final.png",
}


def main():
    html = REPORT.read_text(encoding="utf-8")
    total_bytes = 0
    for token, rel_path in MAP.items():
        src = ROOT / rel_path
        data = src.read_bytes()
        total_bytes += len(data)
        b64 = base64.b64encode(data).decode("ascii")
        uri = f"data:image/png;base64,{b64}"
        count = html.count(token)
        if count == 0:
            print(f"WARNING: token {token} not found in report")
            continue
        html = html.replace(token, uri)
        print(f"embedded {token} <- {rel_path} ({len(data)} bytes, {count} occurrence(s))")
    REPORT.write_text(html, encoding="utf-8")
    print(f"\nTotal embedded bytes: {total_bytes:,} ({total_bytes/1024/1024:.2f} MB)")
    print(f"Final HTML size: {REPORT.stat().st_size:,} bytes ({REPORT.stat().st_size/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
