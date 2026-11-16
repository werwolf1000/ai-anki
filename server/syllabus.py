"""Учебные программы учебника: главы (основные темы) и уроки (подтемы).

Программа — текстовый файл <id>.txt:

    title: PHP
    match: php8-plus|pro-php|php-live
    kind: code            # code — две колоды (вопросы + live-coding), theory / math / anatomy — одна
    lang: php             # язык кода для live-coding и подсветки
    # 1. Продвинутое ООП
    SOLID-принципы: SRP, OCP, LSP, ISP, DIP
    Traits — горизонтальное переиспользование кода

Встроенные программы лежат в decks/syllabus/ (в Docker — только чтение), правки из интерфейса
сохраняются в <data>/syllabus/<id>.txt и перекрывают встроенный файл с тем же id.
`match` — регулярное выражение по «<deck_id> <имя файла> <название колоды>» (видео, старые колоды).
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path

SYLLABUS_DIR = Path(__file__).resolve().parent.parent / "decks" / "syllabus"


def override_dir() -> Path:
    from app.config_store import data_dir

    return Path(os.environ.get("AI_ANKI_SYLLABUS_DIR") or data_dir() / "syllabus")


@dataclass
class Chapter:
    title: str
    lessons: list[str] = field(default_factory=list)


@dataclass
class Syllabus:
    id: str
    title: str
    match: str
    chapters: list[Chapter]
    kind: str = "theory"  # code | theory | math | anatomy
    lang: str = ""
    track: str = ""  # учебник профессии: id трека из decks/tracks.json
    edited: bool = False  # есть правки из интерфейса (файл в <data>/syllabus)

    @property
    def key(self) -> str:
        """Ключ статей и отметок «прочитано» — общий для всех колод программы."""
        return f"book:{self.id}"

    @property
    def is_code(self) -> bool:
        return self.kind == "code"

    @property
    def has_practice(self) -> bool:
        return self.is_code or bool(self.track)

    def lessons(self) -> list[tuple[str, str]]:
        return [(ch.title, ls) for ch in self.chapters for ls in ch.lessons]

    def lesson_titles(self) -> list[str]:
        return [ls for ch in self.chapters for ls in ch.lessons]

    def chapter_of(self, lesson: str) -> str | None:
        for ch in self.chapters:
            if lesson in ch.lessons:
                return ch.title
        return None

    def to_text(self) -> str:
        head = [f"title: {self.title}", f"match: {self.match}", f"kind: {self.kind}"]
        if self.lang:
            head.append(f"lang: {self.lang}")
        if self.track:
            head.append(f"track: {self.track}")
        body = []
        for ch in self.chapters:
            body.append(f"# {ch.title}")
            body.extend(ch.lessons)
        return "\n".join(head + body) + "\n"


def parse_syllabus(sid: str, text: str) -> Syllabus:
    title, match, kind, lang, track, chapters = sid, "", "theory", "", "", []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if not chapters and re.match(r"^(title|match|kind|lang|track):", line):
            key, value = line.split(":", 1)
            value = value.split("  #")[0].strip()
            if key == "title":
                title = value
            elif key == "match":
                match = value
            elif key == "kind":
                kind = value or "theory"
            elif key == "track":
                track = value
            else:
                lang = value
        elif line.startswith("#"):
            chapters.append(Chapter(line.lstrip("#").strip()))
        else:
            if not chapters:
                raise ValueError(f"{sid}: урок «{line}» вне главы")
            if line in seen:
                raise ValueError(f"{sid}: урок «{line}» повторяется")
            seen.add(line)
            chapters[-1].lessons.append(line)
    if not match:
        raise ValueError(f"{sid}: нет строки match:")
    return Syllabus(sid, title, match, chapters, kind=kind, lang=lang, track=track)


_cache: dict[str, tuple[float, Syllabus]] = {}


def _read(path: Path) -> Syllabus:
    mtime = path.stat().st_mtime
    hit = _cache.get(str(path))
    if not hit or hit[0] != mtime:
        hit = (mtime, parse_syllabus(path.stem, path.read_text(encoding="utf-8")))
        _cache[str(path)] = hit
    return hit[1]


def all_syllabi(directory: Path = SYLLABUS_DIR) -> list[Syllabus]:
    """Программы: встроенные, перекрытые правками из <data>/syllabus (по id)."""
    books: dict[str, Syllabus] = {}
    for path in sorted(directory.glob("*.txt")):
        books[path.stem] = _read(path)
    over = override_dir()
    if directory == SYLLABUS_DIR and over.is_dir():
        for path in sorted(over.glob("*.txt")):
            try:
                sy = copy(_read(path))
            except (OSError, ValueError):
                continue
            sy.edited = True
            # Старые пользовательские программы ещё не содержат связь с профессией.
            builtin = books.get(path.stem)
            if builtin and not sy.track:
                sy.track = builtin.track
            books[path.stem] = sy
    return [books[k] for k in sorted(books)]


def track_syllabus(track_id: str) -> Syllabus | None:
    return next((s for s in all_syllabi() if s.track == track_id), None)


def get_syllabus(sid: str) -> Syllabus | None:
    return next((s for s in all_syllabi() if s.id == sid), None)


def save_syllabus(sy: Syllabus) -> None:
    """Сохранить правку программы в <data>/syllabus (встроенный файл не трогается)."""
    over = override_dir()
    over.mkdir(parents=True, exist_ok=True)
    path = over / f"{sy.id}.txt"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(sy.to_text(), encoding="utf-8")
    tmp.replace(path)
    _cache.pop(str(path), None)


BOOK_FILE = re.compile(r"^book-(.+?)(?:-live-coding)?$")


def syllabus_for(deck_id: str, name: str, paths: list[str] | None = None) -> Syllabus | None:
    books = all_syllabi()
    for p in paths or []:  # колоды учебников: book-<id>.json / book-<id>-live-coding.json
        m = BOOK_FILE.match(Path(p).stem)
        if m:
            hit = next((s for s in books if s.id == m[1]), None)
            if hit:
                return hit
    hay = " ".join([deck_id, name, *(Path(p).stem for p in (paths or []))]).lower()
    for p in paths or []:
        stem = Path(p).stem
        if stem.startswith("pro-"):
            track = stem.removeprefix("pro-").removesuffix("-live-coding")
            hit = next((s for s in books if s.track == track), None)
            if hit:
                return hit
    # сначала учебники профессий: колоды pro-* относятся к ним, а не к общим учебникам языков
    for sy in sorted(books, key=lambda s: not s.track):
        if re.search(sy.match, hay, re.I):
            return sy
    return None


# ── подбор карточек к уроку ─────────────────────────────────────────

_WORD = re.compile(r"[a-zа-яё0-9_]{3,}", re.I)
_STOP = {
    "что", "как", "для", "это", "или", "при", "все", "его", "так", "чем", "где", "когда", "the", "and", "with",
    "работа", "основы", "через", "между", "vs", "под", "капотом", "настройка", "когда", "почему",
}


def stems(text: str) -> set[str]:
    return {w[:6] for w in (m.lower() for m in _WORD.findall(text)) if w not in _STOP}


class CardIndex:
    """Ранжирование карточек колоды по близости к названию урока (IDF-взвешенное пересечение основ)."""

    def __init__(self, cards: list) -> None:
        self.cards = cards
        self.card_stems = [stems(f"{c.topic} {c.question} {c.reference[:400]}") for c in cards]
        df = Counter(s for cs in self.card_stems for s in cs)
        n = max(len(cards), 1)
        self.idf = {s: math.log(1 + n / k) for s, k in df.items()}

    def rank(self, query: str, context: str = "", limit: int = 8) -> list:
        """Слова урока решают, слова главы (context) лишь слегка подтягивают близкие карточки."""
        q = stems(query)
        ctx = stems(context) - q
        scored = []
        for card, cs in zip(self.cards, self.card_stems):
            hit = q & cs
            if not hit:
                continue
            score = sum(self.idf.get(s, 0.0) for s in hit) + 0.25 * sum(self.idf.get(s, 0.0) for s in ctx & cs)
            if score > 0:
                scored.append((score, card))
        if not scored:
            return []
        scored.sort(key=lambda x: -x[0])
        floor = scored[0][0] * 0.35
        return [c for s, c in scored[:limit] if s >= floor]


def main_topic(cards: list) -> str:
    topics = Counter(c.topic.strip() for c in cards if c.topic.strip())
    return topics.most_common(1)[0][0] if topics else ""
