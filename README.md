# AI Anki

Интерактивные карточки с проверкой ответов через Ollama: свободная формулировка, подсказки, уточняющие вопросы, live-coding и формулы LaTeX.

## Требования

- Python 3.10+
- Доступ к Ollama API (локально или удалённый сервер)
- **Desktop:** PyQt6, PyQt6-WebEngine (MathLive/KaTeX), PyQt6-QScintilla (редактор кода)
- **Web:** см. `requirements-server.txt` или Docker

## Запуск

### Linux / macOS

```bash
git clone git@github.com:werwolf1000/ai-anki.git
cd ai-anki
./run.sh
```

### Windows

1. Установите [Python 3.10+](https://www.python.org/downloads/) и отметьте **«Add python.exe to PATH»** при установке.
2. Клонируйте репозиторий и запустите:

```bat
git clone git@github.com:werwolf1000/ai-anki.git
cd ai-anki
run.bat
```

Или двойной щелчок по `run.bat` в проводнике (если репозиторий уже скачан).

При первом запуске создаётся `.venv` и ставятся зависимости из `requirements.txt`. Настройки и прогресс на Windows хранятся в `%USERPROFILE%\.ai-anki\` (аналог `~/.ai-anki/` на Linux).

---

### Веб-версия (Docker / TrueNAS)

Серверная версия для браузера — тот же движок карточек и Ollama, без PyQt6.

```bash
cd ai-anki
docker compose up -d --build
# http://localhost:8080
```

Развёртывание на **TrueNAS Scale** (`/mnt/storage/web/ai-anki`, SMB `smb://truenas.local/web/ai-anki`): см. **[TRUENAS.md](TRUENAS.md)** — используйте `docker-compose.truenas.yml`.

Данные веб-версии: каталог `./data/`. В контейнере: `AI_ANKI_DATA_DIR=/data`.

Локально без Docker:

```bash
pip install -r requirements-server.txt
export AI_ANKI_DATA_DIR=./data
uvicorn server.main:app --host 0.0.0.0 --port 8080
```

---

## Как пользоваться

### 1. Главный экран

После запуска откроется список колод и блок **«Настройки»**.

**Настройки** (сохраняются в `~/.ai-anki/config.json` на Linux/macOS или `%USERPROFILE%\.ai-anki\config.json` на Windows):

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| Карточек за сессию | 20 | Сколько карточек максимум за один заход (до 50) |
| Порог зачёта | 75 | Минимальная оценка 0–100 для «засчитано» |
| Макс. уточнений | 2 | Уточняющие вопросы модели и правки кода на одной карточке |
| Автопереход | 10 с | Пауза перед следующей карточкой **после зачёта** (0 — выключено) |
| Тема редактора | light | Светлая / тёмная (код и Monaco в web) |
| Ollama URL / Модель / Таймаут | см. `config.json` | Подключение к API |
| ASR (web) | см. `config.json` | Whisper для голосового ввода |

Нажмите **«Сохранить»**, затем **«Проверить Ollama»** — должны появиться доступные модели.

**Таблица колод** показывает: всего карточек, усвоено (интервал ≥ 7 дней и хороший балл), **сегодня** (засчитано за текущий день), к повтору, новые, слабые, средний балл.

Выберите строку в таблице и режим занятия:

| Режим | Когда использовать |
|-------|----------------------|
| **Повторить (к сроку)** | Обычный режим: новые + просроченные по SRS |
| **Только новые** | Карточки, которые ещё ни разу не проходили |
| **Слабые места** | Лучший балл ниже порога зачёта |
| **Вся колода** | Все карточки подряд (без фильтра по сроку) |

**Двойной щелчок** по колоде — быстрый старт в режиме «Повторить» (desktop и web).

**Выбор темы:** если в колоде две и более тем (`topic` на карточках), перед сессией откроется список тем — в занятие попадут только карточки выбранной темы. Работает для live-coding, математики, Python/PHP/PyTorch, Agile и др.

**Добавить колоду…** — свой JSON или Anki TXT. **Обновить** — перечитать прогресс и колоды с диска.

---

### 2. Сессия занятий

В шапке: **Сегодня** · **Усвоено** · **к повтору** · **сессия N/M**.

1. Прочитайте **вопрос** (для карточек с кодом — исходный фрагмент и задание; для math — KaTeX-рендер).
2. Введите ответ:
   - **Теория** — поле «Ваш ответ» (в web — 🎤 голосом через ASR).
   - **Код** — редактор с номерами строк (QScintilla / Monaco).
   - **Math** — MathLive + предпросмотр KaTeX (LaTeX).
3. **Ctrl+Enter** или **«Проверить ответ»** — Ollama оценит ответ (0–100) и даст обратную связь.
4. При необходимости:
   - **Подсказка** — дополнительная подсказка от модели.
   - **Уточняющий вопрос** — ответьте в том же поле и снова нажмите «Проверить».
   - **Правки кода / формул** — если балл ниже порога, ответ **не стирается**; исправьте и отправьте снова.
5. При **зачёте** через **автопереход** откроется следующая карточка, либо **«Следующая →»** сразу.
6. **«← Колоды»** — на главный экран; прогресс сохраняется автоматически.
7. **«История карточки»** (desktop) — все прошлые ответы по текущей карточке.

---

### 3. Типы карточек

**Теория** — ответ своими словами:

```json
{
  "question": "Что такое standalone-компонент?",
  "reference": "Компонент с imports в @Component, без NgModule…",
  "topic": "Компоненты"
}
```

**Код (исправить / дополнить):**

```json
{
  "card_type": "code",
  "question": "ngModel не работает",
  "task": "Добавь недостающий import",
  "code": "@Component({...})",
  "reference": "imports: [FormsModule], …"
}
```

**Live-coding** — код с нуля:

```json
{
  "card_type": "live_code",
  "question": "Standalone-компонент приветствия",
  "reference": "… эталонный код …",
  "language": "typescript",
  "topic": "Компоненты"
}
```

**Математика (LaTeX):**

```json
{
  "card_type": "math",
  "answer_mode": "math",
  "question": "Производная $\\sin x$",
  "reference": "\\cos x",
  "topic": "Производные"
}
```

Поле **`topic`** опционально; при двух и более различных темах в колоде включается выбор темы перед сессией.

**Анатомия** — текстовый ответ с иллюстрацией на каждой карточке. Поле `image` — локальный путь или **HTTPS-ссылка** (Wikimedia Commons, OpenStax и т.п.):

```json
{
  "card_type": "anatomy",
  "question": "Назовите камеры сердца",
  "reference": "Правое и левое предсердия; правый и левый желудочки.",
  "topic": "Сердечно-сосудистая",
  "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/2000_Human_Heart_Photo.jpg/960px-2000_Human_Heart_Photo.jpg",
  "image_alt": "Сердце и камеры"
}
```

Перегенерация колоды с фото OpenStax (по умолчанию): `python3 decks/generate_anatomy.py`.  
Офлайн SVG: `python3 decks/generate_anatomy.py --local-svg`.

---

### 4. Прогресс и повторения

Данные в `~/.ai-anki/` (или `AI_ANKI_DATA_DIR`):

| Файл | Содержимое |
|------|------------|
| `progress.json` | Баллы, интервалы SRS, история ответов |
| `decks.json` | Зарегистрированные колоды |
| `config.json` | Настройки приложения |
| `decks/` | Пользовательские колоды (web volume) |

**Интервальное повторение:** при зачёте интервал растёт; при ошибке — возврат через несколько минут. **Усвоено** — интервал ≥ 7 дней и лучший балл ≥ порога.

---

## Настройка Ollama

1. **URL** — например `http://ollama.webmastermsk.ru:30068`.
2. **API-ключ** — для прямого Ollama не нужен; для Open WebUI — ключ из *Settings → Account*.
3. **Модель** — например `qwen3-coder:30b`.
4. **Проверить Ollama** на главном экране.

Настройки по умолчанию — в `config.json` проекта; при первом сохранении копируются в user config.

---

## Встроенные колоды

| Колода | Файл |
|--------|------|
| PHP 8+ | `decks/php8-plus.json` |
| **Laravel** | `decks/laravel-basics.json` |
| **Laravel Live-coding** | `decks/laravel-live-coding.json` |
| **Анатомия** (фото/схемы) | `decks/anatomy.json` (+ опционально `decks/anatomy-assets/`) |
| Python — основы | `decks/python-basics.json` |
| tkinter.ttk | `decks/ttk-widgets.json` |
| PyTorch | `decks/pytorch-basics.json` |
| **Высшая математика** | `decks/higher-math.json` |
| Angular (пример) | `decks/angular-sample.json` |
| **Angular Live-coding** | `decks/angular-live-coding.json` |
| **Python Live-coding** | `decks/python-live-coding.json` |
| **PHP Live-coding** | `decks/php-live-coding.json` |
| **Angular (полная)** | `decks/anki-angular.txt` + `decks/angular-code.json` |
| Agile — основы | `decks/agile-fundamentals.json` |
| Scrum | `decks/scrum-framework.json` |
| Kanban | `decks/kanban-method.json` |
| SAFe | `decks/safe-scaled-agile.json` |

Составная колода **Angular (полная)** объединяет `decks/anki-angular.txt` и `decks/angular-code.json`.

Перегенерация: скрипты `decks/generate_*.py` (из каталога `decks/`). Laravel: `generate_laravel_deck.py`, `generate_laravel_live_coding.py`. Темы — `laravel_topics.py`, `live_coding_topics.py` (`assign_laravel_topic`).

---

## Структура проекта

```
ai-anki/
├── main.py                 # точка входа desktop
├── run.sh / run.bat
├── docker-compose.yml
├── docker-compose.truenas.yml
├── Dockerfile
├── TRUENAS.md
├── requirements.txt        # desktop
├── requirements-server.txt # web
├── docs/                   # API-справочник (классы, методы, функции)
├── scripts/
│   └── generate_api_docs.py
├── server/                 # FastAPI + статический UI
│   ├── main.py             # REST API
│   ├── services.py         # веб-сессии
│   └── static/             # index.html, app.js, Monaco, MathLive
└── app/                    # общее ядро (desktop + web)
    ├── gui.py              # PyQt6: сессия, MainWindow
    ├── welcome.py          # главный экран
    ├── deck.py             # Card, Deck
    ├── progress.py         # SRS, очереди, история
    ├── registry.py         # реестр колод
    ├── live_coding.py      # темы, live-coding / math
    ├── ollama_client.py    # Ollama + промпты
    ├── config_store.py     # config.json
    ├── code_editor.py      # QScintilla
    ├── math_editor.py      # MathLive (WebEngine)
    ├── topic_picker.py     # выбор темы
    ├── asr_client.py       # Whisper (web)
    └── assets/             # math_editor.html, math_question.html
```

---

## Документация API

Подробный справочник по **каждому классу, методу и функции** — в каталоге **[docs/](docs/README.md)**:

| Раздел | Описание |
|--------|----------|
| [docs/README.md](docs/README.md) | Оглавление API |
| [docs/classes/](docs/classes/) | Классы (`Card`, `ProgressStore`, `AppServices`, …) |
| [docs/methods/](docs/methods/) | Отдельный файл на каждый метод |
| [docs/functions/](docs/functions/) | Модульные функции |
| [docs/modules/](docs/modules/) | Оглавление по Python-модулям |

Обновление после изменения кода:

```bash
python3 scripts/generate_api_docs.py
```

Описания задаются в словаре `DESCRIPTIONS` в `scripts/generate_api_docs.py`.

---

## Web API (кратко)

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/decks` | Список колод и статистика |
| GET | `/api/deck/{id}/topics` | Темы колоды |
| POST | `/api/session` | Старт сессии `{deck_id, mode, topic?}` |
| POST | `/api/session/{id}/answer` | Проверка ответа |
| POST | `/api/session/{id}/next` | Следующая карточка |
| POST | `/api/session/{id}/hint` | Подсказка |
| POST | `/api/asr/transcribe` | Голос → текст |

Подробнее: [docs/modules/server.main.md](docs/modules/server.main.md), [docs/classes/AppServices.md](docs/classes/AppServices.md).
