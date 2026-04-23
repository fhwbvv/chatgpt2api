from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from services.paths import get_base_dir


@dataclass(frozen=True)
class StoredGeneratedImage:
    filename: str
    path: Path
    mime_type: str


def _detect_image_type(image_bytes: bytes) -> tuple[str, str]:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return ".webp", "image/webp"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")):
        return ".gif", "image/gif"
    return ".png", "image/png"


class GeneratedImageStore:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def save(self, image_bytes: bytes) -> StoredGeneratedImage:
        if not image_bytes:
            raise ValueError("image_bytes is required")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        suffix, mime_type = _detect_image_type(image_bytes)
        filename = f"{uuid.uuid4().hex}{suffix}"
        path = self.root_dir / filename
        path.write_bytes(image_bytes)
        return StoredGeneratedImage(filename=filename, path=path, mime_type=mime_type)

    def resolve(self, image_name: str) -> Path | None:
        clean_name = Path(str(image_name or "")).name
        if not clean_name or clean_name != str(image_name or ""):
            return None
        candidate = self.root_dir / clean_name
        try:
            candidate.relative_to(self.root_dir)
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        return candidate


generated_image_store = GeneratedImageStore(get_base_dir() / "data" / "generated-images")
