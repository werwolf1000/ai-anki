from __future__ import annotations

import re

import requests
from requests.auth import HTTPBasicAuth


def normalize_asr_url(url: str) -> str:
    return url.strip().rstrip("/")


def _auth(login: str, password: str) -> HTTPBasicAuth | None:
    login = login.strip()
    password = password.strip()
    if login and password:
        return HTTPBasicAuth(login, password)
    return None


def _text_from_response(data: dict) -> str:
    if isinstance(data.get("text"), str) and data["text"].strip():
        return data["text"].strip()
    segments = data.get("segments")
    if isinstance(segments, list) and segments:
        parts = [str(seg.get("text", "")).strip() for seg in segments if str(seg.get("text", "")).strip()]
        if parts:
            return " ".join(parts)
    return ""


def transcribe_whisper(
    base_url: str,
    audio_bytes: bytes,
    filename: str,
    *,
    language: str = "ru",
    login: str = "",
    password: str = "",
    timeout: int | None = None,
) -> str:
    if not audio_bytes:
        raise ValueError("Пустой аудиофайл")
    url = f"{normalize_asr_url(base_url)}/asr"
    auth = _auth(login, password)
    size_mb = len(audio_bytes) / (1024 * 1024)
    req_timeout = timeout or max(120, int(size_mb * 45 + 60))

    params_variants = [
        {
            "encode": "true",
            "task": "transcribe",
            "language": language or "ru",
            "output": "json",
            "vad_filter": "false",
        },
        {
            "encode": "true",
            "task": "transcribe",
            "language": language or "ru",
            "output": "json",
        },
    ]

    last_error: Exception | None = None
    safe_name = re.sub(r"[^\w.\-]+", "_", filename or "recording.webm") or "recording.webm"

    for params in params_variants:
        try:
            response = requests.post(
                url,
                params=params,
                files={"audio_file": (safe_name, audio_bytes)},
                timeout=req_timeout,
                auth=auth,
            )
            if response.status_code != 200:
                raise RuntimeError(f"ASR HTTP {response.status_code}: {response.text[:200]}")
            data = response.json()
            text = _text_from_response(data)
            if text:
                return text
            raise RuntimeError("ASR вернул пустой текст")
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    raise RuntimeError(f"Ошибка распознавания речи: {last_error}")
