from __future__ import annotations

from services.paths import get_base_dir


BASE_DIR = get_base_dir()
VERSION_FILE = BASE_DIR / "VERSION"


def get_app_version() -> str:
    try:
        value = VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "0.0.0"
    return value or "0.0.0"
