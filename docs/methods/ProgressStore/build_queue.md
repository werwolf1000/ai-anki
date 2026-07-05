# `ProgressStore.build_queue`

**Модуль:** [`app.progress`](../../modules/app.progress.md)  
**Исходник:** `app/progress.py`

## Сигнатура

```python
def build_queue(deck: Deck, mode: StudyMode) -> list
```

## Описание

Формирует очередь карточек для сессии. mode — StudyMode; topic — фильтр по теме; limit — session_limit; pass_score — для WEAK. Новые и просроченные сортируются по приоритету SRS.

## См. также

- [Класс `ProgressStore`](../../classes/ProgressStore.md)
