from __future__ import annotations

import json
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.deck import Deck


def _deck_id_for_path(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DeckEntry:
    deck_id: str
    name: str
    paths: list[str] = field(default_factory=list)
    added_at: str = ""

    @property
    def primary_path(self) -> str:
        return self.paths[0] if self.paths else ""

    @classmethod
    def from_dict(cls, data: dict) -> DeckEntry:
        paths = data.get("paths") or ([data["path"]] if data.get("path") else [])
        return cls(
            deck_id=data.get("deck_id", ""),
            name=data.get("name", ""),
            paths=paths,
            added_at=data.get("added_at", ""),
        )


class DeckRegistry:
    def __init__(self, path: Path, builtin_dir: Path) -> None:
        self.path = path
        self.builtin_dir = builtin_dir
        self.entries: list[DeckEntry] = []

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = [DeckEntry.from_dict(e) for e in raw.get("decks", [])]
        else:
            self.entries = []
        self._ensure_builtin_decks()
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"decks": [asdict(e) for e in self.entries]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_builtin_decks(self) -> None:
        known_ids = {e.deck_id for e in self.entries}

        builtins = [
            ("PHP 8+", self.builtin_dir / "php8-plus.json"),
            ("Python — основы", self.builtin_dir / "python-basics.json"),
            ("tkinter.ttk", self.builtin_dir / "ttk-widgets.json"),
            ("PyTorch", self.builtin_dir / "pytorch-basics.json"),
            ("Angular (пример)", self.builtin_dir / "angular-sample.json"),
            ("Agile — основы", self.builtin_dir / "agile-fundamentals.json"),
            ("Scrum", self.builtin_dir / "scrum-framework.json"),
            ("Kanban", self.builtin_dir / "kanban-method.json"),
            ("SAFe", self.builtin_dir / "safe-scaled-agile.json"),
        ]
        for name, p in builtins:
            if p.exists():
                self._add_file_entry(p, name=name, skip_if_exists=True)

        php = self.builtin_dir / "php8-plus.json"
        angular_txt = Path.home() / "Documents" / "anki-angular.txt"
        angular_code = self.builtin_dir / "angular-code.json"
        composite_id = "angular-full"
        if angular_txt.exists() and angular_code.exists() and composite_id not in known_ids:
            paths = [str(angular_txt.resolve()), str(angular_code.resolve())]
            self.entries.append(
                DeckEntry(
                    deck_id=composite_id,
                    name="Angular (полная)",
                    paths=paths,
                    added_at=_iso_now(),
                )
            )

    def _add_file_entry(self, path: Path, *, name: str | None = None, skip_if_exists: bool = False) -> DeckEntry | None:
        path = path.resolve()
        did = _deck_id_for_path(path)
        if skip_if_exists and any(e.deck_id == did for e in self.entries):
            return None
        if any(e.deck_id == did for e in self.entries):
            return self.get(did)
        entry = DeckEntry(
            deck_id=did,
            name=name or path.stem,
            paths=[str(path)],
            added_at=_iso_now(),
        )
        self.entries.append(entry)
        return entry

    def register_file(self, path: str | Path) -> DeckEntry:
        p = Path(path).resolve()
        if not p.exists():
            raise FileNotFoundError(path)
        existing = self.find_by_path(p)
        if existing:
            return existing
        try:
            deck = Deck.load_json(p) if p.suffix.lower() == ".json" else Deck.load_anki_txt(p)
            name = deck.name
        except Exception:
            name = p.stem
        entry = self._add_file_entry(p, name=name)
        assert entry is not None
        self.save()
        return entry

    def find_by_path(self, path: Path) -> DeckEntry | None:
        resolved = str(path.resolve())
        for e in self.entries:
            if any(str(Path(p).resolve()) == resolved for p in e.paths):
                return e
        return None

    def get(self, deck_id: str) -> DeckEntry | None:
        for e in self.entries:
            if e.deck_id == deck_id:
                return e
        return None

    def load_deck(self, entry: DeckEntry) -> Deck:
        if not entry.paths:
            raise ValueError("Колода без файлов")
        deck: Deck | None = None
        for i, p in enumerate(entry.paths):
            path = Path(p).expanduser()
            part = Deck.load_json(path) if path.suffix.lower() == ".json" else Deck.load_anki_txt(path)
            if deck is None:
                deck = part
            else:
                deck.merge(part, suffix_name=(i == len(entry.paths) - 1))
        if deck is None:
            raise ValueError("Не удалось загрузить колоду")
        deck.deck_id = entry.deck_id
        deck.name = entry.name
        return deck
