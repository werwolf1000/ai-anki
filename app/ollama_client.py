from __future__ import annotations

import json
import re

import requests

from app.deck import Card, ChatMessage, ReviewResult

SYSTEM_PROMPT = """Ты — терпеливый преподаватель в режиме карточек (как Anki).
Проверяешь ответ ученика на вопрос по программированию/Angular.

Правила:
1. Ученик может отвечать своими словами — не требуй дословного совпадения с эталоном.
2. Оцени понимание по шкале 0–100.
3. correct=true если score >= 75 (хорошее понимание), иначе false.
4. Если ответ неполный или неверный — дай короткую подсказку (hint), НЕ раскрывая весь эталон сразу.
5. Если есть пробелы — задай один уточняющий вопрос (follow_up), чтобы направить мысль.
6. Если ответ отличный — follow_up может быть пустым или углубляющим (по желанию).
7. feedback — 2–4 предложения на русском, дружелюбно и по делу.
8. Отвечай ТОЛЬКО валидным JSON без markdown:

{
  "correct": true,
  "score": 85,
  "feedback": "...",
  "hint": "...",
  "follow_up": "...",
  "reference_summary": "краткий эталон 1-2 предложения"
}

Если hint не нужен — пустая строка. Если follow_up не нужен — пустая строка."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def health(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def chat(self, messages: list[ChatMessage]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": 0.3},
        }
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")


class AnswerEvaluator:
    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    def evaluate(
        self,
        card: Card,
        user_answer: str,
        history: list[ChatMessage] | None = None,
        *,
        is_follow_up: bool = False,
    ) -> ReviewResult:
        history = history or []
        if is_follow_up:
            user_prompt = (
                f"Исходный вопрос карточки: {card.question}\n"
                f"Эталонный ответ: {card.reference}\n\n"
                f"Это ответ ученика на уточняющий вопрос. Оцени, учитывая весь диалог.\n"
                f"Ответ ученика:\n{user_answer}"
            )
        else:
            user_prompt = (
                f"Вопрос карточки: {card.question}\n"
                f"Эталонный ответ: {card.reference}\n\n"
                f"Ответ ученика:\n{user_answer}"
            )

        messages = [ChatMessage("system", SYSTEM_PROMPT)]
        messages.extend(history)
        messages.append(ChatMessage("user", user_prompt))

        raw = self.client.chat(messages)
        return self._parse_review(raw)

    @staticmethod
    def _parse_review(raw: str) -> ReviewResult:
        cleaned = raw.strip()
        think_tag = "think"
        cleaned = re.sub(
            rf"<{think_tag}>.*?</{think_tag}>",
            "",
            cleaned,
            flags=re.S | re.I,
        )
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.S | re.I)
        cleaned = cleaned.strip()

        json_text = cleaned
        fence = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.S | re.I)
        if fence:
            json_text = fence.group(1)
        else:
            brace = re.search(r"\{.*\}", cleaned, flags=re.S)
            if brace:
                json_text = brace.group(0)

        try:
            data = json.loads(json_text)
            score = int(data.get("score", 0))
            return ReviewResult(
                correct=bool(data.get("correct", score >= 75)),
                score=score,
                feedback=str(data.get("feedback", "")),
                hint=str(data.get("hint", "") or ""),
                follow_up=str(data.get("follow_up", "") or ""),
                reference_summary=str(data.get("reference_summary", "") or ""),
                raw=raw,
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return ReviewResult(
                correct=False,
                score=0,
                feedback=raw or "Не удалось разобрать ответ модели.",
                raw=raw,
            )
