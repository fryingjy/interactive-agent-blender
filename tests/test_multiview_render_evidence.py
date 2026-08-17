from pathlib import Path

from PIL import Image

from tools.verify_multiview_render_evidence import evaluate


def make_image(path: Path, *, fill=(0, 0, 0, 255), patch=None):
    image = Image.new("RGBA", (20, 20), fill)
    if patch:
        image.paste(patch[2], patch[:2])
    image.save(path)


def test_rejects_blank_and_duplicate_views(tmp_path):
    blank = tmp_path / "blank.png"
    copy = tmp_path / "copy.png"
    make_image(blank)
    make_image(copy)
    result = evaluate([("front", blank), ("side", copy)])
    assert result["pass"] is False
    assert result["blank_views"] == ["front", "side"]
    assert result["duplicate_view_groups"] == [["front", "side"]]


def test_accepts_distinct_nonblank_views(tmp_path):
    front, side = tmp_path / "front.png", tmp_path / "side.png"
    make_image(front, patch=(2, 2, Image.new("RGBA", (8, 8), (100, 100, 100, 255))))
    make_image(side, patch=(8, 8, Image.new("RGBA", (6, 6), (120, 120, 120, 255))))
    result = evaluate([("front", front), ("side", side)])
    assert result["pass"] is True
