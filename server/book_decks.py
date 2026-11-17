"""Колоды учебников: по одной теме на урок программы.

Для каждой программы (server/syllabus.py) в <data>/decks лежат:
    book-<id>.json               — вопросы (вопрос → эталон)
    book-<id>-live-coding.json   — live-coding и практические задания профессий

При первом запуске в них раскладываются карточки прежних колод этого учебника (по близости к урокам),
прогресс повторений переносится по id карточек, прежние колоды скрываются. Колоды профессий (pro-*)
также переходят на колоды учебников: они используются в экзаменах и сертификатах.

Правка программы (добавить / переименовать / удалить главу или урок) переносит за уроком его карточки,
статью, отметки «прочитано» и привязки видео. Недостающие карточки догенерирует выбранная модель учебника.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.card_targets import QA_TARGET, LIVE_TARGET, PROFESSION_QA_TARGET, PROFESSION_LIVE_TARGET, card_targets
from server.syllabus import Chapter, Syllabus, all_syllabi, get_syllabus, save_syllabus, stems, syllabus_for

STATE_VERSION = 1
CARD_FIELDS = ("question", "reference", "card_type", "code", "task", "language", "answer_mode", "image", "image_alt")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def card_to_raw(card) -> dict:
    raw = {"id": card.id}
    for k in CARD_FIELDS:
        v = getattr(card, k, "")
        if v:
            raw[k] = v
    return raw


def _norm(q: str) -> str:
    return re.sub(r"[\W_]+", " ", q.lower()).strip()


def is_duplicate(question: str, existing: list[str]) -> bool:
    n = _norm(question)
    qs = stems(question)
    for e in existing:
        if _norm(e) == n:
            return True
        es = stems(e)
        if qs and es and len(qs & es) / len(qs | es) >= 0.75:
            return True
    return False


# ── раскладка карточек по урокам ────────────────────────────────────


class LessonMatcher:
    """Карточка → урок: по смыслу (эмбеддинги Ollama), а если их нет — по словам названия урока."""

    def __init__(self, sy: Syllabus, embed: Callable[[list[str]], np.ndarray] | None = None) -> None:
        self.sy = sy
        self.lessons = sy.lessons()  # [(глава, урок)]
        self.embed = embed
        self.lesson_stems = [stems(ls) for _, ls in self.lessons]
        self.chapter_stems = [stems(ch) for ch, _ in self.lessons]
        df = Counter(s for ls in self.lesson_stems for s in ls)
        n = max(1, len(self.lessons))
        self.idf = {s: math.log(1 + n / k) for s, k in df.items()}
        self._vecs = None
        self.used_vectors = False  # все карточки разложены по эмбеддингам
        self.used_topics = False  # автор уже указал точные названия уроков

    def _lexical(self, text: str, topic: str) -> tuple[float, int]:
        cs = stems(text)
        ts = stems(topic)
        best, best_i = 0.0, -1
        for i, (ls, chs) in enumerate(zip(self.lesson_stems, self.chapter_stems)):
            score = sum(self.idf.get(s, 0) for s in ls & cs) + 1.5 * sum(self.idf.get(s, 0) for s in ls & ts)
            score += 0.3 * sum(1 for s in chs & (cs | ts))
            if score > best:
                best, best_i = score, i
        return best, best_i

    def assign(self, cards: list[dict]) -> list[str]:
        """Урок для каждой карточки (raw dict с полями question/reference/topic)."""
        self.used_topics = self.used_vectors = False
        if not self.lessons:
            return [""] * len(cards)
        exact = {lesson for _, lesson in self.lessons}
        if cards and all(c.get("topic") in exact for c in cards):
            self.used_topics = True
            return [c["topic"] for c in cards]
        out: list[int] = [-1] * len(cards)
        if self.embed is not None:
            try:
                if self._vecs is None:
                    self._vecs = self.embed([f"Урок «{ls}» (глава «{ch}», учебник «{self.sy.title}»)" for ch, ls in self.lessons])
                for start in range(0, len(cards), 32):
                    part = cards[start:start + 32]
                    vecs = self.embed([
                        f"{c.get('topic', '')}. {c.get('question', '')}\n{str(c.get('reference', ''))[:400]}" for c in part
                    ])
                    sims = vecs @ self._vecs.T
                    for j, row in enumerate(sims):
                        out[start + j] = int(np.argmax(row))
                self.used_vectors = True
            except Exception:  # noqa: BLE001 — Ollama недоступна → по словам
                out = [-1] * len(cards)
        if any(i < 0 for i in out):
            topic_votes: dict[str, Counter] = {}
            for k, c in enumerate(cards):
                if out[k] >= 0:
                    continue
                score, i = self._lexical(f"{c.get('question', '')} {str(c.get('reference', ''))[:300]}", c.get("topic", ""))
                if score > 0:
                    out[k] = i
                    topic_votes.setdefault(c.get("topic", ""), Counter())[i] += 1
            for k, c in enumerate(cards):  # без совпадений — туда, куда ушло большинство карточек той же темы
                if out[k] < 0:
                    votes = topic_votes.get(c.get("topic", ""))
                    out[k] = votes.most_common(1)[0][0] if votes else 0
        return [c["topic"] if c.get("topic") in exact else self.lessons[i][1] for c, i in zip(cards, out)]


# ── задача генерации карточек ───────────────────────────────────────


@dataclass
class CardJob:
    running: bool = False
    stop: bool = False
    done: int = 0
    total: int = 0
    added_qa: int = 0
    added_live: int = 0
    failed: int = 0
    current: str = ""
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    status: str = "idle"
    remaining_lessons: int = 0
    remaining_qa: int = 0
    remaining_live: int = 0
    active: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    def say(self, msg: str) -> None:
        self.log.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")
        del self.log[:-60]

    def public(self) -> dict:
        keys = ("running", "done", "total", "added_qa", "added_live", "failed", "current", "error", "started_at", "finished_at",
                "status", "remaining_lessons", "remaining_qa", "remaining_live", "active")
        return {k: getattr(self, k) for k in keys} | {"log": self.log[-12:]}


QA_SYSTEM = """Ты составляешь карточки для интервального повторения (вопрос → эталонный ответ) для подготовки
к собеседованиям и экзаменам. Пиши по-русски; термины, имена функций и код не переводи.
Требования:
- каждый вопрос проверяет одну конкретную идею именно этого урока; без вопросов «да/нет»;
- эталон — точный ответ на 2–6 предложений, при необходимости короткий пример кода в блоке ```;
- опирайся на материалы урока, ничего не выдумывай; не повторяй уже существующие вопросы.
Верни ТОЛЬКО JSON-массив без пояснений: [{"question": "...", "reference": "..."}]"""

MATH_SYSTEM = """Ты составляешь задачи по высшей математике для интервального повторения. Пиши по-русски.
Каждая задача — короткое упражнение по теме урока (вычислить, найти, доказать короткое утверждение);
формулы в LaTeX внутри $...$. Эталон — итоговый ответ в LaTeX без $ (например f'(x)=2x) и, если нужно,
одна строка пояснения после «; ». Не повторяй уже существующие задачи.
Верни ТОЛЬКО JSON-массив: [{"question": "...", "reference": "..."}]"""

LIVE_SYSTEM = """Ты составляешь задания live-coding для собеседований. Основной язык профессии: {lang}.
Каждое задание — небольшая самостоятельная задача по теме урока: что реализовать (функция/класс/скрипт),
входные данные и результат, ограничения и пример вызова. Решение — эталонный рабочий код,
5–40 строк, идиоматичный и с обработкой краевых случаев. Для темы SQL используй SQL,
для Dockerfile — Dockerfile, для Terraform — HCL, для конфигураций — YAML/JSON,
когда это соответствует изучаемому навыку. Укажи фактический язык в language.
Пиши формулировки по-русски. Приведи конкретные входы, ожидаемые результаты и критерии приёмки.
Не повторяй уже существующие задания.
Верни ТОЛЬКО JSON-массив: [{"task": "...", "solution": "...", "language": "..."}]"""


def parse_json_array(text: str) -> list[dict]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M)
    a, b = text.find("["), text.rfind("]")
    if a < 0 or b <= a:
        return []
    try:
        data = json.loads(text[a:b + 1])
    except ValueError:
        # частая ошибка моделей — неэкранированные переводы строк внутри строк
        try:
            data = json.loads(re.sub(r"(?<!\\)\n", "\\\\n", text[a:b + 1]))
        except ValueError:
            return []
    return [x for x in data if isinstance(x, dict)] if isinstance(data, list) else []


# ── менеджер ────────────────────────────────────────────────────────


class EditIn(BaseModel):
    op: str  # chapter.add | chapter.rename | chapter.delete | chapter.move | lesson.add | lesson.rename | lesson.delete | lesson.move
    chapter: str = ""
    lesson: str = ""
    title: str = ""
    index: int | None = None
    delta: int = 0


class GenerateIn(BaseModel):
    book: str = ""  # пусто — все учебники
    lesson: str = ""  # только этот урок
    qa_target: int | None = Field(default=None, ge=0, le=100)
    live_target: int | None = Field(default=None, ge=0, le=100)
    professions_only: bool = False
    workers: int = Field(default=1, ge=1, le=4)


class BookDecks:
    def __init__(self, services) -> None:
        self.services = services
        self.dir: Path = services.registry.custom_dir
        self.state_path: Path = services.data_dir / "books.json"
        self.lock = threading.RLock()
        self.job = CardJob()
        self.generation_path = services.data_dir / "card-generation.json"
        self._generation_request = None
        try:
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}
        self.state.setdefault("version", STATE_VERSION)
        self.state.setdefault("hidden", [])
        self.state.setdefault("built", {})
        self.state.setdefault("migrations", {})  # новая колода → прежние колоды (перенос прогресса)
        self.state.setdefault("assigned", {})  # учебник → «embeddings» | «words»: как разложены карточки
        for sid in self.state["built"]:  # собранные без отметки — считаем разложенными по словам
            self.state["assigned"].setdefault(sid, "words")
        self.assign_status = ""

    def _save_state(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.state_path)

    # — файлы колод —

    def paths(self, sy: Syllabus) -> tuple[Path, Path | None]:
        return self.dir / f"book-{sy.id}.json", (self.dir / f"book-{sy.id}-live-coding.json" if sy.has_practice else None)

    @staticmethod
    def _read(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"cards": []}

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)

    def _meta(self, sy: Syllabus, live: bool) -> dict:
        kind = "code" if sy.is_code else sy.kind
        if sy.has_practice:
            practice = "live-coding" if sy.is_code else "практикум"
            name = f"{sy.title} — {practice}" if live else f"{sy.title} — вопросы"
        else:
            name = sy.title
        return {
            "name": name,
            "language": (sy.lang or "markdown") if live else (sy.lang if sy.is_code else ("latex" if sy.kind == "math" else "")),
            "book": sy.id,
            "track": sy.track,
            "kind": "live" if live else kind,
            "topic_order": sy.lesson_titles(),
            "topic_chapters": {ls: ch for ch, ls in sy.lessons()},
        }

    def _entry_for(self, path: Path, name: str):
        reg = self.services.registry
        entry = reg.find_by_path(path)
        if entry is None:
            entry = reg._add_file_entry(path, name=name, scope="custom")
        if entry and entry.name != name:
            entry.name = name
        reg.save()
        return entry

    def deck_ids(self, sy: Syllabus) -> dict:
        qa, live = self.paths(sy)
        reg = self.services.registry
        out = {}
        for key, p in (("qa", qa), ("live", live)):
            if p and p.exists():
                e = reg.find_by_path(p)
                if e:
                    out[key] = e.deck_id
        return out

    def hidden(self) -> set[str]:
        return set(self.state.get("hidden", []))

    # — сборка и перенос —

    def source_entries(self, sy: Syllabus) -> list:
        out = []
        for entry in self.services.registry.entries:
            stems_ = [Path(p).stem for p in entry.paths]
            if any(s.startswith("book-") for s in stems_):
                continue
            hit = syllabus_for(entry.deck_id, entry.name, entry.paths)
            if hit and hit.id == sy.id:
                out.append(entry)
        return out

    @staticmethod
    def _is_pro(entry) -> bool:
        return any(Path(p).name.startswith("pro-") for p in entry.paths)

    def _embedder(self):
        services = self.services

        def embed(texts: list[str]) -> np.ndarray:
            return services.rag_client().embed(services.embed_model(), texts)

        return embed

    def build(self, sy: Syllabus, *, use_embeddings: bool = False, reassign: bool = False, say=lambda m: None) -> dict:
        """Собрать колоды учебника из прежних колод (новые карточки дописываются, уже перенесённые не трогаются).

        reassign=True — заново разложить перенесённые карточки по урокам (сгенерированные остаются на своих уроках).
        """
        with self.lock:
            qa_path, live_path = self.paths(sy)
            qa, live = self._read(qa_path), (self._read(live_path) if live_path else None)
            split_practice = live is not None and any(c.get("card_type") == "live_code" for c in qa.get("cards", []))
            # Ранее практикум теоретических профессий попадал в общую колоду.
            if live is not None:
                live_ids = {c["id"] for c in live.get("cards", [])}
                for c in qa.get("cards", []):
                    if c.get("card_type") == "live_code" and c["id"] not in live_ids:
                        live.setdefault("cards", []).append(c)
                        live_ids.add(c["id"])
                qa["cards"] = [c for c in qa.get("cards", []) if c.get("card_type") != "live_code"]
            have = {c["id"] for c in qa.get("cards", [])} | ({c["id"] for c in live.get("cards", [])} if live else set())
            have.update(qa.get("retired_ids", []))
            if live is not None:
                have.update(live.get("retired_ids", []))
            pending: list[tuple[dict, bool]] = []  # (raw, в live-колоду)
            sources = self.source_entries(sy)
            migrations: dict[str, set[str]] = {}
            if split_practice:
                old_qa = self.services.registry.find_by_path(qa_path)
                if old_qa:
                    migrations.setdefault(str(live_path), set()).add(old_qa.deck_id)
            for entry in sources:
                try:
                    deck = self.services.load_deck(entry)
                except Exception as exc:  # noqa: BLE001
                    say(f"[{sy.id}] колода «{entry.name}» не загрузилась: {exc}")
                    continue
                for card in deck.cards:
                    to_live = bool(live is not None and card.is_live_code)
                    target_path = live_path if to_live else qa_path
                    migrations.setdefault(str(target_path), set()).add(entry.deck_id)
                    if card.id in have:
                        continue
                    have.add(card.id)
                    raw = card_to_raw(card) | {"topic": card.topic, "origin": f"migrated:{entry.deck_id}"}
                    pending.append((raw, to_live))
            if reassign:
                for data, is_live in ((qa, False), (live, True)):
                    if not data:
                        continue
                    keep = []
                    for c in data.get("cards", []):
                        if str(c.get("origin", "")).startswith("migrated:"):
                            c["topic"] = c.get("orig_topic", c.get("topic", ""))
                            pending.append((c, is_live))
                        else:
                            keep.append(c)
                    data["cards"] = keep
            matcher = LessonMatcher(sy, self._embedder() if use_embeddings else None)
            used_vectors = False
            raws = [r for r, _ in pending]
            for r in raws:
                r.setdefault("orig_topic", r.get("topic", ""))
            lessons = matcher.assign([{"question": r.get("question", ""), "reference": r.get("reference", ""), "topic": r.get("orig_topic", "")} for r in raws])
            used_vectors = matcher.used_vectors
            for (raw, to_live), lesson in zip(pending, lessons):
                raw["topic"] = lesson
                (live if to_live else qa)["cards"].append(raw)
            for data, path, is_live in ((qa, qa_path, False), (live, live_path, True)):
                if data is None or path is None:
                    continue
                data.update(self._meta(sy, is_live))
                data.setdefault("retired_ids", [])
                self._write(path, data)
                entry = self._entry_for(path, data["name"])
                old = migrations.get(str(path), set())
                if sy.track:
                    ids = {c["id"] for c in data.get("cards", [])}
                    # Прогресс мог быть получен в прежнем учебнике языка или в общей колоде профессии.
                    for previous in self.services.registry.entries:
                        if previous.deck_id == entry.deck_id or not Path(previous.primary_path).name.startswith("book-"):
                            continue
                        if any(c.get("id") in ids for c in self._read(Path(previous.primary_path)).get("cards", [])):
                            old.add(previous.deck_id)
                if entry and old:
                    cur = set(self.state["migrations"].get(entry.deck_id, []))
                    self.state["migrations"][entry.deck_id] = sorted(cur | old)
            hidden = set(self.state["hidden"]) | {e.deck_id for e in sources if sy.track or not self._is_pro(e)}
            self.state["hidden"] = sorted(hidden)
            self.state["built"][sy.id] = _now()
            if sy.track:
                self.state.setdefault("track_books", {})[sy.id] = 1
            if pending:  # «words» — фоновая задача потом переразложит по смыслу
                if matcher.used_topics:
                    self.state["assigned"][sy.id] = "topics"
                elif not used_vectors:
                    self.state["assigned"][sy.id] = "words"
                elif reassign or sy.id not in self.state["assigned"]:
                    self.state["assigned"][sy.id] = "embeddings"
            else:
                self.state["assigned"].setdefault(sy.id, "embeddings")
            self._save_state()
        self.services._deck_cache.clear()
        self.migrate_loaded_progress()
        n_qa, n_live = len(qa.get("cards", [])), len(live.get("cards", [])) if live else 0
        say(f"[{sy.id}] перенесено {len(pending)} карточек; в колодах: вопросов {n_qa}, live-coding {n_live}")
        return {"moved": len(pending), "qa": n_qa, "live": n_live}

    def ensure_all(self) -> None:
        """Создать колоды для программ, у которых их ещё нет; обновить порядок тем и названия у остальных."""
        for sy in all_syllabi():
            try:
                if (sy.id not in self.state["built"] or not self.paths(sy)[0].exists()
                        or (sy.track and self.state.get("track_books", {}).get(sy.id) != 1)):
                    self.build(sy)
                else:
                    self.sync_meta(sy)
            except Exception as exc:  # noqa: BLE001 — одна программа не должна ронять остальные
                print(f"book decks [{sy.id}]: {exc}", flush=True)

    def start_refine(self) -> None:
        """Фоном: переразложить по смыслу (эмбеддинги) карточки учебников, разложенных по словам."""
        threading.Thread(target=self._refine_loop, daemon=True, name="book-refine").start()

    def _refine_loop(self) -> None:
        time.sleep(15)
        while True:
            todo = [s for s in all_syllabi() if self.state["assigned"].get(s.id) == "words"]
            if not todo:
                self.assign_status = ""
                return
            for i, sy in enumerate(todo, 1):
                self.assign_status = f"Раскладка карточек по смыслу: {sy.title} ({i}/{len(todo)})"
                try:
                    self.build(sy, use_embeddings=True, reassign=True)
                    if self.state["assigned"].get(sy.id) not in ("embeddings", "topics"):
                        raise RuntimeError("эмбеддинги недоступны")
                    print(f"book decks [{sy.id}]: карточки разложены по смыслу", flush=True)
                except Exception as exc:  # noqa: BLE001 — Ollama недоступна: повторим позже
                    self.assign_status = f"Раскладка по смыслу отложена: {exc}"
                    break
            else:
                continue
            time.sleep(1800)

    def sync_meta(self, sy: Syllabus) -> None:
        with self.lock:
            qa_path, live_path = self.paths(sy)
            if sy.has_practice and live_path and not live_path.exists():
                self._write(live_path, {"cards": [], "retired_ids": []} | self._meta(sy, True))
            for path, is_live in ((qa_path, False), (live_path, True)):
                if not path or not path.exists():
                    continue
                data = self._read(path)
                meta = self._meta(sy, is_live)
                if any(data.get(k) != v for k, v in meta.items()):
                    data.update(meta)
                    self._write(path, data)
                self._entry_for(path, meta["name"])
        self.services._deck_cache.clear()

    # — прогресс —

    def migrate_progress(self, progress) -> bool:
        """Скопировать прогресс карточек из прежних колод в колоды учебников (по id карточек)."""
        changed = False
        reg = self.services.registry
        for new_id, old_ids in self.state.get("migrations", {}).items():
            entry = reg.get(new_id)
            if not entry:
                continue
            try:
                ids = {c.id for c in self.services.load_deck(entry).cards}
            except Exception:  # noqa: BLE001
                continue
            target = progress.data.setdefault(new_id, {})
            for old in old_ids:
                for cid, prog in progress.data.get(old, {}).items():
                    if cid in ids and cid not in target:
                        target[cid] = copy.deepcopy(prog)
                        changed = True
        if changed:
            progress.save()
        return changed

    def migrate_loaded_progress(self) -> None:
        for ctx in list(self.services._contexts.values()):
            with ctx.lock:
                self.migrate_progress(ctx.progress)

    # — состав уроков —

    def lesson_for_card(self, sy: Syllabus, card_id: str) -> str:
        for path in self.paths(sy):
            if path:
                for card in self._read(path).get("cards", []):
                    if card.get("id") == card_id:
                        return card.get("topic", "")
        return ""

    def lesson_counts(self, sy: Syllabus) -> dict[str, dict]:
        qa_path, live_path = self.paths(sy)
        out: dict[str, dict] = {ls: {"qa": 0, "live": 0} for ls in sy.lesson_titles()}
        for path, key in ((qa_path, "qa"), (live_path, "live")):
            if path and path.exists():
                for c in self._read(path).get("cards", []):
                    if c.get("topic") in out:
                        out[c["topic"]][key] += 1
        return out

    def _rewrite_cards(self, sy: Syllabus, fn: Callable[[dict], dict | None]) -> None:
        """fn(card) → card (изменённая) или None (удалить; id уходит в retired_ids)."""
        for path in self.paths(sy):
            if not path or not path.exists():
                continue
            data = self._read(path)
            keep, retired = [], set(data.get("retired_ids", []))
            for c in data.get("cards", []):
                res = fn(c)
                if res is None:
                    retired.add(c["id"])
                else:
                    keep.append(res)
            data["cards"], data["retired_ids"] = keep, sorted(retired)
            self._write(path, data)
        self.services._deck_cache.clear()

    def _rename_lesson_data(self, sy: Syllabus, old: str, new: str) -> None:
        def ren(c: dict) -> dict:
            if c.get("topic") == old:
                c["topic"] = new
            return c

        self._rewrite_cards(sy, ren)
        store = self.services.knowledge
        with store._lock, store._db:
            store._db.execute("DELETE FROM articles WHERE deck_id=? AND topic=?", (sy.key, new))
            store._db.execute("UPDATE articles SET topic=? WHERE deck_id=? AND topic=?", (new, sy.key, old))
        videos = getattr(self.services, "videos", None)
        if videos:
            videos.rename_lesson(sy.key, old, new)
        self._rewrite_marks(sy.key, lambda m: {(new if k == old else k): v for k, v in m.items()})

    def _delete_lesson_data(self, sy: Syllabus, lesson: str) -> None:
        self._rewrite_cards(sy, lambda c: None if c.get("topic") == lesson else c)
        store = self.services.knowledge
        with store._lock, store._db:
            store._db.execute("DELETE FROM articles WHERE deck_id=? AND topic=?", (sy.key, lesson))
        videos = getattr(self.services, "videos", None)
        if videos:
            videos.delete_lesson(sy.key, lesson)
        self._rewrite_marks(sy.key, lambda m: {k: v for k, v in m.items() if k != lesson})

    def _rewrite_marks(self, key: str, fn) -> None:
        for path in self.services.users_dir.glob("*/textbook.json"):
            try:
                marks = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if key in marks:
                marks[key] = fn(marks[key])
                path.write_text(json.dumps(marks, ensure_ascii=False, indent=1), encoding="utf-8")

    # — правка программы —

    def edit(self, sid: str, body: EditIn) -> Syllabus:
        with self.lock:
            sy = get_syllabus(sid)
            if sy is None:
                raise HTTPException(404, "Учебник не найден")
            sy = copy.deepcopy(sy)
            title = " ".join(body.title.split())
            chapters = sy.chapters
            ch_titles = [c.title for c in chapters]
            all_lessons = sy.lesson_titles()

            def chapter(name: str) -> Chapter:
                for c in chapters:
                    if c.title == name:
                        return c
                raise HTTPException(404, f"Глава «{name}» не найдена")

            def lesson_place(name: str) -> tuple[Chapter, int]:
                for c in chapters:
                    if name in c.lessons:
                        return c, c.lessons.index(name)
                raise HTTPException(404, f"Урок «{name}» не найден")

            op = body.op
            if op in ("chapter.add", "chapter.rename", "lesson.add", "lesson.rename") and not title:
                raise HTTPException(400, "Пустое название")
            if op in ("chapter.add", "chapter.rename") and title in ch_titles and title != body.chapter:
                raise HTTPException(400, "Глава с таким названием уже есть")
            if op in ("lesson.add", "lesson.rename") and title in all_lessons and title != body.lesson:
                raise HTTPException(400, "Урок с таким названием уже есть в этом учебнике")
            if op in ("lesson.add", "lesson.rename", "chapter.add", "chapter.rename") and (
                title.startswith(("#", "//")) or re.match(r"^(title|match|kind|lang):", title)
            ):
                raise HTTPException(400, "Название не может начинаться с «#», «//» или «title:/match:/kind:/lang:»")

            if op == "chapter.add":
                idx = len(chapters) if body.index is None else max(0, min(len(chapters), body.index))
                chapters.insert(idx, Chapter(title))
            elif op == "chapter.rename":
                chapter(body.chapter).title = title
            elif op == "chapter.delete":
                ch = chapter(body.chapter)
                for ls in list(ch.lessons):
                    self._delete_lesson_data(sy, ls)
                chapters.remove(ch)
            elif op == "chapter.move":
                i = ch_titles.index(chapter(body.chapter).title)
                j = max(0, min(len(chapters) - 1, i + body.delta))
                chapters.insert(j, chapters.pop(i))
            elif op == "lesson.add":
                ch = chapter(body.chapter)
                idx = len(ch.lessons) if body.index is None else max(0, min(len(ch.lessons), body.index))
                ch.lessons.insert(idx, title)
            elif op == "lesson.rename":
                ch, i = lesson_place(body.lesson)
                if title != body.lesson:
                    ch.lessons[i] = title
                    self._rename_lesson_data(sy, body.lesson, title)
            elif op == "lesson.delete":
                ch, i = lesson_place(body.lesson)
                ch.lessons.pop(i)
                self._delete_lesson_data(sy, body.lesson)
            elif op == "lesson.move":
                ch, i = lesson_place(body.lesson)
                j = i + body.delta
                ci = chapters.index(ch)
                if 0 <= j < len(ch.lessons):
                    ch.lessons.insert(j, ch.lessons.pop(i))
                elif j < 0 and ci > 0:  # выше первой — в конец предыдущей главы
                    chapters[ci - 1].lessons.append(ch.lessons.pop(i))
                elif j >= len(ch.lessons) and ci < len(chapters) - 1:  # ниже последней — в начало следующей
                    chapters[ci + 1].lessons.insert(0, ch.lessons.pop(i))
            else:
                raise HTTPException(400, "Неизвестная операция")
            save_syllabus(sy)
            fresh = get_syllabus(sid) or sy
            self.sync_meta(fresh)
            return fresh

    # — генерация карточек —

    def _generate(self, sy: Syllabus, lesson: str, need: int, live: bool, existing: list[str]) -> list[dict]:
        services = self.services
        ctx_text = services.lesson_context(sy, lesson) if hasattr(services, "lesson_context") else ""
        if live:
            system = LIVE_SYSTEM.replace("{lang}", sy.lang or "python")
            if not sy.is_code:
                system = (
                    f"Составь практические задания для профессии «{sy.title}» по указанному уроку. "
                    "Попроси подготовить промпт, план, разбор кейса или рабочий документ. "
                    "Не требуй программирования. Укажи конкретную ситуацию и критерии результата. "
                    'Верни только JSON-массив: [{"task": "задание", "solution": "эталон в Markdown"}]. Пиши по-русски.'
                )
        elif sy.kind == "math":
            system = MATH_SYSTEM
        else:
            system = QA_SYSTEM
        listed = "\n".join(f"- {q[:200]}" for q in existing[:40]) or "—"
        user = (
            f"Учебник: {sy.title}\nГлава: {sy.chapter_of(lesson)}\nУрок: {lesson}\n\n{ctx_text}\n\n"
            f"УЖЕ ЕСТЬ ({'задания' if live else 'вопросы'}):\n{listed}\n\n"
            f"Составь {need + 2} новых {'практических заданий' if live else 'карточек'} строго по уроку «{lesson}». "
            "Проверяй разные аспекты: основной приём, применение, ограничения, ошибки и граничные случаи. "
            "Не создавай перефразированные копии одного вопроса или задачи."
        )
        from server.knowledge import ThinkFilter

        filt = ThinkFilter()
        parts = []
        for piece in services.textbook_llm().stream(
            [{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.5
        ):
            parts.append(filt.feed(piece))
            if self.job.stop:
                return []
        parts.append(filt.flush())
        items = parse_json_array("".join(parts))
        out: list[dict] = []
        seen = list(existing)
        for it in items:
            fields = ('task', 'solution') if live else ('question', 'reference')
            if any(not isinstance(it.get(key), str) for key in fields):
                continue
            if live:
                q, ref = str(it.get("task", "")).strip(), str(it.get("solution", "")).strip()
                ref = re.sub(r"^```\w*\n|\n?```$", "", ref).strip()
            else:
                q, ref = str(it.get("question", "")).strip(), str(it.get("reference", "")).strip()
            if len(q) < 12 or len(ref) < (12 if sy.track else 2) or is_duplicate(q, seen):
                continue
            if live:
                lang = sy.lang or ("python" if sy.is_code else "markdown")
                suggested = str(it.get('language', '')).strip().lower()
                if sy.is_code and suggested in {'python', 'php', 'javascript', 'typescript', 'go', 'bash', 'shell',
                                                'yaml', 'json', 'dockerfile', 'sql', 'hcl', 'terraform', 'toml'}:
                    lang = suggested
                if lang == 'python':
                    import ast
                    try:
                        ast.parse(ref)
                    except SyntaxError:
                        continue
                card = {"card_type": "live_code", "question": q, "reference": ref, "language": lang}
            elif sy.kind == "math":
                card = {"card_type": "math", "answer_mode": "math", "question": q, "reference": ref}
            else:
                card = {"card_type": "text", "question": q, "reference": ref}
            seen.append(q)
            identity = json.dumps([sy.id, lesson, card['card_type'], q, ref], ensure_ascii=False)
            card_id = 'gen-' + hashlib.sha256(identity.encode()).hexdigest()[:24]
            out.append({"id": card_id, **card, "topic": lesson, "origin": "gen", "created_at": _now()})
            if len(out) >= need:
                break
        return out

    def _append(self, sy: Syllabus, live: bool, cards: list[dict]) -> int:
        if not cards:
            return 0
        with self.lock:
            qa_path, live_path = self.paths(sy)
            path = live_path if live else qa_path
            data = self._read(path)
            ids = {c["id"] for c in data.get("cards", [])}
            ids.update(data.get("retired_ids", []))
            questions = {}
            for card in data.get("cards", []):
                questions.setdefault(card.get("topic"), []).append(card.get("question", ""))
            new = []
            for card in cards:
                seen = questions.setdefault(card.get("topic"), [])
                if card["id"] in ids or is_duplicate(card["question"], seen):
                    continue
                new.append(card)
                ids.add(card["id"])
                seen.append(card["question"])
            data.setdefault("cards", []).extend(new)
            data.update(self._meta(sy, live))
            self._write(path, data)
            self._entry_for(path, data["name"])
        self.services._deck_cache.clear()
        return len(new)

    def coverage(self, body: GenerateIn) -> dict:
        books = [s for s in all_syllabi() if (not body.book or s.id == body.book)
                 and (not body.professions_only or s.track)]
        items: list[tuple[str, str]] = []
        missing_qa = missing_live = 0
        for sy in books:
            counts = self.lesson_counts(sy)
            targets = card_targets(sy, body.qa_target, body.live_target)
            for ls in sy.lesson_titles():
                if body.lesson and ls != body.lesson:
                    continue
                c = counts.get(ls, {"qa": 0, "live": 0})
                qa = max(0, targets['qa'] - c['qa'])
                live = max(0, targets['live'] - c['live'])
                missing_qa += qa
                missing_live += live
                if qa or live:
                    items.append((sy.id, ls))
        return {'items': items, 'remaining_lessons': len(items), 'remaining_qa': missing_qa, 'remaining_live': missing_live}

    def _checkpoint(self):
        with self.lock:
            if self._generation_request is None:
                return
            self._write(self.generation_path, {'request': self._generation_request.model_dump(), 'job': self.job.public()})

    def resume_generation(self):
        """Resume only a previously requested job interrupted by a server restart."""
        saved = self._read(self.generation_path)
        if saved.get('job', {}).get('status') == 'running' and saved.get('request'):
            self.start_generation(GenerateIn(**saved['request']))

    def stop_generation(self):
        with self.lock:
            self.job.stop = True
            self.job.status = 'stopped'
            self._checkpoint()

    def start_generation(self, body: GenerateIn) -> int:
        if body.book and get_syllabus(body.book) is None:
            raise HTTPException(404, 'Учебник не найден')
        with self.lock:
            if self.job.running:
                raise HTTPException(409, "Генерация карточек уже идёт")
            coverage = self.coverage(body)
            items = coverage.pop('items')
            self._generation_request = body
            if not items:
                self.job = CardJob(status='completed', finished_at=_now(), **coverage)
                self._checkpoint()
                return 0
            self.job = CardJob(running=True, status='running', total=len(items), started_at=_now(), **coverage)
            self.job.say(f"Уроков с нехваткой карточек: {len(items)}")
            self._checkpoint()
        threading.Thread(target=self._run, args=(items, body), daemon=True, name="book-cards").start()
        return len(items)

    def _fill_lesson(self, sid: str, lesson: str, body: GenerateIn):
        sy = get_syllabus(sid)
        if sy is None or lesson not in sy.lesson_titles():
            return
        label = f'{sy.title} › {lesson}'
        with self.lock:
            self.job.active.append(label)
            self.job.current = ' · '.join(self.job.active)
        try:
            targets = card_targets(sy, body.qa_target, body.live_target)
            for live in ((False, True) if sy.has_practice else (False,)):
                empty_attempts = 0
                while not self.job.stop:
                    path = self.paths(sy)[1 if live else 0]
                    with self.lock:
                        cards = [c for c in self._read(path).get('cards', []) if c.get('topic') == lesson]
                    need = targets['live' if live else 'qa'] - len(cards)
                    if need <= 0:
                        break
                    # Small responses avoid truncated JSON and allow checkpointing.
                    batch = min(need, 4 if live else 8)
                    t0 = time.time()
                    new = self._generate(sy, lesson, batch, live, [c.get('question', '') for c in cards])
                    if self.job.stop:
                        return
                    added = self._append(sy, live, new)
                    with self.lock:
                        if live:
                            self.job.added_live += added
                        else:
                            self.job.added_qa += added
                        self.job.say(f'{label}: +{added} {"заданий" if live else "вопросов"} за {time.time() - t0:.0f} с')
                        self._checkpoint()
                    empty_attempts = empty_attempts + 1 if added == 0 else 0
                    if empty_attempts >= 3:
                        raise RuntimeError(f'Модель не добавила новых карточек за три попытки; осталось {need}')
        finally:
            with self.lock:
                self.job.active.remove(label)
                self.job.current = ' · '.join(self.job.active)

    def _run(self, items: list[tuple[str, str]], body: GenerateIn) -> None:
        job = self.job
        streak = 0
        try:
            remaining = iter(items)
            # The desktop bridge processes one local-model request at a time.
            # Avoid a bulk queue expiring while Strata is still finishing a lesson.
            provider = str(getattr(self.services, 'config', {}).get('llm_textbook', '') or '')
            workers = 1 if provider.startswith('bridge:') else body.workers
            if workers < body.workers:
                job.say('Локальная модель через приложение: генерируем по одному уроку.')
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix='book-lesson') as pool:
                pending = {}
                def submit():
                    if job.stop or job.error:
                        return
                    item = next(remaining, None)
                    if item:
                        pending[pool.submit(self._fill_lesson, *item, body)] = item
                for _ in range(workers):
                    submit()
                while pending:
                    finished, _ = wait(pending, return_when=FIRST_COMPLETED)
                    for future in finished:
                        _, lesson = pending.pop(future)
                        try:
                            future.result()
                            streak = 0
                        except Exception as exc:  # noqa: BLE001
                            job.failed += 1
                            streak += 1
                            job.say(f'Ошибка «{lesson}»: {exc}')
                            if streak >= 3:
                                job.error = f'Три ошибки подряд, генерация остановлена: {exc}'
                        job.done += 1
                        submit()
                    coverage = self.coverage(body)
                    for key in ('remaining_lessons', 'remaining_qa', 'remaining_live'):
                        setattr(job, key, coverage[key])
                    self._checkpoint()
        finally:
            coverage = self.coverage(body)
            for key in ('remaining_lessons', 'remaining_qa', 'remaining_live'):
                setattr(job, key, coverage[key])
            job.status = 'stopped' if job.stop else 'incomplete' if job.remaining_lessons else 'completed'
            job.say(f'{"Готово" if job.status == "completed" else "Не завершено"}: +{job.added_qa} вопросов, '
                    f'+{job.added_live} заданий. Ещё не хватает: {job.remaining_qa} вопросов, {job.remaining_live} заданий.')
            job.running = False
            job.current = ""
            job.finished_at = _now()
            self._checkpoint()
            self.migrate_loaded_progress()


# ── API ─────────────────────────────────────────────────────────────


class BuildIn(BaseModel):
    book: str = ""
    embeddings: bool = True
    reassign: bool = False


def build_router(services, current_ctx) -> APIRouter:
    r = APIRouter()
    books: BookDecks = services.books

    def admin(ctx=Depends(current_ctx)):
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        return ctx

    def book_payload(sy: Syllabus) -> dict:
        counts = books.lesson_counts(sy)
        return {
            "id": sy.id, "title": sy.title, "kind": sy.kind, "lang": sy.lang, "is_code": sy.is_code, "edited": sy.edited,
            "track": sy.track, "has_practice": sy.has_practice,
            "targets": card_targets(sy),
            "decks": books.deck_ids(sy),
            "chapters": [
                {"title": ch.title, "lessons": [{"title": ls, **counts.get(ls, {"qa": 0, "live": 0})} for ls in ch.lessons]}
                for ch in sy.chapters
            ],
        }

    @r.get("/api/books")
    def list_books(ctx=Depends(current_ctx)) -> dict:
        out = []
        for sy in all_syllabi():
            counts = books.lesson_counts(sy)
            targets = card_targets(sy)
            out.append({
                "id": sy.id, "title": sy.title, "kind": sy.kind, "is_code": sy.is_code, "decks": books.deck_ids(sy),
                "track": sy.track, "has_practice": sy.has_practice,
                "chapters": len(sy.chapters), "lessons": len(counts),
                "qa": sum(c["qa"] for c in counts.values()), "live": sum(c["live"] for c in counts.values()),
                "thin": sum(1 for c in counts.values() if c["qa"] < targets['qa'] or c["live"] < targets['live']),
                "targets": targets,
                "assigned": books.state["assigned"].get(sy.id, ""),
            })
        return {
            "books": out, "job": books.job.public(), "targets": {"qa": QA_TARGET, "live": LIVE_TARGET},
            "profession_targets": {"qa": PROFESSION_QA_TARGET, "live": PROFESSION_LIVE_TARGET},
            "assign_status": books.assign_status,
        }

    @r.get("/api/books/{sid}")
    def get_book(sid: str, ctx=Depends(current_ctx)) -> dict:
        sy = get_syllabus(sid)
        if sy is None:
            raise HTTPException(404, "Учебник не найден")
        return book_payload(sy)

    @r.post("/api/books/{sid}/edit")
    def edit_book(sid: str, body: EditIn, ctx=Depends(admin)) -> dict:
        return book_payload(books.edit(sid, body))

    @r.post("/api/books/build")
    def build(body: BuildIn, ctx=Depends(admin)) -> dict:
        """Пересобрать колоды учебников (в фоне: раскладка по смыслу идёт минуты)."""
        if books.assign_status and not books.assign_status.startswith(("Готово", "Раскладка по смыслу отложена")):
            raise HTTPException(409, "Пересборка уже идёт")
        targets = [sy for sy in all_syllabi() if not body.book or sy.id == body.book]

        def run() -> None:
            done = 0
            for i, sy in enumerate(targets, 1):
                books.assign_status = f"Раскладка карточек: {sy.title} ({i}/{len(targets)})"
                try:
                    books.build(sy, use_embeddings=body.embeddings, reassign=body.reassign)
                    done += 1
                except Exception as exc:  # noqa: BLE001
                    books.assign_status = f"Раскладка по смыслу отложена: {exc}"
                    return
            books.assign_status = f"Готово: пересобрано учебников {done}"

        threading.Thread(target=run, daemon=True, name="book-build").start()
        return {"ok": True, "started": len(targets)}

    @r.post("/api/books/generate")
    def generate(body: GenerateIn, ctx=Depends(admin)) -> dict:
        return {"ok": True, "queued": books.start_generation(body)}

    @r.post("/api/books/generate/stop")
    def stop(ctx=Depends(admin)) -> dict:
        books.stop_generation()
        return {"ok": True}

    @r.get("/api/books-job")
    def job(ctx=Depends(admin)) -> dict:
        return books.job.public()

    return r
