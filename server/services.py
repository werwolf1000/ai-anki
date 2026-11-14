from __future__ import annotations

import shutil
import threading
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.anatomy_image import anatomy_image_url
from app.config_store import (
    AUTO_ADVANCE_MAX_SEC,
    clamp_auto_advance_ms,
    clamp_session_limit,
    custom_decks_dir,
    data_dir,
    load_config,
    normalize_code_editor_theme,
    save_config,
)
from app.deck import Card, ChatMessage, Deck
from app.live_coding import has_topic_picker_deck, topic_summaries
from app.ollama_client import AnswerEvaluator, OllamaClient
from app.progress import ProgressStore, StudyMode
from app.registry import DeckEntry, DeckRegistry
from server.auth import User
from server.knowledge import KnowledgeIndexer, KnowledgeStore, OllamaRag

# Настройки, которые каждый пользователь задаёт сам
USER_KEYS = (
    "session_limit",
    "pass_score",
    "max_follow_ups",
    "auto_advance_ms",
    "code_editor_theme",
    "asr_language",
    "asr_correct",
)
# Общие настройки сервера — меняет только администратор
GLOBAL_KEYS = (
    "ollama_url",
    "model",
    "api_key",
    "timeout",
    "asr_url",
    "asr_user",
    "asr_password",
    "embed_model",
    "textbook_model",
)


@dataclass
class StudySession:
    id: str
    user_id: int
    deck: Deck
    mode: StudyMode
    topic: str = ""
    queue: list[Card] = field(default_factory=list)
    index: int = 0
    chat_history: list[ChatMessage] = field(default_factory=list)
    awaiting_follow_up: bool = False
    follow_up_count: int = 0
    revision_count: int = 0
    pending_finalize: bool = False
    last_review: dict | None = None
    last_feedback: str = ""
    cached_hint: str = ""
    answered: int = 0
    passed: int = 0
    scores: list[int] = field(default_factory=list)
    initial_size: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current(self) -> Card | None:
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

    @property
    def finished(self) -> bool:
        return self.index >= len(self.queue)


@dataclass
class UserContext:
    """Данные одного пользователя: прогресс SRS и личные настройки."""

    user: User
    dir: Path
    progress: ProgressStore
    settings: dict
    lock: threading.RLock = field(default_factory=threading.RLock)

    def save_settings(self) -> None:
        import json

        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "settings.json").write_text(
            json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )


class AppServices:
    SESSION_TTL = timedelta(hours=12)

    def __init__(self, root: Path) -> None:
        self.root = root
        dd = data_dir()
        dd.mkdir(parents=True, exist_ok=True)
        self.data_dir = dd
        self.users_dir = dd / "users"
        self.config, self.config_path = load_config(root)
        self.registry = DeckRegistry(dd / "decks.json", root / "decks", custom_decks_dir())
        self.registry.load()
        self.sessions: dict[str, StudySession] = {}
        self._contexts: dict[int, UserContext] = {}
        self._ctx_lock = threading.Lock()
        self._deck_cache: dict[str, tuple[tuple, Deck]] = {}
        self.knowledge = KnowledgeStore(dd / "knowledge.db")
        self.indexer = KnowledgeIndexer(self.knowledge)

    def rag_client(self) -> OllamaRag:
        return OllamaRag(self.config["ollama_url"], self.config.get("api_key", ""), timeout=max(120, int(self.config.get("timeout", 120)) * 3))

    def textbook_model(self) -> str:
        return (self.config.get("textbook_model") or "").strip() or self.config["model"]

    def embed_model(self) -> str:
        return (self.config.get("embed_model") or "").strip() or "qwen3-embedding:8b"

    # ── конфигурация ────────────────────────────────────────────────

    def reload_config(self) -> None:
        self.config, self.config_path = load_config(self.root)
        self.registry.load()

    def effective_config(self, ctx: UserContext) -> dict:
        cfg = dict(self.config)
        cfg["code_editor_theme"] = "dark"  # по умолчанию под тёмный интерфейс
        for key in USER_KEYS:
            if key in ctx.settings:
                cfg[key] = ctx.settings[key]
        cfg["session_limit"] = clamp_session_limit(cfg.get("session_limit", 20))
        cfg["auto_advance_ms"] = clamp_auto_advance_ms(cfg.get("auto_advance_ms", 10000))
        cfg["code_editor_theme"] = normalize_code_editor_theme(cfg.get("code_editor_theme"))
        return cfg

    def pass_score(self, ctx: UserContext) -> int:
        return int(self.effective_config(ctx).get("pass_score", 75))

    def max_follow_ups(self, ctx: UserContext) -> int:
        return int(self.effective_config(ctx).get("max_follow_ups", 2))

    def evaluator(self) -> AnswerEvaluator:
        c = self.config
        client = OllamaClient(
            c["ollama_url"],
            c["model"],
            timeout=int(c.get("timeout", 120)),
            api_key=c.get("api_key", ""),
        )
        return AnswerEvaluator(client)

    def config_payload(self, ctx: UserContext) -> dict:
        c = self.effective_config(ctx)
        payload = {
            "session_limit": int(c.get("session_limit", 20)),
            "session_limit_max": 50,
            "pass_score": int(c.get("pass_score", 75)),
            "max_follow_ups": int(c.get("max_follow_ups", 2)),
            "auto_advance_sec": int(c.get("auto_advance_ms", 10000)) // 1000,
            "auto_advance_max_sec": AUTO_ADVANCE_MAX_SEC,
            "code_editor_theme": c.get("code_editor_theme", "dark"),
            "asr_language": c.get("asr_language", "ru"),
            "asr_correct": bool(c.get("asr_correct", True)),
            "model": c.get("model", ""),
            "asr_enabled": bool(str(c.get("asr_url", "")).strip()),
            "is_admin": ctx.user.is_admin,
        }
        if ctx.user.is_admin:
            for key in GLOBAL_KEYS:
                payload[key] = c.get(key, "")
            payload["timeout"] = int(c.get("timeout", 120))
        return payload

    def save_settings(self, ctx: UserContext, payload: dict) -> None:
        with ctx.lock:
            for key in USER_KEYS:
                if key in payload:
                    ctx.settings[key] = payload[key]
            if "auto_advance_sec" in payload:
                ctx.settings["auto_advance_ms"] = int(payload["auto_advance_sec"]) * 1000
            if "session_limit" in ctx.settings:
                ctx.settings["session_limit"] = clamp_session_limit(ctx.settings["session_limit"])
            if "auto_advance_ms" in ctx.settings:
                ctx.settings["auto_advance_ms"] = clamp_auto_advance_ms(ctx.settings["auto_advance_ms"])
            ctx.save_settings()
        if ctx.user.is_admin:
            changed = False
            for key in GLOBAL_KEYS:
                if key in payload:
                    self.config[key] = payload[key]
                    changed = True
            if changed:
                save_config(self.config_path, self.config)
                self.reload_config()

    def test_ollama(self) -> tuple[bool, str]:
        client = OllamaClient(
            self.config["ollama_url"],
            self.config["model"],
            timeout=int(self.config.get("timeout", 120)),
            api_key=self.config.get("api_key", ""),
        )
        return client.health()

    # ── пользователи ────────────────────────────────────────────────

    def context(self, user: User) -> UserContext:
        with self._ctx_lock:
            ctx = self._contexts.get(user.id)
            if ctx is not None:
                ctx.user = user
                return ctx
            import json

            udir = self.users_dir / str(user.id)
            udir.mkdir(parents=True, exist_ok=True)
            settings_path = udir / "settings.json"
            settings = {}
            if settings_path.exists():
                try:
                    settings = json.loads(settings_path.read_text(encoding="utf-8"))
                except ValueError:
                    settings = {}
            progress = ProgressStore(udir / "progress.json")
            progress.load()
            self.registry.migrate_progress(progress)
            ctx = UserContext(user=user, dir=udir, progress=progress, settings=settings)
            self._contexts[user.id] = ctx
            return ctx

    def adopt_legacy_data(self, user: User) -> bool:
        """Первому пользователю (админу) достаётся прогресс однопользовательской версии."""
        legacy = self.data_dir / "progress.json"
        udir = self.users_dir / str(user.id)
        target = udir / "progress.json"
        if not legacy.exists() or target.exists():
            return False
        udir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, target)
        return True

    # ── колоды ──────────────────────────────────────────────────────

    def load_deck(self, entry: DeckEntry) -> Deck:
        stamp = []
        for p in entry.paths:
            try:
                stamp.append((p, Path(p).stat().st_mtime_ns))
            except OSError:
                stamp.append((p, 0))
        key = tuple(stamp)
        cached = self._deck_cache.get(entry.deck_id)
        if cached and cached[0] == key:
            return cached[1]
        deck = self.registry.load_deck(entry)
        self._deck_cache[entry.deck_id] = (key, deck)
        return deck

    def deck_summary_row(self, ctx: UserContext, entry: DeckEntry) -> dict:
        deck = self.load_deck(entry)
        ps = self.pass_score(ctx)
        with ctx.lock:
            ctx.progress.reconcile_deck(deck, ps)
            s = ctx.progress.summary(deck, ps)
        topics = sorted({c.topic for c in deck.cards if c.topic})
        return {
            "deck_id": entry.deck_id,
            "name": entry.name,
            "kind": self._deck_kind(entry, deck),
            "language": deck.language,
            "is_live_coding": entry.is_live_coding,
            "is_math": entry.is_math,
            "has_topics": has_topic_picker_deck(deck),
            "topics_count": len(topics),
            "total": s.total,
            "mastered": s.mastered,
            "passed_today": s.passed_today,
            "due": s.due,
            "new": s.new,
            "weak": s.weak,
            "avg_score": s.avg_score,
            "studied": s.studied,
            "last_reviewed_at": s.last_reviewed_at,
        }

    @staticmethod
    def _deck_kind(entry: DeckEntry, deck: Deck) -> str:
        if entry.is_live_coding:
            return "live"
        if entry.is_math:
            return "math"
        if any(c.is_anatomy for c in deck.cards[:5]):
            return "anatomy"
        if deck.language:
            return "code"
        return "theory"

    def list_decks(self, ctx: UserContext) -> list[dict]:
        rows = []
        for entry in self.registry.entries:
            try:
                rows.append(self.deck_summary_row(ctx, entry))
            except Exception as exc:  # noqa: BLE001
                rows.append({"deck_id": entry.deck_id, "name": entry.name, "error": str(exc)})
        return rows

    def deck_topics(self, ctx: UserContext, deck_id: str) -> dict:
        entry = self.registry.get(deck_id)
        if not entry:
            raise ValueError("Колода не найдена")
        deck = self.load_deck(entry)
        if not has_topic_picker_deck(deck):
            raise ValueError("У этой колоды нет тем для выбора")
        ps = self.pass_score(ctx)
        with ctx.lock:
            ctx.progress.reconcile_deck(deck, ps)
            topics = topic_summaries(deck, ctx.progress, pass_score=ps)
        return {"deck_id": deck_id, "name": entry.name, "topics": topics}

    # ── статистика для дашборда ─────────────────────────────────────

    def dashboard(self, ctx: UserContext, days: int = 28) -> dict:
        ps = self.pass_score(ctx)
        today = datetime.now().astimezone().date()
        start = today - timedelta(days=days - 1)
        answered: Counter = Counter()
        passed: Counter = Counter()
        score_sum: Counter = Counter()
        total_answers = 0
        with ctx.lock:
            for cards in ctx.progress.data.values():
                for prog in cards.values():
                    for rec in prog.history:
                        if rec.is_follow_up and not rec.finalized:
                            continue
                        try:
                            day = datetime.fromisoformat(rec.at.replace("Z", "+00:00")).astimezone().date()
                        except ValueError:
                            continue
                        total_answers += 1
                        if day < start:
                            continue
                        answered[day] += 1
                        score_sum[day] += rec.score
                        if rec.score >= ps:
                            passed[day] += 1
        series = []
        for i in range(days):
            d = start + timedelta(days=i)
            n = answered[d]
            series.append(
                {
                    "date": d.isoformat(),
                    "answered": n,
                    "passed": passed[d],
                    "avg_score": round(score_sum[d] / n, 1) if n else None,
                }
            )
        streak = 0
        d = today if answered[today] else today - timedelta(days=1)
        while answered.get(d, 0) > 0:
            streak += 1
            d -= timedelta(days=1)
        week = series[-7:]
        week_n = sum(x["answered"] for x in week)
        week_scores = sum(score_sum[start + timedelta(days=days - 7 + i)] for i in range(7))
        return {
            "activity": series,
            "streak": streak,
            "total_answers": total_answers,
            "week_answers": week_n,
            "week_avg_score": round(week_scores / week_n, 1) if week_n else None,
            "pass_score": ps,
        }

    # ── учебные сессии ──────────────────────────────────────────────

    def _gc_sessions(self) -> None:
        now = datetime.now(timezone.utc)
        for sid in [s for s, v in self.sessions.items() if now - v.created_at > self.SESSION_TTL]:
            self.sessions.pop(sid, None)

    def get_session(self, ctx: UserContext, session_id: str) -> StudySession | None:
        s = self.sessions.get(session_id)
        if s is None or s.user_id != ctx.user.id:
            return None
        return s

    def start_session(
        self, ctx: UserContext, deck_id: str, mode: str, *, topic: str | None = None
    ) -> StudySession:
        self._gc_sessions()
        entry = self.registry.get(deck_id)
        if not entry:
            raise ValueError("Колода не найдена")
        try:
            study_mode = StudyMode(mode)
        except ValueError as exc:
            raise ValueError(f"Неизвестный режим: {mode}") from exc
        deck = self.load_deck(entry)
        ps = self.pass_score(ctx)
        cfg = self.effective_config(ctx)
        with ctx.lock:
            ctx.progress.reconcile_deck(deck, ps)
            topic = (topic or "").strip()
            if has_topic_picker_deck(deck) and topic:
                known = {row["name"] for row in topic_summaries(deck, ctx.progress, pass_score=ps)}
                if topic not in known:
                    raise ValueError(f"Неизвестная тема: {topic}")
            queue = ctx.progress.build_queue(
                deck,
                study_mode,
                pass_score=ps,
                limit=clamp_session_limit(cfg.get("session_limit", 20)),
                topic=topic or None,
            )
        sid = uuid.uuid4().hex
        session = StudySession(
            id=sid, user_id=ctx.user.id, deck=deck, mode=study_mode, topic=topic, queue=queue,
            initial_size=len(queue),
        )
        self.sessions[sid] = session
        return session

    def session_stats(self, ctx: UserContext, session: StudySession) -> dict:
        with ctx.lock:
            s = ctx.progress.summary(session.deck, self.pass_score(ctx))
        return {
            "passed_today": s.passed_today,
            "mastered": s.mastered,
            "total": s.total,
            "due": s.due,
            "queue": len(session.queue),
            "index": min(session.index + 1, len(session.queue)) if session.queue else 0,
            "initial": session.initial_size,
            "remaining": max(0, len(session.queue) - session.index),
            "answered": session.answered,
            "passed": session.passed,
            "avg_score": round(sum(session.scores) / len(session.scores), 1) if session.scores else None,
        }

    def session_display_name(self, session: StudySession) -> str:
        if session.topic:
            return f"{session.deck.name} · {session.topic}"
        return session.deck.name

    def card_payload(self, ctx: UserContext, session: StudySession) -> dict | None:
        card = session.current
        if not card:
            return None
        with ctx.lock:
            prog = ctx.progress.get(session.deck, card.id)
        image = ""
        if card.image.strip():
            image = anatomy_image_url(card.image)
            if not image.startswith(("http", "/")):
                image = "/deck-assets/" + image.lstrip("/")
        return {
            "id": card.id,
            "card_type": card.card_type,
            "question": card.display_text(),
            "prompt": card.question.strip(),
            "code": "" if card.is_live_code else card.code.strip(),
            "task": "" if card.is_live_code else card.task.strip(),
            "needs_code": card.needs_code_editor,
            "needs_math": card.needs_math_editor,
            "is_anatomy": card.is_anatomy,
            "image": image,
            "image_alt": card.image_alt,
            "language": card.language,
            "is_live_code": card.is_live_code,
            "topic": card.topic,
            "math_starter": card.task if card.needs_math_editor else "",
            "attempts": prog.attempts,
            "best_score": prog.best_score,
            "last_score": prog.last_score,
        }

    def submit_answer(self, ctx: UserContext, session: StudySession, answer: str) -> dict:
        card = session.current
        if not card:
            raise ValueError("Сессия завершена")
        if not answer.strip():
            raise ValueError("Пустой ответ")

        was_follow_up = session.awaiting_follow_up
        code_card = bool(card.needs_code_editor)
        math_card = bool(card.needs_math_editor)
        editor_card = code_card or math_card
        max_fu = self.max_follow_ups(ctx)
        ps = self.pass_score(ctx)
        remaining = 0 if editor_card else max(0, max_fu - session.follow_up_count)
        result = self.evaluator().evaluate(
            card,
            answer.strip(),
            session.chat_history.copy(),
            is_follow_up=was_follow_up and not editor_card,
            follow_ups_remaining=remaining,
            deck_name=session.deck.name,
        )
        session.chat_history.append(ChatMessage("user", answer.strip()))
        session.chat_history.append(ChatMessage("assistant", result.feedback))

        lines = [f"Оценка: {result.score}/100", "", result.feedback]
        passed = result.score >= ps
        interactions = session.follow_up_count + session.revision_count
        finalize = True
        follow_up = ""
        note = ""
        status = "passed" if passed else "failed"

        if result.follow_up and session.follow_up_count < max_fu and not editor_card:
            session.follow_up_count += 1
            session.awaiting_follow_up = True
            follow_up = result.follow_up
            lines += ["", f"❓ Уточнение ({session.follow_up_count}/{max_fu}): {result.follow_up}"]
            finalize = False
            status = "follow_up"
        elif not passed and editor_card and interactions < max_fu:
            session.revision_count += 1
            session.awaiting_follow_up = False
            label = "формулу" if math_card else "код"
            left = max_fu - session.follow_up_count - session.revision_count
            note = f"Исправьте {label} и отправьте снова — осталось попыток: {left}."
            lines += ["", f"✏️ {note}"]
            finalize = False
            status = "revise"
        else:
            session.awaiting_follow_up = False
            if result.follow_up and session.follow_up_count >= max_fu:
                note = f"Лимит уточнений ({max_fu}) исчерпан — карточка завершена."
            elif not passed and editor_card and interactions >= max_fu:
                note = f"Лимит правок ({max_fu}) исчерпан — карточка завершена."
            if note:
                lines += ["", f"ℹ️ {note}"]

        if finalize:
            lines += ["", "✅ Засчитано!" if passed else "↻ Карточка вернётся в повторение через несколько минут."]
            session.answered += 1
            session.scores.append(result.score)
            if passed:
                session.passed += 1

        session.last_review = {"hint": result.hint, "reference_summary": result.reference_summary}
        session.last_feedback = "\n".join(lines)
        session.pending_finalize = finalize

        with ctx.lock:
            ctx.progress.record_answer(
                session.deck,
                card.id,
                answer=answer.strip(),
                score=result.score,
                correct=passed,
                feedback=result.feedback,
                pass_score=ps,
                is_follow_up=was_follow_up,
                finalize=finalize,
            )

        cfg = self.effective_config(ctx)
        return {
            "feedback": session.last_feedback,
            "review": {
                "score": result.score,
                "passed": passed,
                "status": status,
                "feedback": result.feedback,
                "follow_up": follow_up,
                "note": note,
                "reference_summary": result.reference_summary if finalize else "",
                "follow_up_index": session.follow_up_count,
                "max_follow_ups": max_fu,
            },
            "finalize": finalize,
            "passed": passed,
            "can_submit": not finalize,
            "clear_answer": session.awaiting_follow_up and not editor_card,
            "auto_advance_ms": int(cfg.get("auto_advance_ms", 10000)) if finalize and passed else 0,
            "stats": self.session_stats(ctx, session),
        }

    def transcribe_audio(self, ctx: UserContext, content: bytes, filename: str, context: str = "") -> dict:
        from app.asr_client import build_initial_prompt, transcribe_whisper

        cfg = self.effective_config(ctx)
        raw = transcribe_whisper(
            cfg.get("asr_url", ""),
            content,
            filename,
            language=str(cfg.get("asr_language", "ru")),
            login=str(cfg.get("asr_user", "")),
            password=str(cfg.get("asr_password", "")),
            initial_prompt=build_initial_prompt(context),
        )
        text = raw
        corrected = False
        if raw and cfg.get("asr_correct", True):
            fixed = self.correct_transcript(raw, context)
            if fixed and fixed != raw:
                text, corrected = fixed, True
        return {"text": text, "raw": raw, "corrected": corrected}

    def correct_transcript(self, raw: str, context: str) -> str:
        """ИИ-корректура распознанной речи: только ошибки распознавания, без изменения смысла."""
        import re

        system = (
            "Ты исправляешь ошибки автоматического распознавания русской речи в ответе студента на учебный вопрос.\n"
            "Исправь: неверно распознанные слова и технические термины (например «эсквель» → «SQL», "
            "«база донных» → «база данных», «пэхапэ» → «PHP», «джейсон» → «JSON»), склеенные или разорванные слова, "
            "пунктуацию и регистр.\n"
            "НЕЛЬЗЯ: добавлять новые мысли, исправлять фактические ошибки студента, отвечать на вопрос, "
            "менять порядок изложения. Если текст уже корректен — верни его без изменений.\n"
            "Верни ТОЛЬКО исправленный текст, без кавычек и комментариев."
        )
        user = f"Вопрос: {context.strip()[:800] or '—'}\n\nРаспознанный текст:\n{raw}"
        try:
            # свой короткий таймаут: если модель занята, отдаём распознанный текст без задержки
            client = OllamaClient(
                self.config["ollama_url"], self.config["model"], timeout=25, api_key=self.config.get("api_key", "")
            )
            out = client.chat([ChatMessage("system", system), ChatMessage("user", user)])
        except Exception:  # noqa: BLE001 — без корректуры, но с распознанным текстом
            return raw
        out = re.sub(r"<think>[\s\S]*?</think>", "", out).strip().strip("«»\"'").strip()
        # защита от «ответа вместо исправления»: длина не должна сильно меняться
        if not out or len(out) > len(raw) * 1.6 + 40 or len(out) < len(raw) * 0.5:
            return raw
        return out

    def request_hint(self, session: StudySession, draft: str = "") -> str:
        card = session.current
        if not card:
            raise ValueError("Сессия завершена")
        if session.last_review:
            hint = session.last_review.get("hint") or session.last_review.get("reference_summary") or ""
            if hint:
                return hint
        if session.cached_hint and not draft.strip():
            return session.cached_hint
        hint = self.evaluator().request_hint(card, deck_name=session.deck.name, user_draft=draft.strip())
        session.cached_hint = hint
        return hint

    def next_card(self, ctx: UserContext, session: StudySession) -> dict:
        if session.pending_finalize and session.index < len(session.queue):
            session.queue.pop(session.index)
        else:
            session.index += 1
        session.pending_finalize = False
        session.chat_history = []
        session.awaiting_follow_up = False
        session.follow_up_count = 0
        session.revision_count = 0
        session.last_review = None
        session.last_feedback = ""
        session.cached_hint = ""

        if session.finished:
            return {"done": True, "stats": self.session_stats(ctx, session)}
        return {
            "done": False,
            "card": self.card_payload(ctx, session),
            "stats": self.session_stats(ctx, session),
        }
