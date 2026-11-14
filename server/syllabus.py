"""Учебные программы учебника: главы и уроки, не зависящие от тем карточек.

Программа — текстовый файл decks/syllabus/<id>.txt:

    title: PHP
    match: php8-plus|pro-php|php-live
    # 1. Продвинутое ООП
    SOLID-принципы: SRP, OCP, LSP, ISP, DIP
    Traits — горизонтальное переиспользование кода

`match` — регулярное выражение по «<deck_id> <имя файла> <название колоды>».
Строка `# …` начинает главу, остальные непустые строки — уроки главы.
Уроки одной программы общие для всех её колод: статья пишется один раз.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

SYLLABUS_DIR = Path(__file__).resolve().parent.parent / "decks" / "syllabus"


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

    @property
    def key(self) -> str:
        """Ключ статей и отметок «прочитано» — общий для всех колод программы."""
        return f"book:{self.id}"

    def lessons(self) -> list[tuple[str, str]]:
        return [(ch.title, ls) for ch in self.chapters for ls in ch.lessons]

    def chapter_of(self, lesson: str) -> str | None:
        for ch in self.chapters:
            if lesson in ch.lessons:
                return ch.title
        return None


def parse_syllabus(sid: str, text: str) -> Syllabus:
    title, match, chapters = sid, "", []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("title:") and not chapters:
            title = line[6:].strip()
        elif line.startswith("match:") and not chapters:
            match = line[6:].strip()
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
    return Syllabus(sid, title, match, [c for c in chapters if c.lessons])


_cache: dict[str, tuple[float, Syllabus]] = {}


def all_syllabi(directory: Path = SYLLABUS_DIR) -> list[Syllabus]:
    out = []
    for path in sorted(directory.glob("*.txt")):
        mtime = path.stat().st_mtime
        hit = _cache.get(str(path))
        if not hit or hit[0] != mtime:
            hit = (mtime, parse_syllabus(path.stem, path.read_text(encoding="utf-8")))
            _cache[str(path)] = hit
        out.append(hit[1])
    return out


def syllabus_for(deck_id: str, name: str, paths: list[str] | None = None) -> Syllabus | None:
    hay = " ".join([deck_id, name, *(Path(p).stem for p in (paths or []))]).lower()
    for sy in all_syllabi():
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
