from __future__ import annotations

import re


def _blob(card: dict) -> str:
    return f"{card.get('question', '')} {card.get('task', '')} {card.get('reference', '')}"


def _has(text: str, *needles: str) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


def assign_angular_topic(card: dict) -> str:
    text = _blob(card)
    if re.search(r"\b(signal|computed|effect)\s*\(", text) or _has(
        text, "toSignal", "input.required", " input()", "output()"
    ):
        return "Сигналы"
    if _has(text, "HostListener", "HostBinding", "ngClass", "ngStyle", "NgClass", "NgStyle", "@for", "@if", "@defer", "trackBy", "ngFor"):
        return "Директивы и шаблоны"
    if _has(text, "FormGroup", "FormArray", "FormControl", "ngModel", "ReactiveForms", "Validator", "formControlName", "Validators"):
        return "Формы"
    if _has(text, "Router", "Routes", "CanActivate", "CanDeactivate", "loadComponent", "redirectTo", "RouterLink", "guard", "Resolver"):
        return "Роутинг"
    if _has(text, "HttpClient", "HttpInterceptor", "Observable", "rxjs", "interceptor"):
        return "HTTP и RxJS"
    if _has(text, "TestBed", "describe(", "fixture", ".spec"):
        return "Тестирование"
    if _has(text, "InjectionToken", "providedIn", "inject(", "Provider", "useValue", "useFactory"):
        return "DI и провайдеры"
    if _has(text, "Pipe", "AsyncPipe", "DatePipe", "ControlValueAccessor", "CVA"):
        return "Pipes и CVA"
    if _has(text, "@Component", "standalone", "@Input", "@Output", "EventEmitter"):
        return "Компоненты"
    return "Разное"


def assign_python_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "async def", "await ", "asyncio"):
        return "Async"
    if _has(text, "TypedDict", "Protocol", "NamedTuple"):
        return "Typing"
    if _has(text, "@dataclass", "class Counter", "class User", "class HttpResponse", "Enum"):
        return "ООП"
    if _has(text, "@lru_cache", "contextmanager", "generator", " yield", "partial", "decorator", "groupby"):
        return "Функциональное"
    if _has(text, "Counter", "defaultdict", "deque", "bisect"):
        return "Collections"
    if _has(text, "pathlib", "json.", "tempfile", "sqlite", "argparse", "itertools", "SplFile", "import os"):
        return "Stdlib"
    return "Основы"


def assign_php_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "enum ", "#[", "Attribute"):
        return "Enums и Attributes"
    if _has(text, "interface ", "abstract class", "implements ", "trait ", "readonly class", "__toString"):
        return "ООП"
    if _has(text, "PDO", "password_hash", "HttpResponse", "password_verify"):
        return "PDO и HTTP"
    if _has(text, "array_", "usort", "array_chunk", "array_column", "array_combine", "array_merge", "array_filter"):
        return "Массивы"
    if _has(text, "json_", "str_", "htmlspecialchars", "preg_", "str_starts_with", "str_contains"):
        return "Строки и JSON"
    if _has(text, "Router", "DTO", "Value Object", "ValueObject", "SplQueue", "Generator", "SplFileObject"):
        return "Паттерны"
    if _has(text, "match ", "nullsafe", "throw new", ": never", "int|string", "promoted", "readonly "):
        return "PHP 8+"
    return "Основы"


def assign_topics(cards: list[dict], deck_kind: str) -> list[dict]:
    assigners = {
        "angular": assign_angular_topic,
        "python": assign_python_topic,
        "php": assign_php_topic,
    }
    assign = assigners.get(deck_kind)
    if not assign:
        return cards
    for card in cards:
        if not card.get("topic"):
            card["topic"] = assign(card)
    return cards
