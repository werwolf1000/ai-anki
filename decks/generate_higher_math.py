#!/usr/bin/env python3
"""Generate higher-math deck with topics (30+ cards each)."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from higher_math_bank import build_cards

MIN_PER_TOPIC = 30


def main() -> None:
    cards = build_cards()
    counts = Counter(c["topic"] for c in cards)
    bad = {t: n for t, n in counts.items() if n < MIN_PER_TOPIC}
    if bad:
        print("Topics below minimum:", bad, file=sys.stderr)
        sys.exit(1)

    deck = {
        "name": "Высшая математика",
        "language": "latex",
        "cards": cards,
    }
    out = Path(__file__).with_name("higher-math.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} math cards -> {out}")
    for topic in sorted(counts):
        print(f"  {topic}: {counts[topic]}")


if __name__ == "__main__":
    main()
