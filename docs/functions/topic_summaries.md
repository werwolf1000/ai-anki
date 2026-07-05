# `topic_summaries`

**Модуль:** [`app.live_coding`](../modules/app.live_coding.md)  
**Исходник:** `app/live_coding.py`

## Сигнатура

```python
def topic_summaries(deck: Deck, progress: ProgressStore) -> list[dict]
```

## Описание

Список dict для UI: name, total, due, new, weak — агрегация ProgressStore по card.topic.
