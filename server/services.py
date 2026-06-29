from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.config_store import clamp_session_limit, data_dir, load_config, save_config
from app.deck import Card, ChatMessage, Deck
from app.ollama_client import AnswerEvaluator, OllamaClient
from app.progress import ProgressStore, StudyMode
from app.registry import DeckRegistry


@dataclass
class StudySession:
    id: str
    deck: Deck
    mode: StudyMode
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

    @property
    def current(self) -> Card | None:
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

    @property
    def finished(self) -> bool:
        return self.index >= len(self.queue)


class AppServices:
    def __init__(self, root: Path) -> None:
        self.root = root
        dd = data_dir()
        dd.mkdir(parents=True, exist_ok=True)
        self.data_dir = dd
        self.config, self.config_path = load_config(root)
        self.progress = ProgressStore(dd / "progress.json")
        self.progress.load()
        self.registry = DeckRegistry(dd / "decks.json", root / "decks")
        self.registry.load()
        self.sessions: dict[str, StudySession] = {}

    def reload_config(self) -> None:
        self.config, self.config_path = load_config(self.root)
        self.progress.load()
        self.registry.load()

    def pass_score(self) -> int:
        return int(self.config.get("pass_score", 75))

    def max_follow_ups(self) -> int:
        return int(self.config.get("max_follow_ups", 2))

    def evaluator(self) -> AnswerEvaluator:
        c = self.config
        client = OllamaClient(
            c["ollama_url"],
            c["model"],
            timeout=int(c.get("timeout", 120)),
            api_key=c.get("api_key", ""),
        )
        return AnswerEvaluator(client)

    def deck_summary_row(self, entry) -> dict:
        deck = self.registry.load_deck(entry)
        self.progress.reconcile_deck(deck, self.pass_score())
        s = self.progress.summary(deck, self.pass_score())
        return {
            "deck_id": entry.deck_id,
            "name": entry.name,
            "total": s.total,
            "mastered": s.mastered,
            "passed_today": s.passed_today,
            "due": s.due,
            "new": s.new,
            "weak": s.weak,
            "avg_score": s.avg_score,
            "studied": s.studied,
        }

    def start_session(self, deck_id: str, mode: str) -> StudySession:
        entry = self.registry.get(deck_id)
        if not entry:
            raise ValueError("Колода не найдена")
        deck = self.registry.load_deck(entry)
        self.progress.load()
        self.progress.reconcile_deck(deck, self.pass_score())
        queue = self.progress.build_queue(
            deck,
            StudyMode(mode),
            pass_score=self.pass_score(),
            limit=clamp_session_limit(self.config.get("session_limit", 20)),
        )
        sid = uuid.uuid4().hex
        session = StudySession(id=sid, deck=deck, mode=StudyMode(mode), queue=queue)
        self.sessions[sid] = session
        return session

    def session_stats(self, session: StudySession) -> dict:
        s = self.progress.summary(session.deck, self.pass_score())
        return {
            "passed_today": s.passed_today,
            "mastered": s.mastered,
            "total": s.total,
            "due": s.due,
            "queue": len(session.queue),
            "index": session.index + 1 if session.queue else 0,
        }

    def card_payload(self, session: StudySession) -> dict | None:
        card = session.current
        if not card:
            return None
        prog = self.progress.get(session.deck, card.id)
        return {
            "question": card.display_text(),
            "needs_code": card.needs_code_editor,
            "language": card.language,
            "is_live_code": card.is_live_code,
            "attempts": prog.attempts,
            "best_score": prog.best_score,
            "last_score": prog.last_score,
        }

    def submit_answer(self, session: StudySession, answer: str) -> dict:
        card = session.current
        if not card:
            raise ValueError("Сессия завершена")
        if not answer.strip():
            raise ValueError("Пустой ответ")

        was_follow_up = session.awaiting_follow_up
        code_card = bool(card.needs_code_editor)
        remaining = 0 if code_card else max(0, self.max_follow_ups() - session.follow_up_count)
        result = self.evaluator().evaluate(
            card,
            answer.strip(),
            session.chat_history.copy(),
            is_follow_up=was_follow_up and not code_card,
            follow_ups_remaining=remaining,
            deck_name=session.deck.name,
        )
        session.chat_history.append(ChatMessage("user", answer.strip()))
        session.chat_history.append(ChatMessage("assistant", result.feedback))

        lines = [f"Оценка: {result.score}/100", "", result.feedback]

        passed = result.score >= self.pass_score()
        max_fu = self.max_follow_ups()
        interactions = session.follow_up_count + session.revision_count
        finalize = True

        if (
            result.follow_up
            and session.follow_up_count < max_fu
            and not card.needs_code_editor
        ):
            session.follow_up_count += 1
            session.awaiting_follow_up = True
            lines.append("")
            lines.append(f"❓ Уточнение ({session.follow_up_count}/{max_fu}): {result.follow_up}")
            finalize = False
        elif not passed and card.needs_code_editor and interactions < max_fu:
            session.revision_count += 1
            session.awaiting_follow_up = False
            lines.extend([
                "",
                f"✏️ Исправьте код и отправьте снова "
                f"({session.revision_count}/{max_fu} · "
                f"осталось {max_fu - session.follow_up_count - session.revision_count})",
            ])
            finalize = False
        else:
            session.awaiting_follow_up = False
            if result.follow_up and session.follow_up_count >= max_fu:
                lines.extend(["", f"ℹ️ Лимит уточнений ({max_fu}) исчерпан — карточка завершена."])
            elif not passed and card.needs_code_editor and interactions >= max_fu:
                lines.extend(["", f"ℹ️ Лимит правок ({max_fu}) исчерпан — карточка завершена."])

        if finalize:
            lines.append("")
            lines.append("✅ Засчитано!" if passed else "↻ Карточка вернётся в повторение через несколько минут.")

        session.last_review = {
            "hint": result.hint,
            "reference_summary": result.reference_summary,
        }
        session.last_feedback = "\n".join(lines)
        session.pending_finalize = finalize

        self.progress.record_answer(
            session.deck,
            card.id,
            answer=answer.strip(),
            score=result.score,
            correct=passed,
            feedback=result.feedback,
            pass_score=self.pass_score(),
            is_follow_up=was_follow_up,
            finalize=finalize,
        )

        return {
            "feedback": session.last_feedback,
            "finalize": finalize,
            "passed": passed,
            "can_submit": not finalize,
            "clear_answer": session.awaiting_follow_up and not card.needs_code_editor,
            "auto_advance_ms": int(self.config.get("auto_advance_ms", 10000)) if finalize and passed else 0,
            "stats": self.session_stats(session),
        }

    def transcribe_audio(self, content: bytes, filename: str) -> str:
        from app.asr_client import transcribe_whisper

        return transcribe_whisper(
            self.config.get("asr_url", ""),
            content,
            filename,
            language=str(self.config.get("asr_language", "ru")),
            login=str(self.config.get("asr_user", "")),
            password=str(self.config.get("asr_password", "")),
        )

    def request_hint(self, session: StudySession, draft: str = "") -> str:
        card = session.current
        if not card:
            raise ValueError("Сессия завершена")
        if session.last_review:
            hint = session.last_review.get("hint") or session.last_review.get("reference_summary") or ""
            if hint:
                return hint
        hint = self.evaluator().request_hint(
            card,
            deck_name=session.deck.name,
            user_draft=draft.strip(),
        )
        session.cached_hint = hint
        return hint

    def next_card(self, session: StudySession) -> dict:
        if session.pending_finalize and session.index < len(session.queue):
            session.pending_finalize = False
            session.queue.pop(session.index)
            session.chat_history = []
            session.awaiting_follow_up = False
            session.follow_up_count = 0
            session.revision_count = 0
            session.last_review = None
            session.last_feedback = ""
            session.cached_hint = ""
        else:
            session.index += 1
            session.chat_history = []
            session.awaiting_follow_up = False
            session.follow_up_count = 0
            session.revision_count = 0
            session.last_review = None
            session.last_feedback = ""
            session.cached_hint = ""

        if session.finished:
            return {"done": True, "stats": self.session_stats(session)}

        return {
            "done": False,
            "card": self.card_payload(session),
            "stats": self.session_stats(session),
        }

    def save_settings(self, payload: dict) -> None:
        allowed = (
            "session_limit", "pass_score", "max_follow_ups", "auto_advance_ms",
            "ollama_url", "model", "api_key", "timeout",
            "asr_url", "asr_user", "asr_password", "asr_language",
        )
        for key in allowed:
            if key in payload:
                self.config[key] = payload[key]
        if "auto_advance_sec" in payload:
            self.config["auto_advance_ms"] = int(payload["auto_advance_sec"]) * 1000
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
