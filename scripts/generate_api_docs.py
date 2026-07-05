#!/usr/bin/env python3
"""Generate docs/classes, docs/methods, docs/functions from API registry."""
from __future__ import annotations

import ast
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Hand-written descriptions (Russian). Key: "module:qualname"
DESCRIPTIONS: dict[str, str] = {
    # deck.py
    "app.deck:stable_card_id": "Вычисляет стабильный числовой id карточки по содержимому. Одинаковый на desktop, web и после перезапуска.",
    "app.deck:infer_language_from_name": "Угадывает язык редактора (python, typescript, php, latex) по имени колоды.",
    "app.deck:Card": "Одна карточка Anki: вопрос, эталон, тип (text/code/live_code/math), код, тема.",
    "app.deck:Card.__post_init__": "Присваивает id через stable_card_id, если не задан явно.",
    "app.deck:Card.is_live_code": "True, если card_type == live_code.",
    "app.deck:Card.is_code": "True для code/live_code или если задан фрагмент code.",
    "app.deck:Card.is_math": "True для card_type math или answer_mode math.",
    "app.deck:Card.needs_code_editor": "Нужен ли QScintilla/Monaco для ответа.",
    "app.deck:Card.needs_math_editor": "Нужен ли MathLive-редактор LaTeX для ответа.",
    "app.deck:Card.display_text": "Текст вопроса для UI: вопрос + код + задание.",
    "app.deck:ChatMessage": "Сообщение в диалоге с Ollama (role, content).",
    "app.deck:ReviewResult": "Результат проверки ответа моделью: балл, feedback, hint, follow_up.",
    "app.deck:Deck": "Колода карточек с именем, языком и списком Card.",
    "app.deck:Deck.merge": "Добавляет карточки из другой колоды; опционально меняет имя.",
    "app.deck:Deck.load_json": "Загружает колоду из JSON (объект с cards или массив).",
    "app.deck:Deck.load_anki_txt": "Загружает колоду из Anki TXT (front\\tback).",
    # progress.py
    "app.progress:StudyMode": "Режим сессии: DUE, NEW, WEAK, ALL.",
    "app.progress:AnswerRecord": "Одна запись в истории ответов по карточке.",
    "app.progress:AnswerRecord.from_dict": "Десериализация из progress.json.",
    "app.progress:CardProgress": "SRS-состояние одной карточки: баллы, интервал, due_at, history.",
    "app.progress:CardProgress.from_dict": "Десериализация из progress.json.",
    "app.progress:CardProgress.is_due": "Пора ли повторять (due_at <= now или карточка новая).",
    "app.progress:CardProgress.is_new": "Карточка ещё ни разу не проходилась.",
    "app.progress:CardProgress.days_until_due": "Дней до due_at (отрицательное — просрочено).",
    "app.progress:DeckSummary": "Агрегированная статистика колоды для главного экрана.",
    "app.progress:ProgressStore": "Хранилище progress.json: очереди, SRS, история ответов.",
    "app.progress:ProgressStore.load": "Загрузить progress.json с диска.",
    "app.progress:ProgressStore.save": "Сохранить progress.json.",
    "app.progress:ProgressStore.deck_key": "Ключ колоды в JSON (deck_id или имя).",
    "app.progress:ProgressStore.get": "Прогресс карточки; создаёт пустой CardProgress при отсутствии.",
    "app.progress:ProgressStore.record_answer": "Записывает ответ, обновляет SRS и историю.",
    "app.progress:ProgressStore.summary": "Сводка: total, mastered, due, new, weak, avg_score.",
    "app.progress:ProgressStore.build_queue": (
        "Формирует очередь карточек для сессии. mode — StudyMode; topic — фильтр по теме; "
        "limit — session_limit; pass_score — для WEAK. Новые и просроченные сортируются по приоритету SRS."
    ),
    "app.progress:ProgressStore.card_history": "Список AnswerRecord по card_id.",
    "app.progress:ProgressStore.next_cards": "Следующие карточки к сроку (legacy helper).",
    "app.progress:ProgressStore.update": "Обновляет CardProgress после зачёта/незачёта.",
    "app.progress:ProgressStore.reconcile_deck": "Синхронизирует ключи/id с текущим составом колоды.",
    "app.progress:ProgressStore.remap_unstable_card_ids": "Переносит прогресс при смене id карточек.",
    "app.progress:ProgressStore.migrate_deck_keys": "Переносит прогресс при смене deck_id.",
    # registry.py
    "app.registry:legacy_deck_id": "Legacy id колоды по абсолютному пути файла.",
    "app.registry:deck_id_for_path": "Стабильный id: по scope+имя файла или legacy.",
    "app.registry:DeckEntry": "Запись о колоде в decks.json: id, имя, пути к файлам.",
    "app.registry:DeckEntry.primary_path": "Первый путь из paths.",
    "app.registry:DeckEntry.is_live_coding": "True, если в имени файла есть live-coding.",
    "app.registry:DeckEntry.is_math": "True, если math в имени json-файла.",
    "app.registry:DeckEntry.has_topics": "Быстрая эвристика; точнее has_topic_picker_deck(deck).",
    "app.registry:DeckEntry.from_dict": "Десериализация из decks.json.",
    "app.registry:DeckRegistry": "Реестр колод: builtin, custom, миграции id.",
    "app.registry:DeckRegistry.load": "Загрузить decks.json, просканировать каталоги, сохранить.",
    "app.registry:DeckRegistry.migrate_progress": "Применить миграции deck_id к ProgressStore.",
    "app.registry:DeckRegistry.save": "Записать decks.json.",
    "app.registry:DeckRegistry.register_file": "Добавить пользовательский файл колоды.",
    "app.registry:DeckRegistry.find_by_path": "Найти DeckEntry по пути файла.",
    "app.registry:DeckRegistry.get": "DeckEntry по deck_id или None.",
    "app.registry:DeckRegistry.load_deck": "Загрузить Deck; для составных — merge частей.",
    # live_coding.py
    "app.live_coding:is_live_coding_entry": "True, если live-coding в имени файла.",
    "app.live_coding:is_math_entry": "True для *math*.json.",
    "app.live_coding:is_live_coding_deck": "Все карточки — live_code.",
    "app.live_coding:is_math_deck": "Все карточки — math.",
    "app.live_coding:has_topic_picker_deck": (
        "True, если в колоде **две или более** различных непустых темы на карточках. "
        "Desktop и web показывают диалог выбора темы перед стартом сессии."
    ),
    # registry.py
    "app.live_coding:deck_topics": "Отсортированный список уникальных topic на карточках.",
    "app.live_coding:topic_summaries": (
        "Список dict для UI: name, total, due, new, weak — агрегация ProgressStore по card.topic."
    ),
    "app.live_coding:filter_cards_by_topic": "Фильтр карточек по имени темы.",
    # config_store.py
    "app.config_store:normalize_code_editor_theme": "light или dark; иначе default.",
    "app.config_store:monaco_theme_name": "vs или vs-dark для Monaco в web.",
    "app.config_store:data_dir": "~/.ai-anki или AI_ANKI_DATA_DIR.",
    "app.config_store:custom_decks_dir": "data_dir/decks — пользовательские колоды.",
    "app.config_store:user_config_path": "data_dir/config.json.",
    "app.config_store:load_config": "defaults → project config.json → user config.json.",
    "app.config_store:clamp_auto_advance_ms": "0 … AUTO_ADVANCE_MAX_SEC×1000 мс.",
    "app.config_store:auto_advance_seconds": "Секунды автоперехода для UI.",
    "app.config_store:migrate_config": "Миграция устаревших значений config.",
    "app.config_store:clamp_session_limit": "1 … SESSION_LIMIT_MAX.",
    "app.config_store:save_config": "Запись config.json с clamp/normalize.",
    # ollama_client.py
    "app.ollama_client:normalize_ollama_url": "Нормализует URL Ollama/Open WebUI.",
    "app.ollama_client:OllamaClient": "HTTP-клиент chat API Ollama.",
    "app.ollama_client:OllamaClient.health": "Проверка доступности и списка моделей.",
    "app.ollama_client:OllamaClient.chat": "Отправка messages, возврат текста ответа.",
    "app.ollama_client:AnswerEvaluator": "Промпты и разбор JSON-оценки ответов.",
    "app.ollama_client:AnswerEvaluator.evaluate": "Оценка ответа 0–100, hint, follow_up.",
    "app.ollama_client:AnswerEvaluator.request_hint": "Запрос подсказки без финальной оценки.",
    # code_completions.py
    "app.code_completions:normalize_editor_language": "python | typescript | php | plaintext.",
    "app.code_completions:completion_items": "Список подсказок Ctrl+Space для языка.",
    # asr_client.py
    "app.asr_client:normalize_asr_url": "Базовый URL Whisper ASR.",
    "app.asr_client:transcribe_whisper": "POST аудио → текст (web голосовой ввод).",
    # math_editor.py
    "app.math_editor:create_math_editor_panel": "MathLive-панель или fallback PlainText.",
    "app.math_editor:create_math_question_view": "KaTeX-просмотр вопроса или fallback.",
    "app.math_editor:MathEditorPanel": "PyQt WebEngine + MathLive для ввода LaTeX.",
    "app.math_editor:MathEditorPanel.plain_text": "Текущий LaTeX из редактора.",
    "app.math_editor:MathEditorPanel.set_text": "Установить LaTeX (с очередью до ready).",
    "app.math_editor:MathEditorPanel.clear": "Очистить редактор.",
    "app.math_editor:MathEditorPanel.set_focus": "Фокус в MathLive.",
    "app.math_editor:MathQuestionView": "KaTeX-рендер вопроса в WebEngine.",
    "app.math_editor:MathQuestionView.set_question": "Отобразить текст/LaTeX вопроса.",
    "app.math_editor:MathEditorPanelFallback": "PlainText fallback без WebEngine.",
    "app.math_editor:MathQuestionViewFallback": "Read-only PlainText для вопроса.",
    # code_editor.py
    "app.code_editor:CodeEditor": "QScintilla с подсветкой и Ctrl+Space.",
    "app.code_editor:CodeEditor.set_theme": "light/dark палитра.",
    "app.code_editor:CodeEditor.set_language": "Lexer по языку карточки.",
    "app.code_editor:CodeEditorPanel": "Обёртка CodeEditor + submit по Ctrl+Enter.",
    "app.code_editor:CodeEditorPanel.set_theme": "Прокидывает тему в редактор.",
    "app.code_editor:CodeEditorPanel.set_placeholder": "Подсказка в пустом редакторе.",
    "app.code_editor:CodeEditorPanel.set_language_hint": "Язык подсветки.",
    "app.code_editor:CodeEditorPanel.plain_text": "Текст кода.",
    "app.code_editor:CodeEditorPanel.set_plain_text": "Задать код (starter для live_code).",
    "app.code_editor:CodeEditorPanel.clear": "Очистить.",
    "app.code_editor:CodeEditorPanel.set_focus": "Фокус в редактор.",
    # topic_picker.py
    "app.topic_picker:TopicPickerDialog": "Диалог выбора темы перед сессией.",
    "app.topic_picker:TopicPickerDialog.selected_topic": "Имя выбранной темы после accept.",
    # welcome.py
    "app.welcome:WelcomeScreen": "Главный экран: колоды, настройки, режимы.",
    "app.welcome:WelcomeScreen.sync_from_config": "Синхронизировать виджеты из config.",
    "app.welcome:WelcomeScreen.refresh": "Перечитать колоды и статистику.",
    # gui.py
    "app.gui:EvaluateWorker": "QThread: evaluate() в фоне.",
    "app.gui:HintWorker": "QThread: request_hint() в фоне.",
    "app.gui:HistoryDialog": "Диалог истории ответов по карточке.",
    "app.gui:StudyScreen": "Экран сессии: вопрос, редактор, Ollama.",
    "app.gui:StudyScreen.apply_config": "Обновить настройки без перезапуска.",
    "app.gui:MainWindow": "QMainWindow: welcome ↔ study stack.",
    "app.gui:run_app": "Точка входа PyQt6-приложения.",
    # server
    "server.services:StudySession": "Состояние веб-сессии занятий.",
    "server.services:StudySession.current": "Текущая карточка из queue[index].",
    "server.services:StudySession.finished": "index >= len(queue).",
    "server.services:AppServices": "Бизнес-логика веб-версии.",
    "server.services:AppServices.reload_config": "Перечитать config и registry.",
    "server.services:AppServices.pass_score": "Порог зачёта из config.",
    "server.services:AppServices.max_follow_ups": "Лимит уточнений.",
    "server.services:AppServices.evaluator": "AnswerEvaluator с текущим Ollama.",
    "server.services:AppServices.deck_summary_row": "Строка таблицы колод для API.",
    "server.services:AppServices.deck_topics": "Список тем колоды для picker.",
    "server.services:AppServices.start_session": "Новая StudySession с очередью.",
    "server.services:AppServices.session_stats": "Статистика для UI сессии.",
    "server.services:AppServices.session_display_name": "Имя колоды · тема.",
    "server.services:AppServices.card_payload": "JSON карточки для frontend.",
    "server.services:AppServices.submit_answer": "Проверка ответа, обновление session.",
    "server.services:AppServices.transcribe_audio": "Whisper ASR для web.",
    "server.services:AppServices.request_hint": "Подсказка по текущей карточке.",
    "server.services:AppServices.next_card": "Переход к следующей карточке.",
    "server.services:AppServices.save_settings": "POST /api/config.",
    "server.services:AppServices.test_ollama": "Health-check Ollama.",
    "server.main:NoCacheStaticFiles": "StaticFiles без кэша для .js/.css.",
    "server.main:SettingsIn": "Pydantic: тело POST /api/config.",
    "server.main:SessionStartIn": "Pydantic: deck_id, mode, topic.",
    "server.main:AnswerIn": "Pydantic: answer.",
    "server.main:HintIn": "Pydantic: draft.",
    "server.main:index": "GET / — index.html.",
    "server.main:list_decks": "GET /api/decks.",
    "server.main:get_config": "GET /api/config.",
    "server.main:save_config_api": "POST /api/config.",
    "server.main:test_ollama": "POST /api/ollama/test.",
    "server.main:deck_topics": "GET /api/deck/{deck_id}/topics.",
    "server.main:start_session": "POST /api/session.",
    "server.main:get_session": "GET /api/session/{id}.",
    "server.main:submit_answer": "POST /api/session/{id}/answer.",
    "server.main:next_card": "POST /api/session/{id}/next.",
    "server.main:show_hint": "POST /api/session/{id}/hint.",
    "server.main:transcribe_audio": "POST /api/asr/transcribe.",
    "main:main": "Вызов app.gui.run_app().",
}

MODULES = [
    ROOT / "main.py",
    ROOT / "app" / "deck.py",
    ROOT / "app" / "progress.py",
    ROOT / "app" / "registry.py",
    ROOT / "app" / "live_coding.py",
    ROOT / "app" / "config_store.py",
    ROOT / "app" / "ollama_client.py",
    ROOT / "app" / "code_completions.py",
    ROOT / "app" / "asr_client.py",
    ROOT / "app" / "math_editor.py",
    ROOT / "app" / "code_editor.py",
    ROOT / "app" / "topic_picker.py",
    ROOT / "app" / "welcome.py",
    ROOT / "app" / "gui.py",
    ROOT / "server" / "services.py",
    ROOT / "app" / "server" / "main.py" if False else ROOT / "server" / "main.py",
]


def module_key(path: Path) -> str:
    rel = path.relative_to(ROOT)
    parts = list(rel.parts)
    if parts[-1] == "main.py" and len(parts) == 1:
        return "main"
    if parts[0] == "app":
        return "app." + path.stem
    if parts[0] == "server":
        return "server." + path.stem
    return ".".join(parts)


def qual(module: str, name: str) -> str:
    return f"{module}:{name}"


def get_sig(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = []
        for a in node.args.args:
            if a.arg == "self":
                continue
            ann = ""
            if a.annotation:
                ann = f": {ast.unparse(a.annotation)}"
            args.append(f"{a.arg}{ann}")
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        ret = ""
        if node.returns:
            ret = f" -> {ast.unparse(node.returns)}"
        return f"({', '.join(args)}){ret}"
    return ""


def describe(key: str, fallback: str) -> str:
    return DESCRIPTIONS.get(key, fallback or "—")


def write_method(class_name: str, method_name: str, module: str, sig: str, desc: str, source: str) -> Path:
    path = DOCS / "methods" / class_name / f"{method_name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    rel_module = module.replace(".", "/")
    content = f"""# `{class_name}.{method_name}`

**Модуль:** [`{module}`](../../modules/{module}.md)  
**Исходник:** `{source}`

## Сигнатура

```python
def {method_name}{sig}
```

## Описание

{desc}

## См. также

- [Класс `{class_name}`](../../classes/{class_name}.md)
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_function(name: str, module: str, sig: str, desc: str, source: str) -> Path:
    path = DOCS / "functions" / f"{name}.md"
    content = f"""# `{name}`

**Модуль:** [`{module}`](../modules/{module}.md)  
**Исходник:** `{source}`

## Сигнатура

```python
def {name}{sig}
```

## Описание

{desc}
"""
    path.write_text(content, encoding="utf-8")
    return path


def write_class(name: str, module: str, methods: list[str], desc: str, source: str) -> None:
    path = DOCS / "classes" / f"{name}.md"
    method_links = "\n".join(
        f"- [`{m}`](../methods/{name}/{m}.md)" for m in sorted(set(methods))
    ) or "_Нет публичных методов._"
    content = f"""# `{name}`

**Модуль:** [`{module}`](../modules/{module}.md)  
**Исходник:** `{source}`

## Описание

{desc}

## Методы и свойства

{method_links}
"""
    path.write_text(content, encoding="utf-8")


def write_module_overview(module: str, items: list[str], source_rel: str) -> None:
    path = DOCS / "modules" / f"{module}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(f"- {i}" for i in items)
    content = f"""# Модуль `{module}`

**Файл:** `{source_rel}`

## Содержимое

{lines}
"""
    path.write_text(content, encoding="utf-8")


def process_file(path: Path) -> tuple[list[str], list[str]]:
    mod = module_key(path)
    source_rel = str(path.relative_to(ROOT))
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module_items: list[str] = []
    classes_info: list[tuple[str, list[str]]] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("_") and node.name not in ("StudyMode",):
                continue
            methods: list[str] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_") and item.name != "__post_init__":
                        continue
                    methods.append(item.name)
                    key = qual(mod, f"{node.name}.{item.name}")
                    sig = get_sig(item)
                    desc = describe(key, f"Метод класса `{node.name}`.")
                    write_method(node.name, item.name, mod, sig, desc, source_rel)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    # property via @property is FunctionDef
                    pass
            # @property methods
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("_"):
                    continue
                if isinstance(item, ast.FunctionDef):
                    decs = [ast.unparse(d) for d in item.decorator_list]
                    if any("property" in d for d in decs):
                        if item.name not in methods:
                            methods.append(item.name)
                            key = qual(mod, f"{node.name}.{item.name}")
                            sig = " (property)"
                            desc = describe(key, f"Свойство класса `{node.name}`.")
                            write_method(node.name, item.name, mod, sig, desc, source_rel)

            key = qual(mod, node.name)
            desc = describe(key, f"Класс `{node.name}` в модуле `{mod}`.")
            write_class(node.name, mod, methods, desc, source_rel)
            module_items.append(f"[Класс `{node.name}`](../classes/{node.name}.md)")
            classes_info.append((node.name, methods))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            key = qual(mod, node.name)
            sig = get_sig(node)
            desc = describe(key, f"Функция модуля `{mod}`.")
            write_function(node.name, mod, sig, desc, source_rel)
            module_items.append(f"[`{node.name}`](../functions/{node.name}.md)")

    write_module_overview(mod, module_items, source_rel)
    return module_items, [c[0] for c in classes_info]


def write_index(all_modules: list[str]) -> None:
    mod_lines = "\n".join(f"- [`{m}`](modules/{m}.md)" for m in sorted(all_modules))
    content = f"""# API — справочник AI Anki

Подробная документация по каждому **классу**, **методу** и **функции** Python-кода.

## Структура

| Каталог | Содержимое |
|---------|------------|
| [`classes/`](classes/) | Обзор класса + ссылки на методы |
| [`methods/`](methods/) | Отдельный файл на каждый метод/свойство |
| [`functions/`](functions/) | Модульные функции |
| [`modules/`](modules/) | Оглавление по файлам |

## Модули

{mod_lines}

## Перегенерация

```bash
python3 scripts/generate_api_docs.py
```

Скрипт обновляет каркас файлов; описания задаются в `DESCRIPTIONS` внутри скрипта.
"""
    (DOCS / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    modules: list[str] = []
    for path in MODULES:
        if not path.exists():
            continue
        process_file(path)
        modules.append(module_key(path))
    write_index(modules)
    print(f"Generated docs in {DOCS}")


if __name__ == "__main__":
    main()
