# `stable_card_id`

**Модуль:** [`app.deck`](../modules/app.deck.md)  
**Исходник:** `app/deck.py`

## Сигнатура

```python
def stable_card_id(question: str, code: str, task: str) -> str
```

## Описание

Вычисляет стабильный числовой id карточки по содержимому. Одинаковый на desktop, web и после перезапуска.
