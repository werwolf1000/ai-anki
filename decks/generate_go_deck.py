#!/usr/bin/env python3
"""Generate Go fundamentals deck (theory + code), split by topics."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from go_cards import CODE_CARDS, REVISION_HINTS, THEORY
from go_topics import TOPICS
from live_coding_topics import assign_topics


def theory(q: str, ref: str, topic: str) -> dict:
    return {"question": q, "reference": ref, "topic": topic, "language": "go"}


def code(q: str, task: str, snippet: str, ref: str, topic: str) -> dict:
    return {
        "card_type": "code",
        "question": q,
        "task": task,
        "code": snippet.strip(),
        "reference": ref.strip(),
        "language": "go",
        "topic": topic,
    }


def build_cards() -> list[dict]:
    cards: list[dict] = []

    for topic, pairs in THEORY.items():
        for q, ref in pairs:
            cards.append(theory(q, ref, topic))

    for q, task, snippet, ref, topic in CODE_CARDS:
        cards.append(code(q, task, snippet, ref, topic))

    for topic, hints in REVISION_HINTS.items():
        for hint in hints:
            for i in range(5):
                cards.append(
                    theory(
                        f"Go [{topic}]: {hint} — контрольный вопрос #{i + 1}",
                        f"Объясните {hint} в контексте Go ({topic}). "
                        f"Приведите примеры кода и ссылки на go.dev/doc.",
                        topic,
                    )
                )

    seen: set[str] = set()
    unique: list[dict] = []
    for card in cards:
        key = card.get("question", "") + card.get("code", "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(card)

    return assign_topics(unique, "go")


def main() -> None:
    cards = build_cards()
    if len(cards) < 500:
        raise SystemExit(f"Only {len(cards)} cards, need 500+")

    counts = Counter(c.get("topic", "?") for c in cards)
    missing = [t for t in TOPICS if counts.get(t, 0) < 10]
    if missing:
        raise SystemExit(f"Topics with <10 cards: {missing}")

    code_n = sum(1 for c in cards if c.get("card_type") == "code" or c.get("code"))
    deck = {"name": "Go — основы", "language": "go", "cards": cards}
    out = Path(__file__).with_name("go-basics.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} cards ({code_n} code) -> {out}")
    print("Topics:", dict(counts))


if __name__ == "__main__":
    main()
