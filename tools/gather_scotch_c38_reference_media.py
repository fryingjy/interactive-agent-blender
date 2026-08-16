"""Download the reviewed C38 reference candidates for local inspection only.

The images remain ignored research media.  Their URLs, identity limits, and intended
uses are recorded in the adjacent manifest rather than being treated as source truth.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "runs" / "2026-08-16_reference-gathering-scotch-c38" / "media"

ITEMS = (
    {
        "path": "official/c38_product_primary.jpg",
        "url": "https://multimedia.3m.com/mws/media/622150J/scotch-c38-dispenser.jpg?width=1200",
        "source_url": "https://www.scotchbrand.com/3M/en_US/p/d/v000451417/",
        "purpose": ["PRIMARY_FORM", "MATERIAL"],
        "view": "left_side_oblique",
        "variant": "Scotch C38 classic black current product",
    },
    {
        "path": "retailer/texas_art_white_background.jpg",
        "url": "https://texasart.b-cdn.net/skupix/2000x2000/2/s29930.jpg",
        "source_url": "https://www.texasart.com/products/3m-scotch-desk-tape-dispenser-c-38",
        "purpose": ["PRIMARY_FORM", "DETAIL"],
        "view": "right_side_oblique",
        "variant": "Scotch C38 black",
    },
    {
        "path": "retailer/ofix_clean_profile.jpg",
        "url": "https://ofixmx.vtexassets.com/arquivos/ids/165401-800-450?aspect=true&height=450&v=638417577925500000&width=800",
        "source_url": "https://www.ofix.mx/despachador-chico-para-cinta-negro-c-38---scotch-70005291441/p",
        "purpose": ["PRIMARY_FORM", "DETAIL"],
        "view": "right_side_profile",
        "variant": "Scotch C38 black 70005291441",
    },
    {
        "path": "retailer/office_depot_replacement_hub.jpg",
        "url": "https://media.officedepot.com/images/f_auto%2Cq_auto%2Ce_sharpen%2Ch_450/products/946343/946343_p_1_clear/946343",
        "source_url": "https://www.officedepot.com/a/products/946343/3M-Plastic-Replacement-Core-1/",
        "purpose": ["CONSTRUCTION", "DIMENSION"],
        "view": "hub_detail",
        "variant": "officially compatible 1-inch C38 replacement hub",
    },
)


def download(item: dict[str, object]) -> dict[str, object]:
    destination = OUTPUT / str(item["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(str(item["url"]), headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        content = response.read()
        content_type = response.headers.get_content_type()
    if not content.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF")):
        raise ValueError(f"{item['path']}: response is not a recognizable raster image ({content_type})")
    destination.write_bytes(content)
    return {
        "path": str(destination.relative_to(OUTPUT.parent)).replace("\\", "/"),
        "source_url": item["source_url"],
        "download_url": item["url"],
        "purpose": item["purpose"],
        "view": item["view"],
        "variant": item["variant"],
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "content_type": content_type,
    }


def main() -> None:
    downloaded = [download(item) for item in ITEMS]
    inventory = {
        "target": "Scotch C38 Classic Desktop Tape Dispenser, black",
        "retention": "Third-party and manufacturer media is ignored local reference media for inspection only.",
        "items": downloaded,
    }
    output = OUTPUT.parent / "media_inventory.json"
    output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
