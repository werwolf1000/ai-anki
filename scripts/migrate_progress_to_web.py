#!/usr/bin/env python3
"""Перенос progress.json с desktop (или старого web) на web с stable deck_id.

Ключи прогресса на desktop считаются по абсолютному пути файла колоды
(/home/.../decks/foo.json). На web — по имени файла (stable id).
Без перекодировки ключей прогресс «не подтягивается», хотя файл лежит в data/.

Пример:
  python3 scripts/migrate_progress_to_web.py \\
    ~/.ai-anki/progress.json \\
    ~/.ai-anki/decks.json \\
    progress.web.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def stable_deck_id(filename: str, scope: str = "builtin") -> str:
    return hashlib.sha256(f"{scope}:{filename}".encode()).hexdigest()[:16]


def build_mapping(decks: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in decks:
        old_id = entry.get("deck_id", "")
        if not old_id:
            continue
        if old_id == "angular-full":
            mapping[old_id] = "angular-full"
            continue
        paths = entry.get("paths") or []
        if not paths:
            continue
        fname = Path(paths[0]).name
        if fname.endswith(".txt") and len(paths) > 1:
            # составная колода — только angular-full
            continue
        mapping[old_id] = stable_deck_id(fname)
    return mapping


def migrate_progress(progress: dict, mapping: dict[str, str]) -> tuple[dict, list[str]]:
    out: dict = {}
    notes: list[str] = []
    for old_key, cards in progress.items():
        new_key = mapping.get(old_key, old_key)
        if old_key not in mapping:
            notes.append(f"ключ без маппинга (оставлен как есть): {old_key}")
        if new_key in out:
            out[new_key].update(cards)
            notes.append(f"объединено: {old_key} → {new_key}")
        else:
            out[new_key] = dict(cards)
    return out, notes


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 1

    progress_path = Path(sys.argv[1])
    decks_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    decks_raw = json.loads(decks_path.read_text(encoding="utf-8"))
    decks = decks_raw.get("decks", decks_raw if isinstance(decks_raw, list) else [])

    mapping = build_mapping(decks)
    migrated, notes = migrate_progress(progress, mapping)

    out_path.write_text(json.dumps(migrated, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Записано: {out_path}")
    print(f"Колод в исходнике: {len(progress)}, после миграции: {len(migrated)}")
    print("Маппинг deck_id:")
    for old, new in sorted(mapping.items(), key=lambda x: x[1]):
        n = len(progress.get(old, {}))
        print(f"  {old} → {new}  ({n} карточек)")
    for note in notes:
        print(f"  ! {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
