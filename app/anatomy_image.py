from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

_DECKS_DIR = Path(__file__).resolve().parent.parent / "decks"
_ASSETS_PREFIX = "anatomy-assets/"
_USER_AGENT = "AI-Anki/1.0 (education; anatomy flashcards)"
_ALLOWED_IMAGE_HOSTS = frozenset(
    {
        "upload.wikimedia.org",
        "commons.wikimedia.org",
    }
)


def decks_dir() -> Path:
    return _DECKS_DIR


def is_remote_image(path: str) -> bool:
    p = (path or "").strip().lower()
    return p.startswith("http://") or p.startswith("https://")


def resolve_anatomy_image_path(relative: str) -> Path | None:
    """Resolve bundled anatomy asset path (anatomy-assets/…)."""
    if is_remote_image(relative):
        return None
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


def fetch_anatomy_image_bytes(url: str, *, timeout: float = 20.0) -> bytes | None:
    """Download remote anatomy image (HTTPS only, whitelisted hosts)."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_IMAGE_HOSTS:
        return None
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=timeout,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if content_type and not content_type.startswith("image/"):
            return None
        return resp.content
    except requests.RequestException:
        return None


def anatomy_image_url(relative: str) -> str:
    """URL for web UI: local assets via /deck-assets, remote via proxy."""
    rel = (relative or "").strip()
    if is_remote_image(rel):
        return f"/api/image-proxy?url={quote(rel, safe='')}"
    rel = rel.lstrip("/")
    if not rel.startswith(_ASSETS_PREFIX):
        rel = f"{_ASSETS_PREFIX}{rel}"
    return f"/deck-assets/{rel}"


def image_label_from_path(path: str) -> str:
    """Human-readable label from URL or local asset path."""
    name = path.rstrip("/").split("/")[-1]
    name = re.sub(r"^\d+px-", "", name)
    if "?" in name:
        name = name.split("?", 1)[0]
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return stem.replace("_", " ").replace("-", " ")
