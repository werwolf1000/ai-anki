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
    initial_prompt: str = "",
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

    if initial_prompt.strip():
        # подсказка Whisper: контекст и термины, чтобы «SQL» не превращался в «эсквель»
        for params in params_variants:
            params["initial_prompt"] = initial_prompt.strip()[:600]

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


_TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.+#/-]*[A-Za-z0-9+#]|[A-Z]{2,}")


def build_initial_prompt(context: str, max_chars: int = 500) -> str:
    """Подсказка для Whisper: начало вопроса и латинские термины из него."""
    context = " ".join((context or "").split())
    if not context:
        return ""
    terms = []
    for t in _TERM_RE.findall(context):
        if t.lower() not in {x.lower() for x in terms} and len(terms) < 25:
            terms.append(t)
    head = context[:300]
    prompt = f"Ответ на вопрос: {head}"
    if terms:
        prompt += f" Термины: {', '.join(terms)}."
    return prompt[:max_chars]


def transcribe_segments(
    base_url: str,
    audio_bytes: bytes,
    filename: str,
    *,
    language: str = "",
    login: str = "",
    password: str = "",
    initial_prompt: str = "",
    timeout: int = 1800,
) -> tuple[list[dict], str]:
    """Расшифровка с таймкодами: ([{start, end, text}], язык). Пустой language — автоопределение."""
    params = {"encode": "true", "task": "transcribe", "output": "json"}
    if language.strip():
        params["language"] = language.strip()
    if initial_prompt.strip():
        params["initial_prompt"] = initial_prompt.strip()[:600]
    safe_name = re.sub(r"[^\w.\-]+", "_", filename or "audio.mp3") or "audio.mp3"
    response = requests.post(
        f"{normalize_asr_url(base_url)}/asr",
        params=params,
        files={"audio_file": (safe_name, audio_bytes)},
        timeout=timeout,
        auth=_auth(login, password),
    )
    if response.status_code != 200:
        raise RuntimeError(f"ASR HTTP {response.status_code}: {response.text[:200]}")
    data = response.json()
    segments = []
    for seg in data.get("segments") or []:
        text = str(seg.get("text", "")).strip()
        if text:
            segments.append({"start": float(seg.get("start", 0)), "end": float(seg.get("end", 0)), "text": text})
    if not segments and str(data.get("text", "")).strip():
        segments.append({"start": 0.0, "end": 0.0, "text": str(data["text"]).strip()})
    return segments, str(data.get("language") or language or "")
