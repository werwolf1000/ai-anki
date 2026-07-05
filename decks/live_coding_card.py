from __future__ import annotations

"""Shared builder for live-coding cards with verbose question text."""


def live(
    title: str,
    assignment: str,
    reference: str,
    *,
    lang: str = "python",
    topic: str = "",
    context: str = "",
    requirements: list[str] | None = None,
) -> dict:
    """Create a live_code card with an expanded question for the learner."""
    heading = title.strip()
    if not heading.lower().startswith(("задача", "напиш", "реализ", "создай", "implement")):
        heading = f"Задача: {heading.rstrip('.')}."

    parts = [heading, "", assignment.strip()]
    if context.strip():
        parts.extend(["", "Контекст:", context.strip()])
    if requirements:
        parts.extend(["", "Требования:"])
        parts.extend(f"• {item.strip()}" for item in requirements if item.strip())
    parts.extend([
        "",
        "Напишите полное решение с нуля в редакторе кода. "
        "Допускаются необходимые import и вспомогательные определения.",
    ])
    question = "\n".join(parts)
    return {
        "card_type": "live_code",
        "question": question,
        "task": assignment.strip(),
        "reference": reference.strip(),
        "language": lang,
        "topic": topic,
    }
