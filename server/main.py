from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from app.anatomy_image import _ALLOWED_IMAGE_HOSTS, _USER_AGENT
from server.auth import AuthError, User, UserStore
from server.services import AppServices, UserContext

ROOT = Path(__file__).resolve().parent.parent
DIST = Path(os.environ.get("AI_ANKI_WEB_DIST") or ROOT / "web" / "dist")

# open — регистрация открыта всем; closed — только первый пользователь (админ)
REGISTRATION = os.environ.get("AI_ANKI_REGISTRATION", "open").strip().lower()


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        else:
            # файлы сборки Vite содержат хэш в имени
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


app = FastAPI(title="AI Anki", version="2.0")
services = AppServices(ROOT)
users = UserStore(services.data_dir / "users.db")

# Electron-клиент ходит с origin app://, авторизация — только через Bearer-токен (без cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

if (DIST / "assets").is_dir():
    app.mount("/assets", NoCacheStaticFiles(directory=DIST / "assets"), name="assets")


# ── модели запросов ─────────────────────────────────────────────────


class RegisterIn(BaseModel):
    username: str
    password: str
    display_name: str = ""
    client: str = "web"


class LoginIn(BaseModel):
    username: str
    password: str
    client: str = "web"


class PasswordIn(BaseModel):
    old_password: str
    new_password: str


class ProfileIn(BaseModel):
    display_name: str


class SettingsIn(BaseModel):
    session_limit: int | None = None
    pass_score: int | None = None
    max_follow_ups: int | None = None
    auto_advance_sec: int | None = None
    code_editor_theme: str | None = None
    asr_language: str | None = None
    ollama_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    timeout: int | None = None
    asr_url: str | None = None
    asr_user: str | None = None
    asr_password: str | None = None


class SessionStartIn(BaseModel):
    deck_id: str
    mode: str = "due"
    topic: str | None = None


class AnswerIn(BaseModel):
    answer: str


class HintIn(BaseModel):
    draft: str = ""


# ── авторизация ─────────────────────────────────────────────────────


def _bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else ""


def current_user(authorization: str | None = Header(default=None)) -> User:
    user = users.user_for_token(_bearer(authorization))
    if user is None:
        raise HTTPException(401, "Требуется вход в аккаунт")
    return user


def current_ctx(user: User = Depends(current_user)) -> UserContext:
    return services.context(user)


def _auth_response(user: User, client: str) -> dict:
    token = users.issue_token(user.id, client)
    return {"token": token, "user": user.public()}


@app.get("/api/auth/status")
def auth_status() -> dict:
    has_users = users.count() > 0
    return {
        "has_users": has_users,
        "registration_open": REGISTRATION != "closed" or not has_users,
        "version": app.version,
    }


@app.post("/api/auth/register")
def register(body: RegisterIn) -> dict:
    first = users.count() == 0
    if REGISTRATION == "closed" and not first:
        raise HTTPException(403, "Регистрация закрыта администратором")
    try:
        user = users.register(body.username, body.password, body.display_name)
    except AuthError as exc:
        raise HTTPException(400, str(exc)) from exc
    if user.is_admin:
        services.adopt_legacy_data(user)
    return _auth_response(user, body.client)


@app.post("/api/auth/login")
def login(body: LoginIn) -> dict:
    user = users.authenticate(body.username, body.password)
    if user is None:
        time.sleep(0.4)
        raise HTTPException(401, "Неверный логин или пароль")
    return _auth_response(user, body.client)


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    users.revoke(_bearer(authorization))
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"user": user.public()}


@app.post("/api/account/password")
def change_password(body: PasswordIn, user: User = Depends(current_user)) -> dict:
    try:
        users.change_password(user.id, body.old_password, body.new_password)
    except AuthError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True}


@app.post("/api/account/profile")
def update_profile(body: ProfileIn, user: User = Depends(current_user)) -> dict:
    users.update_profile(user.id, body.display_name)
    updated = users.get(user.id)
    return {"user": updated.public() if updated else user.public()}


# ── публичные ресурсы (картинки карточек) ───────────────────────────


@app.get("/deck-assets/{asset_path:path}")
def deck_asset(asset_path: str) -> FileResponse:
    assets_root = (ROOT / "decks" / "anatomy-assets").resolve()
    full = (ROOT / "decks" / asset_path).resolve()
    if not str(full).startswith(str(assets_root)) or not full.is_file():
        raise HTTPException(404, "Изображение не найдено")
    media = "image/svg+xml" if full.suffix.lower() == ".svg" else "application/octet-stream"
    return FileResponse(full, media_type=media, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/image-proxy")
def image_proxy(url: str) -> Response:
    """Прокси для разрешённых внешних изображений (User-Agent, кэширование)."""
    target = unquote(url).strip()
    parsed = urlparse(target)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_IMAGE_HOSTS:
        raise HTTPException(400, "URL изображения не разрешён")
    try:
        resp = requests.get(target, headers={"User-Agent": _USER_AGENT}, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(502, f"Не удалось загрузить изображение: {exc}") from exc
    content_type = resp.headers.get("content-type", "application/octet-stream")
    if not content_type.startswith("image/"):
        raise HTTPException(502, "Ответ не является изображением")
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ── настройки ───────────────────────────────────────────────────────


@app.get("/api/config")
def get_config(ctx: UserContext = Depends(current_ctx)) -> dict:
    return services.config_payload(ctx)


@app.post("/api/config")
def save_config_api(body: SettingsIn, ctx: UserContext = Depends(current_ctx)) -> dict:
    services.save_settings(ctx, body.model_dump(exclude_none=True))
    return {"ok": True, "config": services.config_payload(ctx)}


@app.post("/api/ollama/test")
def test_ollama(ctx: UserContext = Depends(current_ctx)) -> dict:
    ok, detail = services.test_ollama()
    return {"ok": ok, "detail": detail}


# ── колоды и статистика ─────────────────────────────────────────────


@app.get("/api/decks")
def list_decks(ctx: UserContext = Depends(current_ctx)) -> dict:
    return {"decks": services.list_decks(ctx)}


@app.get("/api/dashboard")
def dashboard(ctx: UserContext = Depends(current_ctx)) -> dict:
    return services.dashboard(ctx)


@app.get("/api/deck/{deck_id}/topics")
def deck_topics(deck_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
    try:
        return services.deck_topics(ctx, deck_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# ── учебная сессия ──────────────────────────────────────────────────


def _session(ctx: UserContext, session_id: str):
    session = services.get_session(ctx, session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена — начните заново")
    return session


@app.post("/api/session")
def start_session(body: SessionStartIn, ctx: UserContext = Depends(current_ctx)) -> dict:
    try:
        session = services.start_session(ctx, body.deck_id, body.mode, topic=body.topic)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    card = services.card_payload(ctx, session)
    return {
        "session_id": session.id,
        "deck_id": body.deck_id,
        "deck_name": services.session_display_name(session),
        "mode": session.mode.value,
        "topic": session.topic,
        "empty": card is None,
        "card": card,
        "stats": services.session_stats(ctx, session),
    }


@app.get("/api/session/{session_id}")
def get_session(session_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
    session = _session(ctx, session_id)
    return {
        "deck_name": services.session_display_name(session),
        "card": services.card_payload(ctx, session),
        "stats": services.session_stats(ctx, session),
        "feedback": session.last_feedback,
        "done": session.finished,
    }


@app.post("/api/session/{session_id}/answer")
def submit_answer(session_id: str, body: AnswerIn, ctx: UserContext = Depends(current_ctx)) -> dict:
    session = _session(ctx, session_id)
    try:
        return services.submit_answer(ctx, session, body.answer)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Ollama: {exc}") from exc


@app.post("/api/session/{session_id}/next")
def next_card(session_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
    return services.next_card(ctx, _session(ctx, session_id))


@app.post("/api/session/{session_id}/hint")
def show_hint(session_id: str, body: HintIn | None = None, ctx: UserContext = Depends(current_ctx)) -> dict:
    session = _session(ctx, session_id)
    if not session.current:
        raise HTTPException(404, "Подсказка недоступна")
    try:
        hint = services.request_hint(session, body.draft if body else "")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Ollama: {exc}") from exc
    if not hint:
        raise HTTPException(404, "Подсказка недоступна")
    return {"hint": hint}


@app.post("/api/asr/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), ctx: UserContext = Depends(current_ctx)) -> dict:
    try:
        content = await audio.read()
        text = services.transcribe_audio(ctx, content, audio.filename or "recording.webm")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"ASR: {exc}") from exc
    if not text:
        raise HTTPException(502, "ASR вернул пустой текст")
    return {"text": text}


from server.textbook import build_router  # noqa: E402

app.include_router(build_router(services, current_ctx))


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


# ── SPA ─────────────────────────────────────────────────────────────


def _spa_index() -> Response:
    index = DIST / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>AI Anki</h1><p>Фронтенд не собран: выполните <code>npm run build</code> в каталоге web/.</p>",
            status_code=503,
        )
    return FileResponse(index, headers={"Cache-Control": "no-cache, must-revalidate"})


@app.get("/")
def index() -> Response:
    return _spa_index()


@app.get("/{name}")
def root_files(name: str) -> Response:
    """Файлы из web/public (favicon и т.п.) и fallback на SPA."""
    if name.startswith("api"):
        raise HTTPException(404)
    candidate = (DIST / name).resolve()
    if candidate.parent == DIST.resolve() and candidate.is_file():
        return FileResponse(candidate)
    return _spa_index()
