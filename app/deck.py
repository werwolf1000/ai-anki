from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Card:
    question: str
    reference: str
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(abs(hash(self.question)) % 10_000_000)


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ReviewResult:
    correct: bool
    score: int
    feedback: str
    hint: str = ""
    follow_up: str = ""
    reference_summary: str = ""
    raw: str = ""


@dataclass
class CardProgress:
    card_id: str
    attempts: int = 0
    best_score: int = 0
    mastered: bool = False
    last_score: int = 0


@dataclass
class Deck:
    name: str
    cards: list[Card] = field(default_factory=list)

    @classmethod
    def load_json(cls, path: str | Path) -> Deck:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, list):
            cards = [Card(**item) if isinstance(item, dict) else Card(question=str(item), reference="") for item in data]
            return cls(name=Path(path).stem, cards=cards)
        cards = [Card(**c) for c in data.get("cards", [])]
        return cls(name=data.get("name", Path(path).stem), cards=cards)

    @classmethod
    def load_anki_txt(cls, path: str | Path) -> Deck:
        cards: list[Card] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" not in line:
                continue
            front, back = line.split("\t", 1)
            front = _strip_html(front)
            back = _strip_html(back)
            if front:
                cards.append(Card(question=front, reference=back))
        return cls(name=Path(path).stem, cards=cards)


def _strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<code>(.*?)</code>", r"\1", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()
