from __future__ import annotations

"""Shared builder for live-coding cards with structured question text."""

import re

_LANG_LABEL = {
    "php": "PHP",
    "python": "Python",
    "typescript": "TypeScript/Angular",
    "ts": "TypeScript/Angular",
}

_TYPE_HINT_ARROW = re.compile(
    r"\)\s*->\s*(?:str|int|float|bool|void|None|list|dict|set|tuple|array|Generator|Closure|Observable|Promise|\w+\[\])"
)


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


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def _extract_io_examples(text: str) -> list[str]:
    """Pull input→output examples from assignment prose (not type hints)."""
    examples: list[str] = []
    for segment in re.split(r"[\n;]", text):
        segment = segment.strip()
        if not segment:
            continue
        if "→" in segment:
            left, right = segment.split("→", 1)
            examples.append(f"{left.strip()} → {right.strip().rstrip('.')}")
            continue
        for m in re.finditer(
            r"((?:пуст\w*|empty)\s+\w+(?:\s+\w+)*)\s+->\s+(\[\]|None|null|'[^']*'|\"[^\"]*\"|\[[^\]]*\]|\d+)",
            segment,
            re.I,
        ):
            left, right = m.group(1).strip(), m.group(2).strip().rstrip(".")
            examples.append(f"{left} → {right}")
        for m in re.finditer(
            r"(?:для|при|если|меньше|больше|отсутств)\s+(\[[^\]]+\]|\"[^\"]+\"|'[^']+'|\w+\([^)]*\))\s+->\s+(\[[^\]]*\]|'[^']*'|\"[^\"]*\"|None|null|\d+|[^,\n\.]+)",
            segment,
            re.I,
        ):
            left, right = m.group(1).strip(), m.group(2).strip().rstrip(".")
            examples.append(f"{left} → {right}")
        cleaned = _TYPE_HINT_ARROW.sub("", segment)
        for m in re.finditer(
            r"(\[[^\]]+\]|\"[^\"]+\"|'[^']+'|\w+\([^)]*\))\s*->\s+(\[[^\]]*\]|'[^']*'|\"[^\"]*\"|None|null|\d+|[^,\n\.]+)",
            cleaned,
        ):
            left, right = m.group(1).strip(), m.group(2).strip().rstrip(".")
            if "->" in left:
                continue
            examples.append(f"{left} → {right}")
    return _dedupe(examples)


def _headline_overlaps(headline: str, text: str) -> bool:
    h = re.sub(r"^Реализовать\s+\S+(?:/\S+)?:\s*", "", headline, flags=re.I).strip().rstrip(".")
    h2 = re.sub(r"^Реализовать\s+\S+-функцию\s+", "", headline, flags=re.I).strip().rstrip(".")
    t = text.strip().rstrip(".")
    for candidate in (h, h2, headline.strip().rstrip(".")):
        if not candidate:
            continue
        cl, ct = candidate.lower(), t.lower()
        if cl == ct or cl in ct or ct in cl:
            return True
    return False


def _behavioral_description(text: str, lang: str, reference: str = "") -> str:
    low = text.lower()

    m = re.search(r"возвраща(?:ющ\w*|ет)\s+(.+)$", text, re.I)
    if m:
        return f"Результат работы: {m.group(1).strip().rstrip('.')}."

    if " — " in text:
        return text.split(" — ", 1)[1].strip().rstrip(".") + "."

    if lang in ("typescript", "ts"):
        if "httpclient" in low or "observable" in low:
            return "Сервис выполняет HTTP-запрос и возвращает типизированный Observable."
        if "ngmodel" in low.replace(" ", ""):
            return "Двустороннее связывание поля ввода с переменной и отображение значения в шаблоне."
        if "formgroup" in low or "reactive" in low:
            return "Reactive-форма с валидацией полей; submit недоступен при invalid."
        if "router" in low or "loadcomponent" in low.replace(" ", ""):
            return "Конфигурация маршрута с lazy load компонента по указанному path."
        if "@output" in low or "eventemitter" in low:
            return "Компонент эмитит событие родителю при действии пользователя."
        if "pipe" in low and "transform" in low:
            return "Pipe преобразует значение в шаблоне через transform()."
        if "guard" in low:
            return "Guard проверяет доступ к маршруту и перенаправляет при отказе."
        if "signal" in low or "effect" in low:
            return "Signals/effect для реактивного состояния и побочных эффектов."
        if "standalone" in low and "компонент" in low:
            return "Standalone-компонент отображает данные в шаблоне по входным параметрам."
        if "сервис" in low or "injectable" in low:
            return "Injectable-сервис инкапсулирует логику для DI в компонентах."
        if "directive" in low or "директив" in low:
            return "Директива меняет поведение или вид host-элемента."
        if "маршрут" in low or "routes" in low:
            return "Описание маршрутов приложения: path, component, guards."

    if lang == "php":
        if "promoted" in low or "promotion" in low:
            return "Класс с constructor property promotion для указанных полей."
        if "readonly class" in low:
            return "Immutable DTO с readonly-полями (PHP 8.2+)."
        if "enum" in low:
            return "Backed enum с перечисленными case и строковыми значениями."
        if "match" in low:
            return "Выбор метки/значения через match по переданному коду."

    if lang == "python":
        if "dataclass" in low:
            return "Dataclass с полями и методами экземпляра."
        if "@property" in low or "property" in low:
            return "Property вычисляет производное значение из полей объекта."

    if any(k in low for k in ("класс ", "class ")):
        return "Класс с требуемыми полями, методами и инкапсуляцией состояния."
    if "enum" in low:
        return "Enum с указанными case."
    if any(k in low for k in ("функц", "function", "метод")):
        return "Функция должна соответствовать сигнатуре и описанному поведению."

    sentences = _split_sentences(text)
    if len(sentences) > 1:
        rest = ". ".join(s.rstrip(".") for s in sentences[1:])
        return rest + ("." if not rest.endswith(".") else "")

    return "Реализуйте решение с нуля согласно описанию задания."


def _infer_python_example(assignment: str, reference: str) -> str:
    low = assignment.lower()
    if "enum" in low:
        cls = re.search(r"class\s+(\w+)", reference)
        if cls:
            return f"{cls.group(1)}.ACTIVE.value == 'active'"
    cls = re.search(r"class\s+(\w+)", reference)
    if not cls:
        return ""
    cname = cls.group(1)
    if "person" in low and "full_name" in low.replace(" ", ""):
        return "Person('John', 'Doe').full_name → 'John Doe'"
    if "stack" in low:
        return "push(1); push(2); pop() → 2"
    if "queue" in low:
        return "enqueue(1); dequeue() → 1"
    if "validationerror" in low.replace(" ", ""):
        return "validate_non_empty('', 'email') → ValidationError"
    if "card" in low and "label" in low:
        return "Card('A', 'spades').label() → 'A of spades'"
    methods = re.findall(r"^\s+def\s+(\w+)\s*\(", reference, re.M)
    public = [m for m in methods if not m.startswith("_")]
    if public:
        return f"{cname}().{public[0]}() — поведение согласно описанию"
    return f"использование класса {cname} согласно описанию"


def _infer_php_example(assignment: str, reference: str) -> str:
    low = assignment.lower()
    cls = re.search(r"(?:class|enum)\s+(\w+)", reference)
    name = cls.group(1) if cls else ""
    if "promoted" in low and name:
        return f"new {name}(1, 'user@mail.com') — id и email доступны"
    if "readonly class" in low and name:
        return f"new {name}(100, 'USD') — поля только для чтения"
    if "enum" in low and name:
        return f"{name}::Active->value === 'active'"
    if "match" in low or "statuslabel" in low.replace(" ", ""):
        return "statusLabel(200) → 'OK', statusLabel(404) → 'Not Found'"
    if "fromstring" in low.replace(" ", "") and name:
        return f"{name}::fromString('user@mail.com') — фабричный метод"
    if "validationexception" in low.replace(" ", "") and name:
        return "validateNonEmpty('', 'email') → ValidationException"
    if "attribute" in low or "#[route" in low.replace(" ", ""):
        return "GET /api/users → вызов listUsers() с атрибутом Route"
    fn = re.search(r"function\s+(\w+)\s*\(", reference)
    if fn and fn.group(1) not in ("__construct",):
        return f"{fn.group(1)}(...) — поведение согласно описанию"
    if name:
        return f"использование {name} согласно описанию"
    return ""


def _infer_angular_example(assignment: str, reference: str) -> str:
    low = assignment.lower()
    ref_low = reference.lower()
    combined = f"{low} {ref_low}"
    comb_flat = combined.replace(" ", "")

    if "hello" in ref_low or "greeting" in ref_low:
        return 'name="Alice" → шаблон «Hello, Alice!»'
    if "counterservice" in ref_low or ("increment" in low and "сервис" in low):
        return "increment() → 1, increment() → 2, value() → 2"
    if "ngmodel" in comb_flat:
        return 'title="Draft" → значение в input и <p>'
    if "getusers" in comb_flat:
        return "getUsers() → Observable<User[]> (GET /api/users)"
    if "rating" in low and ("eventemitter" in comb_flat or "@output" in combined):
        return 'клик «3» → rated.emit(3)'
    if "loadcomponent" in comb_flat:
        return "path 'admin' → lazy load AdminPage"
    if "authguard" in comb_flat or "canactivatefn" in ref_low:
        return "!isLoggedIn() → parseUrl('/login'); иначе true"
    if "truncate" in low:
        return "'abcdefghij' | truncate:5 → 'abcde…'"
    if "@for" in low or ("async" in low and "users" in low):
        return "users$ | async → список в шаблоне через @for"
    if "routerlink" in comb_flat:
        return 'routerLinkActive="active" на текущем маршруте'
    if "formgroup" in comb_flat or "reactive form" in low:
        return "кнопка submit disabled, пока form.invalid"
    if "signal" in comb_flat and "effect" in comb_flat:
        return "effect срабатывает при изменении signal query"
    if "interceptor" in comb_flat:
        return "исходящий запрос получает заголовок Authorization: Bearer …"
    if "resolver" in comb_flat:
        return "route param id → данные пользователя до открытия страницы"
    if "candeactivate" in comb_flat:
        return "form.dirty → confirm('Leave?') перед уходом"
    if ("директив" in low or "@directive" in ref_low) and (
        "hostbinding" in comb_flat or "hostlistener" in comb_flat
    ):
        return "mouseenter → подсветка фона host-элемента"
    if "matdialog" in ref_low or "openconfirm" in comb_flat:
        return 'openConfirm("Delete?") → Observable<boolean>'
    if "bootstrapapplication" in comb_flat:
        return "bootstrapApplication(AppComponent, { providers: [provideRouter(...), ...] })"
    if "errorhandler" in comb_flat:
        return "handleError(err) → console.error(err)"
    if "appinitializer" in comb_flat:
        return "provideAppInitializer(() => inject(ConfigService).load())"
    if "title:" in low and "data:" in low:
        return "route title и data доступны через ActivatedRoute"
    if "withcomponentinputbinding" in comb_flat:
        return "route param :id → input.required<string>() в компоненте"
    if "canmatch" in comb_flat:
        return "canMatch решает, подходит ли маршрут для URL"
    if "validatorfn" in comb_flat or "validators" in comb_flat and "email" in low:
        return "невалидный email → { email: true }"
    if "injectiontoken" in comb_flat or "api_url" in comb_flat:
        return "inject(API_URL) → базовый URL API из providers"
    if "canactivatechild" in comb_flat or "authchildguard" in comb_flat:
        return "дочерний маршрут без login → redirect /login"
    if "multi:" in low or "multi: true" in reference.lower():
        return "несколько VALIDATORS объединяются в форме"
    if "provideanimations" in comb_flat:
        return "provideAnimations() в app.config.ts включает анимации"
    if "configuretestingmodule" in comb_flat or "spectator" in comb_flat or " spec " in f" {low} ":
        return "TestBed.createComponent → detectChanges → проверка DOM"
    if "transferstate" in comb_flat:
        return "SSR: данные из TransferState доступны на клиенте"
    if "platformserver" in comb_flat:
        return "renderApplication(AppComponent, { document, url }) на сервере"
    pipe = re.search(r"@Pipe\(\{\s*name:\s*['\"](\w+)['\"]", reference)
    if pipe:
        return f"| {pipe.group(1)} применяет transform в шаблоне"
    sel = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", reference)
    if sel and "@Directive" in reference:
        return f"элемент {sel.group(1)} — поведение директивы"
    if sel and "Component" in reference:
        return f"<{sel.group(1)} /> — рендер шаблона компонента"
    if "@Injectable" in reference:
        cls = re.search(r"export class (\w+)", reference)
        if cls:
            return f"inject({cls.group(1)}) в компоненте или сервисе"
    if "routes" in ref_low and ("path:" in reference or "Routes" in reference):
        return "path из routes[] → соответствующий компонент"
    if "CanActivateChildFn" in reference or "CanActivateFn" in reference:
        return "guard возвращает true или UrlTree redirect"
    if "InjectionToken" in reference:
        tok = re.search(r"InjectionToken\w*<[^>]+>\(['\"](\w+)['\"]", reference)
        name = tok.group(1) if tok else "TOKEN"
        return f"inject({name}) → значение из providers"
    if "ValidatorFn" in reference or "Validators" in reference:
        return "validator возвращает null (valid) или объект ошибки"
    if "TestBed" in reference or "describe(" in reference:
        return "it('...', () => { ... expect(...) }) — unit-тест компонента"
    return ""


def _infer_example(assignment: str, reference: str, lang: str, headline: str) -> str:
    _, ex = _split_example(assignment)
    if ex:
        return ex
    extracted = _extract_io_examples(assignment)
    if extracted:
        return extracted[0]
    if " → " in assignment:
        return assignment.split(" → ", 1)[1].strip().rstrip(".")
    low = assignment.lower()
    if "greet" in low or "hello" in low:
        if lang == "php":
            return 'greet("Alice") → "Hello, Alice!"'
        if lang == "python":
            return 'greet("Alice") → "Hello, Alice!"'
        if lang in ("typescript", "ts"):
            return 'name="Alice" → "Hello, Alice!"'
    if "total" in low and ("sum" in low or "сумм" in low):
        sample = "[1, 2, 3] → 6" if lang != "php" else "total([1, 2, 3]) → 6"
        return sample
    if "squares" in low or "квадрат" in low:
        return "squares(4) → [0, 1, 4, 9]" if lang == "python" else "squares([1, 2, 3]) → [1, 4, 9]"
    if "evens" in low or "чётн" in low:
        return "evens([1, 2, 3, 4]) → [2, 4]"
    if "match" in low and "200" in assignment:
        return "statusLabel(200) → 'OK', statusLabel(404) → 'Not Found'"
    if "counter" in low and ("increment" in low or "счётчик" in low):
        return "increment() → 1, increment() → 2, value() → 2"
    if "formgroup" in low or "reactive form" in low:
        return "form.invalid === true пока email/password пусты"
    if lang in ("typescript", "ts"):
        ex = _infer_angular_example(assignment, reference)
        if ex:
            return ex
    if lang == "python":
        ex = _infer_python_example(assignment, reference)
        if ex:
            return ex
    if lang == "php":
        if "statuslabel" in low or "match" in low:
            return "statusLabel(200) → 'OK', statusLabel(404) → 'Not Found'"
        if "enum" in low and "status" in low:
            return "Status::Active->value === 'active'"
        if "money" in low or "readonly class" in low:
            return "new Money(100, 'USD') — поля только для чтения"
        ex = _infer_php_example(assignment, reference)
        if ex:
            return ex
    fn = re.search(r"(?:function|def)\s+(\w+)\s*\(", reference)
    if fn and lang == "python":
        name = fn.group(1)
        if name not in ("__init__",):
            return f"{name}(...) — поведение согласно описанию"
    return ""


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
        if low.startswith(("создайте ", "создай ", "реализуйте ", "реализуй ", "напиши ")):
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
    low = text.lower()
    sentences = _split_sentences(text)
    first = sentences[0] if sentences else text

    if " — " in first and len(sentences) <= 1:
        detail = first.split(" — ", 1)[1].strip()
        if detail:
            return detail.rstrip(".") + "."
    if " - " in first and not re.search(r"\$\w+\s*=\s*", first) and len(sentences) <= 1:
        left, detail = first.split(" - ", 1)
        if len(left) < 90 and detail.strip():
            return detail.strip().rstrip(".") + "."
    if len(sentences) <= 1:
        if re.match(r"Generator function\s+", text, re.I):
            name = re.search(r"Generator function\s+(\w+)", text, re.I)
            fn = name.group(1) if name else "функция"
            return (
                f"Функция {fn} должна возвращать последовательность значений через yield "
                f"в соответствии с переданными параметрами."
            )
        if sentences and _headline_overlaps(headline, sentences[0]):
            return _behavioral_description(text, lang)
        if sentences:
            s = sentences[0].rstrip(".")
            if _headline_overlaps(headline, s):
                return _behavioral_description(text, lang)
            if any(k in low for k in ("класс ", "class ", "dataclass", "компонент", "сервис", "enum", "interface", "маршрут", "pipe", "directive")):
                return _behavioral_description(text, lang)
            if any(k in low for k in ("функц", "function", "метод")):
                return _behavioral_description(text, lang)
            return s + "."
        return _behavioral_description(text, lang)

    if sentences and _headline_overlaps(headline, sentences[0]):
        rest = ". ".join(s.rstrip(".") for s in sentences[1:])
        if rest:
            if not rest.endswith("."):
                rest += "."
            return rest
        return _behavioral_description(text, lang)

    rest = ". ".join(s.rstrip(".") for s in sentences[1:])
    if rest and not rest.endswith("."):
        rest += "."
    return rest


def _default_considerations(assignment: str, lang: str, reference: str = "") -> list[str]:
    items: list[str] = []
    text = assignment.lower()
    ref = reference.lower()

    if lang == "python":
        items.append("Соблюдение указанных type hints и возвращаемого типа")
    elif lang == "php":
        items.append("declare(strict_types=1) и строгая типизация параметров")
    elif lang in ("typescript", "ts"):
        items.append("Корректные imports и декораторы Angular")

    for m in re.finditer(r"без\s+([a-z_][\w.]*(?:\(\))?)", text, re.I):
        items.append(f"Реализовать вручную, без использования {m.group(1)}")

    if any(w in text for w in ("пуст", "empty", "[]", "пустой список", "пустая строка", "пустой массив")):
        items.append("Корректная обработка пустого входа")
    elif any(w in text for w in ("list[", "array", "массив", "dict", "словар", "set(", "iterable")):
        items.append("Корректная работа с пустым массивом или списком")

    if any(w in text for w in ("none", "| none", "nullable", "optional", "null", "?->")):
        items.append("Безопасная обработка None / null / optional значений")

    if any(w in text for w in ("мин", "max", "clamp", "границ", "диапазон", "low", "high", "bound")):
        items.append("Граничные значения и краевые случаи")

    if "generator" in text or "yield" in text or "yield" in ref:
        items.extend([
            "Последовательную выдачу значений через yield",
            "Корректную работу граничных значений и остановку итерации",
        ])
    if "$step" in assignment or re.search(r"\bstep\b", text):
        items.append("Поддержку положительного и отрицательного шага")

    if any(w in text for w in ("метод", "method", "property", "@property", "increment", "value()")):
        items.append("Инкапсуляция состояния и публичный API")

    if "match" in text or "enum" in text:
        items.append("Покрытие всех указанных веток / case и значение по умолчанию")

    if "async" in text or "await" in ref or "observable" in text:
        items.append("Корректное использование async/await или Observable")

    if "required" in text or "validators" in text or "validator" in text:
        items.append("Валидация обязательных полей и сообщений об ошибках")

    if lang in ("typescript", "ts"):
        if "standalone" in text:
            items.append("Standalone-компонент с корректным imports в декораторе")
        if "@input" in text or "@output" in text or "input()" in text or "output()" in text:
            items.append("Корректные @Input/@Output или signal inputs/outputs")
        if "formgroup" in text or "reactive" in text:
            items.append("Reactive Forms: FormGroup, FormControl, Validators")
        if "ngmodel" in text.replace(" ", ""):
            items.append("Импорт FormsModule и двустороннее связывание [(ngModel)]")
        if "router" in text or "routerlink" in text.replace(" ", ""):
            items.append("Маршрутизация: RouterLink, RouterOutlet или loadComponent")
        if "http" in text or "httpclient" in text.replace(" ", ""):
            items.append("HttpClient и типизация ответа API")
        if "signal" in text or "computed" in text or "effect" in text:
            items.append("Signals API: signal, computed, effect — по заданию")
        if "pipe" in text and "standalone" in text:
            items.append("Standalone pipe с корректным именем в декораторе @Pipe")
        if "directive" in text or "директив" in text:
            items.append("Директива: selector, standalone и host bindings/listeners")

    if "readonly" in text or "promoted" in text or "promotion" in text:
        items.append("Современный синтаксис PHP 8.1+ (readonly, promoted properties)")

    if "dataclass" in text or "@dataclass" in reference:
        items.append("Dataclass с полями и методами экземпляра")

    items = _dedupe(items)
    if len(items) < 2:
        items.append("Соблюдение сигнатуры и ожидаемого поведения из описания")
    if len(items) < 3:
        items.append("Читаемость кода без лишней сложности")
    return items[:5]


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

    if headline.strip():
        h = headline.strip()
        desc = description.strip() or context.strip()
    else:
        h = _legacy_headline(title, assignment_body, lang)
        desc = description.strip() or _legacy_description(title, assignment_body, h, lang)
        if context.strip() and not desc:
            desc = context.strip()
        if not considerations:
            considerations = _default_considerations(assignment_body, lang, reference)

    if re.search(r"rangeStep\s*\(", assignment_body, re.I):
        label = _lang_label(lang)
        h = f"Реализовать {label}-функцию-генератор rangeStep(int $start, int $stop, int $step = 1): Generator."
        desc = "Функция должна возвращать последовательность чисел от $start до $stop с шагом $step."
        considerations = [
            "Работу с положительным и отрицательным шагом",
            "Проверку на $step = 0 (выбросить исключение или вернуть пустой результат)",
            "Корректную обработку граничных условий (включительно $stop)",
        ]
        example = example or ex_from_text or "rangeStep(1, 10, 2) → 1, 3, 5, 7, 9"
    if not example:
        example = ex_from_text or _infer_example(assignment_body, reference, lang, h)

    if not example:
        extracted = _extract_io_examples(assignment_body)
        if extracted:
            example = extracted[0]

    if not example and lang == "php":
        example = _infer_php_example(assignment_body, reference)

    if not example and lang == "python":
        example = _infer_python_example(assignment_body, reference)

    if not example and lang in ("python", "php", "typescript", "ts"):
        fn = re.search(r"(?:function|def)\s+(\w+)\s*\(", reference)
        if fn and fn.group(1) not in ("__init__", "__construct"):
            name = fn.group(1)
            if lang == "python" and "class " in reference.lower():
                example = f"метод {name}() — поведение согласно описанию"
            else:
                example = f"{name}(...) — поведение согласно описанию"
        elif lang in ("typescript", "ts"):
            ex = _infer_angular_example(assignment_body, reference)
            if ex:
                example = ex
            elif "Component" in reference:
                sel = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", reference)
                if sel:
                    example = f"<{sel.group(1)} /> — рендер шаблона"
            elif "Service" in reference:
                cls = re.search(r"export class (\w+)", reference)
                if cls:
                    example = f"{cls.group(1)} inject через DI в компоненте"

    if not desc:
        desc = _legacy_description(title, assignment_body, h, lang)

    if not considerations:
        considerations = _default_considerations(assignment_body, lang, reference)

    question = _build_question(h, desc, considerations=considerations, example=example)
    return {
        "card_type": "live_code",
        "question": question,
        "task": "",
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
