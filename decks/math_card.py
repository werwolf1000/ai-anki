from __future__ import annotations

"""Helper for math deck cards."""


def math(question: str, reference: str, *, topic: str) -> dict:
    return {
        "card_type": "math",
        "question": question.strip(),
        "reference": reference.strip(),
        "topic": topic.strip(),
    }
