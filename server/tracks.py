"""Профессиональные треки: обзор, экзамены, AI-собеседования и сертификаты."""
from __future__ import annotations

import json
import random
import re
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.deck import Card, ChatMessage
from app.ollama_client import _loads_llm_json
from app.registry import deck_id_for_path
from server.services import AppServices, UserContext
from server.syllabus import track_syllabus, syllabus_for


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


# ── хранилище результатов ───────────────────────────────────────────


class TrackStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._db:
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,              -- exam | interview
                    user_id INTEGER NOT NULL,
                    track_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    score REAL NOT NULL,
                    passed INTEGER NOT NULL,
                    details TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS attempts_user ON attempts(user_id, track_id, kind);
                CREATE TABLE IF NOT EXISTS certificates (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    track_id TEXT NOT NULL,
                    track_title TEXT NOT NULL,
                    holder TEXT NOT NULL,
                    issued_at TEXT NOT NULL,
                    exam_score REAL NOT NULL,
                    interview_score REAL NOT NULL,
                    coverage REAL NOT NULL,
                    UNIQUE (user_id, track_id)
                );
                """
            )

    def add_attempt(self, kind: str, user_id: int, track_id: str, started: str, score: float, passed: bool, details: dict) -> str:
        aid = uuid.uuid4().hex
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, kind, user_id, track_id, started, _iso(), score, int(passed), json.dumps(details, ensure_ascii=False)),
            )
        return aid

    def attempts(self, user_id: int, track_id: str, kind: str | None = None, limit: int = 20) -> list[dict]:
        q = "SELECT * FROM attempts WHERE user_id = ? AND track_id = ?"
        args: list = [user_id, track_id]
        if kind:
            q += " AND kind = ?"
            args.append(kind)
        q += " ORDER BY finished_at DESC LIMIT ?"
        args.append(limit)
        with self._lock:
            rows = self._db.execute(q, args).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d["details"])
            d["passed"] = bool(d["passed"])
            out.append(d)
        return out

    def get_attempt(self, attempt_id: str, user_id: int) -> dict | None:
        with self._lock:
            r = self._db.execute("SELECT * FROM attempts WHERE id = ? AND user_id = ?", (attempt_id, user_id)).fetchone()
        if r is None:
            return None
        d = dict(r)
        d["details"] = json.loads(d["details"])
        d["passed"] = bool(d["passed"])
        return d

    def best(self, user_id: int, track_id: str, kind: str) -> dict | None:
        with self._lock:
            r = self._db.execute(
                "SELECT id, score, passed, finished_at FROM attempts WHERE user_id = ? AND track_id = ? AND kind = ?"
                " ORDER BY score DESC LIMIT 1",
                (user_id, track_id, kind),
            ).fetchone()
        return dict(r) | {"passed": bool(r["passed"])} if r else None

    def certificate(self, user_id: int, track_id: str) -> dict | None:
        with self._lock:
            r = self._db.execute("SELECT * FROM certificates WHERE user_id = ? AND track_id = ?", (user_id, track_id)).fetchone()
        return dict(r) if r else None

    def certificate_by_id(self, cert_id: str) -> dict | None:
        with self._lock:
            r = self._db.execute("SELECT * FROM certificates WHERE id = ?", (cert_id.upper(),)).fetchone()
        return dict(r) if r else None

    def certificates_for_user(self, user_id: int) -> list[dict]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM certificates WHERE user_id = ? ORDER BY issued_at", (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def issue(self, user_id: int, track_id: str, track_title: str, holder: str, exam: float, interview: float, coverage: float) -> dict:
        existing = self.certificate(user_id, track_id)
        if existing:
            return existing
        cert_id = f"AIA-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO certificates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (cert_id, user_id, track_id, track_title, holder, _iso(), exam, interview, coverage),
            )
        return self.certificate(user_id, track_id)  # type: ignore[return-value]


def public_certificate(c: dict) -> dict:
    return {
        "id": c["id"],
        "track_id": c["track_id"],
        "track_title": c["track_title"],
        "holder": c["holder"],
        "issued_at": c["issued_at"],
        "exam_score": round(c["exam_score"], 1),
        "interview_score": round(c["interview_score"], 1),
        "coverage": round(c["coverage"], 3),
    }


# ── активные экзамены и собеседования (в памяти) ───────────────────


@dataclass
class ExamItem:
    card: Card
    kind: str  # theory | practice
    answer: str = ""
    score: int | None = None
    feedback: str = ""
    reference_summary: str = ""
    version: int = 0
    worker: threading.Thread | None = None


@dataclass
class ExamSession:
    id: str
    user_id: int
    track_id: str
    deck_name: str
    items: list[ExamItem]
    started_at: datetime
    deadline: datetime
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class InterviewQuestion:
    card: Card
    kind: str
    history: list[ChatMessage] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    follow_up_used: bool = False
    in_follow_up: bool = False
    score: int | None = None
    feedback: str = ""


@dataclass
class InterviewSession:
    id: str
    user_id: int
    track_id: str
    track_title: str
    deck_name: str
    questions: list[InterviewQuestion]
    index: int = 0
    transcript: list[dict] = field(default_factory=list)
    started_at: datetime = field(default_factory=_now)
    done: bool = False
    result: dict | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


ACKS = ["Понял, спасибо.", "Хорошо, принято.", "Спасибо за ответ.", "Ясно.", "Хорошо."]
LEADS = ["Следующий вопрос.", "Идём дальше.", "Теперь такой вопрос.", "Следующая тема."]

REPORT_SYSTEM = """Ты — опытный технический интервьюер. По стенограмме собеседования и оценкам ответов составь отчёт.
Отвечай ТОЛЬКО валидным JSON без markdown:
{"summary": "2–3 предложения об уровне кандидата",
 "strengths": ["сильная сторона", ...],
 "gaps": ["пробел в знаниях", ...],
 "recommendations": ["что изучить или потренировать", ...],
 "level": "Junior" | "Middle" | "Senior"}
Пиши на русском, конкретно, опираясь на ответы. 2–4 пункта в каждом списке."""


class ExamIn(BaseModel):
    pass


class ExamAnswerIn(BaseModel):
    index: int
    answer: str


class InterviewAnswerIn(BaseModel):
    answer: str


def build_router(services: AppServices, current_ctx: Callable[..., UserContext]) -> APIRouter:
    r = APIRouter()
    store = TrackStore(services.data_dir / "tracks.db")
    exams: dict[str, ExamSession] = {}
    interviews: dict[str, InterviewSession] = {}

    # ── манифест и колоды трека ────────────────────────────────────

    def manifest() -> dict:
        path = services.root / "decks" / "tracks.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"tracks": [], "exam": {}, "interview": {}, "coverage": 0.6}

    def track_or_404(track_id: str) -> dict:
        for t in manifest()["tracks"]:
            if t["id"] == track_id:
                return t
        raise HTTPException(404, "Профессия не найдена")

    def deck_entry(filename: str):
        did = deck_id_for_path(services.root / "decks" / filename, scope="builtin")
        return services.registry.get(did)

    def track_decks(track: dict) -> list[tuple]:
        sy = track_syllabus(track["id"])
        books = getattr(services, "books", None)
        if sy and books:
            ids = books.deck_ids(sy)
            entries = [services.registry.get(ids.get(k, "")) for k in ("qa", "live")]
            if all(entries):
                return [(Path(e.primary_path).name, e, services.load_deck(e)) for e in entries]
        out = []
        for fn in track["decks"]:
            entry = deck_entry(fn)
            if entry:
                out.append((fn, entry, services.load_deck(entry)))
        return out

    def coverage(ctx: UserContext, track: dict) -> tuple[float, int, int, list[dict]]:
        passed_total = cards_total = 0
        rows = []
        ps = services.pass_score(ctx)
        for fn, entry, deck in track_decks(track):
            with ctx.lock:
                ctx.progress.reconcile_deck(deck, ps)
                s = ctx.progress.summary(deck, ps)
            passed = max(0, s.studied - s.weak)
            passed_total += passed
            cards_total += s.total
            rows.append(
                {
                    "deck_id": entry.deck_id,
                    "file": fn,
                    "name": entry.name,
                    "kind": "live" if "live-coding" in fn else "theory",
                    "total": s.total,
                    "passed": passed,
                    "due": s.due,
                    "new": s.new,
                    "weak": s.weak,
                    "studied": s.studied,
                    "avg_score": s.avg_score,
                }
            )
        return (passed_total / cards_total if cards_total else 0.0), passed_total, cards_total, rows

    def status(ctx: UserContext, track: dict, *, with_decks: bool = False) -> dict:
        m = manifest()
        cov, passed, total, decks = coverage(ctx, track)
        exam = store.best(ctx.user.id, track["id"], "exam")
        interview = store.best(ctx.user.id, track["id"], "interview")
        need_cov = float(m.get("coverage", 0.6))
        req = {
            "coverage": {"value": round(cov, 3), "required": need_cov, "done": cov >= need_cov, "passed": passed, "total": total},
            "exam": {"best": exam["score"] if exam else None, "required": m["exam"].get("pass_score", 70), "done": bool(exam and exam["passed"])},
            "interview": {"best": interview["score"] if interview else None, "required": m["interview"].get("pass_score", 65), "done": bool(interview and interview["passed"])},
        }
        cert = store.certificate(ctx.user.id, track["id"])
        sy = track_syllabus(track["id"])
        books = getattr(services, "books", None)
        book = None
        if sy and books:
            counts = books.lesson_counts(sy)
            book = {"id": sy.id, "title": sy.title, "is_code": sy.is_code,
                    "decks": books.deck_ids(sy), "lessons": len(counts), "chapter_count": len(sy.chapters)}
            if with_decks:
                book["chapters"] = [
                    {"title": ch.title, "lessons": [{"title": ls, **counts[ls]} for ls in ch.lessons]}
                    for ch in sy.chapters
                ]
        out = {
            "id": track["id"],
            "title": track["title"],
            "description": track["description"],
            "icon": track["icon"],
            "language": track["language"],
            "subjects": [ch.title for ch in sy.chapters] if sy else track["subjects"],
            "book": book,
            "requirements": req,
            "eligible": all(v["done"] for v in req.values()),
            "certificate": public_certificate(cert) if cert else None,
        }
        if with_decks:
            out["decks"] = decks
            related = []
            for fn in track.get("related", []):
                e = deck_entry(fn)
                if e:
                    related_sy = syllabus_for(e.deck_id, e.name, e.paths)
                    if related_sy and books:
                        key = "live" if "live-coding" in fn else "qa"
                        e = services.registry.get(books.deck_ids(related_sy).get(key, "")) or e
                    related.append({"deck_id": e.deck_id, "name": e.name})
            out["related"] = related
            out["exam_config"] = m["exam"]
            out["interview_config"] = m["interview"]
            out["history"] = [
                {k: a[k] for k in ("id", "kind", "finished_at", "score", "passed")}
                | {"level": a["details"].get("level")}
                for a in store.attempts(ctx.user.id, track["id"])
            ]
        return out

    def maybe_issue(ctx: UserContext, track: dict) -> dict | None:
        st = status(ctx, track)
        if not st["eligible"]:
            return None
        cert = store.issue(
            ctx.user.id,
            track["id"],
            track["title"],
            ctx.user.display_name or ctx.user.username,
            float(st["requirements"]["exam"]["best"] or 0),
            float(st["requirements"]["interview"]["best"] or 0),
            float(st["requirements"]["coverage"]["value"]),
        )
        return public_certificate(cert)

    # ── выбор вопросов ─────────────────────────────────────────────

    def pick(track: dict, n_theory: int, n_practice: int) -> tuple[list[tuple[Card, str]], str]:
        decks = track_decks(track)
        theory_cards = [c for fn, _, d in decks if "live-coding" not in fn for c in d.cards]
        practice_cards = [c for fn, _, d in decks if "live-coding" in fn for c in d.cards]
        rng = random.Random()
        by_topic: dict[str, list[Card]] = {}
        for c in theory_cards:
            by_topic.setdefault(c.topic or "Разное", []).append(c)
        topics = list(by_topic)
        rng.shuffle(topics)
        for t in topics:
            rng.shuffle(by_topic[t])
        chosen: list[Card] = []
        while len(chosen) < n_theory and any(by_topic.values()):
            for t in topics:
                if by_topic[t] and len(chosen) < n_theory:
                    chosen.append(by_topic[t].pop())
        practice = rng.sample(practice_cards, min(n_practice, len(practice_cards)))
        deck_name = decks[0][1].name if decks else track["title"]
        return [(c, "theory") for c in chosen] + [(c, "practice") for c in practice], deck_name

    def card_view(card: Card, kind: str) -> dict:
        return {
            "kind": kind,
            "question": card.question.strip(),
            "code": card.code.strip(),
            "task": card.task.strip(),
            "topic": card.topic,
            "language": card.language,
            "needs_code": card.needs_code_editor,
        }

    # ── обзор треков и сертификаты ─────────────────────────────────

    @r.get("/api/tracks")
    def list_tracks(ctx: UserContext = Depends(current_ctx)) -> dict:
        m = manifest()
        return {
            "tracks": [status(ctx, t) for t in m["tracks"]],
            "exam": m.get("exam", {}),
            "interview": m.get("interview", {}),
            "coverage": m.get("coverage", 0.6),
        }

    @r.get("/api/tracks/{track_id}")
    def track_detail(track_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        return status(ctx, track_or_404(track_id), with_decks=True)

    @r.post("/api/tracks/{track_id}/certificate")
    def issue_certificate(track_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        cert = maybe_issue(ctx, track_or_404(track_id))
        if not cert:
            raise HTTPException(400, "Условия сертификата ещё не выполнены")
        return {"certificate": cert}

    @r.get("/api/certificates")
    def my_certificates(ctx: UserContext = Depends(current_ctx)) -> dict:
        return {"certificates": [public_certificate(c) for c in store.certificates_for_user(ctx.user.id)]}

    @r.get("/api/certificates/{cert_id}")
    def verify_certificate(cert_id: str) -> dict:
        cert = store.certificate_by_id(cert_id.strip())
        if not cert:
            raise HTTPException(404, "Сертификат не найден")
        return {"certificate": public_certificate(cert), "valid": True}

    @r.get("/api/attempts/{attempt_id}")
    def attempt_detail(attempt_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        a = store.get_attempt(attempt_id, ctx.user.id)
        if not a:
            raise HTTPException(404, "Попытка не найдена")
        return a

    # ── экзамен ────────────────────────────────────────────────────

    def gc() -> None:
        now = _now()
        for sid in [k for k, v in exams.items() if now > v.deadline + timedelta(hours=2)]:
            exams.pop(sid, None)
        for sid in [k for k, v in interviews.items() if now - v.started_at > timedelta(hours=6)]:
            interviews.pop(sid, None)

    def exam_or_404(exam_id: str, ctx: UserContext) -> ExamSession:
        ex = exams.get(exam_id)
        if not ex or ex.user_id != ctx.user.id:
            raise HTTPException(404, "Экзамен не найден — начните заново")
        return ex

    def exam_state(ex: ExamSession) -> dict:
        return {
            "exam_id": ex.id,
            "track_id": ex.track_id,
            "deadline": _iso(ex.deadline),
            "seconds_left": max(0, int((ex.deadline - _now()).total_seconds())),
            "questions": [card_view(it.card, it.kind) | {"answered": bool(it.answer)} for it in ex.items],
        }

    @r.post("/api/tracks/{track_id}/exam")
    def start_exam(track_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        gc()
        track = track_or_404(track_id)
        cfg = manifest()["exam"]
        picked, deck_name = pick(track, int(cfg.get("theory", 9)), int(cfg.get("practice", 3)))
        if not picked:
            raise HTTPException(400, "В треке нет карточек")
        now = _now()
        ex = ExamSession(
            id=uuid.uuid4().hex,
            user_id=ctx.user.id,
            track_id=track_id,
            deck_name=deck_name,
            items=[ExamItem(card=c, kind=k) for c, k in picked],
            started_at=now,
            deadline=now + timedelta(minutes=int(cfg.get("minutes", 60))),
        )
        exams[ex.id] = ex
        return exam_state(ex) | {"pass_score": cfg.get("pass_score", 70), "title": track["title"]}

    @r.post("/api/exams/{exam_id}/answer")
    def exam_answer(exam_id: str, body: ExamAnswerIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        ex = exam_or_404(exam_id, ctx)
        if _now() > ex.deadline:
            raise HTTPException(409, "Время экзамена истекло")
        if not 0 <= body.index < len(ex.items):
            raise HTTPException(400, "Нет такого вопроса")
        answer = body.answer.strip()
        if not answer:
            raise HTTPException(400, "Пустой ответ")
        it = ex.items[body.index]
        with ex.lock:
            it.answer = answer
            it.score = None
            it.version += 1
            version = it.version

        def grade() -> None:
            try:
                res = services.evaluator().evaluate(
                    it.card, answer, [], is_follow_up=False, follow_ups_remaining=0, deck_name=ex.deck_name
                )
                score, feedback, ref = int(res.score), res.feedback, res.reference_summary
            except Exception as exc:  # noqa: BLE001
                score, feedback, ref = 0, f"Не удалось проверить ответ: {exc}", ""
            with ex.lock:
                if it.version == version:  # ответ не перезаписан
                    it.score, it.feedback, it.reference_summary = score, feedback, ref

        # проверка идёт в фоне — кандидат сразу переходит к следующему вопросу
        it.worker = threading.Thread(target=grade, daemon=True, name=f"exam-grade-{ex.id[:6]}-{body.index}")
        it.worker.start()
        return {"ok": True, "index": body.index, "answered": sum(1 for x in ex.items if x.answer)}

    @r.post("/api/exams/{exam_id}/finish")
    def finish_exam(exam_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        ex = exam_or_404(exam_id, ctx)
        exams.pop(exam_id, None)
        for it in ex.items:  # дождаться фоновых проверок
            if it.worker is not None:
                it.worker.join(timeout=300)
        track = track_or_404(ex.track_id)
        cfg = manifest()["exam"]
        items = []
        by_topic: dict[str, list[int]] = {}
        for it in ex.items:
            score = it.score if it.score is not None else 0
            by_topic.setdefault(it.card.topic or "Разное", []).append(score)
            items.append(
                card_view(it.card, it.kind)
                | {
                    "answer": it.answer,
                    "score": score,
                    "feedback": it.feedback or ("Нет ответа" if not it.answer else ""),
                    "reference_summary": it.reference_summary,
                }
            )
        total = round(sum(x["score"] for x in items) / len(items), 1) if items else 0.0
        passed = total >= float(cfg.get("pass_score", 70))
        details = {
            "items": items,
            "topics": {t: round(sum(v) / len(v), 1) for t, v in by_topic.items()},
            "answered": sum(1 for x in items if x["answer"]),
            "duration_sec": int((_now() - ex.started_at).total_seconds()),
            "pass_score": cfg.get("pass_score", 70),
        }
        aid = store.add_attempt("exam", ctx.user.id, ex.track_id, _iso(ex.started_at), total, passed, details)
        cert = maybe_issue(ctx, track)
        return {"attempt_id": aid, "score": total, "passed": passed, "details": details, "certificate": cert}

    # ── AI-собеседование ───────────────────────────────────────────

    def interview_or_404(iid: str, ctx: UserContext) -> InterviewSession:
        s = interviews.get(iid)
        if not s or s.user_id != ctx.user.id:
            raise HTTPException(404, "Собеседование не найдено — начните заново")
        return s

    def ask_text(s: InterviewSession, q: InterviewQuestion, lead: str) -> str:
        body = q.card.question.strip()
        if q.kind == "practice":
            return f"{lead} Практическое задание — напишите решение в редакторе:\n\n{body}"
        return f"{lead} {body}" if lead else body

    def say(s: InterviewSession, text: str, **extra) -> dict:
        msg = {"role": "interviewer", "text": text, "at": _iso()} | extra
        s.transcript.append(msg)
        return msg

    def current_meta(s: InterviewSession) -> dict:
        q = s.questions[s.index] if s.index < len(s.questions) else None
        return {
            "index": min(s.index + 1, len(s.questions)),
            "total": len(s.questions),
            "input": ("code" if q and q.card.needs_code_editor else "text") if q else None,
            "language": q.card.language if q else "",
            "topic": q.card.topic if q else "",
        }

    @r.post("/api/tracks/{track_id}/interview")
    def start_interview(track_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        gc()
        track = track_or_404(track_id)
        cfg = manifest()["interview"]
        picked, deck_name = pick(track, int(cfg.get("theory", 5)), int(cfg.get("practice", 1)))
        if not picked:
            raise HTTPException(400, "В треке нет карточек")
        s = InterviewSession(
            id=uuid.uuid4().hex,
            user_id=ctx.user.id,
            track_id=track_id,
            track_title=track["title"],
            deck_name=deck_name,
            questions=[InterviewQuestion(card=c, kind=k) for c, k in picked],
        )
        interviews[s.id] = s
        name = ctx.user.display_name or ctx.user.username
        greet = (
            f"Здравствуйте, {name}! Я проведу техническое собеседование на позицию «{track['title']}». "
            f"Будет {len(s.questions)} вопросов, последний — практический. Отвечайте своими словами, как на настоящем интервью; "
            "иногда я буду задавать уточняющие вопросы."
        )
        msgs = [say(s, greet), say(s, ask_text(s, s.questions[0], "Первый вопрос."), topic=s.questions[0].card.topic)]
        return {"interview_id": s.id, "track_id": track_id, "title": track["title"], "messages": msgs, "done": False, **current_meta(s)}

    def build_report(s: InterviewSession) -> dict:
        cfg = manifest()["interview"]
        scores = [q.score or 0 for q in s.questions]
        overall = round(sum(scores) / len(scores), 1) if scores else 0.0
        lines = []
        for i, q in enumerate(s.questions, 1):
            ans = " / ".join(a[:600] for a in q.answers) or "—"
            lines.append(f"{i}. [{q.card.topic}] Вопрос: {q.card.question[:400]}\nОтвет кандидата: {ans}\nОценка: {q.score}/100. Комментарий: {q.feedback[:300]}")
        report: dict = {}
        try:
            raw = services.evaluator().client.chat(
                [
                    ChatMessage("system", REPORT_SYSTEM),
                    ChatMessage("user", f"Позиция: {s.track_title}\nСредняя оценка: {overall}/100\n\n" + "\n\n".join(lines)),
                ]
            )
            report = _loads_llm_json(re.sub(r"<think>[\s\S]*?</think>", "", raw))
        except Exception:  # noqa: BLE001
            report = {}
        level = report.get("level") if report.get("level") in ("Junior", "Middle", "Senior") else (
            "Senior" if overall >= 85 else "Middle" if overall >= 65 else "Junior"
        )
        passed = overall >= float(cfg.get("pass_score", 65))
        return {
            "score": overall,
            "passed": passed,
            "level": level,
            "summary": report.get("summary") or ("Собеседование пройдено." if passed else "Пока есть пробелы в базовых темах."),
            "strengths": [str(x) for x in report.get("strengths", [])][:5],
            "gaps": [str(x) for x in report.get("gaps", [])][:5],
            "recommendations": [str(x) for x in report.get("recommendations", [])][:5],
            "questions": [
                {
                    "topic": q.card.topic,
                    "question": q.card.question,
                    "kind": q.kind,
                    "answers": q.answers,
                    "score": q.score,
                    "feedback": q.feedback,
                }
                for q in s.questions
            ],
            "pass_score": cfg.get("pass_score", 65),
        }

    @r.post("/api/interviews/{interview_id}/answer")
    def interview_answer(interview_id: str, body: InterviewAnswerIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        s = interview_or_404(interview_id, ctx)
        if s.done:
            raise HTTPException(409, "Собеседование уже завершено")
        answer = body.answer.strip()
        if not answer:
            raise HTTPException(400, "Пустой ответ")
        if not s.lock.acquire(blocking=False):
            raise HTTPException(409, "Предыдущий ответ ещё обрабатывается")
        try:
            q = s.questions[s.index]
            s.transcript.append({"role": "candidate", "text": answer, "at": _iso()})
            practice = q.kind == "practice"
            try:
                res = services.evaluator().evaluate(
                    q.card,
                    answer,
                    q.history.copy(),
                    is_follow_up=q.in_follow_up,
                    follow_ups_remaining=0 if (q.follow_up_used or practice) else 1,
                    deck_name=s.deck_name,
                )
            except Exception as exc:  # noqa: BLE001
                s.transcript.pop()
                raise HTTPException(502, f"Ollama: {exc}") from exc
            q.history += [ChatMessage("user", answer), ChatMessage("assistant", res.feedback)]
            q.answers.append(answer)
            new: list[dict] = []
            if res.follow_up and not q.follow_up_used and not practice:
                q.follow_up_used = True
                q.in_follow_up = True
                q.score = int(res.score)
                q.feedback = res.feedback
                new.append(say(s, f"Уточню: {res.follow_up}", follow_up=True))
                return {"messages": new, "done": False, **current_meta(s)}
            q.score = max(int(res.score), q.score or 0) if q.in_follow_up else int(res.score)
            q.feedback = res.feedback
            q.in_follow_up = False
            s.index += 1
            if s.index < len(s.questions):
                nq = s.questions[s.index]
                lead = random.choice(LEADS) if nq.kind != "practice" else "И последнее."
                new.append(say(s, f"{random.choice(ACKS)} " + ask_text(s, nq, lead), topic=nq.card.topic))
                return {"messages": new, "done": False, **current_meta(s)}
            # финал
            new.append(say(s, "Спасибо, на этом всё! Готовлю отчёт по собеседованию…"))
            report = build_report(s)
            s.done = True
            aid = store.add_attempt(
                "interview",
                ctx.user.id,
                s.track_id,
                _iso(s.started_at),
                report["score"],
                report["passed"],
                report | {"transcript": s.transcript},
            )
            interviews.pop(s.id, None)
            cert = maybe_issue(ctx, track_or_404(s.track_id))
            return {"messages": new, "done": True, "report": report, "attempt_id": aid, "certificate": cert, **current_meta(s)}
        finally:
            if s.lock.locked():
                s.lock.release()

    return r
