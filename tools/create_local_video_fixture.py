"""Create a tiny project-owned modeling lesson used to prove legal video ingestion."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _frame(index: int, fps: int, size=(640, 360)) -> Image.Image:
    second = index / fps
    stages = [
        ("STEP 1", "Inspect the base cage", (55, 120, 210)),
        ("STEP 2", "Inspect the evaluated surface", (215, 115, 55)),
        ("STEP 3", "Compare front, side, and top", (70, 165, 100)),
    ]
    stage = stages[min(2, int(second // 2))]
    image = Image.new("RGB", size, (22, 25, 31))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=24)
    small = ImageFont.load_default(size=17)
    draw.rounded_rectangle((42, 42, 598, 318), radius=18, outline=stage[2], width=5)
    draw.text((72, 75), stage[0], fill=stage[2], font=font)
    draw.text((72, 122), stage[1], fill=(240, 242, 246), font=small)
    if second < 2:
        draw.rectangle((115, 185, 260, 280), outline=(220, 220, 220), width=3)
        draw.line((115, 185, 260, 280), fill=(220, 220, 220), width=2)
        draw.text((330, 218), "BASE", fill=(220, 220, 220), font=small)
    elif second < 4:
        draw.rounded_rectangle((115, 185, 260, 280), radius=28, outline=(240, 185, 80), width=5)
        draw.text((330, 218), "EVALUATED", fill=(240, 185, 80), font=small)
    else:
        for offset, label in zip((0, 110, 220), ("FRONT", "SIDE", "TOP")):
            draw.ellipse((95 + offset, 188, 170 + offset, 263), outline=(110, 220, 145), width=4)
            draw.text((96 + offset, 275), label, fill=(200, 230, 210), font=small)
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fps = 6
    with tempfile.TemporaryDirectory() as temp:
        frame_dir = Path(temp)
        for index in range(fps * 6):
            _frame(index, fps).save(frame_dir / f"{index:04d}.png")
        command = [
            _ffmpeg_exe(),
            "-y",
            "-framerate", str(fps),
            "-i", str(frame_dir / "%04d.png"),
            "-f", "lavfi",
            "-i", "sine=frequency=440:sample_rate=44100:duration=6",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            str(output),
        ]
        subprocess.run(command, check=True, capture_output=True)
    output.with_suffix(".vtt").write_text(
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:02.000\nStep 1: inspect the base cage.\n\n"
        "00:00:02.000 --> 00:00:04.000\nStep 2: inspect the evaluated surface.\n\n"
        "00:00:04.000 --> 00:00:06.000\nStep 3: compare front, side, and top views.\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
