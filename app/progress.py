from __future__ import annotations

import json
import re
from pathlib import Path

from app.deck import CardProgress, Deck


class ProgressStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data: dict[str, dict[str, CardProgress]] = {}

    def load(self) -> None:
        if not self.path.exists():
            self.data = {}
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.data = {}
        for deck_name, cards in raw.items():
            self.data[deck_name] = {
                cid: CardProgress(**values) for cid, values in cards.items()
            }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            deck: {cid: prog.__dict__ for cid, prog in cards.items()}
            for deck, cards in self.data.items()
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, deck: Deck, card_id: str) -> CardProgress:
        deck_map = self.data.setdefault(deck.name, {})
        if card_id not in deck_map:
            deck_map[card_id] = CardProgress(card_id=card_id)
        return deck_map[card_id]

    def update(self, deck: Deck, progress: CardProgress, pass_score: int) -> None:
        progress.mastered = progress.best_score >= pass_score
        self.data.setdefault(deck.name, {})[progress.card_id] = progress
        self.save()

    def next_cards(self, deck: Deck, limit: int = 20) -> list:
        """Сначала неосвоенные, потом с низким best_score."""
        result = []
        for card in deck.cards:
            prog = self.get(deck, card.id)
            if not prog.mastered:
                result.append((card, prog))
        result.sort(key=lambda item: (item[1].best_score, item[1].attempts))
        if not result:
            return deck.cards[:limit]
        return [card for card, _ in result[:limit]]
