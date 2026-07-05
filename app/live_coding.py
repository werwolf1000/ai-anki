from __future__ import annotations

from app.deck import Card, Deck
from app.progress import CardProgress, ProgressStore, StudyMode, _now, _parse_iso


def is_live_coding_entry(filename: str) -> bool:
    return "live-coding" in filename.lower()


def is_math_entry(filename: str) -> bool:
    name = filename.lower()
    return name.endswith(".json") and "math" in name


def is_live_coding_deck(deck: Deck) -> bool:
    return bool(deck.cards) and all(c.is_live_code for c in deck.cards)


def is_math_deck(deck: Deck) -> bool:
    return bool(deck.cards) and all(c.is_math for c in deck.cards)


def has_topic_picker_deck(deck: Deck) -> bool:
    return len(deck_topics(deck)) >= 2


def deck_topics(deck: Deck) -> list[str]:
    names = sorted({c.topic.strip() for c in deck.cards if c.topic.strip()})
    return names


def topic_summaries(
    deck: Deck,
    progress: ProgressStore,
    *,
    pass_score: int = 75,
) -> list[dict]:
    now = _now()
    key = progress.deck_key(deck)
    cards_map = progress.data.get(key, {})
    buckets: dict[str, dict] = {}

    for card in deck.cards:
        name = card.topic.strip() or "Разное"
        if name not in buckets:
            buckets[name] = {"name": name, "total": 0, "due": 0, "new": 0, "weak": 0}
        bucket = buckets[name]
        bucket["total"] += 1
        prog = cards_map.get(card.id) or CardProgress(card_id=card.id)
        if prog.is_new():
            bucket["new"] += 1
            bucket["due"] += 1
        elif prog.is_due(now):
            bucket["due"] += 1
        if prog.attempts > 0 and prog.best_score < pass_score:
            bucket["weak"] += 1

    return [buckets[name] for name in sorted(buckets)]


def filter_cards_by_topic(cards: list[Card], topic: str | None) -> list[Card]:
    if not topic:
        return cards
    wanted = topic.strip()
    return [c for c in cards if (c.topic.strip() or "Разное") == wanted]
