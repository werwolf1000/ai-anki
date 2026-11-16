"""Интерактивный учебник: статьи по темам колод (RAG) и вопросы к учебнику."""
from __future__ import annotations

import json
import re
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
from server.syllabus import CardIndex, main_topic, stems, syllabus_for

# Порог косинусного сходства «урок ↔ фрагмент видео» (qwen3-embedding): своя тема 0.63–0.80,
# соседние темы ≤ 0.48, посторонние ≤ 0.41 — видео ниже порога в статью не попадают.
VIDEO_MIN_SIM = 0.45
VIDEO_K = 3
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


class LessonVideoIn(BaseModel):
    topic: str
    video: str
    action: str  # pin | block | reset
    start: float = 0.0


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


_VIDEO_MARK = re.compile(r"^[ \t]*\[\[video:(\d+)\]\][ \t]*\n?", re.M)


def clean_video_markers(content: str, sources: list[dict]) -> str:
    """Оставить маркеры [[video:n]] только для видеоисточников, каждое видео — один раз."""
    videos = {s["n"]: s.get("video") for s in sources if s.get("video")}
    used: set[str] = set()

    def keep(m: re.Match) -> str:
        vid = videos.get(int(m[1]))
        if not vid or vid in used:
            return ""
        used.add(vid)
        return m[0]

    return re.sub(r"\n{3,}", "\n\n", _VIDEO_MARK.sub(keep, content))


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

    def book_of(entry):
        return syllabus_for(entry.deck_id, entry.name, entry.paths)

    def book_key(entry) -> str:
        """Статьи и отметки программы общие для всех её колод."""
        sy = book_of(entry)
        return sy.key if sy else entry.deck_id

    def entry_key(deck_id: str) -> str:
        entry = services.registry.get(deck_id)
        if not entry:
            raise HTTPException(404, "Колода не найдена")
        return book_key(entry)

    _indexes: dict[str, tuple[int, CardIndex]] = {}

    def card_index(entry, deck) -> CardIndex:
        hit = _indexes.get(entry.deck_id)
        if not hit or hit[0] != len(deck.cards):
            hit = (len(deck.cards), CardIndex(deck.cards))
            _indexes[entry.deck_id] = hit
        return hit[1]

    def lesson_cards(entry, deck, topic: str, sy=None) -> list | None:
        """Карточки урока; None — такого урока/темы нет."""
        sy = sy or book_of(entry)
        if not sy:
            cards = topic_cards(deck, topic)
            return cards or None
        chapter = sy.chapter_of(topic)
        if chapter is None:
            return None
        if deck.book:  # колода учебника: тема карточки = урок
            return [c for c in deck.cards if c.topic == topic]
        return card_index(entry, deck).rank(topic, chapter, limit=8)

    def deck_sources(entry, deck) -> list[str]:
        stats = services.knowledge.stats()
        docs = [s for s in sources_for_deck(entry.deck_id, entry.name, deck.language) if stats.get(s, {}).get("chunks")]
        sy = book_of(entry)
        videos = getattr(services, "videos", None)
        return docs + (videos.sources_for_book(sy.id) if sy and videos else [])

    def all_deck_topics(with_vocab: bool = False) -> list[dict]:
        out = []
        for entry in services.registry.entries:
            try:
                deck = services.load_deck(entry)
            except Exception:  # noqa: BLE001 — битая колода не мешает остальным
                continue
            topics = sorted({c.topic.strip() or "Разное" for c in deck.cards})
            vocab = deck_vocab([c.question + " " + c.reference for c in deck.cards]) if with_vocab else []
            sy = book_of(entry) if with_vocab else None
            if sy and set(sources_for_deck(entry.deck_id, entry.name, deck.language)) <= {"wikipedia_ru"}:
                # только Википедия — ищем статьи и по урокам программы
                topics += [ls for _, ls in sy.lessons()]
            out.append({"id": entry.deck_id, "name": entry.name, "topics": topics, "vocab": vocab})
        return out

    def all_books() -> list[dict]:
        """Учебники без повторов: программа (общая для нескольких колод) или темы колоды."""
        out: list[dict] = []
        seen: set[str] = set()
        for entry in sorted(services.registry.entries, key=lambda e: e.is_live_coding):
            sy = book_of(entry)
            key = sy.key if sy else entry.deck_id
            if key in seen:
                continue
            if sy:
                topics = [ls for _, ls in sy.lessons()]
            else:
                try:
                    deck = services.load_deck(entry)
                except Exception:  # noqa: BLE001
                    continue
                topics = sorted({c.topic.strip() or "Разное" for c in deck.cards})
            seen.add(key)
            out.append({"key": key, "id": entry.deck_id, "name": sy.title if sy else entry.name, "topics": topics})
        return out

    def article_query(entry, topic: str, cards: list | None = None) -> str:
        """Запрос к базе знаний; без cards — короткий запрос для поиска видео."""
        sy = book_of(entry)
        chapter = sy.chapter_of(topic) if sy else None
        subject = sy.title if sy else entry.name
        q = f"{topic}. {chapter + '. ' if chapter else ''}{subject}."
        if cards:
            q += " " + " ".join(c.question.split("\n")[0][:160] for c in cards[:6])
        return q

    _attach_cache: dict[tuple, list[dict]] = {}

    def attach_videos(entry, deck, topic: str, cards: list, cached: dict) -> list[dict]:
        """Источники сохранённой статьи с учётом видео: скрытые админом убираются, закреплённые
        и найденные после написания статьи — добавляются (текст статьи не перегенерируется)."""
        videos_lib = getattr(services, "videos", None)
        videos = [s for s in deck_sources(entry, deck) if s.startswith("vid:")]
        links = videos_lib.links(book_key(entry), topic) if videos_lib else {"pin": [], "block": set()}
        if not videos and not links["pin"]:
            return cached["sources"]
        pinned = {p["video"]: p["start"] for p in links["pin"]}
        base = max((int(s.get("n", 0)) for s in cached["sources"]), default=0)
        kept = []
        for s in cached["sources"]:
            vid = s.get("video")
            if vid and (vid in links["block"] or (vid in pinned and int(s.get("start", 0)) != int(pinned[vid]))):
                continue  # скрыто или закреплено с другого момента — ссылка [n] в тексте станет серой
            kept.append(s | ({"pinned": True} if vid in pinned else {}))
        have = {s.get("source") for s in kept}
        key = (book_key(entry), topic, cached["created_at"], tuple(sorted(videos)), videos_lib.links_version if videos_lib else 0, min_sim())
        extra = _attach_cache.get(key)
        if extra is None:
            vq = article_query(entry, topic)
            rows = lesson_videos(entry, topic, embed_query(vq), videos, query=vq, exclude=have)
            _, extra = format_context(rows, [])
            extra = [s | ({"pinned": True} if r.get("pinned") else {}) for s, r in zip(extra, rows)]
            if len(_attach_cache) > 2000:
                _attach_cache.clear()
            _attach_cache[key] = extra
        return kept + [s | {"n": base + i + 1, "attached": True} for i, s in enumerate(extra)]

    def article_prompt(entry, deck, topic: str, cards: list) -> tuple[str, str, list[dict], str]:
        sy = book_of(entry)
        chapter = sy.chapter_of(topic) if sy else None
        chunks, mode = retrieve(
            article_query(entry, topic, cards), deck_sources(entry, deck), k=8, video_query=article_query(entry, topic),
            lesson=(entry, topic),
        )
        ctx_text, sources = format_context(
            chunks, [{"question": c.question, "reference": c.reference} for c in cards]
        )
        system = ARTICLE_SYSTEM.replace("{lang}", deck.language or "")
        if sy:
            user_prompt = (
                f"Учебник: {sy.title}\nГлава: {chapter}\nУрок: {topic}\n\n{ctx_text}\n\n"
                f"Напиши урок учебника «{topic}» (глава «{chapter}»). Раскрой именно эту тему, не пересказывай "
                "соседние уроки главы. Карточки — ориентир, что должен уметь читатель после урока."
            )
        else:
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
        sy = book_of(entry)
        key = sy.key if sy else deck_id
        marks = read_marks(ctx).get(key, {})
        written = services.knowledge.articles_for_deck(key)
        topics = []
        books = getattr(services, "books", None)
        decks = books.deck_ids(sy) if (sy and books) else {}
        if sy:
            counts = books.lesson_counts(sy) if books else {}
            idx = None if deck.book or counts else card_index(entry, deck)
            for chapter, lesson in sy.lessons():
                if idx is None:
                    c = counts.get(lesson, {"qa": 0, "live": 0})
                    n, live, card_topic = c["qa"], c["live"], lesson
                else:
                    cards = idx.rank(lesson, chapter, limit=8)
                    n, live, card_topic = len(cards), 0, main_topic(cards)
                topics.append({
                    "name": lesson, "chapter": chapter, "cards": n, "live": live, "card_topic": card_topic,
                    "read_at": marks.get(lesson), "has_article": lesson in written,
                })
        else:
            counts: dict[str, int] = {}
            for c in deck.cards:
                name = c.topic.strip() or "Разное"
                counts[name] = counts.get(name, 0) + 1
            topics = [
                {"name": n, "chapter": "", "cards": counts[n], "card_topic": n, "read_at": marks.get(n), "has_article": n in written}
                for n in sorted(counts)
            ]
        srcs = deck_sources(entry, deck)
        return {
            "deck_id": deck_id,
            "name": entry.name,
            "book": {"id": sy.id, "title": sy.title, "is_code": sy.is_code, "kind": sy.kind, "edited": sy.edited,
                     "track": sy.track, "has_practice": sy.has_practice,
                     "chapters": [c.title for c in sy.chapters]} if sy else None,
            "decks": decks,
            "topics": topics,
            "sources": [{"id": s, "title": SOURCES[s].title, "url": SOURCES[s].homepage} for s in srcs if s in SOURCES],
            "videos": sum(1 for s in srcs if s.startswith("vid:")),
        }

    @r.get("/api/textbook/{deck_id}/videos-debug")
    def videos_debug(deck_id: str, topic: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        """Диагностика для администратора: какие видео рассматривались для урока и почему."""
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        entry, deck = deck_and_entry(deck_id)
        sy = book_of(entry)
        videos = getattr(services, "videos", None)
        if not sy or not videos:
            return {"book": None, "videos": [], "candidates": [], "threshold": min_sim()}
        stats = services.knowledge.stats()
        summary = [
            v | {"embedded": stats.get(f"vid:{v['id']}", {}).get("embedded", 0)} for v in videos.book_summary(sy.id)
        ]
        srcs = videos.sources_for_book(sy.id)
        query = article_query(entry, topic)
        qvec = embed_query(query)
        cands = video_candidates(qvec, query, srcs, 10)
        rows = {r["id"]: r for r in services.knowledge.get_chunks([cid for _, cid, _ in cands])}
        return {
            "book": sy.id,
            "query": query,
            "embedding": qvec is not None,
            "threshold": min_sim(),
            "videos": summary,
            "candidates": [
                {"score": round(s, 3), "how": how, "title": rows[cid]["title"], "section": rows[cid]["section"],
                 "text": rows[cid]["text"][:160], "passed": how == "words" or s >= min_sim()}
                for s, cid, how in sorted(cands, reverse=True)[:10] if cid in rows
            ],
        }

    def lesson_context(sy, lesson: str) -> str:
        """Материалы урока для генерации карточек: статья (если написана) и фрагменты документации."""
        books = getattr(services, "books", None)
        qa_id = books.deck_ids(sy).get("qa") if books else None
        entry = services.registry.get(qa_id) if qa_id else None
        parts = []
        art = services.knowledge.get_article(sy.key, lesson)
        if art:
            parts.append("СТАТЬЯ УРОКА:\n" + art["content"][:6000])
        if entry:
            deck = services.load_deck(entry)
            docs = [s for s in deck_sources(entry, deck) if not s.startswith("vid:")]
            if docs:
                chunks, _ = retrieve(article_query(entry, lesson), docs, k=5)
                ctx_text, _ = format_context(chunks, [])
                parts.append(ctx_text)
        return "\n\n".join(parts)

    services.lesson_context = lesson_context  # type: ignore[attr-defined]

    @r.get("/api/textbook/{deck_id}/lesson-videos")
    def lesson_videos_get(deck_id: str, topic: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        """Админ: закреплённые/скрытые видео урока, подсказки со сходством и вся видеотека для ручного выбора."""
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        entry, deck = deck_and_entry(deck_id)
        lib = getattr(services, "videos", None)
        if lib is None:
            return {"enabled": False}
        sy = book_of(entry)
        key = book_key(entry)
        links = lib.links(key, topic)
        library = lib.library()
        by_id = {v["id"]: v for v in library}
        srcs = lib.sources_for_book(sy.id) if sy else []
        query = article_query(entry, topic)
        qvec = embed_query(query)
        cands = video_candidates(qvec, query, srcs, 12)
        rows = {r["id"]: r for r in services.knowledge.get_chunks([cid for _, cid, _ in cands])}
        thr = min_sim()
        suggestions, seen = [], set()
        for s, cid, how in sorted(cands, reverse=True):
            row = rows.get(cid)
            if not row or row["source"] in seen:
                continue
            seen.add(row["source"])
            vid = row["source"][4:]
            m = re.search(r"#t=(\d+)", row["url"])
            suggestions.append({
                "video": vid, "title": by_id.get(vid, {}).get("title", row["title"]), "folder": by_id.get(vid, {}).get("folder", ""),
                "start": int(m[1]) if m else 0, "section": row["section"], "text": row["text"][:220],
                "score": round(s, 3), "how": how, "passed": how == "words" or s >= thr,
                "pinned": vid in {p["video"] for p in links["pin"]}, "blocked": vid in links["block"],
            })
            if len(suggestions) >= 12:
                break
        return {
            "enabled": True,
            "book": sy.id if sy else None,
            "threshold": thr,
            "embedding": qvec is not None,
            "pins": [p | {"title": by_id.get(p["video"], {}).get("title", p["video"]), "folder": by_id.get(p["video"], {}).get("folder", "")} for p in links["pin"]],
            "blocks": [{"video": v, "title": by_id.get(v, {}).get("title", v), "folder": by_id.get(v, {}).get("folder", "")} for v in links["block"]],
            "suggestions": suggestions,
            "library": library,
        }

    @r.post("/api/textbook/{deck_id}/lesson-videos")
    def lesson_videos_set(deck_id: str, body: LessonVideoIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        if body.action not in ("pin", "block", "reset"):
            raise HTTPException(400, "Неизвестное действие")
        lib = getattr(services, "videos", None)
        if lib is None or lib.get(body.video) is None:
            raise HTTPException(404, "Видео не найдено")
        entry = services.registry.get(deck_id)
        if not entry:
            raise HTTPException(404, "Колода не найдена")
        lib.set_link(book_key(entry), body.topic.strip(), body.video, body.action, body.start)
        return {"ok": True}

    @r.get("/api/textbook/{deck_id}/article")
    def get_article(deck_id: str, topic: str, ctx: UserContext = Depends(current_ctx)) -> dict:
        key = entry_key(deck_id)
        art = services.knowledge.get_article(key, topic)
        marks = read_marks(ctx).get(key, {})
        return {"article": art, "read_at": marks.get(topic)}

    @r.post("/api/textbook/{deck_id}/read")
    def mark_read(deck_id: str, body: ReadIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        key = entry_key(deck_id)
        with ctx.lock:
            marks = read_marks(ctx)
            deck_marks = marks.setdefault(key, {})
            if body.read:
                deck_marks[body.topic] = datetime.now(timezone.utc).isoformat()
            else:
                deck_marks.pop(body.topic, None)
            save_marks(ctx, marks)
        return {"ok": True, "read_at": marks[key].get(body.topic)}

    # ── поиск по базе знаний ────────────────────────────────────────

    def embed_query(query: str):
        try:
            return services.rag_client().embed(services.embed_model(), [QUERY_INSTRUCT + query[:2000]])[0]
        except Exception:  # noqa: BLE001 — нет модели эмбеддингов → только BM25
            return None

    def min_sim() -> float:
        try:
            return float(services.config.get("video_min_sim") or VIDEO_MIN_SIM)
        except (TypeError, ValueError):
            return VIDEO_MIN_SIM

    def lexical_video_hits(query: str, sources: list[str], limit: int) -> list[tuple[float, int]]:
        """Для видео без векторов: фрагменты, где встречается больше половины основ слов урока."""
        want = stems(query)
        if not want or not sources:
            return []
        out = []
        for row in services.knowledge.get_chunks(services.knowledge.fts_search(query, sources, limit=limit * 4)):
            share = len(want & stems(row["title"] + " " + row["text"])) / len(want)
            if share > 0.5:
                out.append((share, int(row["id"])))
        return sorted(out, reverse=True)[:limit]

    def video_candidates(qvec, query: str, video_sources: list[str], k: int) -> list[tuple[float, int, str]]:
        """(оценка, id фрагмента, способ) — по векторам, а для видео без векторов — по словам."""
        stats = services.knowledge.stats()
        with_vec = [s for s in video_sources if stats.get(s, {}).get("embedded")]
        no_vec = [s for s in video_sources if s not in with_vec]
        out = []
        if qvec is not None and with_vec:
            out += [(s, cid, "vector") for s, cid in services.knowledge.vector_scores(qvec, with_vec, limit=k * 6)]
        if no_vec or qvec is None:
            out += [(s, cid, "words") for s, cid in lexical_video_hits(query, no_vec if qvec is not None else video_sources, k * 2)]
        return out

    def related_videos(qvec, video_sources: list[str], exclude: set[str] = frozenset(), k: int = VIDEO_K, query: str = "") -> list[dict]:
        """Фрагменты видео, близкие к запросу: не больше одного на видео, только выше порога сходства."""
        if not video_sources:
            return []
        thr = min_sim()
        scored = [(s, cid) for s, cid, how in video_candidates(qvec, query, video_sources, k) if how == "words" or s >= thr]
        picked, seen = [], set(exclude)
        for row in services.knowledge.get_chunks([cid for _, cid in scored]):
            if row["source"] in seen:
                continue
            seen.add(row["source"])
            picked.append(row)
            if len(picked) >= k:
                break
        return picked

    def lesson_videos(entry, topic: str, qvec, video_sources: list[str], query: str = "", exclude: set[str] = frozenset()) -> list[dict]:
        """Видео урока: сначала закреплённые админом (с выбранного момента), затем автоподбор без скрытых."""
        lib = getattr(services, "videos", None)
        links = lib.links(book_key(entry), topic) if lib else {"pin": [], "block": set()}
        pinned_rows = []
        for p in links["pin"]:
            if f"vid:{p['video']}" in exclude:
                continue
            row = lib.chunk_at(p["video"], p["start"])
            if row:
                pinned_rows.append(row)
        taken = set(exclude) | {r["source"] for r in pinned_rows} | {f"vid:{v}" for v in links["block"]}
        auto_sources = [s for s in video_sources if s not in taken]
        auto = related_videos(qvec, auto_sources, exclude=taken, k=max(0, VIDEO_K - len(pinned_rows)), query=query) if auto_sources else []
        return pinned_rows + auto

    def retrieve(query: str, sources: list[str], k: int, video_query: str = "", lesson: tuple | None = None) -> tuple[list[dict], str]:
        """Документация — гибридным поиском (k фрагментов), видео — отдельной квотой по порогу сходства.

        video_query — короткий запрос без образцов карточек: порог VIDEO_MIN_SIM откалиброван на нём.
        """
        lib = getattr(services, "videos", None)
        if not sources and not (lesson and lib and lib.links(book_key(lesson[0]), lesson[1])["pin"]):
            return [], "none"
        docs = [s for s in sources if not s.startswith("vid:")]
        videos = [s for s in sources if s.startswith("vid:")]
        qvec = embed_query(query)
        mode = "hybrid" if qvec is not None else "bm25"
        chunks = hybrid_search(services.knowledge, query, docs, qvec=qvec, k=k) if docs else []
        lib = getattr(services, "videos", None)
        has_pins = bool(lesson and lib and lib.links(book_key(lesson[0]), lesson[1])["pin"])
        vvec = embed_query(video_query) if video_query and videos else qvec
        if lesson:
            return chunks + lesson_videos(lesson[0], lesson[1], vvec, videos, query=video_query or query), mode
        return chunks + (related_videos(vvec, videos, query=video_query or query) if videos or has_pins else []), mode

    def stream_answer(system: str, user_prompt: str, sources: list[dict], mode: str, on_done=None) -> Iterator[str]:
        yield _ndjson({"type": "sources", "sources": sources, "retrieval": mode, "model": services.textbook_model()})
        text = []
        filt = ThinkFilter()
        try:
            for piece in services.textbook_llm().stream(
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
            yield _ndjson({"type": "error", "message": f"Модель ({services.textbook_model()}): {exc}"})
            return
        content = "".join(text).strip()
        if on_done and content:
            on_done(content)
        yield _ndjson({"type": "done"})

    @r.post("/api/textbook/{deck_id}/article/stream")
    def stream_article(deck_id: str, body: ArticleIn, ctx: UserContext = Depends(current_ctx)) -> StreamingResponse:
        entry, deck = deck_and_entry(deck_id)
        topic = body.topic.strip()
        cards = lesson_cards(entry, deck, topic)
        if cards is None:
            raise HTTPException(404, "В учебнике нет такой темы")
        key = book_key(entry)
        cached = services.knowledge.get_article(key, topic)
        if cached and not body.regenerate:
            srcs = attach_videos(entry, deck, topic, cards, cached)

            def replay() -> Iterator[str]:
                yield _ndjson({"type": "sources", "sources": srcs, "cached": True, "model": cached["model"]})
                yield _ndjson({"type": "delta", "text": cached["content"]})
                yield _ndjson({"type": "done", "cached": True})
            return StreamingResponse(replay(), media_type="application/x-ndjson")

        system, user_prompt, sources, mode = article_prompt(entry, deck, topic, cards)

        def save(content: str) -> None:
            content = clean_video_markers(strip_title(content, topic), sources)
            services.knowledge.save_article(key, topic, content, sources, services.textbook_model())

        return StreamingResponse(stream_answer(system, user_prompt, sources, mode, save), media_type="application/x-ndjson")

    @r.post("/api/textbook/{deck_id}/ask")
    def ask(deck_id: str, body: AskIn, ctx: UserContext = Depends(current_ctx)) -> StreamingResponse:
        entry, deck = deck_and_entry(deck_id)
        question = body.question.strip()
        if not question:
            raise HTTPException(400, "Пустой вопрос")
        topic = body.topic.strip()
        chunks, mode = retrieve(f"{topic}. {question}", deck_sources(entry, deck), k=6, video_query=question,
                                lesson=(entry, topic) if topic else None)
        cards = (lesson_cards(entry, deck, topic) or []) if topic else []
        ctx_text, sources = format_context(chunks, [{"question": c.question, "reference": c.reference} for c in cards], card_limit=8)
        user_prompt = f"Колода: {entry.name}\nТема: {topic or '—'}\n\n{ctx_text}\n\nВОПРОС: {question}"
        return StreamingResponse(stream_answer(ASK_SYSTEM, user_prompt, sources, mode), media_type="application/x-ndjson")

    # ── генерация статей для всех тем (фон) ─────────────────────────

    batch = ArticleBatch()
    services.article_batch = batch  # type: ignore[attr-defined]
    batch_lock = threading.Lock()

    def generate_one(entry, deck, topic: str) -> bool:
        cards = lesson_cards(entry, deck, topic)
        if cards is None:
            return False
        system, user_prompt, sources, _mode = article_prompt(entry, deck, topic, cards)
        filt = ThinkFilter()
        parts: list[str] = []
        for piece in services.textbook_llm().stream(
            [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
        ):
            parts.append(filt.feed(piece))
            if batch.stop:
                return False
        parts.append(filt.flush())
        content = clean_video_markers(strip_title("".join(parts).strip(), topic), sources)
        if len(content) < 200:
            raise RuntimeError("модель вернула слишком короткий текст")
        services.knowledge.save_article(book_key(entry), topic, content, sources, services.textbook_model())
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
                if not regenerate and services.knowledge.get_article(book_key(entry), topic):
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
        for d in all_books():
            have = services.knowledge.articles_for_deck(d["key"])
            total += len(d["topics"])
            written += sum(1 for t in d["topics"] if t in have)
        return {"topics_total": total, "topics_written": written}

    @r.post("/api/textbook/generate-all")
    def generate_all(body: GenerateAllIn, ctx: UserContext = Depends(current_ctx)) -> dict:
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        books = all_books()
        if body.deck_id:
            key = entry_key(body.deck_id)
            books = [d | {"id": body.deck_id} for d in books if d["key"] == key]
        items = [(d["id"], t) for d in books for t in d["topics"]]
        if not body.regenerate:
            have = {d["id"]: services.knowledge.articles_for_deck(d["key"]) for d in books}
            items = [(i, t) for i, t in items if t not in have[i]]
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
