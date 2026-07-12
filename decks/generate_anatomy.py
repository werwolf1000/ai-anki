#!/usr/bin/env python3
"""Generate anatomy deck with topics and diagram on every card."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from anatomy_bank import TOPICS, build_cards, use_local_svg_images
from generate_anatomy_assets import write_assets

MIN_PER_TOPIC = 30


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate anatomy.json deck")
    parser.add_argument(
        "--local-svg",
        action="store_true",
        help="Use bundled SVG in decks/anatomy-assets/ instead of remote photos",
    )
    args = parser.parse_args()

    if args.local_svg:
        write_assets()
        use_local_svg_images()

    cards = build_cards()
    counts = Counter(c["topic"] for c in cards)
    bad = {t: n for t, n in counts.items() if n < MIN_PER_TOPIC}
    if bad:
        print("Topics below minimum:", bad, file=sys.stderr)
        sys.exit(1)
    no_image = [c for c in cards if not c.get("image")]
    if no_image:
        print(f"{len(no_image)} cards without image", file=sys.stderr)
        sys.exit(1)

    deck = {
        "name": "Анатомия",
        "cards": cards,
    }
    out = Path(__file__).with_name("anatomy.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    mode = "local SVG" if args.local_svg else "remote photos"
    print(f"Written {len(cards)} anatomy cards ({mode}) -> {out}")
    for topic in TOPICS:
        print(f"  {topic}: {counts[topic]}")


if __name__ == "__main__":
    main()
