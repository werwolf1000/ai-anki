from __future__ import annotations

"""Shared builder for live-coding cards with structured question text."""

import re

_LANG_LABEL = {
    "php": "PHP",
    "python": "Python",
    "typescript": "TypeScript/Angular",
    "ts": "TypeScript/Angular",
}


def _lang_label(lang: str) -> str:
    return _LANG_LABEL.get(lang.lower(), lang or "код")


def _build_question(
    headline: str,
    description: str,
    *,
    considerations: list[str] | None = None,
    example: str = "",
) -> str:
    parts = [headline.strip(), ""]
    if description.strip():
        parts.append(description.strip())
    items = [c.strip().lstrip("-•") for c in (considerations or []) if c and c.strip()]
    if items:
        parts.extend(["", "Необходимо предусмотреть:"])
        parts.extend(f"- {item.rstrip('.')}" for item in items)
    if example.strip():
        parts.extend(["", f"Пример: {example.strip()}"])
    return "\n".join(parts)


def _split_example(text: str) -> tuple[str, str]:
    for marker in ("\nПример:", "\nExample:", "Пример:"):
        if marker in text:
            idx = text.index(marker)
            body = text[:idx].strip()
            example = text[idx + len(marker) :].strip()
            return body, example
    return text.strip(), ""


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _legacy_headline(title: str, assignment: str, lang: str) -> str:
    label = _lang_label(lang)
    text = assignment.strip()
    title = title.strip()

    m = re.match(
        r"Generator function\s+(\w+\([^)]*\)(?:\s*:\s*\S+)?)\.?\s*$",
        text,
        re.I,
    )
    if m:
        sig = m.group(1).rstrip(".")
        return f"Реализовать {label}-функцию-генератор {sig}."

    sentences = _split_sentences(text)
    if sentences:
        first = sentences[0].rstrip(".")
        low = first.lower()
        if low.startswith("объявите класс"):
            rest = first[len("Объявите класс") :].strip()
            return f"Реализовать {label}-класс {rest}."
        if low.startswith("напишите функцию"):
            rest = first[len("Напишите функцию") :].strip()
            return f"Реализовать {label}-функцию {rest}."
        if low.startswith("напиши функцию"):
            rest = first[len("Напиши функцию") :].strip()
            return f"Реализовать {label}-функцию {rest}."
        if low.startswith("функция "):
            return f"Реализовать {label}-функцию {first[len('Функция '):].strip()}."
        if low.startswith(("создайте ", "создай ", "реализуйте ", "реализуй ")):
            return first[0].upper() + first[1:] + ("." if not first.endswith(".") else "")
        if low.startswith("объявите "):
            return f"Реализовать {label}: {first[len('Объявите '):].strip()}."
        if title and len(sentences) == 1 and len(first) < 100:
            return f"Реализовать {label}: {first}."
        return first + ("." if not first.endswith(".") else "")

    if title:
        return f"Реализовать {label}: {title.rstrip('.')}."
    return f"Реализовать {label}-задание."


def _legacy_description(title: str, assignment: str, headline: str, lang: str) -> str:
    text, _ = _split_example(assignment)
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        if re.match(r"Generator function\s+", text, re.I):
            name = re.search(r"Generator function\s+(\w+)", text, re.I)
            fn = name.group(1) if name else "функция"
            return (
                f"Функция {fn} должна возвращать последовательность значений через yield "
                f"в соответствии с переданными параметрами."
            )
        return ""

    rest = ". ".join(s.rstrip(".") for s in sentences[1:])
    if rest and not rest.endswith("."):
        rest += "."
    return rest


def _default_considerations(assignment: str, lang: str) -> list[str]:
    items: list[str] = []
    text = assignment.lower()
    if "generator" in text or "yield" in text:
        items.extend([
            "Корректную работу граничных значений start/stop",
            "Обработку некорректного шага (0 или неверное направление), если применимо",
        ])
    if "$step" in assignment or "step" in text:
        items.append("Поддержку положительного и отрицательного шага")
    if "array" in text or "массив" in text:
        items.append("Корректную работу с пустым входным массивом")
    if "nullable" in text or "null" in text or "?->" in assignment:
        items.append("Безопасную обработку null / optional значений")
    if "required" in text or "required" in assignment:
        items.append("Валидацию обязательных полей")
    if lang == "typescript" and "standalone" in text:
        items.append("Standalone-компонент с корректным imports в декораторе")
    return items


def _legacy_example(assignment: str, reference: str) -> str:
    _, ex = _split_example(assignment)
    if ex:
        return ex
    if " → " in assignment:
        return assignment.split(" → ", 1)[1].strip()
    return ""


def live(
    title: str,
    assignment: str,
    reference: str,
    *,
    lang: str = "python",
    topic: str = "",
    headline: str = "",
    description: str = "",
    considerations: list[str] | None = None,
    example: str = "",
    requirements: list[str] | None = None,
    context: str = "",
) -> dict:
    """Create a live_code card. Pass headline/description directly or legacy title+assignment."""
    considerations = [c for c in (considerations or requirements or []) if c and c.strip()]
    assignment_body, ex_from_text = _split_example(assignment)
    if not example:
        example = ex_from_text or _legacy_example(assignment, reference)

    if headline.strip():
        h = headline.strip()
        desc = description.strip() or context.strip()
    else:
        h = _legacy_headline(title, assignment_body, lang)
        desc = description.strip() or _legacy_description(title, assignment_body, h, lang)
        if context.strip() and not desc:
            desc = context.strip()
        if not considerations:
            considerations = _default_considerations(assignment_body, lang)

    # rangeStep and similar generators — richer default spec
    if re.search(r"rangeStep\s*\(", assignment_body, re.I):
        h = "Реализовать PHP-функцию-генератор rangeStep(int $start, int $stop, int $step = 1): Generator."
        desc = "Функция должна возвращать последовательность чисел от $start до $stop с шагом $step."
        considerations = [
            "Работу с положительным и отрицательным шагом",
            "Проверку на $step = 0 (выбросить исключение или вернуть пустой результат)",
            "Корректную обработку граничных условий (включительно $stop)",
        ]
        example = example or "rangeStep(1, 10, 2) → 1, 3, 5, 7, 9"

    question = _build_question(h, desc, considerations=considerations, example=example)
    return {
        "card_type": "live_code",
        "question": question,
        "task": assignment_body.strip(),
        "reference": reference.strip(),
        "language": lang,
        "topic": topic,
    }


def refresh_question(card: dict, *, lang: str = "") -> dict:
    """Rebuild question text for an existing card dict (e.g. after format change)."""
    language = lang or card.get("language", "python")
    title = card.get("question", "").split("\n")[0].replace("Задача:", "").strip()
    rebuilt = live(
        title=title,
        assignment=card.get("task") or card.get("question", ""),
        reference=card.get("reference", ""),
        lang=language,
        topic=card.get("topic", ""),
    )
    card["question"] = rebuilt["question"]
    if not card.get("task"):
        card["task"] = rebuilt["task"]
    return card
