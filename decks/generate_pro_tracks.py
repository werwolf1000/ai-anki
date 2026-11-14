"""Генерация колод профессиональных треков и манифеста decks/tracks.json.

Запуск из корня проекта:
    python decks/generate_pro_tracks.py

Для каждого трека из decks/pro_tracks/*.py создаются:
    decks/pro-<id>.json              — теория (темы = предметы профессии)
    decks/pro-<id>-live-coding.json  — практикум (live-coding / практические задания)
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

ORDER = ["php", "nodejs", "go", "devops", "fde", "ai_trainer", "prompt_engineer", "llm_evaluator", "ai_artist"]

EXAM = {"theory": 9, "practice": 3, "minutes": 60, "pass_score": 70}
INTERVIEW = {"theory": 5, "practice": 1, "pass_score": 65}
COVERAGE = 0.6  # доля карточек трека, которые нужно сдать хотя бы раз
MIN_PER_TOPIC = 20  # предупреждать, если в теме трека меньше карточек


def build(track: dict) -> tuple[dict, dict]:
    tid = track["id"]
    lang = track.get("language", "")
    theory_cards = []
    for topic, items in track["theory"].items():
        for q, a in items:
            theory_cards.append({"question": q, "reference": a, "topic": topic, "card_type": "text"})
    practice_cards = []
    for topic, plang, task, ref in track["practice"]:
        practice_cards.append(
            {"card_type": "live_code", "question": task, "reference": ref, "language": plang, "topic": topic}
        )
    theory = {
        "name": f"{track['title']} — теория",
        "language": lang if lang not in ("markdown",) else "",
        "track": tid,
        "cards": theory_cards,
    }
    practice = {
        "name": f"{track['title']} — практикум",
        "language": lang,
        "track": tid,
        "cards": practice_cards,
    }
    return theory, practice


def merge_more(track: dict, mod_name: str) -> None:
    """Добавить карточки из pro_tracks/<модуль>_more.py (MORE = {тема: [(вопрос, эталон), ...]})."""
    try:
        more = importlib.import_module(f"pro_tracks.{mod_name}_more").MORE
    except ModuleNotFoundError:
        return
    for topic, items in more.items():
        if topic not in track["theory"]:
            raise SystemExit(f"{mod_name}_more: неизвестная тема «{topic}»")
        seen = {q.strip().lower() for q, _ in track["theory"][topic]}
        for q, a in items:
            if q.strip().lower() in seen:
                raise SystemExit(f"{mod_name}_more: дубликат вопроса «{q}»")
            seen.add(q.strip().lower())
            track["theory"][topic].append((q, a))
    small = {t: len(v) for t, v in track["theory"].items() if len(v) < MIN_PER_TOPIC}
    if small:
        print(f"  внимание: в теме меньше {MIN_PER_TOPIC} карточек: {small}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    manifest = {"version": 1, "exam": EXAM, "interview": INTERVIEW, "coverage": COVERAGE, "tracks": []}
    for mod_name in ORDER:
        track = importlib.import_module(f"pro_tracks.{mod_name}").TRACK
        merge_more(track, mod_name)
        tid = track["id"]
        theory, practice = build(track)
        theory_file = f"pro-{tid}.json"
        practice_file = f"pro-{tid}-live-coding.json"
        for name, data in ((theory_file, theory), (practice_file, practice)):
            (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["tracks"].append(
            {
                "id": tid,
                "title": track["title"],
                "description": track["description"],
                "icon": track.get("icon", tid),
                "language": track.get("language", ""),
                "decks": [theory_file, practice_file],
                "related": track.get("related", []),
                "subjects": list(track["theory"].keys()),
            }
        )
        print(f"{tid}: теория {len(theory['cards'])}, практикум {len(practice['cards'])}")
    (ROOT / "tracks.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("tracks.json:", len(manifest["tracks"]), "треков")


if __name__ == "__main__":
    main()
