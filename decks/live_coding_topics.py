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
    if _has(text, "async def", "await ", "asyncio", "async/await", "корутин"):
        return "Async"
    if _has(text, "TypedDict", "Protocol", "NamedTuple", "TypeVar", "Optional", "Union", "type hint", "typing"):
        return "Typing"
    if _has(
        text,
        "@dataclass",
        "class ",
        "наследован",
        "self",
        "__init__",
        "staticmethod",
        "classmethod",
        "property",
        "MRO",
        "super()",
        "dunder",
        "ABC",
        "abstractmethod",
        "Enum",
        "Counter",
        "class User",
        "class HttpResponse",
    ):
        return "ООП"
    if _has(text, "@lru_cache", "contextmanager", "generator", " yield", "partial", "decorator", "groupby", "closure"):
        return "Функциональное"
    if _has(text, "defaultdict", "deque", "bisect", "Counter", "namedtuple"):
        return "Collections"
    if _has(
        text,
        "pathlib",
        "json.",
        "tempfile",
        "sqlite",
        "argparse",
        "itertools",
        "re module",
        "subprocess",
        "logging",
        "unittest",
        "pytest",
        "GIL",
        "threading",
        "multiprocessing",
    ):
        return "Stdlib"
    return "Основы"


def assign_php_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "enum ", "#[", "Attribute", "атрибут"):
        return "Enums и Attributes"
    if _has(
        text,
        "interface ",
        "abstract class",
        "implements ",
        "trait ",
        "readonly class",
        "__toString",
        "наследован",
        "promoted propert",
        "constructor property",
    ):
        return "ООП"
    if _has(text, "PDO", "password_hash", "HttpResponse", "password_verify"):
        return "PDO и HTTP"
    if _has(text, "array_", "usort", "array_chunk", "array_column", "array_combine", "array_merge", "array_filter"):
        return "Массивы"
    if _has(text, "json_", "str_", "htmlspecialchars", "preg_", "str_starts_with", "str_contains"):
        return "Строки и JSON"
    if _has(text, "Router", "DTO", "Value Object", "ValueObject", "SplQueue", "Generator", "SplFileObject"):
        return "Паттерны"
    if _has(
        text,
        "match ",
        "nullsafe",
        "throw new",
        ": never",
        "int|string",
        "promoted",
        "readonly ",
        "named argument",
        "union type",
        "PHP 8",
    ):
        return "PHP 8+"
    return "Основы"


def assign_go_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "goroutine", "go func", "chan ", "channel", "select ", "WaitGroup", "Mutex", "RWMutex", "sync.", "context.Context", "ctx.Done"):
        return "Goroutines и каналы"
    if _has(text, "interface ", "implements", "type switch", "io.Reader", "io.Writer", "Stringer", "ServeHTTP", "method ", "receiver"):
        return "Методы и интерфейсы"
    if _has(text, "error", "errors.", "fmt.Errorf", "panic", "recover", "ErrNotFound", "%w"):
        return "Ошибки"
    if _has(text, "[T", "comparable", "cmp.Ordered", "generic", "~map", "type parameters"):
        return "Generics"
    if _has(text, "testing.", "t.Run", "Benchmark", "httptest", "t.Helper", "t.Parallel", "TestMain"):
        return "Тестирование"
    if _has(text, "go.mod", "module ", "internal/", "cmd/", "go:build", "package config", "GOPROXY", "go get"):
        return "Модули и пакеты"
    if _has(text, "json.", "http.", "context.", "time.", "os.", "bufio", "sort.", "slog.", "template.", "url.Parse", "net/http"):
        return "Stdlib"
    if _has(text, "defer ", "func ", "closure", "variadic", "named return", "panic", "recover"):
        return "Функции и defer"
    if _has(text, "struct ", "slice", "map[", "append(", "make(", "[]int", "pointer", "embed"):
        return "Типы и структуры"
    return "Основы"


def assign_pytorch_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "DataLoader", "Dataset", "collate_fn", "num_workers", "pin_memory", "__getitem__"):
        return "DataLoader"
    if _has(text, "cuda", "GPU", "device", "amp", "GradScaler", "autocast", "OOM", "mixed precision"):
        return "GPU и производительность"
    if _has(text, "optim.", "SGD", "Adam", "scheduler", "backward", "zero_grad", "loss", "optimizer"):
        return "Обучение"
    if _has(text, "nn.", "Conv2d", "Linear", "BatchNorm", "Dropout", "Module", "Sequential"):
        return "Модули nn"
    if _has(text, "tensor", "Tensor", "view", "reshape", "permute", "detach", "requires_grad"):
        return "Тензоры"
    return "Основы"


def assign_ttk_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "Treeview", "Notebook", "Panedwindow"):
        return "Сложные виджеты"
    if _has(text, "Style", "theme", "layout", "theme_use", "tag_configure"):
        return "Стили и темы"
    if _has(text, "Combobox", "Spinbox", "Scale", "Progressbar", "Entry"):
        return "Элементы ввода"
    if _has(text, "Button", "Label", "Frame", "Checkbutton", "Radiobutton", "Scrollbar"):
        return "Базовые виджеты"
    return "Основы"


def assign_agile_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "Scrum", "Kanban", "SAFe", "LeSS", "Nexus", "XP", "Crystal"):
        return "Фреймворки"
    if _has(text, "backlog", "story", "Epic", "MVP", "INVEST", "acceptance", "DoR", "DoD"):
        return "Backlog и stories"
    if _has(text, "retro", "Kaizen", "impediment", "retrospective", "feedback"):
        return "Командные практики"
    if _has(text, "velocity", "story point", "metric", "WIP", "burndown", "cycle time", "throughput"):
        return "Метрики и поток"
    if _has(text, "Lean", "muda", "value stream", "build-measure", "pivot"):
        return "Lean"
    return "Основы"


def assign_scrum_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "Product Owner", "Scrum Master", "Developer", "Stakeholder", "роль"):
        return "Роли"
    if _has(text, "Sprint Planning", "Daily Scrum", "Review", "Retrospective", "Refinement", "событие", "ceremony"):
        return "События"
    if _has(text, "Increment", "Product Backlog", "Sprint Backlog", "артефакт", "Definition of Done"):
        return "Артефакты"
    if _has(text, "Nexus", "LeSS", "масштаб", "Scrum of Scrums"):
        return "Масштабирование"
    return "Основы"


def assign_kanban_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "WIP", "limit", "политик", "policy", "class of service"):
        return "WIP и политики"
    if _has(text, "lead time", "cycle time", "throughput", "CFD", "метрик", "SLA"):
        return "Метрики потока"
    if _has(text, "replenish", "upstream", "discovery", "triage", "queue"):
        return "Поток работы"
    if _has(text, "Swimlane", "доск", "board", "column", "visual"):
        return "Визуализация"
    return "Основы"


def assign_safe_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "Portfolio", "Value Stream", "Solution Train", "Large Solution"):
        return "Portfolio и потоки"
    if _has(text, "PI Planning", "ART", "Program Increment", "Objective"):
        return "PI Planning"
    if _has(text, "Epic", "Feature", "Enabler", "Story", "backlog"):
        return "Backlog SAFe"
    if _has(text, "RTE", "System Architect", "Product Management", "Business Owner", "роль"):
        return "Роли SAFe"
    return "Основы"


def assign_laravel_topic(card: dict) -> str:
    text = _blob(card)
    if _has(text, "Route::", "Route ", "routing", "middleware('auth')", "resource routes", "api.php", "web.php"):
        return "Роутинг"
    if _has(text, "Controller", "Form Request", "StorePostRequest", "invokable", "redirect()->"):
        return "Контроллеры"
    if _has(
        text,
        "Eloquent",
        "belongsTo",
        "hasMany",
        "Model",
        "fillable",
        "SoftDeletes",
        "with(",
        "scope",
        "Observer",
    ):
        return "Eloquent"
    if _has(text, "Schema::", "migration", "Blueprint", "foreignId", "Seeder", "Factory"):
        return "Миграции"
    if _has(text, "Blade", "@extends", "@section", "@csrf", "<x-", "view(", "components"):
        return "Blade"
    if _has(text, "Middleware", "middleware", "handle(Request", "Terminate"):
        return "Middleware"
    if _has(text, "validate", "Validator", "Rule::", "Form Request", "rules()"):
        return "Валидация"
    if _has(text, "Sanctum", "Auth::", "Policy", "Gate::", "authorize", "guard", "password", "Breeze", "Fortify"):
        return "Аутентификация"
    if _has(text, "ShouldQueue", "dispatch(", "Job", "queue:work", "Horizon", "Bus::"):
        return "Очереди"
    if _has(text, "Event", "Listener", "Observer", "broadcast", "ShouldBroadcast"):
        return "События"
    if _has(text, "PHPUnit", "Pest", "assertDatabase", "actingAs", "RefreshDatabase", "test("):
        return "Тестирование"
    if _has(text, "Resource", "ApiResource", "Sanctum token", "JSON API", "apiResource"):
        return "API"
    if _has(text, "ServiceProvider", "App::bind", "singleton", "container", "IoC", "resolve"):
        return "Service Container"
    if _has(text, "collect(", "Collection", "pluck", "groupBy", "LazyCollection", "Str::"):
        return "Collections"
    if _has(text, "artisan", ".env", "config(", "Vite", "provider", "Laravel"):
        return "Основы"
    return "Основы"


def assign_topics(cards: list[dict], deck_kind: str) -> list[dict]:
    assigners = {
        "angular": assign_angular_topic,
        "python": assign_python_topic,
        "php": assign_php_topic,
        "go": assign_go_topic,
        "laravel": assign_laravel_topic,
        "pytorch": assign_pytorch_topic,
        "ttk": assign_ttk_topic,
        "agile": assign_agile_topic,
        "scrum": assign_scrum_topic,
        "kanban": assign_kanban_topic,
        "safe": assign_safe_topic,
    }
    assign = assigners.get(deck_kind)
    if not assign:
        return cards
    for card in cards:
        if not card.get("topic"):
            card["topic"] = assign(card)
    return cards
