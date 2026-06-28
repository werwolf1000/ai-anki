from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import requests

from app.deck import Card, ChatMessage, ReviewResult, infer_language_from_name

def _topic_context(card: Card, deck_name: str = "") -> str:
    label = _language_label(card, deck_name)
    lang = _normalize_language(card, deck_name)
    if deck_name:
        if lang in ("php", "python", "py", "typescript", "ts", "javascript", "js"):
            return f"колоды «{deck_name}» ({label})"
        return f"колоды «{deck_name}»"
    if lang in ("php", "python", "py", "typescript", "ts", "javascript", "js"):
        return label
    return "программированию"


def _language_scope_rule(card: Card, deck_name: str = "") -> str:
    lang = (card.language or infer_language_from_name(deck_name) or "").strip().lower()
    conflicts = {
        "php": "Python, JavaScript или TypeScript/Angular",
        "python": "PHP, JavaScript или TypeScript/Angular",
        "py": "PHP, JavaScript или TypeScript/Angular",
        "typescript": "PHP или Python",
        "ts": "PHP или Python",
        "javascript": "PHP или Python",
        "js": "PHP или Python",
    }
    if lang not in conflicts:
        return ""
    label = _language_label(card, deck_name)
    return (
        f"9. Вопрос про {label}. НЕ интерпретируй ответ как {conflicts[lang]} — "
        f"оценивай только в контексте {label}.\n"
    )


def _system_prompt_text(card: Card, deck_name: str = "") -> str:
    topic = _topic_context(card, deck_name)
    scope = _language_scope_rule(card, deck_name)
    return f"""Ты — терпеливый преподаватель по теме {topic} в режиме карточек (как Anki).
Проверяешь ответ ученика на вопрос в контексте {topic}.

Правила:
1. Ученик может отвечать своими словами — не требуй дословного совпадения с эталоном.
2. Оцени понимание по шкале 0–100.
3. correct=true если score >= 75 (хорошее понимание), иначе false.
4. Если ответ неполный или неверный — дай короткую подсказку (hint), НЕ раскрывая весь эталон сразу.
5. Если есть пробелы и остались уточнения — задай один уточняющий вопрос (follow_up).
6. Если лимит уточнений исчерпан — follow_up обязательно пустая строка, только hint и feedback.
7. feedback — 2–4 предложения на русском, дружелюбно и по делу.
8. Отвечай ТОЛЬКО валидным JSON без markdown:
{{
  "correct": true,
  "score": 85,
  "feedback": "...",
  "hint": "...",
  "follow_up": "...",
  "reference_summary": "краткий эталон 1-2 предложения"
}}
{scope}Если hint не нужен — пустая строка. Если follow_up не нужен — пустая строка."""


def _text_card_prefix(card: Card, deck_name: str = "") -> str:
    topic = _topic_context(card, deck_name)
    if deck_name:
        return f"Тема колоды: {deck_name}\nКонтекст: {topic}\n\n"
    if topic != "программированию":
        return f"Контекст: {topic}\n\n"
    return ""

_LIVE_CODE_JSON = """
{
  "correct": true,
  "score": 85,
  "feedback": "...",
  "hint": "...",
  "follow_up": "...",
  "reference_summary": "кратко что должно быть в решении"
}"""

_CODE_JSON = _LIVE_CODE_JSON


def _effective_language(card: Card, deck_name: str = "") -> str:
    return (
        (card.language or "").strip().lower()
        or infer_language_from_name(deck_name)
        or "typescript"
    )


def _normalize_language(card: Card, deck_name: str = "") -> str:
    return _effective_language(card, deck_name)


def _language_label(card: Card, deck_name: str = "") -> str:
    labels = {
        "typescript": "TypeScript",
        "ts": "TypeScript",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "python": "Python",
        "py": "Python",
        "php": "PHP",
    }
    lang = _normalize_language(card, deck_name)
    return labels.get(lang, lang.capitalize())


def _fence_lang(card: Card, deck_name: str = "") -> str:
    fences = {
        "typescript": "typescript",
        "ts": "typescript",
        "javascript": "javascript",
        "js": "javascript",
        "python": "python",
        "py": "python",
        "php": "php",
    }
    lang = _normalize_language(card, deck_name)
    return fences.get(lang, lang)


def _is_angular_context(card: Card, deck_name: str = "") -> bool:
    if _normalize_language(card, deck_name) not in ("typescript", "ts", "javascript", "js"):
        return False
    blob = f"{card.reference}\n{card.question}\n{card.task}\n{card.code}"
    return "@angular" in blob or "@Component" in blob or "standalone:" in blob


def _system_prompt_live_code(card: Card, deck_name: str = "") -> str:
    label = _language_label(card, deck_name)
    if _is_angular_context(card, deck_name):
        topic = f"Angular/{label}"
        criteria = f"API, idioms Angular/{label} и корректность решения"
    else:
        topic = label
        criteria = f"синтаксис, idioms языка {label}, типы (если есть), логику и соответствие заданию"
    return f"""Ты — преподаватель {topic} в режиме live-coding.
Ученик пишет код с нуля по заданию карточки. Ожидаемый язык ответа: {label}.

Правила:
1. Сравни код ученика с эталоном по смыслу и {criteria} — не требуй посимвольного совпадения.
2. НЕ требуй TypeScript/Angular, если карточка на другом языке. Оценивай код на {label}.
3. Допускай эквивалентные решения, если они корректны для {label}.
4. Оценка 0–100; correct=true если score >= 75.
5. При ошибках — короткая hint (область проблемы, не полное решение).
6. follow_up всегда пустая строка: ученик отвечает только кодом в редакторе, текстовых уточнений нет.
7. feedback — 2–4 предложения на русском.
8. Только JSON:{_LIVE_CODE_JSON}"""


def _system_prompt_code(card: Card, deck_name: str = "") -> str:
    label = _language_label(card, deck_name)
    if _is_angular_context(card, deck_name):
        topic = f"Angular/{label}"
    else:
        topic = label
    return f"""Ты — преподаватель {topic}. Карточка с кодом: ученик должен исправить или дополнить фрагмент.
Ожидаемый язык ответа: {label}.

Правила:
1. Сравни ответ ученика с эталоном по смыслу — не требуй посимвольного совпадения.
2. НЕ требуй TypeScript/Angular, если карточка на {label}.
3. Проверь: исправлена ли ошибка / добавлено ли требуемое / корректен ли синтаксис и логика на {label}.
4. Оценка 0–100; correct=true если score >= 75.
5. При ошибках — короткая hint (укажи область проблемы, не давай готовое решение целиком).
6. follow_up всегда пустая строка: ученик отвечает только кодом в редакторе, текстовых уточнений нет.
7. feedback — что верно, что нет, 2–4 предложения на русском.
8. Только JSON:{_CODE_JSON}"""


def _system_prompt_hint(card: Card, deck_name: str = "") -> str:
    topic = _topic_context(card, deck_name)
    label = _language_label(card, deck_name)
    return f"""Ты — преподаватель по теме {topic}.
Ученик нажал «Подсказка» и просит помощь по карточке, не отправляя ответ на полную проверку.

Правила:
1. Дай короткую подсказку (1–3 предложения): направление, ключевая идея, что проверить или с чего начать.
2. НЕ давай полный эталонный ответ, готовый код целиком и не пересказывай reference дословно.
3. Контекст: {topic}. Язык/предмет: {label}.
4. Если есть черновик ученика — подскажи, что в нём не так или чего не хватает, без готового решения.
5. Отвечай ТОЛЬКО валидным JSON без markdown:
{{"hint": "..."}}"""


def _build_hint_body(card: Card, deck_name: str, user_draft: str) -> str:
    prefix = _text_card_prefix(card, deck_name)
    ref_note = f"Эталон (только для тебя, НЕ цитируй ученику):\n{card.reference}\n\n"
    draft = user_draft.strip()

    if card.is_live_code:
        fence = _fence_lang(card, deck_name)
        body = (
            prefix
            + f"Задание (live-coding): {card.question}\n"
            + (f"Описание задания: {card.task}\n" if card.task else "")
            + ref_note
        )
        if draft:
            body += f"Черновик кода ученика:\n```{fence}\n{draft}\n```\n\n"
        return body + "Дай подсказку, как двигаться дальше."

    if card.is_code:
        fence = _fence_lang(card, deck_name)
        body = (
            prefix
            + f"Исходный код:\n```{fence}\n{card.code}\n```\n\n"
            + f"Задание: {card.task or 'Исправь или дополни код.'}\n"
            + ref_note
        )
        if draft:
            body += f"Черновик ответа ученика:\n```{fence}\n{draft}\n```\n\n"
        return body + "Дай подсказку, не раскрывая эталон."

    body = prefix + f"Вопрос: {card.question}\n" + ref_note
    if draft:
        body += f"Черновик ответа ученика:\n{draft}\n\n"
    return body + "Дай подсказку, не раскрывая эталон."


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
        deck_name: str = "",
    ) -> ReviewResult:
        history = history or []
        code_only = card.needs_code_editor
        if code_only:
            follow_ups_remaining = 0
            is_follow_up = False
        limit_note = (
            "Карточка с кодом: ученик отвечает только кодом в редакторе. "
            "follow_up обязательно пустая строка; при ошибках используй hint."
            if code_only
            else (
                f"Осталось уточняющих вопросов: {follow_ups_remaining}. "
                "Не задавай follow_up, если лимит 0."
            )
        )
        if card.is_live_code:
            fence = _fence_lang(card, deck_name)
            label = _language_label(card, deck_name)
            prefix = (
                f"Язык карточки: {label}\n"
                f"Задание (live-coding): {card.question}\n"
                f"{('Подсказка: ' + card.task) if card.task else ''}\n"
                f"Эталонное решение:\n```{fence}\n{card.reference}\n```\n\n"
            )
            if is_follow_up:
                body = prefix + f"Код ученика (ответ на уточнение):\n```{fence}\n{user_answer}\n```"
            else:
                body = prefix + f"Код ученика:\n```{fence}\n{user_answer}\n```"
            system = _system_prompt_live_code(card, deck_name) + "\n\n" + limit_note
        elif card.is_code:
            fence = _fence_lang(card, deck_name)
            label = _language_label(card, deck_name)
            prefix = (
                f"Язык карточки: {label}\n"
                f"Исходный код:\n```{fence}\n{card.code}\n```\n\n"
                f"Задание: {card.task or 'Исправь или дополни код.'}\n"
                f"Эталонное решение:\n```{fence}\n{card.reference}\n```\n\n"
            )
            if is_follow_up:
                body = prefix + f"Ответ ученика на уточняющий вопрос (учти диалог):\n```{fence}\n{user_answer}\n```"
            else:
                body = prefix + f"Ответ ученика:\n```{fence}\n{user_answer}\n```"
            system = _system_prompt_code(card, deck_name) + "\n\n" + limit_note
        elif is_follow_up:
            prefix = _text_card_prefix(card, deck_name)
            body = (
                prefix
                + f"Исходный вопрос карточки: {card.question}\n"
                f"Эталонный ответ: {card.reference}\n\n"
                f"Это ответ ученика на уточняющий вопрос. Оцени, учитывая весь диалог.\n"
                f"Ответ ученика:\n{user_answer}"
            )
            system = _system_prompt_text(card, deck_name) + "\n\n" + limit_note
        else:
            prefix = _text_card_prefix(card, deck_name)
            body = (
                prefix
                + f"Вопрос карточки: {card.question}\n"
                f"Эталонный ответ: {card.reference}\n\n"
                f"Ответ ученика:\n{user_answer}"
            )
            system = _system_prompt_text(card, deck_name) + "\n\n" + limit_note

        messages = [ChatMessage("system", system)]
        messages.extend(history)
        messages.append(ChatMessage("user", body))

        raw = self.client.chat(messages)
        result = self._parse_review(raw)
        if follow_ups_remaining <= 0 and result.follow_up:
            result.follow_up = ""
        if code_only and result.follow_up:
            if not result.hint:
                result.hint = result.follow_up
            result.follow_up = ""
        return result

    def request_hint(
        self,
        card: Card,
        *,
        deck_name: str = "",
        user_draft: str = "",
    ) -> str:
        system = _system_prompt_hint(card, deck_name)
        body = _build_hint_body(card, deck_name, user_draft)
        messages = [
            ChatMessage("system", system),
            ChatMessage("user", body),
        ]
        raw = self.client.chat(messages)
        return self._parse_hint(raw)

    @staticmethod
    def _parse_hint(raw: str) -> str:
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
            hint = str(data.get("hint", "") or "").strip()
            if hint:
                return hint
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return cleaned or "Не удалось получить подсказку."

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
