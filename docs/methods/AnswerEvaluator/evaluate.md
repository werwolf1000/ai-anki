# `AnswerEvaluator.evaluate`

**Модуль:** [`app.ollama_client`](../../modules/app.ollama_client.md)  
**Исходник:** `app/ollama_client.py`

## Сигнатура

```python
def evaluate(card: Card, user_answer: str, history: list[ChatMessage] | None) -> ReviewResult
```

## Описание

Оценка ответа 0–100, hint, follow_up.

## См. также

- [Класс `AnswerEvaluator`](../../classes/AnswerEvaluator.md)
