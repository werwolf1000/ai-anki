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

4. Создайте каталог для данных (прогресс, настройки):

```bash
mkdir -p /mnt/storage/web/ai-anki/data
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
   - Build context: **`/mnt/storage/web/ai-anki`**
5. **Save** → **Deploy**.

### Альтернатива: SSH на TrueNAS

```bash
cd /mnt/storage/web/ai-anki
docker compose -f docker-compose.truenas.yml up -d --build
```

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
| `/data/progress.json` | `./data/progress.json` | Прогресс SRS |
| `/data/config.json` | `./data/config.json` | Настройки |
| `/data/decks.json` | `./data/decks.json` | Реестр колод |

Колоды (JSON) — в `./decks/` (read-only в образе). Для добавления своих колод положите JSON в `decks/` и пересоберите образ, либо смонтируйте volume:

```yaml
volumes:
  - ./data:/data
  - ./decks:/app/decks:ro
```

## 6. Обновление

```bash
cd /mnt/storage/web/ai-anki
git pull
docker compose -f docker-compose.truenas.yml up -d --build
```

## 7. Устранение неполадок

| Проблема | Решение |
|----------|---------|
| 502 / Ollama error | Проверьте URL из контейнера: `docker exec ai-anki curl -s http://.../api/tags` |
| Пустой список колод | Проверьте наличие `decks/*.json` в образе |
| Нет прав на data | `chown -R 1000:1000 data` или `chmod 775 data` |

## Desktop vs Web

| | Desktop (`run.sh`) | Web (Docker) |
|--|-------------------|--------------|
| UI | PyQt6 | Браузер |
| Данные | `~/.ai-anki/` | `./data/` на NAS |
| Код-карточки | Редактор с номерами строк | Textarea monospace |

Прогресс **не синхронизируется** автоматически между desktop и web — разные каталоги данных.
