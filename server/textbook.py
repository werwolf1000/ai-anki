"""Интерактивный учебник: статьи по темам колод (RAG) и вопросы к учебнику."""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from server.kb_sources import SOURCES, deck_vocab, sources_for_deck
from server.knowledge import ARTICLE_SYSTEM, ASK_SYSTEM, ThinkFilter, format_context, hybrid_search
from server.services import AppServices, UserContext

QUERY_INSTRUCT = "Instruct: Given a study topic, retrieve relevant passages from the official documentation\nQuery: "


class GenerateAllIn(BaseModel):
    deck_id: str = ""  # пусто — все колоды
    regenerate: bool = False


@dataclass
class ArticleBatch:
    """Фоновая генерация статей учебника для всех тем."""

    running: bool = False
    stop: bool = False
    done: int = 0
    total: int = 0
    written: int = 0
    failed: int = 0
    current: str = ""
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    log: list[str] = field(default_factory=list)

    def say(self, msg: str) -> None:
        self.log.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")
        del self.log[:-50]

    def public(self) -> dict:
        keys = ("running", "done", "total", "written", "failed", "current", "error", "started_at", "finished_at")
        return {k: getattr(self, k) for k in keys} | {"log": self.log[-6:]}


class ArticleIn(BaseModel):
    topic: str
    regenerate: bool = False


class AskIn(BaseModel):
    topic: str = ""
    question: str


class ReadIn(BaseModel):
    topic: str
    read: bool = True


class RebuildIn(BaseModel):
    source_id: str = "all"  # id источника или "all"
    download: bool = True


def strip_title(content: str, topic: str) -> str:
    """Убрать ведущий заголовок, повторяющий название темы."""
    lines = content.lstrip().split("\n", 1)
    head = lines[0].lstrip("#").strip().strip("*").strip().lower()
    if lines[0].startswith("#") and head == topic.strip().lower():
        return lines[1].lstrip() if len(lines) > 1 else ""
    return content


def _ndjson(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False) + "\n"


def build_router(services: AppServices, current_ctx: Callable[..., UserContext]) -> APIRouter:
    r = APIRouter()

    # ── отметки «прочитано» ─────────────────────────────────────────

    def read_marks(ctx: UserContext) -> dict:
        path = ctx.dir / "textbook.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_marks(ctx: UserContext, marks: dict) -> None:
        ctx.dir.mkdir(parents=True, exist_ok=True)
        (ctx.dir / "textbook.json").write_text(json.dumps(marks, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── колода и её темы ────────────────────────────────────────────

    def deck_and_entry(deck_id: str):
        entry = services.registry.get(deck_id)
        if not entry:
            raise HTTPException(404, "Колода не найдена")
        return entry, services.load_deck(entry)

    def topic_cards(deck, topic: str) -> list:
        return [c for c in deck.cards if (c.topic.strip() or "Разное") == topic]

    def deck_sources(entry, deck) -> list[str]:
        stats = services.knowledge.stats()
        return [s for s in sources_for_deck(entry.deck_id, entry.name, deck.language) if stats.get(s, {}).get("chunks")]

    def all_deck_topics(with_vocab: bool = False) -> list[dict]:
        out = []
        for entry in services.registry.entries:
            try:
                deck = services.load_deck(entry)
            except Exception:  # noqa: BLE001 — битая колода не мешает остальным
                continue
            topics = sorted({c.topic.strip() or "Разное" for c in deck.cards})
            vocab = deck_vocab([c.question + " " + c.reference for c in deck.cards]) if with_vocab else []
            out.append({"id": entry.deck_id, "name": entry.name, "topics": topics, "vocab": vocab})
        return out

    def article_prompt(entry, deck, topic: str, cards: list) -> tuple[str, str, list[dict], str]:
        samples = " ".join(c.question.split("\n")[0][:160] for c in cards[:10])
        query = f"{topic}. {entry.name}. {samples}"
        chunks, mode = retrieve(query, deck_sources(entry, deck), k=8)
        ctx_text, sources = format_context(
            chunks, [{"question": c.question, "reference": c.reference} for c in cards]
        )
        system = ARTICLE_SYSTEM.replace("{lang}", deck.language or "")
        user_prompt = (
            f"Колода: {entry.name}\nТема: {topic}\n\n{ctx_text}\n\n"
            f"Напиши статью учебника по теме «{topic}», которая подготовит к ответам на карточки этой темы."
        )
        if chunks:
            user_prompt += (
                f"\n\nВАЖНО: после каждого факта из источников ставь сноску с его номером — [1]…[{len(chunks)}]. "
                "Минимум 5 сносок по всему тексту. Не начинай статью с заголовка-названия темы."
            )
        else:
            user_prompt += "\n\nОфициальных источников по теме нет — опирайся на карточки и общеизвестные факты, ссылки [n] не ставь."
        return system, user_prompt, sources, mode

    @r.get("/api/textbook/{deck_id}")
    def textbook_deck(deck_id: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        entry, deck = deck_and_entry(deck_id)
        marks = read_marks(ctx).get(deck_id, {})
        written = services.knowledge.articles_for_deck(deck_id)
        counts: dict[str, int] = {}
        for c in deck.cards:
            name = c.topic.strip() or "Разное"
            counts[name] = counts.get(name, 0) + 1
        topics = [
            {"name": n, "cards": counts[n], "read_at": marks.get(n), "has_article": n in written}
            for n in sorted(counts)
        ]
        srcs = deck_sources(entry, deck)
        return {
            "deck_id": deck_id,
            "name": entry.name,
            "topics": topics,
            "sources": [{"id": s, "title": SOURCES[s].title, "url": SOURCES[s].homepage} for s in srcs],
        }

    @r.get("/api/textbook/{deck_id}/article")
    def get_article(deck_id: str, topic: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        art = services.knowledge.get_article(deck_id, topic)
        marks = read_marks(ctx).get(deck_id, {})
        return {"article": art, "read_at": marks.get(topic)}

    @r.post("/api/textbook/{deck_id}/read")
    def mark_read(deck_id: str, body: ReadIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        with ctx.lock:
            marks = read_marks(ctx)
            deck_marks = marks.setdefault(deck_id, {})
            if body.read:
                deck_marks[body.topic] = datetime.now(timezone.utc).isoformat()
            else:
                deck_marks.pop(body.topic, None)
            save_marks(ctx, marks)
        return {"ok": True, "read_at": marks[deck_id].get(body.topic)}

    # ── поиск по базе знаний ────────────────────────────────────────

    def retrieve(query: str, sources: list[str], k: int) -> tuple[list[dict], str]:
        if not sources:
            return [], "none"
        qvec = None
        mode = "bm25"
        try:
            qvec = services.rag_client().embed(services.embed_model(), [QUERY_INSTRUCT + query[:2000]])[0]
            mode = "hybrid"
        except Exception:  # noqa: BLE001 — нет модели эмбеддингов → только BM25
            qvec = None
        return hybrid_search(services.knowledge, query, sources, qvec=qvec, k=k), mode

    def stream_answer(system: str, user_prompt: str, sources: list[dict], mode: str, on_done=None) -> Iterator[str]:
        yield _ndjson({"type": "sources", "sources": sources, "retrieval": mode, "model": services.textbook_model()})
        text = []
        filt = ThinkFilter()
        try:
            for piece in services.rag_client().stream_chat(
                services.textbook_model(),
                [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
            ):
                out = filt.feed(piece)
                if out:
                    text.append(out)
                    yield _ndjson({"type": "delta", "text": out})
            tail = filt.flush()
            if tail:
                text.append(tail)
                yield _ndjson({"type": "delta", "text": tail})
        except Exception as exc:  # noqa: BLE001
            yield _ndjson({"type": "error", "message": f"Ollama: {exc}"})
            return
        content = "".join(text).strip()
        if on_done and content:
            on_done(content)
        yield _ndjson({"type": "done"})

    @r.post("/api/textbook/{deck_id}/article/stream")
    def stream_article(deck_id: str, body: ArticleIn, ctx: UserContext = Depends(current_ctx)) -> StreamingResponse:
        entry, deck = deck_and_entry(deck_id)
        topic = body.topic.strip()
        cards = topic_cards(deck, topic)
        if not cards:
            raise HTTPException(404, "В колоде нет такой темы")
        cached = services.knowledge.get_article(deck_id, topic)
        if cached and not body.regenerate:
            def replay() -> Iterator[str]:
                yield _ndjson({"type": "sources", "sources": cached["sources"], "cached": True, "model": cached["model"]})
                yield _ndjson({"type": "delta", "text": cached["content"]})
                yield _ndjson({"type": "done", "cached": True})
            return StreamingResponse(replay(), media_type="application/x-ndjson")

        system, user_prompt, sources, mode = article_prompt(entry, deck, topic, cards)

        def save(content: str) -> None:
            content = strip_title(content, topic)
            services.knowledge.save_article(deck_id, topic, content, sources, services.textbook_model())

        return StreamingResponse(stream_answer(system, user_prompt, sources, mode, save), media_type="application/x-ndjson")

    @r.post("/api/textbook/{deck_id}/ask")
    def ask(deck_id: str, body: AskIn, ctx: UserContext = Depends(current_ctx)) -> StreamingResponse:
        entry, deck = deck_and_entry(deck_id)
        question = body.question.strip()
        if not question:
            raise HTTPException(400, "Пустой вопрос")
        topic = body.topic.strip()
        chunks, mode = retrieve(f"{topic}. {question}", deck_sources(entry, deck), k=6)
        cards = topic_cards(deck, topic) if topic else []
        ctx_text, sources = format_context(chunks, [{"question": c.question, "reference": c.reference} for c in cards], card_limit=8)
        user_prompt = f"Колода: {entry.name}\nТема: {topic or '—'}\n\n{ctx_text}\n\nВОПРОС: {question}"
        return StreamingResponse(stream_answer(ASK_SYSTEM, user_prompt, sources, mode), media_type="application/x-ndjson")

    # ── генерация статей для всех тем (фон) ─────────────────────────

    batch = ArticleBatch()
    services.article_batch = batch  # type: ignore[attr-defined]
    batch_lock = threading.Lock()

    def generate_one(entry, deck, topic: str) -> bool:
        cards = topic_cards(deck, topic)
        if not cards:
            return False
        system, user_prompt, sources, _mode = article_prompt(entry, deck, topic, cards)
        filt = ThinkFilter()
        parts: list[str] = []
        for piece in services.rag_client().stream_chat(
            services.textbook_model(),
            [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
        ):
            parts.append(filt.feed(piece))
            if batch.stop:
                return False
        parts.append(filt.flush())
        content = strip_title("".join(parts).strip(), topic)
        if len(content) < 200:
            raise RuntimeError("модель вернула слишком короткий текст")
        services.knowledge.save_article(entry.deck_id, topic, content, sources, services.textbook_model())
        return True

    def run_batch(items: list[tuple[str, str]], regenerate: bool) -> None:
        streak = 0
        try:
            for deck_id, topic in items:
                if batch.stop:
                    batch.say("Остановлено")
                    break
                entry = services.registry.get(deck_id)
                if entry is None:
                    batch.done += 1
                    continue
                if not regenerate and services.knowledge.get_article(deck_id, topic):
                    batch.done += 1
                    continue
                batch.current = f"{entry.name} › {topic}"
                try:
                    if generate_one(entry, services.load_deck(entry), topic):
                        batch.written += 1
                    streak = 0
                except Exception as exc:  # noqa: BLE001
                    batch.failed += 1
                    streak += 1
                    batch.say(f"Ошибка «{topic}» ({entry.name}): {exc}")
                    if streak >= 3:
                        batch.error = f"Три ошибки подряд, генерация остановлена: {exc}"
                        batch.say(batch.error)
                        break
                batch.done += 1
            else:
                batch.say(f"Готово: написано {batch.written}, ошибок {batch.failed}")
        finally:
            batch.running = False
            batch.current = ""
            batch.finished_at = datetime.now(timezone.utc).isoformat()

    def articles_coverage() -> dict:
        total = written = 0
        for d in all_deck_topics():
            have = services.knowledge.articles_for_deck(d["id"])
            total += len(d["topics"])
            written += sum(1 for t in d["topics"] if t in have)
        return {"topics_total": total, "topics_written": written}

    @r.post("/api/textbook/generate-all")
    def generate_all(body: GenerateAllIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        decks = all_deck_topics()
        if body.deck_id:
            decks = [d for d in decks if d["id"] == body.deck_id]
            if not decks:
                raise HTTPException(404, "Колода не найдена")
        items = [(d["id"], t) for d in decks for t in d["topics"]]
        if not body.regenerate:
            items = [(i, t) for i, t in items if t not in services.knowledge.articles_for_deck(i)]
        if not items:
            return {"ok": True, "queued": 0}
        with batch_lock:
            if batch.running:
                raise HTTPException(409, "Генерация уже идёт")
            batch.__init__()  # сброс состояния
            batch.running = True
            batch.total = len(items)
            batch.started_at = datetime.now(timezone.utc).isoformat()
            batch.say(f"В очереди тем: {len(items)}")
        threading.Thread(target=run_batch, args=(items, body.regenerate), daemon=True, name="textbook-batch").start()
        return {"ok": True, "queued": len(items)}

    @r.post("/api/textbook/generate-all/stop")
    def generate_all_stop(ctx: UserContext = Depends(current_ctx)) -> dict:
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        batch.stop = True
        return {"ok": True}

    # ── управление базой знаний ─────────────────────────────────────

    @r.get("/api/knowledge/status")
    def knowledge_status(ctx: UserContext = Depends(current_ctx)) -> dict:
        stats = services.knowledge.stats()
        return {
            "sources": [
                {
                    "id": s.id,
                    "title": s.title,
                    "url": s.homepage,
                    "description": s.description,
                    "pages": stats.get(s.id, {}).get("pages", 0),
                    "chunks": stats.get(s.id, {}).get("chunks", 0),
                    "embedded": stats.get(s.id, {}).get("embedded", 0),
                    "updated_at": stats.get(s.id, {}).get("updated_at"),
                }
                for s in SOURCES.values()
            ],
            "job": services.indexer.job.public(),
            "articles": batch.public() | articles_coverage(),
            "embed_model": services.embed_model(),
            "textbook_model": services.textbook_model(),
        }

    @r.post("/api/knowledge/rebuild")
    def knowledge_rebuild(body: RebuildIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        if body.source_id == "all":
            ids = list(SOURCES)
            if not body.download:  # довекторизовать только уже загруженные
                stats = services.knowledge.stats()
                ids = [s for s in ids if stats.get(s, {}).get("chunks")]
        elif body.source_id in SOURCES:
            ids = [body.source_id]
        else:
            raise HTTPException(400, "Неизвестный источник")
        started = services.indexer.start(
            ids, services.rag_client(), services.embed_model(), download=body.download, context={"decks": all_deck_topics(with_vocab=True)}
        )
        if not started:
            raise HTTPException(409, "Индексация уже идёт")
        return {"ok": True}

    return r
