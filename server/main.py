from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config_store import AUTO_ADVANCE_MAX_SEC, SESSION_LIMIT_MAX, auto_advance_seconds
from server.services import AppServices

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith((".css", ".js", ".html")):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response


app = FastAPI(title="AI Anki Web", version="1.0")
services = AppServices(ROOT)

app.mount("/static", NoCacheStaticFiles(directory=STATIC), name="static")


class SettingsIn(BaseModel):
    session_limit: int | None = None
    pass_score: int | None = None
    max_follow_ups: int | None = None
    auto_advance_sec: int | None = None
    ollama_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    timeout: int | None = None
    asr_url: str | None = None
    asr_user: str | None = None
    asr_password: str | None = None
    asr_language: str | None = None


class SessionStartIn(BaseModel):
    deck_id: str
    mode: str = "due"


class AnswerIn(BaseModel):
    answer: str


class HintIn(BaseModel):
    draft: str = ""


@app.get("/")
def index() -> FileResponse:
    return FileResponse(
        STATIC / "index.html",
        headers={"Cache-Control": "no-cache, must-revalidate"},
    )


@app.get("/api/decks")
def list_decks() -> dict:
    services.reload_config()
    rows = []
    for entry in services.registry.entries:
        try:
            rows.append(services.deck_summary_row(entry))
        except Exception as exc:  # noqa: BLE001
            rows.append({"deck_id": entry.deck_id, "name": entry.name, "error": str(exc)})
    return {"decks": rows}


@app.get("/api/config")
def get_config() -> dict:
    services.reload_config()
    c = services.config
    return {
        "session_limit": int(c.get("session_limit", 20)),
        "session_limit_max": SESSION_LIMIT_MAX,
        "pass_score": int(c.get("pass_score", 75)),
        "max_follow_ups": int(c.get("max_follow_ups", 2)),
        "auto_advance_sec": auto_advance_seconds(c.get("auto_advance_ms", 10000)),
        "auto_advance_max_sec": AUTO_ADVANCE_MAX_SEC,
        "ollama_url": c.get("ollama_url", ""),
        "model": c.get("model", ""),
        "api_key": c.get("api_key", ""),
        "timeout": int(c.get("timeout", 120)),
        "asr_url": c.get("asr_url", ""),
        "asr_user": c.get("asr_user", ""),
        "asr_password": c.get("asr_password", ""),
        "asr_language": c.get("asr_language", "ru"),
    }


@app.post("/api/config")
def save_config_api(body: SettingsIn) -> dict:
    services.save_settings(body.model_dump(exclude_none=True))
    return {"ok": True}


@app.post("/api/ollama/test")
def test_ollama() -> dict:
    ok, detail = services.test_ollama()
    return {"ok": ok, "detail": detail}


@app.post("/api/session")
def start_session(body: SessionStartIn) -> dict:
    try:
        session = services.start_session(body.deck_id, body.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    card = services.card_payload(session)
    return {
        "session_id": session.id,
        "deck_name": session.deck.name,
        "mode": session.mode.value,
        "empty": card is None,
        "card": card,
        "stats": services.session_stats(session),
    }


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> dict:
    session = services.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    return {
        "deck_name": session.deck.name,
        "card": services.card_payload(session),
        "stats": services.session_stats(session),
        "feedback": session.last_feedback,
        "done": session.finished,
    }


@app.post("/api/session/{session_id}/answer")
def submit_answer(session_id: str, body: AnswerIn) -> dict:
    session = services.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    try:
        return services.submit_answer(session, body.answer)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Ollama: {exc}") from exc


@app.post("/api/session/{session_id}/next")
def next_card(session_id: str) -> dict:
    session = services.sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    return services.next_card(session)


@app.post("/api/session/{session_id}/hint")
def show_hint(session_id: str, body: HintIn | None = None) -> dict:
    session = services.sessions.get(session_id)
    if not session or not session.current:
        raise HTTPException(404, "Подсказка недоступна")
    draft = body.draft if body else ""
    try:
        hint = services.request_hint(session, draft)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Ollama: {exc}") from exc
    if not hint:
        raise HTTPException(404, "Подсказка недоступна")
    return {"hint": hint}


@app.post("/api/asr/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)) -> dict:
    try:
        content = await audio.read()
        text = services.transcribe_audio(content, audio.filename or "recording.webm")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"ASR: {exc}") from exc
    if not text:
        raise HTTPException(502, "ASR вернул пустой текст")
    return {"text": text}
