from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import requests

from app.deck import Card, ChatMessage, ReviewResult

SYSTEM_PROMPT_TEXT = """Ты — терпеливый преподаватель в режиме карточек (как Anki).
Проверяешь ответ ученика на вопрос по программированию/Angular.

Правила:
1. Ученик может отвечать своими словами — не требуй дословного совпадения с эталоном.
2. Оцени понимание по шкале 0–100.
3. correct=true если score >= 75 (хорошее понимание), иначе false.
4. Если ответ неполный или неверный — дай короткую подсказку (hint), НЕ раскрывая весь эталон сразу.
5. Если есть пробелы и остались уточнения — задай один уточняющий вопрос (follow_up).
6. Если лимит уточнений исчерпан — follow_up обязательно пустая строка, только hint и feedback.
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

SYSTEM_PROMPT_CODE = """Ты — преподаватель Angular/TypeScript. Карточка с кодом: ученик должен исправить или дополнить фрагмент.

Правила:
1. Сравни ответ ученика с эталоном по смыслу — не требуй посимвольного совпадения.
2. Проверь: исправлена ли ошибка / добавлено ли требуемое / корректен ли синтаксис и логика.
3. Оценка 0–100; correct=true если score >= 75.
4. При ошибках — короткая hint (укажи область проблемы, не давай готовое решение целиком).
5. Если остались уточнения — один follow_up; если лимит исчерпан — follow_up пустой.
6. feedback — что верно, что нет, 2–4 предложения на русском.
7. Только JSON:

{
  "correct": true,
  "score": 85,
  "feedback": "...",
  "hint": "...",
  "follow_up": "...",
  "reference_summary": "кратко что должно быть в решении"
}"""


def normalize_ollama_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not url:
        raise ValueError("URL Ollama не задан.")
    parsed = urlparse(url)
    if parsed.port is not None and parsed.port > 65535:
        raise ValueError(
            f"Некорректный порт {parsed.port} (максимум 65535). "
            "Проверьте URL — возможно, лишняя цифра в порте."
        )
    if not parsed.scheme:
        url = f"https://{url}"
    return url.rstrip("/")


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120, api_key: str = "") -> None:
        self.base_url = normalize_ollama_url(base_url)
        self.model = model
        self.timeout = timeout
        self.api_key = api_key.strip()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                timeout=kwargs.pop("timeout", self.timeout),
                **kwargs,
            )
        except requests.exceptions.InvalidURL as exc:
            raise ValueError(
                f"Некорректный URL: {self.base_url}. "
                "Для Open WebUI используйте https://хост/ollama"
            ) from exc
        return response

    def health(self) -> tuple[bool, str]:
        try:
            response = self._request("GET", "/api/tags", timeout=10)
            if response.status_code == 401:
                return False, "401 — нужен API-ключ (Settings → Account в Open WebUI)"
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            data = response.json()
            names = [m.get("name", "") for m in data.get("models", [])]
            if names:
                return True, f"OK, модели: {', '.join(names[:5])}" + ("…" if len(names) > 5 else "")
            return True, "OK"
        except ValueError as exc:
            return False, str(exc)
        except requests.RequestException as exc:
            return False, str(exc)

    def chat(self, messages: list[ChatMessage]) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": 0.3},
        }
        response = self._request("POST", "/api/chat", json=payload)
        if response.status_code == 401:
            raise PermissionError("401 — укажите API-ключ Open WebUI в настройках")
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
        follow_ups_remaining: int = 0,
    ) -> ReviewResult:
        history = history or []
        limit_note = (
            f"Осталось уточняющих вопросов: {follow_ups_remaining}. "
            "Не задавай follow_up, если лимит 0."
        )
        if card.is_code:
            prefix = (
                f"Исходный код:\n```\n{card.code}\n```\n\n"
                f"Задание: {card.task or 'Исправь или дополни код.'}\n"
                f"Эталонное решение:\n```\n{card.reference}\n```\n\n"
            )
            if is_follow_up:
                body = prefix + f"Ответ ученика на уточняющий вопрос (учти диалог):\n```\n{user_answer}\n```"
            else:
                body = prefix + f"Ответ ученика:\n```\n{user_answer}\n```"
            system = SYSTEM_PROMPT_CODE + "\n\n" + limit_note
        elif is_follow_up:
            body = (
                f"Исходный вопрос карточки: {card.question}\n"
                f"Эталонный ответ: {card.reference}\n\n"
                f"Это ответ ученика на уточняющий вопрос. Оцени, учитывая весь диалог.\n"
                f"Ответ ученика:\n{user_answer}"
            )
            system = SYSTEM_PROMPT_TEXT + "\n\n" + limit_note
        else:
            body = (
                f"Вопрос карточки: {card.question}\n"
                f"Эталонный ответ: {card.reference}\n\n"
                f"Ответ ученика:\n{user_answer}"
            )
            system = SYSTEM_PROMPT_TEXT + "\n\n" + limit_note

        messages = [ChatMessage("system", system)]
        messages.extend(history)
        messages.append(ChatMessage("user", body))

        raw = self.client.chat(messages)
        result = self._parse_review(raw)
        if follow_ups_remaining <= 0 and result.follow_up:
            result.follow_up = ""
        return result

    @staticmethod
    def _parse_review(raw: str) -> ReviewResult:
        cleaned = raw.strip()
        for tag in ("think", "redacted_thinking"):
            cleaned = re.sub(rf"<{tag}>.*?</{tag}>", "", cleaned, flags=re.S | re.I)
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
