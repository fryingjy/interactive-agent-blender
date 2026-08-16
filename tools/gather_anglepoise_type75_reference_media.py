"""Download official Anglepoise Type 75 reference media for local inspection.

Only the manufacturer's cutout-image pack and technical sheet are retained under
the ignored run ``media`` directory. No CAD/3D pack is requested or downloaded.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "2026-08-16_reference-gathering-anglepoise-type75"
MEDIA = RUN / "media"
IMAGE_PACK_URL = (
    "https://anglepoise.s3.eu-west-1.amazonaws.com/asset-bank/type-75/"
    "2-cut-out-photography/1-type-75-cut-out-all/type-75-cut-out-all.zip"
)
TECHNICAL_SHEET_URL = (
    "https://anglepoise.s3.eu-west-1.amazonaws.com/asset-bank/type-75/"
    "4-technical-datasheets/2-eu/type-75-desk-lamp-technical-data-eu.pdf"
)
SOURCE_URL = "https://support.anglepoise.com/hc/en-gb/articles/360014173717-Anglepoise-Type-75-Desk-Lamp"


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def safe_extract_images(archive: zipfile.ZipFile, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    extracted = []
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    target_prefixes = (
        "type-75-desk-lamp-slate-grey-",
        "type-75-desk-lamp-jet-black-",
    )
    for member in archive.infolist():
        filename = Path(member.filename).name.lower()
        if (
            member.is_dir()
            or Path(filename).suffix.lower() not in allowed
            or not filename.startswith(target_prefixes)
        ):
            continue
        output = (destination / Path(member.filename).name).resolve()
        if destination.resolve() not in output.parents:
            raise ValueError(f"unsafe archive member: {member.filename}")
        with archive.open(member) as source, output.open("wb") as target:
            shutil.copyfileobj(source, target)
        extracted.append(output)
    if not extracted:
        raise ValueError("official cutout pack contained no supported raster images")
    return sorted(extracted)


def record(path: Path, *, download_url: str, purpose: list[str]) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": str(path.relative_to(RUN)).replace("\\", "/"),
        "source_url": SOURCE_URL,
        "download_url": download_url,
        "purpose": purpose,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    cutout_directory = MEDIA / "official_cutouts"
    cutout_directory.mkdir(parents=True, exist_ok=True)
    for existing in cutout_directory.iterdir():
        if not existing.is_file():
            raise ValueError(f"refusing to clean unexpected nested path: {existing}")
        existing.unlink()
    with tempfile.TemporaryDirectory(prefix="anglepoise_type75_") as temporary:
        archive_path = Path(temporary) / "cutouts.zip"
        archive_path.write_bytes(fetch(IMAGE_PACK_URL))
        with zipfile.ZipFile(archive_path) as archive:
            images = safe_extract_images(archive, cutout_directory)

    sheet = MEDIA / "type75_technical_sheet_eu.pdf"
    sheet.write_bytes(fetch(TECHNICAL_SHEET_URL))
    inventory = {
        "schema_version": 1,
        "target": "Anglepoise Type 75 Desk Lamp, Slate Grey, standard desk-base variant",
        "source": SOURCE_URL,
        "retention": "Manufacturer media is ignored local reference material; hashes and URLs are tracked.",
        "exclusion": "No manufacturer CAD or 3D source mesh was requested or downloaded.",
        "items": [
            record(image, download_url=IMAGE_PACK_URL, purpose=["PRIMARY_FORM", "DETAIL", "MATERIAL"])
            for image in images
        ]
        + [record(sheet, download_url=TECHNICAL_SHEET_URL, purpose=["DIMENSION", "CONSTRUCTION"])],
    }
    (RUN / "media_inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"images": len(images), "inventory": str(RUN / "media_inventory.json")}, indent=2))


if __name__ == "__main__":
    main()
