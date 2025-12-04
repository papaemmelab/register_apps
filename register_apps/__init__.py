"""register_apps module."""

from pathlib import Path

# make sure we use absolute paths
ROOT = Path(__file__).resolve().parent

VERSION_FILE = ROOT / "VERSION"
__version__ = VERSION_FILE.read_text(encoding="utf-8").strip()
