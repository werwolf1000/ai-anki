# AI Anki на TrueNAS Scale

Развёртывание веб-версии в dataset **`web/ai-anki`** (SMB: `smb://truenas.local/web/ai-anki`).

## 1. Подготовка dataset

1. **Datasets** → создайте dataset `web/ai-anki` (или используйте существующий `web`).
2. Включите **SMB** для share `web`, если ещё не включён.
3. Скопируйте проект на NAS:

```bash
# с рабочей машины
git clone git@github.com:werwolf1000/ai-anki.git
# скопируйте в SMB-share, например:
cp -r ai-anki /mnt/web/ai-anki
```

На TrueNAS путь для pool **storage**: **`/mnt/storage/web/ai-anki`**

4. Создайте каталоги для данных (прогресс, настройки, свои колоды):

```bash
mkdir -p /mnt/storage/web/ai-anki/data/decks
chmod -R 775 /mnt/storage/web/ai-anki/data
```

## 2. Запуск через веб-интерфейс TrueNAS (Custom App)

### TrueNAS Scale 24.x+

1. **Apps** → **Discover Apps** → **Custom App** (или **Install via Compose**).
2. Загрузите **`docker-compose.truenas.yml`** из dataset (не generic `docker-compose.yml`).
3. **Host Path** проекта: `/mnt/storage/web/ai-anki`
4. Проверьте mapping:
   - Port **8080** → Host port (например `8080`)
   - Volume **`/mnt/storage/web/ai-anki/data:/data`**
   - Volume **`/mnt/storage/web/ai-anki/decks:/app/decks:ro`**
   - Build context: **`/mnt/storage/web/ai-anki`**
5. **Save** → **Deploy**.

### Альтернатива: SSH на TrueNAS

```bash
cd /mnt/storage/web/ai-anki
docker compose -f docker-compose.truenas.yml up -d --build
```

## 2.1. Подключить проектную практику Python/PHP

Для существующей Custom App используйте полный
[`docker-compose.truenas.practice.yml`](docker-compose.truenas.practice.yml):
приложение, видеотека `/mnt/storage/media/curs` и отдельный worker для практикума.
Сначала выполните на NAS `bash practice/prepare-truenas.sh` из каталога проекта,
затем замените YAML **существующего** приложения в **Apps → anki → Edit**.
Не запускайте второй Compose-стек поверх приложения, которым управляет TrueNAS.
Секрет хранится в `.secrets/practice-worker.env`, в YAML его вставлять не требуется.
Подробности и проверка запуска — в [руководстве по практике](docs/project-practice.md#truenas-apps-готовый-yaml-с-видеотекой).

## 2.2. Первый вход (версия 2.0 с аккаунтами)

1. Откройте сайт и **сразу зарегистрируйтесь** — первый аккаунт становится администратором
   и получает весь прежний прогресс из `data/progress.json`.
2. Остальные пользователи регистрируются сами; у каждого свой прогресс и настройки.
3. Чтобы закрыть регистрацию для посторонних — `AI_ANKI_REGISTRATION: closed` в compose-файле и **Redeploy**.

4. **Учебник:** Настройки → «База знаний учебника» → **Скачать и проиндексировать**. Векторизация идёт в фоне ~40 минут
   (контейнеру нужен доступ в интернет к php.net и к Ollama с моделью `qwen3-embedding:8b`).

Сборка образа скачивает `node:22-alpine` и npm-пакеты фронтенда — первый билд дольше (несколько минут).

## 3. Открыть в браузере

```
http://truenas.local:8080
```

или IP NAS: `http://192.168.x.x:8080`

## 4. Настройка Ollama

Ollama обычно **не** в контейнере AI Anki. На главном экране укажите:

| Поле | Пример |
|------|--------|
| Ollama URL | `http://192.168.x.x:30068` или URL вашего сервера |
| Модель | `qwen3-coder:30b` |

Если Ollama на том же TrueNAS в другом контейнере — используйте IP LAN или имя сервиса в docker-сети.

**Проверить Ollama** → должны появиться модели.

## 5. Данные и бэкапы

| Путь в контейнере | На NAS | Содержимое |
|-------------------|--------|------------|
| `/data/users.db` | `./data/users.db` | Пользователи и токены входа |
| `/data/users/<id>/progress.json` | `./data/users/<id>/` | Прогресс SRS пользователя |
| `/data/users/<id>/settings.json` | `./data/users/<id>/` | Личные настройки обучения |
| `/data/progress.json` | `./data/progress.json` | Прогресс версии 1.x (копируется первому аккаунту) |
| `/data/config.json` | `./data/config.json` | Общие настройки сервера (Ollama, ASR) |
| `/data/knowledge.db` | `./data/knowledge.db` | База знаний учебника и сгенерированные статьи |
| `/data/tracks.db` | `./data/tracks.db` | Попытки экзаменов/собеседований и реестр сертификатов |
| `/data/users/<id>/textbook.json` | `./data/users/<id>/` | Прочитанные темы пользователя |
| `/data/decks.json` | `./data/decks.json` | Реестр колод |
| `/data/decks/` | `./data/decks/` | Свои колоды (JSON/TXT) — **без пересборки** |
| `/app/decks/` | `./decks/` (volume) | Встроенные колоды из репозитория |

**Важно:** прогресс и настройки живут только в `./data/`. При деплое обязательно монтируйте оба volume:

```yaml
volumes:
  - /mnt/storage/web/ai-anki/data:/data
  - /mnt/storage/web/ai-anki/decks:/app/decks:ro
```

### Добавить или обновить карточки (web)

1. **Встроенные колоды** — отредактируйте JSON в `./decks/` на NAS, затем перезапустите контейнер (пересборка не нужна):
   ```bash
   docker compose -f docker-compose.truenas.yml up -d
   ```

2. **Свои колоды** — положите `*.json` или `*.txt` в `./data/decks/` (создайте каталог при первом использовании). Перезапуск не обязателен — достаточно обновить страницу в браузере.

## 6. Обновление

```bash
cd /mnt/storage/web/ai-anki
git pull
docker compose -f docker-compose.truenas.yml up -d --build
```

Прогресс сохранится, если volume `./data` смонтирован. Колоды подхватятся из `./decks` без пересборки образа.

## 7. Устранение неполадок

| Проблема | Решение |
|----------|---------|
| 502 / Ollama error | Проверьте URL из контейнера: `docker exec ai-anki curl -s http://.../api/tags` |
| Пустой список колод | Проверьте наличие `decks/*.json` в образе |
| «Фронтенд не собран» (503) | Пересоберите образ: в Dockerfile этап `web` собирает `web/dist` |
| Забыли пароль | `docker exec -it ai-anki python scripts/reset_password.py <логин> <новый_пароль>` |
| Нет прав на data | `chown -R 1000:1000 data` или `chmod 775 data` |

## Desktop vs Web

| | Desktop (`run.sh`) | Web (Docker) |
|--|-------------------|--------------|
| UI | PyQt6 / Electron (`desktop/`) | Браузер (React) |
| Данные | `~/.ai-anki/` | `./data/` на NAS |
| Код-карточки | Редактор с номерами строк | Textarea monospace |

Electron-приложение (`desktop/`) работает через API сервера: войдите тем же аккаунтом — прогресс общий с веб-версией.
Старое PyQt6-приложение хранит данные локально и **не синхронизируется** с сервером.
