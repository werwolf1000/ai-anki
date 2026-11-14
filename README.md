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

Сервер: FastAPI (тот же движок карточек и Ollama) + интерфейс на **React + Motion + AutoAnimate + Tailwind CSS** (`web/`).
Рабочий адрес: **https://anki.webmastermsk.ru**.

```bash
cd ai-anki
docker compose up -d --build
# http://localhost:8080
```

Образ собирается в два этапа: Node собирает `web/` → `web/dist`, затем Python-образ отдаёт API и статику.
Развёртывание на **TrueNAS Scale** — см. **[TRUENAS.md](TRUENAS.md)** (`docker-compose.truenas.yml`).

#### Аккаунты

- Вход и регистрация — на стартовом экране. У каждого пользователя **свой прогресс SRS, статистика и настройки обучения**.
- **Первый зарегистрированный аккаунт становится администратором** и получает прогресс однопользовательской версии (`data/progress.json`).
- Настройки Ollama и Whisper (ASR) общие для сервера, менять их может только администратор.
- `AI_ANKI_REGISTRATION=closed` закрывает регистрацию после создания первого аккаунта.
- Авторизация — токен в заголовке `Authorization: Bearer …` (пароли — scrypt, база `data/users.db`).

Данные веб-версии: каталог `./data/` (в контейнере `AI_ANKI_DATA_DIR=/data`):

| Файл | Содержимое |
|------|------------|
| `users.db` | пользователи и токены |
| `users/<id>/progress.json` | прогресс пользователя |
| `users/<id>/settings.json` | личные настройки обучения |
| `config.json` | общие настройки сервера (Ollama, ASR) |

Разработка без Docker:

```bash
pip install -r requirements-server.txt
export AI_ANKI_DATA_DIR=./data
uvicorn server.main:app --host 127.0.0.1 --port 8080
# во втором терминале — фронтенд с hot reload (проксирует /api на :8080)
cd web && npm install && npm run dev      # http://localhost:5173
# или собрать: npm run build → web/dist (сервер раздаёт его сам)
```

#### Профессии: треки, AI-собеседования, экзамены, сертификаты

Раздел **«Профессии»** — 9 треков: PHP-разработчик, Node.js-разработчик, Go-разработчик, DevOps-инженер,
Forward Deployed Engineer, AI-тренер, специалист по промпт-инжинирингу, LLM-оценщик / AI QA, нейрокреатор / AI-художник.

- Каждый трек — две колоды: **теория** (8 прикладных предметов × 20 карточек) и **практикум** (10 заданий live-coding:
  PHP, JS/TS, Go, Bash, Dockerfile, YAML, Terraform, SQL, Python; для AI-ролей — промпты, рубрики, JSON Schema, планы).
- **AI-собеседование** — чат с интервьюером: 5 вопросов по разным предметам + практическое задание, уточняющие вопросы,
  в конце отчёт: балл, уровень (Junior/Middle/Senior), сильные стороны, пробелы, рекомендации. Проходной балл — 65.
- **Экзамен** — 9 теоретических + 3 практических задания, 60 минут, без подсказок; ответы проверяются моделью в фоне,
  в конце — разбор по каждому вопросу и по темам. Проходной балл — 70.
- **Сертификат** выдаётся, когда сдано ≥ 60% карточек трека, пройдены собеседование и экзамен (учитываются лучшие попытки).
  У сертификата уникальный номер и публичная страница проверки `/verify/<номер>`; печать в PDF из браузера.
- Контент: `decks/pro_tracks/*.py` → `python decks/generate_pro_tracks.py` → `decks/pro-*.json` и `decks/tracks.json`
  (там же настраиваются число вопросов, время и пороги). Результаты: `data/tracks.db`.

#### Интерактивный учебник (RAG)

Раздел **«Учебник»**: перед прохождением темы можно прочитать статью по ней.

- **Программы** — у каждого учебника своя программа «главы → уроки», не зависящая от тем карточек
  (`decks/syllabus/*.txt`, 20 программ, ~860 уроков: PHP — 11 глав / 88 уроков, Laravel — 62, Python — 61,
  Node.js/JS/TS — 60, Go — 55, Angular — 47, анатомия — 47, высшая математика — 49 и т. д.).
  Программа общая для всех своих колод (например, «PHP 8+», «PHP-разработчик» и PHP live-coding), статья пишется один раз.
  Формат файла:

  ```
  title: PHP
  match: php8|pro-php|php-live      # регулярное выражение по id, имени файла и названию колоды
  # 2. Продвинутое ООП               # глава
  SOLID-принципы: SRP, OCP, LSP, ISP, DIP
  Traits — горизонтальное переиспользование кода
  ```

  К каждому уроку подбираются близкие карточки колоды (по словам названия) — они служат ориентиром для статьи,
  а «Проверить себя» запускает их тему. Колоды без программы показывают темы карточек, как раньше.

- **Источники** — официальная документация (описаны в `server/kb_sources.py`, колоды подбираются по названию и языку):

  | Источник | Язык | Для колод | Объём |
  |---|---|---|---|
  | [PHP Manual](https://www.php.net/manual/ru/) | рус. | PHP, Laravel, PHP-разработчик | ~2600 страниц / ~6900 фрагментов |
  | [MDN JavaScript](https://developer.mozilla.org/ru/docs/Web/JavaScript) | рус. | JS, Node.js, TypeScript, Angular | ~600 / ~2500 |
  | [Python 3.13](https://docs.python.org/3.13/) | англ. | Python, PyTorch, tkinter, AI-тренер, FDE, LLM-оценщик | ~120 / ~3300 |
  | [Node.js v22 API](https://nodejs.org/docs/latest-v22.x/api/) | англ. | Node.js | ~60 / ~3100 |
  | [TypeScript Handbook](https://www.typescriptlang.org/docs/) | англ. | TypeScript, Angular, Node.js | ~80 / ~900 |
  | [Angular](https://angular.dev) | англ. | Angular | ~200 / ~2000 |
  | [Laravel 12.x](https://laravel.com/docs/12.x) | англ. | Laravel, PHP-разработчик | ~100 / ~2900 |
  | [Go](https://go.dev/doc/) (спецификация, Effective Go, руководства) | англ. | Go, Go-разработчик | ~80 / ~1300 |
  | [Scrum Guide 2020](https://scrumguides.org/), [Agile-манифест](https://agilemanifesto.org/iso/ru/manifesto.html), Kanban Guide | рус./англ. | Agile, Scrum, Kanban, SAFe | 4 / ~50 |
  | [Kubernetes](https://kubernetes.io/ru/docs/) | рус. | DevOps | ~100 / ~480 |
  | [Docker](https://docs.docker.com/) (сборка, Compose, сети, тома) | англ. | DevOps, FDE | ~140 / ~1100 |
  | [Prompt Engineering Guide](https://www.promptingguide.ai/ru) | рус./англ. | промпт-инжиниринг, LLM-оценщик, AI-тренер, FDE, AI-художник | ~65 / ~290 |
  | [Hugging Face TRL](https://huggingface.co/docs/trl) | англ. | AI-тренер, PyTorch | ~50 / ~700 |
  | [Hugging Face Diffusers](https://huggingface.co/docs/diffusers) | англ. | нейрокреатор / AI-художник | ~70 / ~660 |
  | [Википедия](https://ru.wikipedia.org/) | рус. | все колоды (анатомия, высшая математика и др.) | ~90 / ~1000 |

  Статьи Википедии подбираются поиском по каждой теме каждой колоды; случайные совпадения (например, револьвер
  «Colt Python» для колоды по Python) отсеиваются по словарю карточек колоды.

  Английские источники используются как есть, статьи всё равно пишутся по-русски. Документация из GitHub-репозиториев
  скачивается через GitHub API (1–2 запроса на источник, лимит без токена — 60 в час; при необходимости задайте `GITHUB_TOKEN`).
- **Поиск** — гибридный: FTS5/BM25 (точные термины вроде `array_map`) + векторы Ollama `qwen3-embedding:8b` (1024 измерения),
  объединение через Reciprocal Rank Fusion. Пока векторы не готовы, работает только BM25.
- **Статья** генерируется Ollama по найденным фрагментам и карточкам темы, со сносками `[n]` на страницы документации,
  печатается потоково и кешируется (общая для всех пользователей; админ может перегенерировать).
- **Интерактив:** оглавление с подсветкой раздела, сноски-ссылки, отметка «прочитано» (автоматически, если дочитали до конца),
  «Спросить учебник» — вопрос по теме с ответом из той же базы, кнопка «Проверить себя» запускает карточки темы.
- Если база знаний для колоды ещё не загружена, статья строится по материалам карточек колоды.

**Первичная индексация:** Настройки → «База знаний учебника» → **Скачать и проиндексировать всё** (только администратор)
или кнопка загрузки у отдельного источника. Скачивание и разбор всех источников — несколько минут, затем в фоне идёт
векторизация (~24 тыс. фрагментов — несколько часов, зависит от Ollama); полнотекстовый поиск работает сразу.
Если индексацию прервал перезапуск — кнопка **Довекторизовать** продолжит с места остановки.

**Статьи для всех тем сразу:** Настройки → «Статьи учебника» → **Написать недостающие** (или кнопка в разделе
«Учебник» для одной колоды). Модель пишет статьи в фоне по очереди, готовые пропускаются; после трёх ошибок подряд
(например, Ollama недоступен) генерация останавливается. Около 860 уроков, на один урок — от 30 секунд до нескольких минут.
База: `data/knowledge.db` (SQLite). Модели меняются там же: `embed_model`, `textbook_model` (пусто — основная модель).

### Десктоп-приложение (Electron)

`desktop/` — frameless-окно Electron с тем же React-интерфейсом (свой заголовок окна, анимации).
Приложение **не хранит данные локально**: вход в тот же аккаунт, прогресс и настройки синхронизируются через API сервера
(по умолчанию `https://anki.webmastermsk.ru`, адрес меняется на экране входа).

```bash
cd web && npm install
cd ../desktop && npm install
npm start          # собрать web и запустить приложение
npm run dist       # установщик Windows: desktop/dist/AI-Anki-Setup-<version>.exe
```

Если после `npm install` нет `node_modules/electron/dist/electron.exe`: `node node_modules/electron/install.js`.
Старое PyQt6-приложение (`run.sh` / `run.bat`) по-прежнему работает автономно, но не синхронизируется с сервером.

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
| **Go — основы** | `decks/go-basics.json` |
| **Go Live-coding** | `decks/go-live-coding.json` |
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

Перегенерация: скрипты `decks/generate_*.py` (из каталога `decks/`). Laravel: `generate_laravel_deck.py`, `generate_laravel_live_coding.py`. Go: `generate_go_deck.py`, `generate_go_live_coding.py`. Темы — `go_topics.py`, `live_coding_topics.py` (`assign_go_topic`, `assign_laravel_topic`).

**После перегенерации обязательно запустите очистку:** `python decks/clean_decks.py` (из корня проекта).
Скрипт удаляет карточки-заглушки (эталон вида «Повторите ключевые идеи темы…», «см. docs»), дубликаты `#0-0/#0-1`,
раскрывает слишком короткие вопросы («withCount?» → «Что такое withCount?») и чистит формулировки live-coding.
id изменённых карточек сохраняются, id удалённых пишутся в `retired_ids` — прогресс не теряется и не переносится на чужие карточки.

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
├── server/                 # FastAPI
│   ├── main.py             # REST API, авторизация, раздача web/dist
│   ├── auth.py             # пользователи и токены (SQLite)
│   ├── knowledge.py        # RAG: разбор HTML, чанки, FTS5 + векторы, промпты
│   ├── kb_sources.py       # источники базы знаний и их загрузка (php.net, docs.python.org, GitHub)
│   ├── textbook.py         # API учебника (статьи, вопросы, «прочитано»)
│   ├── syllabus.py         # программы учебника (decks/syllabus/*.txt) и подбор карточек к урокам
│   ├── tracks.py           # профессии: экзамены, AI-собеседования, сертификаты
│   └── services.py         # данные пользователей, сессии, статистика
├── web/                    # React + Motion + AutoAnimate + Tailwind (Vite)
│   └── src/                # views/ (экраны), components/, lib/
├── desktop/                # Electron: frameless-окно, протокол app://
├── decks/clean_decks.py    # очистка сгенерированных колод
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

Все `/api/*`, кроме `/api/auth/*` и картинок, требуют `Authorization: Bearer <token>`.

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/auth/status` | Есть ли пользователи, открыта ли регистрация |
| POST | `/api/auth/register` | Регистрация `{username, password, display_name?}` → `{token, user}` |
| POST | `/api/auth/login` | Вход → `{token, user}` |
| POST | `/api/auth/logout` | Отозвать токен |
| GET | `/api/auth/me` | Текущий пользователь |
| POST | `/api/account/password`, `/api/account/profile` | Смена пароля, имени |
| GET / POST | `/api/config` | Настройки (личные; серверные — только админ) |
| GET | `/api/decks` | Колоды и статистика пользователя |
| GET | `/api/dashboard` | Активность за 28 дней, серия дней |
| GET | `/api/deck/{id}/topics` | Темы колоды |
| GET | `/api/textbook/{deck_id}` | Темы учебника, отметки «прочитано», источники |
| POST | `/api/textbook/{deck_id}/article/stream` | Статья темы (NDJSON-поток: sources → delta… → done) |
| POST | `/api/textbook/{deck_id}/ask` | Вопрос к учебнику (NDJSON-поток) |
| POST | `/api/textbook/{deck_id}/read` | Отметить тему прочитанной |
| GET / POST | `/api/knowledge/status`, `/api/knowledge/rebuild` | Состояние базы знаний / переиндексация (админ) |
| GET | `/api/tracks`, `/api/tracks/{id}` | Профессии, прогресс и требования к сертификату |
| POST | `/api/tracks/{id}/exam` → `/api/exams/{id}/answer`, `/finish` | Экзамен |
| POST | `/api/tracks/{id}/interview` → `/api/interviews/{id}/answer` | AI-собеседование |
| POST | `/api/tracks/{id}/certificate` | Выдать сертификат (если условия выполнены) |
| GET | `/api/certificates/{номер}` | Публичная проверка сертификата (без входа) |
| POST | `/api/session` | Старт сессии `{deck_id, mode, topic?}` |
| POST | `/api/session/{id}/answer` | Проверка ответа (`review`: оценка, отзыв, уточнение) |
| POST | `/api/session/{id}/next` | Следующая карточка |
| POST | `/api/session/{id}/hint` | Подсказка |
| POST | `/api/asr/transcribe` | Голос → текст |
