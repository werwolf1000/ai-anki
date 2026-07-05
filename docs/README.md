# API — справочник AI Anki

Подробная документация по каждому **классу**, **методу** и **функции** Python-кода.

## Структура

| Каталог | Содержимое |
|---------|------------|
| [`classes/`](classes/) | Обзор класса + ссылки на методы |
| [`methods/`](methods/) | Отдельный файл на каждый метод/свойство |
| [`functions/`](functions/) | Модульные функции |
| [`modules/`](modules/) | Оглавление по файлам |

## Модули

- [`app.asr_client`](modules/app.asr_client.md)
- [`app.code_completions`](modules/app.code_completions.md)
- [`app.code_editor`](modules/app.code_editor.md)
- [`app.config_store`](modules/app.config_store.md)
- [`app.deck`](modules/app.deck.md)
- [`app.gui`](modules/app.gui.md)
- [`app.live_coding`](modules/app.live_coding.md)
- [`app.math_editor`](modules/app.math_editor.md)
- [`app.ollama_client`](modules/app.ollama_client.md)
- [`app.progress`](modules/app.progress.md)
- [`app.registry`](modules/app.registry.md)
- [`app.topic_picker`](modules/app.topic_picker.md)
- [`app.welcome`](modules/app.welcome.md)
- [`main`](modules/main.md)
- [`server.main`](modules/server.main.md)
- [`server.services`](modules/server.services.md)

## Перегенерация

```bash
python3 scripts/generate_api_docs.py
```

Скрипт обновляет каркас файлов; описания задаются в `DESCRIPTIONS` внутри скрипта.
