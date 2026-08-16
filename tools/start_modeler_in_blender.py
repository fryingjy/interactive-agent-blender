"""Start the repository's typed modeler server inside an interactive Blender process."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender_ops import modeler_server  # noqa: E402


modeler_server.start()
