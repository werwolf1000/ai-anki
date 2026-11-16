"""Модели ИИ: Ollama, OpenAI-совместимые API (DeepSeek, Алиса AI / YandexGPT, Strata по сети) и мост через десктоп.

Провайдер — запись в config.json → llm_providers:
    {"id": "deepseek", "name": "DeepSeek", "type": "openai", "base_url": "https://api.deepseek.com/v1",
     "api_key": "...", "model": "deepseek-chat", "folder": ""}
Встроенный провайдер "ollama" берётся из прежних настроек (ollama_url, model, api_key).
"bridge:<user_id>" — локальная модель на компьютере пользователя: десктоп-приложение забирает запросы
с сервера (/api/bridge/poll), отправляет их в свою модель (например, Strata на 127.0.0.1:8081) и потоком
возвращает ответ — модель не нужно открывать в сеть.

Выбор: llm_check — проверка ответов, подсказки, собеседования (пользователь может выбрать свою: llm_provider);
llm_textbook — статьи учебника, вопросы к учебнику и генерация карточек. Эмбеддинги остаются в Ollama.
"""
from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Iterator

import requests

from app.ollama_client import ChatMessage

PRESETS = [
    {"preset": "deepseek", "name": "DeepSeek", "type": "openai", "base_url": "https://api.deepseek.com/v1",
     "model": "deepseek-chat", "hint": "Ключ — platform.deepseek.com → API keys. Модели: deepseek-chat, deepseek-reasoner."},
    {"preset": "yandex", "name": "Алиса AI (YandexGPT)", "type": "openai", "base_url": "https://llm.api.cloud.yandex.net/v1",
     "model": "gpt://<каталог>/yandexgpt/latest",
     "hint": "Yandex AI Studio: API-ключ сервисного аккаунта и ID каталога (поле «Каталог»). Модель — gpt://<каталог>/<модель>/latest."},
    {"preset": "strata_lan", "name": "Strata (по сети)", "type": "openai", "base_url": "http://192.168.1.10:8081/v1",
     "model": "", "hint": "Strata, запущенный с доступом из сети: strata launch --access lan. Ключ — тот, что показал Strata."},
    {"preset": "openai", "name": "OpenAI-совместимый", "type": "openai", "base_url": "https://…/v1", "model": "",
     "hint": "Любой сервер с /v1/chat/completions: LM Studio, vLLM, llama.cpp server, OpenRouter и т. п."},
]


class LLMError(RuntimeError):
    pass


# ── клиенты ─────────────────────────────────────────────────────────


class ChatClient:
    """Общий интерфейс: stream(messages) → куски текста; chat(ChatMessage...) → весь ответ."""

    label = ""
    model = ""

    def stream(self, messages: list[dict], temperature: float = 0.3) -> Iterator[str]:  # pragma: no cover
        raise NotImplementedError

    def chat(self, messages: list[ChatMessage] | list[dict], temperature: float = 0.3) -> str:
        msgs = [m if isinstance(m, dict) else {"role": m.role, "content": m.content} for m in messages]
        return "".join(self.stream(msgs, temperature))


class OllamaChat(ChatClient):
    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: int = 300, num_ctx: int = 16384) -> None:
        from app.ollama_client import normalize_ollama_url

        self.url = normalize_ollama_url(base_url)
        self.model = model
        self.label = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def stream(self, messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
        with requests.post(
            f"{self.url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": True,
                  "options": {"temperature": temperature, "num_ctx": self.num_ctx}},
            headers=self.headers, timeout=self.timeout, stream=True,
        ) as r:
            if r.status_code == 401:
                raise PermissionError("401 — нужен API-ключ Ollama")
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise LLMError(data["error"])
                piece = data.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if data.get("done"):
                    break


def iter_sse(lines: Iterator[bytes | str]) -> Iterator[str]:
    """Куски текста из потока OpenAI /chat/completions (SSE: data: {...})."""
    for raw in lines:
        if not raw:
            continue
        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            data = json.loads(payload)
        except ValueError:
            continue
        if data.get("error"):
            err = data["error"]
            raise LLMError(err.get("message") if isinstance(err, dict) else str(err))
        for ch in data.get("choices") or []:
            piece = (ch.get("delta") or {}).get("content") or ""
            if piece:
                yield piece


class OpenAIChat(ChatClient):
    """OpenAI-совместимый /chat/completions: DeepSeek, Yandex AI Studio, Strata, LM Studio, vLLM…"""

    def __init__(self, base_url: str, model: str, api_key: str = "", folder: str = "", timeout: int = 300, name: str = "") -> None:
        self.base = base_url.strip().rstrip("/")
        if self.base.endswith("/chat/completions"):
            self.base = self.base[: -len("/chat/completions")]
        self.model = model.strip()
        self.label = f"{name or 'API'} · {self.model}" if self.model else (name or self.base)
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        if api_key.strip():
            self.headers["Authorization"] = f"Bearer {api_key.strip()}"
        if folder.strip():  # Yandex AI Studio: каталог (то же, что project в OpenAI SDK)
            self.headers["OpenAI-Project"] = folder.strip()
            self.headers["x-folder-id"] = folder.strip()

    def stream(self, messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
        body = {"model": self.model, "messages": messages, "temperature": temperature, "stream": True}
        with requests.post(f"{self.base}/chat/completions", json=body, headers=self.headers, timeout=self.timeout, stream=True) as r:
            if r.status_code in (401, 403):
                raise PermissionError(f"{r.status_code} — проверьте API-ключ{' и каталог' if 'x-folder-id' in self.headers else ''}: {r.text[:200]}")
            if r.status_code >= 400:
                raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")
            yield from iter_sse(r.iter_lines())

    def models(self) -> list[str]:
        r = requests.get(f"{self.base}/models", headers=self.headers, timeout=15)
        r.raise_for_status()
        return [m.get("id", "") for m in r.json().get("data", [])]


# ── мост через десктоп-приложение ───────────────────────────────────


@dataclass
class BridgeJob:
    id: str
    payload: dict
    events: queue.Queue = field(default_factory=queue.Queue)
    created: float = field(default_factory=time.time)
    taken: bool = False


@dataclass
class BridgeClient:
    last_seen: float = 0.0
    info: dict = field(default_factory=dict)
    jobs: queue.Queue = field(default_factory=queue.Queue)


class BridgeHub:
    """Очередь запросов к локальным моделям пользователей; десктоп забирает их длинным опросом."""

    ONLINE_SECONDS = 45

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.clients: dict[int, BridgeClient] = {}
        self.jobs: dict[str, BridgeJob] = {}

    def _client(self, user_id: int) -> BridgeClient:
        with self.lock:
            return self.clients.setdefault(user_id, BridgeClient())

    def status(self, user_id: int) -> dict:
        c = self.clients.get(user_id)
        online = bool(c and time.time() - c.last_seen < self.ONLINE_SECONDS)
        return {"online": online, "info": (c.info if c else {}), "queued": c.jobs.qsize() if c else 0}

    def online_users(self) -> dict[int, dict]:
        now = time.time()
        return {uid: c.info for uid, c in self.clients.items() if now - c.last_seen < self.ONLINE_SECONDS}

    def poll(self, user_id: int, info: dict, wait: float = 25.0) -> BridgeJob | None:
        c = self._client(user_id)
        c.last_seen = time.time()
        if info:
            c.info = info
        deadline = time.time() + wait
        while True:
            try:
                job = c.jobs.get(timeout=max(0.1, min(5.0, deadline - time.time())))
            except queue.Empty:
                c.last_seen = time.time()
                if time.time() >= deadline:
                    return None
                continue
            if time.time() - job.created > 600:  # запрос давно никто не ждёт
                continue
            job.taken = True
            c.last_seen = time.time()
            return job

    def push(self, user_id: int, job_id: str, event: dict) -> bool:
        job = self.jobs.get(job_id)
        if job is None or job.payload.get("user_id") != user_id:
            return False
        self._client(user_id).last_seen = time.time()
        job.events.put(event)
        return True

    def stream(self, user_id: int, messages: list[dict], temperature: float, *, first_timeout: float = 600, idle_timeout: float = 180) -> Iterator[str]:
        if not self.status(user_id)["online"]:
            raise LLMError("локальная модель не подключена — откройте десктоп-приложение AI Anki и включите в нём «Локальную модель»")
        job = BridgeJob(id=uuid.uuid4().hex, payload={"user_id": user_id, "messages": messages, "temperature": temperature})
        with self.lock:
            self.jobs[job.id] = job
        self._client(user_id).jobs.put(job)
        got_any = False
        try:
            while True:
                try:
                    ev = job.events.get(timeout=idle_timeout if got_any else first_timeout)
                except queue.Empty as exc:
                    raise LLMError("локальная модель не ответила вовремя") from exc
                if ev.get("error"):
                    raise LLMError(f"локальная модель: {ev['error']}")
                if ev.get("delta"):
                    got_any = True
                    yield ev["delta"]
                if ev.get("done"):
                    return
        finally:
            with self.lock:
                self.jobs.pop(job.id, None)


class BridgeChat(ChatClient):
    def __init__(self, hub: BridgeHub, user_id: int, label: str = "") -> None:
        self.hub = hub
        self.user_id = user_id
        info = hub.status(user_id)["info"]
        self.model = info.get("model", "") or "local"
        self.label = label or f"локальная · {self.model}"

    def stream(self, messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
        yield from self.hub.stream(self.user_id, messages, temperature)


# ── реестр провайдеров ──────────────────────────────────────────────


def providers(config: dict) -> list[dict]:
    """Провайдеры из настроек (без ключей наружу не отдавать — см. public_provider)."""
    out = [{"id": "ollama", "name": "Ollama (сервер)", "type": "ollama", "base_url": config.get("ollama_url", ""),
            "model": config.get("model", ""), "builtin": True}]
    for p in config.get("llm_providers") or []:
        if isinstance(p, dict) and p.get("id") and p.get("id") != "ollama":
            out.append(p)
    return out


def public_provider(p: dict) -> dict:
    q = {k: v for k, v in p.items() if k != "api_key"}
    q["has_key"] = bool(p.get("api_key"))
    return q


def make_client(config: dict, provider_id: str, *, hub: BridgeHub | None, model_override: str = "", timeout: int | None = None,
                user_names: dict[int, str] | None = None) -> ChatClient:
    t = timeout or max(120, int(config.get("timeout", 120)) * 3)
    pid = (provider_id or "ollama").strip()
    if pid.startswith("bridge:"):
        if hub is None:
            raise LLMError("мост к локальным моделям не запущен")
        uid = int(pid.split(":", 1)[1])
        who = (user_names or {}).get(uid, "")
        return BridgeChat(hub, uid, label=f"локальная модель{(' · ' + who) if who else ''}")
    for p in providers(config):
        if p["id"] != pid:
            continue
        if p["type"] == "ollama":
            return OllamaChat(config.get("ollama_url", ""), model_override or config.get("model", ""), config.get("api_key", ""), timeout=t)
        return OpenAIChat(p.get("base_url", ""), model_override or p.get("model", ""), p.get("api_key", ""), p.get("folder", ""),
                          timeout=int(p.get("timeout") or t), name=p.get("name", ""))
    raise LLMError(f"провайдер «{pid}» не найден — выберите модель в настройках")


# ── API ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402


class ProviderIn(BaseModel):
    id: str = ""
    name: str
    type: str = "openai"
    base_url: str
    api_key: str | None = None  # пусто при правке — оставить прежний ключ
    model: str = ""
    folder: str = ""
    timeout: int | None = None


class TestIn(BaseModel):
    provider: str
    model: str = ""


class SelectIn(BaseModel):
    check: str | None = None
    textbook: str | None = None
    my: str | None = None


class BridgePollIn(BaseModel):
    info: dict = {}
    wait: float = 25.0


class BridgePushIn(BaseModel):
    delta: str = ""
    done: bool = False
    error: str = ""


def build_router(services, current_ctx) -> APIRouter:
    import re as _re
    import time as _time

    r = APIRouter()
    hub: BridgeHub = services.bridge

    def admin(ctx=Depends(current_ctx)):
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        return ctx

    def names() -> dict[int, str]:
        fn = getattr(services, "user_name", None)
        return {uid: fn(uid) for uid in hub.online_users()} if fn else {}

    @r.get("/api/llm")
    def state(ctx=Depends(current_ctx)) -> dict:
        cfg = services.config
        provs = providers(cfg)
        out = {
            "providers": [
                public_provider(p) if ctx.user.is_admin else {"id": p["id"], "name": p["name"], "model": p.get("model", "")}
                for p in provs
            ],
            "check": cfg.get("llm_check", "") or "ollama",
            "textbook": cfg.get("llm_textbook", "") or "ollama",
            "my": ctx.settings.get("llm_provider", "") or "",
            "bridge": hub.status(ctx.user.id),
        }
        if ctx.user.is_admin:
            online = hub.online_users()
            out["presets"] = PRESETS
            out["bridges"] = [{"id": f"bridge:{uid}", "user": n, "info": online.get(uid, {})} for uid, n in names().items()]
        return out

    @r.post("/api/llm/providers")
    def upsert(body: ProviderIn, ctx=Depends(admin)) -> dict:
        if body.type != "openai":
            raise HTTPException(400, "Поддерживается тип openai (OpenAI-совместимый API)")
        if not _re.match(r"^https?://", body.base_url.strip()):
            raise HTTPException(400, "Адрес должен начинаться с http:// или https://")
        lst = [p for p in (services.config.get("llm_providers") or []) if isinstance(p, dict)]
        pid = body.id.strip() or _re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-") or "provider"
        if pid == "ollama" or pid.startswith("bridge"):
            raise HTTPException(400, "Недопустимый id")
        old = next((p for p in lst if p.get("id") == pid), None)
        if old is None and body.id:
            raise HTTPException(404, "Провайдер не найден")
        if old is None:
            base, n = pid, 2
            while any(p.get("id") == pid for p in lst):
                pid, n = f"{base}-{n}", n + 1
        rec = {
            "id": pid, "name": body.name.strip(), "type": body.type, "base_url": body.base_url.strip().rstrip("/"),
            "model": body.model.strip(), "folder": body.folder.strip(),
            "api_key": body.api_key.strip() if body.api_key else (old or {}).get("api_key", ""),
        }
        if body.timeout:
            rec["timeout"] = int(body.timeout)
        lst = [rec if p.get("id") == pid else p for p in lst] if old else lst + [rec]
        services.update_global({"llm_providers": lst})
        return {"ok": True, "id": pid}

    @r.delete("/api/llm/providers/{pid}")
    def remove(pid: str, ctx=Depends(admin)) -> dict:
        lst = [p for p in (services.config.get("llm_providers") or []) if isinstance(p, dict) and p.get("id") != pid]
        patch: dict = {"llm_providers": lst}
        for key in ("llm_check", "llm_textbook"):
            if services.config.get(key) == pid:
                patch[key] = "ollama"
        services.update_global(patch)
        return {"ok": True}

    @r.post("/api/llm/select")
    def select(body: SelectIn, ctx=Depends(current_ctx)) -> dict:
        valid = {p["id"] for p in providers(services.config)}
        if body.my is not None:  # своя модель для проверки ответов в занятиях — любой пользователь
            if body.my not in ("", "bridge:me") and body.my not in valid:
                raise HTTPException(400, "Нет такой модели")
            services.save_settings(ctx, {"llm_provider": body.my})
        patch = {}
        for key, val in (("llm_check", body.check), ("llm_textbook", body.textbook)):
            if val is None:
                continue
            if not ctx.user.is_admin:
                raise HTTPException(403, "Только для администратора")
            if val not in valid and not (val.startswith("bridge:") and val[7:].isdigit()):
                raise HTTPException(400, "Нет такой модели")
            patch[key] = val
        if patch:
            services.update_global(patch)
        return {"ok": True}

    @r.post("/api/llm/test")
    def test(body: TestIn, ctx=Depends(current_ctx)) -> dict:
        pid = body.provider
        if pid == "bridge:me":
            pid = f"bridge:{ctx.user.id}"
        elif pid.startswith("bridge:") and not ctx.user.is_admin and pid != f"bridge:{ctx.user.id}":
            raise HTTPException(403, "Чужая локальная модель")
        elif not pid.startswith("bridge:") and not ctx.user.is_admin and pid not in {p["id"] for p in providers(services.config)}:
            raise HTTPException(404, "Нет такой модели")
        t0 = _time.time()
        try:
            client = make_client(services.config, pid, hub=hub, model_override=body.model, timeout=120, user_names=names())
            text = client.chat([{"role": "user", "content": "Ответь одним словом по-русски: готово"}], temperature=0)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:400], "ms": int((_time.time() - t0) * 1000)}
        text = _re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        return {"ok": True, "text": text[:200], "model": client.label, "ms": int((_time.time() - t0) * 1000)}

    @r.post("/api/llm/models")
    def models(body: TestIn, ctx=Depends(admin)) -> dict:
        try:
            if body.provider == "ollama":
                from app.ollama_client import normalize_ollama_url

                c = services.config
                headers = {"Authorization": f"Bearer {c['api_key']}"} if c.get("api_key") else {}
                data = requests.get(f"{normalize_ollama_url(c['ollama_url'])}/api/tags", headers=headers, timeout=15).json()
                return {"models": [m.get("name", "") for m in data.get("models", [])]}
            client = make_client(services.config, body.provider, hub=hub)
            return {"models": client.models() if isinstance(client, OpenAIChat) else []}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Не удалось получить список моделей: {exc}") from exc

    # — мост: десктоп-приложение забирает запросы и возвращает ответ своей модели —

    @r.post("/api/bridge/poll")
    def bridge_poll(body: BridgePollIn, ctx=Depends(current_ctx)) -> dict:
        job = hub.poll(ctx.user.id, body.info, wait=max(1.0, min(30.0, body.wait)))
        if job is None:
            return {"job": None}
        return {"job": {"id": job.id, "messages": job.payload["messages"], "temperature": job.payload["temperature"]}}

    @r.post("/api/bridge/jobs/{job_id}")
    def bridge_push(job_id: str, body: BridgePushIn, ctx=Depends(current_ctx)) -> dict:
        return {"ok": hub.push(ctx.user.id, job_id, {"delta": body.delta, "done": body.done, "error": body.error})}

    @r.get("/api/bridge/status")
    def bridge_status(ctx=Depends(current_ctx)) -> dict:
        return hub.status(ctx.user.id)

    return r
