# `transcribe_whisper`

**Модуль:** [`app.asr_client`](../modules/app.asr_client.md)  
**Исходник:** `app/asr_client.py`

## Сигнатура

```python
def transcribe_whisper(base_url: str, audio_bytes: bytes, filename: str) -> str
```

## Описание

POST аудио → текст (web голосовой ввод).
