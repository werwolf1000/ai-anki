"""Очистка сгенерированных колод от мусорных и некорректных карточек.

Запуск (из корня проекта):
    python decks/clean_decks.py            # применить изменения к decks/*.json
    python decks/clean_decks.py --dry-run  # только отчёт

Что делает:
- удаляет карточки-заглушки, у которых эталон — шаблонная фраза
  («Повторите ключевые идеи темы…», «см. docs», «Объясните X в контексте…»);
- удаляет точные дубликаты (одинаковые code/task/reference);
- превращает заголовки вида «PyTorch [zero grad] #1-1» в нормальный вопрос из task;
- раскрывает слишком короткие вопросы («withCount?» → «Что такое withCount?»);
- чистит формулировки live-coding: повторы, шаблонные абзацы, разорванные фразы;
- выносит Go-фрагменты из обёртки `package main / func example()`.

id изменённых карточек сохраняется (поле "id"), поэтому прогресс не теряется.
id удалённых карточек пишутся в "retired_ids" — ProgressStore не будет
переносить их прогресс на чужие карточки.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.deck import _card_from_dict  # noqa: E402

DECKS = ROOT / "decks"

FILLER_REFERENCE = [
    r"^Повторите ключевые идеи темы",
    r"^Объясните .+ в контексте",
    r"^Дай развёрнутый ответ по теме",
    r"^Частые ошибки: неверный shape",
    r"^Типичные задачи: training, inference",
    r"проверь docs",
    r"см\. docs",
    r"см\. документацию",
    r"^Tensor operation \S+ — shape rules",
    r"^Общая опция ttk",
    r"^Общие: style, takefocus",
    r"^Практика ttk\.",
    r"^Типичная реализация «",
    r"^// Пример зависит от",
    r"^Строковая операция PHP\. ",
    r"^Работа с массивами PHP\.",
]
FILLER_QUESTION = [
    r"контрольный вопрос #\d+",
    r"\]: вопрос #\d+$",
    r"— вопрос #\d+$",
]

LIVE_DROP_PARAGRAPHS = [
    r"^Реализуйте решение с нуля согласно описанию задания\.?$",
    r"^Функция должна соответствовать сигнатуре и описанному поведению\.?$",
    r"^Пример: .*— (поведение согласно описанию|рендер шаблона компонента)\.?$",
]
LIVE_DROP_BULLETS = {
    "Читаемость кода без лишней сложности",
    "Соблюдение сигнатуры и ожидаемого поведения из описания",
}

GENERATED_TITLE = re.compile(r"^(.*?)\[([^\]]+)\]\s*#\d+(?:-\d+)?\??$")


def card_id(item: dict) -> str:
    return _card_from_dict(dict(item)).id


def is_filler(item: dict) -> bool:
    ref = str(item.get("reference", "")).strip()
    q = str(item.get("question", "")).strip()
    if item.get("card_type") == "live_code":
        return False
    if any(re.search(p, ref) for p in FILLER_REFERENCE):
        return True
    if any(re.search(p, q) for p in FILLER_QUESTION):
        return True
    return False


def _sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


def fix_generated_title(item: dict) -> str | None:
    """«PyTorch [zero grad] #1-1» → вопрос из task."""
    q = str(item.get("question", "")).strip()
    m = GENERATED_TITLE.match(q)
    if not m:
        return None
    label = m.group(2).strip()
    task = str(item.get("task", "")).strip()
    if item.get("code"):
        base = _sentence(task) if task else f"Исправьте код: {label}."
        return f"{base} Исправьте или допишите код."
    return f"{_sentence(task)}" if task else f"Тема «{label}»: напишите решение."


def expand_terse(q: str) -> str | None:
    """Раскрыть слишком короткие вопросы вида «withCount?»."""
    s = q.strip()
    if len(s) > 26 or not s.endswith("?"):
        return None
    body = s[:-1].strip()
    if not body or re.search(r"[а-яё]", body, re.I):
        return None  # кириллица — вопрос уже сформулирован
    m = re.match(r"^(.+?)\s+vs\.?\s+(.+)$", body, re.I)
    if m:
        return f"В чём разница между {m.group(1)} и {m.group(2)}?"
    words = body.split()
    if len(words) > 3:
        return None
    if body.endswith("()") or re.match(r"^[\w.]+\(.*\)$", body):
        return f"Что делает {body}?"
    if len(words) == 1:
        return f"Что такое {body}?"
    return f"Поясните: {body}."


def clean_live_question(q: str) -> str:
    q = q.replace("\r\n", "\n")
    # разорванные генератором выражения: "?? .\n\n0" → "?? 0"
    q = re.sub(r"\?\?\.\n\n", "?? ", q)
    paras = [p.strip() for p in q.split("\n\n")]
    head = paras[0] if paras else ""
    out = [head]
    for p in paras[1:]:
        if not p:
            continue
        if any(re.match(rx, p) for rx in LIVE_DROP_PARAGRAPHS):
            continue
        if p.startswith("Пример: "):
            probe = p[len("Пример: "):].replace("Функция ", "").strip()[:40].lower()
            so_far = "\n\n".join(out).lower()
            if probe and probe in so_far:
                continue
        core = re.sub(r"^Результат работы:\s*", "", p).rstrip(".").strip()
        if core and core.lower() in head.lower():
            continue  # повтор фрагмента первой фразы
        if p.startswith("Необходимо предусмотреть:"):
            lines = p.split("\n")
            bullets = [ln for ln in lines[1:] if ln.lstrip("- ").strip() not in LIVE_DROP_BULLETS]
            if not bullets:
                continue
            p = "\n".join([lines[0], *bullets])
        out.append(p)
    return "\n\n".join(out).strip()


GO_WRAP = re.compile(r"^package main\n\n(?:// fix me\n)?func example\(\) \{\n(.*)\n\}\s*$", re.S)


def unwrap_go(code: str) -> str | None:
    m = GO_WRAP.match(code.strip())
    if not m:
        return None
    lines = m.group(1).split("\n")
    stripped = [ln[4:] if ln.startswith("    ") else ln for ln in lines]
    return reindent_braces("\n".join(stripped).strip())


def reindent_braces(code: str) -> str:
    """Простейшее выравнивание отступов по фигурным скобкам (для Go-фрагментов)."""
    out: list[str] = []
    depth = 0
    for raw in code.split("\n"):
        line = raw.strip()
        if not line:
            out.append("")
            continue
        closing = line.startswith("}")
        case_label = re.match(r"^(case .*|default):$", line)
        level = depth - (1 if closing else 0)
        if case_label:
            level = max(0, depth - 1)
        out.append("    " * max(0, level) + line)
        depth += line.count("{") - line.count("}")
    return "\n".join(out)


def process_deck(path: Path) -> tuple[dict, Counter]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cards = data["cards"] if isinstance(data, dict) else data
    stats: Counter = Counter()
    retired: list[str] = list(data.get("retired_ids", [])) if isinstance(data, dict) else []
    kept: list[dict] = []
    seen: set[tuple] = set()
    seen_questions: set[str] = set()

    for item in cards:
        original_id = card_id(item)
        if is_filler(item):
            stats["filler_removed"] += 1
            retired.append(original_id)
            continue
        if item.get("card_type") != "live_code" and (item.get("code") or item.get("task")):
            key = (item.get("code", ""), item.get("task", ""), item.get("reference", ""))
            if key in seen:
                stats["duplicates_removed"] += 1
                retired.append(original_id)
                continue
            seen.add(key)

        new = dict(item)
        changed = False

        if new.get("card_type") == "live_code":
            q2 = clean_live_question(new.get("question", ""))
            if q2 != new.get("question"):
                new["question"] = q2
                stats["live_cleaned"] += 1
        else:
            title = fix_generated_title(new)
            if title:
                new["question"] = title
                changed = True
                stats["titles_fixed"] += 1
            else:
                terse = expand_terse(new.get("question", ""))
                if terse:
                    new["question"] = terse
                    changed = True
                    stats["terse_expanded"] += 1
            if new.get("language") == "go" or path.name.startswith("go-"):
                for field in ("code", "reference"):
                    if new.get(field):
                        unwrapped = unwrap_go(new[field])
                        if unwrapped is not None:
                            new[field] = unwrapped
                            changed = True
                            stats[f"go_{field}_unwrapped"] += 1

        if new.get("card_type") != "live_code":
            qkey = (new.get("question", "") + new.get("code", "") + new.get("task", "")).strip()
            if qkey in seen_questions:
                stats["duplicates_removed"] += 1
                retired.append(original_id)
                continue
            seen_questions.add(qkey)

        if changed and "id" not in new:
            new["id"] = original_id  # сохранить прогресс
        kept.append(new)

    if isinstance(data, dict):
        data["cards"] = kept
        data["retired_ids"] = sorted(set(retired) - {c.get("id") or card_id(c) for c in kept})
    else:
        data = kept
    stats["total_before"] = len(cards)
    stats["total_after"] = len(kept)
    return data, stats


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()
    paths = [Path(f) for f in args.files] or sorted(DECKS.glob("*.json"))
    for path in paths:
        data, stats = process_deck(path)
        summary = ", ".join(f"{k}={v}" for k, v in sorted(stats.items()))
        print(f"{path.name}: {summary}")
        if not args.dry_run:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
