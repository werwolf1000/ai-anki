from __future__ import annotations

import json
import hashlib
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.deck import Deck


def legacy_deck_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]


def deck_id_for_path(path: Path, *, scope: str | None = None) -> str:
    """Стабильный id для колод в builtin/custom (по имени файла), legacy — по абс. пути."""
    if scope in ("builtin", "custom"):
        return hashlib.sha256(f"{scope}:{path.name}".encode()).hexdigest()[:16]
    return legacy_deck_id(path)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


BUILTIN_DISPLAY_NAMES: dict[str, str] = {
    "php8-plus.json": "PHP 8+",
    "python-basics.json": "Python — основы",
    "ttk-widgets.json": "tkinter.ttk",
    "pytorch-basics.json": "PyTorch",
    "angular-sample.json": "Angular (пример)",
    "angular-live-coding.json": "Angular Live-coding",
    "python-live-coding.json": "Python Live-coding",
    "php-live-coding.json": "PHP Live-coding",
    "agile-fundamentals.json": "Agile — основы",
    "scrum-framework.json": "Scrum",
    "kanban-method.json": "Kanban",
    "safe-scaled-agile.json": "SAFe",
    "higher-math.json": "Высшая математика",
    "laravel-basics.json": "Laravel",
    "laravel-live-coding.json": "Laravel Live-coding",
}

SKIP_STANDALONE: set[str] = {"angular-code.json"}


@dataclass
class DeckEntry:
    deck_id: str
    name: str
    paths: list[str] = field(default_factory=list)
    added_at: str = ""

    @property
    def primary_path(self) -> str:
        return self.paths[0] if self.paths else ""

    @property
    def is_live_coding(self) -> bool:
        from app.live_coding import is_live_coding_entry

        return any(is_live_coding_entry(p) for p in self.paths)

    @property
    def is_math(self) -> bool:
        from app.live_coding import is_math_entry

        return any(is_math_entry(p) for p in self.paths)

    @property
    def has_topics(self) -> bool:
        """Быстрая эвристика для UI; точнее — has_topic_picker_deck(deck)."""
        return self.is_live_coding or self.is_math

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
    def __init__(self, path: Path, builtin_dir: Path, custom_dir: Path | None = None) -> None:
        self.path = path
        self.builtin_dir = builtin_dir
        self.custom_dir = custom_dir
        self.entries: list[DeckEntry] = []
        self._id_migrations: dict[str, str] = {}

    def load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = [DeckEntry.from_dict(e) for e in raw.get("decks", [])]
        else:
            self.entries = []
        self._id_migrations = self._normalize_entries()
        self._ensure_scanned_decks(self.builtin_dir, scope="builtin")
        if self.custom_dir:
            self.custom_dir.mkdir(parents=True, exist_ok=True)
            self._ensure_scanned_decks(self.custom_dir, scope="custom")
        self._ensure_angular_full_deck()
        self.save()

    def migrate_progress(self, progress) -> bool:
        if not self._id_migrations:
            return False
        return progress.migrate_deck_keys(self._id_migrations)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"decks": [asdict(e) for e in self.entries]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _locate_deck_file(self, filename: str) -> tuple[Path, str] | None:
        if self.custom_dir:
            custom = self.custom_dir / filename
            if custom.exists():
                return custom, "custom"
        builtin = self.builtin_dir / filename
        if builtin.exists():
            return builtin, "builtin"
        return None

    def _normalize_entries(self) -> dict[str, str]:
        migrations: dict[str, str] = {}
        kept: list[DeckEntry] = []
        seen_ids: set[str] = set()

        for entry in self.entries:
            if entry.deck_id == "angular-full":
                kept.append(entry)
                seen_ids.add(entry.deck_id)
                continue
            if not entry.paths:
                continue

            fname = Path(entry.paths[0]).name
            located = self._locate_deck_file(fname)
            if located:
                path, scope = located
                stable_id = deck_id_for_path(path, scope=scope)
                new_path = str(path.resolve())
                if entry.deck_id != stable_id:
                    migrations[entry.deck_id] = stable_id
                if stable_id in seen_ids:
                    continue
                kept.append(
                    DeckEntry(
                        deck_id=stable_id,
                        name=entry.name,
                        paths=[new_path],
                        added_at=entry.added_at or _iso_now(),
                    )
                )
                seen_ids.add(stable_id)
                continue

            path = Path(entry.paths[0]).expanduser()
            if path.exists():
                if entry.deck_id not in seen_ids:
                    kept.append(entry)
                    seen_ids.add(entry.deck_id)
                continue

        self.entries = kept
        return migrations

    def _read_deck_name(self, path: Path) -> str:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if name := data.get("name"):
                return str(name)
        except Exception:
            pass
        return path.stem.replace("-", " ").replace("_", " ").title()

    def _ensure_scanned_decks(self, directory: Path, *, scope: str) -> None:
        if not directory.is_dir():
            return
        patterns = ("*.json", "*.txt") if scope == "custom" else ("*.json",)
        for pattern in patterns:
            for path in sorted(directory.glob(pattern)):
                if scope == "builtin" and path.name in SKIP_STANDALONE:
                    continue
                name = BUILTIN_DISPLAY_NAMES.get(path.name) if scope == "builtin" else None
                if not name:
                    if path.suffix.lower() == ".json":
                        name = self._read_deck_name(path)
                    else:
                        name = path.stem.replace("-", " ").replace("_", " ").title()
                self._add_file_entry(path, name=name, scope=scope, skip_if_exists=True)

    def _angular_txt_path(self) -> Path | None:
        if self.custom_dir:
            custom = self.custom_dir / "anki-angular.txt"
            if custom.exists():
                return custom
        local = Path.home() / "Documents" / "anki-angular.txt"
        bundled = self.builtin_dir / "anki-angular.txt"
        if local.exists():
            return local
        if bundled.exists():
            return bundled
        return None

    def _ensure_angular_full_deck(self) -> None:
        angular_txt = self._angular_txt_path()
        angular_code = self.builtin_dir / "angular-code.json"
        if angular_txt is None or not angular_code.exists():
            return

        paths = [str(angular_txt.resolve()), str(angular_code.resolve())]
        composite_id = "angular-full"
        existing = self.get(composite_id)
        if existing:
            broken = any(not Path(p).expanduser().exists() for p in existing.paths)
            if broken or existing.paths != paths:
                existing.paths = paths
            return

        self.entries.append(
            DeckEntry(
                deck_id=composite_id,
                name="Angular (полная)",
                paths=paths,
                added_at=_iso_now(),
            )
        )

    def _add_file_entry(
        self,
        path: Path,
        *,
        name: str | None = None,
        scope: str | None = None,
        skip_if_exists: bool = False,
    ) -> DeckEntry | None:
        path = path.resolve()
        did = deck_id_for_path(path, scope=scope)
        if skip_if_exists and any(e.deck_id == did for e in self.entries):
            existing = self.get(did)
            if existing and existing.paths != [str(path)]:
                existing.paths = [str(path)]
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

        scope: str | None = None
        if self.custom_dir:
            self.custom_dir.mkdir(parents=True, exist_ok=True)
            try:
                p.relative_to(self.custom_dir.resolve())
                scope = "custom"
            except ValueError:
                dest = self.custom_dir / p.name
                if dest.resolve() != p:
                    shutil.copy2(p, dest)
                    p = dest.resolve()
                scope = "custom"

        existing = self.find_by_path(p)
        if existing:
            return existing
        try:
            deck = Deck.load_json(p) if p.suffix.lower() == ".json" else Deck.load_anki_txt(p)
            name = deck.name
        except Exception:
            name = p.stem
        entry = self._add_file_entry(p, name=name, scope=scope)
        assert entry is not None
        self.save()
        return entry

    def find_by_path(self, path: Path) -> DeckEntry | None:
        resolved = str(path.resolve())
        for e in self.entries:
            if any(str(Path(p).resolve()) == resolved for p in e.paths):
                return e
        fname = path.name
        located = self._locate_deck_file(fname)
        if located:
            deck_path, scope = located
            did = deck_id_for_path(deck_path, scope=scope)
            return self.get(did)
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
            if not path.exists():
                located = self._locate_deck_file(path.name)
                if located:
                    path = located[0]
                else:
                    raise FileNotFoundError(path)
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
