from __future__ import annotations

from pathlib import Path

_DECKS_DIR = Path(__file__).resolve().parent.parent / "decks"
_ASSETS_PREFIX = "anatomy-assets/"


def decks_dir() -> Path:
    return _DECKS_DIR


def resolve_anatomy_image_path(relative: str) -> Path | None:
    """Resolve bundled anatomy asset path (anatomy-assets/…)."""
    rel = (relative or "").strip().lstrip("/")
    if not rel.startswith("anatomy-assets/"):
        rel = f"{_ASSETS_PREFIX}{rel}" if rel else ""
    if not rel:
        return None
    path = (_DECKS_DIR / rel).resolve()
    assets_root = (_DECKS_DIR / "anatomy-assets").resolve()
    if not str(path).startswith(str(assets_root)) or not path.is_file():
        return None
    return path


def anatomy_image_url(relative: str) -> str:
    rel = (relative or "").strip().lstrip("/")
    if rel.startswith("http://") or rel.startswith("https://"):
        return rel
    if not rel.startswith(_ASSETS_PREFIX):
        rel = f"{_ASSETS_PREFIX}{rel}"
    return f"/deck-assets/{rel}"
