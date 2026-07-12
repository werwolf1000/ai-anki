from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


def stable_card_id(question: str, code: str = "", task: str = "") -> str:
    """Стабильный id карточки — одинаковый на desktop, web и после перезапуска."""
    raw = (question + code + task).encode("utf-8")
    return str(int(hashlib.sha256(raw).hexdigest(), 16) % 10_000_000)


@dataclass
class Card:
    question: str
    reference: str
    id: str = ""
    card_type: str = "text"
    code: str = ""
    task: str = ""
    language: str = ""
    answer_mode: str = ""
    topic: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            if self.is_live_code and self.reference.strip():
                # id не зависит от формулировки question — только от эталона
                self.id = stable_card_id("", "", self.reference.strip())
            else:
                self.id = stable_card_id(self.question, self.code, self.task)

    @property
    def is_live_code(self) -> bool:
        return self.card_type == "live_code"

    @property
    def is_code(self) -> bool:
        return self.card_type in ("code", "live_code") or bool(self.code)

    @property
    def is_math(self) -> bool:
        return self.card_type == "math" or self.answer_mode == "math"

    @property
    def needs_code_editor(self) -> bool:
        if self.is_math:
            return False
        if self.answer_mode == "text":
            return False
        if self.answer_mode == "code":
            return True
        return self.card_type in ("code", "live_code")

    @property
    def needs_math_editor(self) -> bool:
        if self.answer_mode == "text" or self.answer_mode == "code":
            return False
        return self.is_math

    def display_text(self) -> str:
        if self.is_live_code:
            return self.question.strip()
        parts = [self.question.strip()]
        if self.code.strip():
            parts.extend(["", "── Код ──", self.code.strip()])
        if self.task.strip():
            parts.extend(["", f"Задание: {self.task.strip()}"])
        return "\n".join(parts)


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


def infer_language_from_name(name: str) -> str:
    n = name.lower()
    if "php" in n:
        return "php"
    if "python" in n or "pytorch" in n or "tkinter" in n or "ttk" in n:
        return "python"
    if "angular" in n or "typescript" in n or "javascript" in n:
        return "typescript"
    if "math" in n or "матем" in n:
        return "latex"
    if "laravel" in n:
        return "php"
    return ""


@dataclass
class Deck:
    name: str
    cards: list[Card] = field(default_factory=list)
    deck_id: str = ""
    language: str = ""

    def merge(self, other: Deck, *, suffix_name: bool = True) -> None:
        self.cards.extend(other.cards)
        if suffix_name and other.name:
            self.name = f"{self.name} + {other.name}"

    @classmethod
    def load_json(cls, path: str | Path) -> Deck:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        name = data.get("name", Path(path).stem)
        default_language = data.get("language") or infer_language_from_name(name) or ""
        if isinstance(data, list):
            cards = [
                _card_from_dict(item, default_language=default_language)
                if isinstance(item, dict)
                else Card(question=str(item), reference="", language=default_language)
                for item in data
            ]
            return cls(name=Path(path).stem, cards=cards, language=default_language)
        cards = [_card_from_dict(c, default_language=default_language) for c in data.get("cards", [])]
        return cls(name=name, cards=cards, language=default_language)

    @classmethod
    def load_anki_txt(cls, path: str | Path) -> Deck:
        name = Path(path).stem
        default_language = infer_language_from_name(name) or ""
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
                cards.append(Card(question=front, reference=back, language=default_language))
        return cls(name=name, cards=cards, language=default_language)


def _card_from_dict(item: dict, *, default_language: str = "") -> Card:
    known = {"question", "reference", "id", "card_type", "code", "task", "language", "answer_mode", "topic"}
    item = {k: v for k, v in item.items() if k in known}
    card_type = item.get("card_type")
    if not card_type:
        if item.get("answer_mode") == "math":
            card_type = "math"
        else:
            card_type = "code" if item.get("code") else "text"
    return Card(
        question=item.get("question", ""),
        reference=item.get("reference", ""),
        id=item.get("id", ""),
        card_type=card_type,
        code=item.get("code", ""),
        task=item.get("task", ""),
        language=item.get("language") or default_language,
        answer_mode=item.get("answer_mode", ""),
        topic=str(item.get("topic", "") or ""),
    )


def _strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<code>(.*?)</code>", r"\1", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()
