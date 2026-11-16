"""Короткие тесты по уроку. Ответы проверяются сервером, отдельно от сертификации."""
from __future__ import annotations

import secrets
import threading
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StrictInt

from server.book_decks import parse_json_array
from server.knowledge import ThinkFilter
from server.syllabus import get_syllabus


class QuizIn(BaseModel):
    lesson: str = Field(min_length=1, max_length=500)


class QuizAnswers(BaseModel):
    answers: list[StrictInt] = Field(min_length=1, max_length=5)


def validate_questions(items: list[dict]) -> list[dict]:
    questions, seen = [], set()
    for item in items:
        question, options, correct = item.get("question"), item.get("options"), item.get("correct")
        if not isinstance(question, str) or not question.strip() or question.strip() in seen:
            continue
        if not isinstance(options, list) or len(options) != 4 or not all(isinstance(x, str) and x.strip() for x in options):
            continue
        options = [x.strip() for x in options]
        if len(set(options)) != 4 or type(correct) is not int or not 0 <= correct < 4:
            continue
        explanation = item.get("explanation", "")
        if not isinstance(explanation, str):
            continue
        seen.add(question.strip())
        questions.append({"question": question.strip(), "options": options, "correct": correct, "explanation": explanation})
        if len(questions) == 5:
            break
    if len(questions) < 3:
        raise ValueError("Модель вернула меньше трёх корректных вопросов. Попробуйте создать тест ещё раз.")
    return questions


def build_router(services, current_ctx) -> APIRouter:
    router = APIRouter()
    quizzes: dict[str, dict] = {}
    generating: set[int] = set()
    lock = threading.Lock()

    @router.post("/api/books/{sid}/quiz")
    def generate(sid: str, body: QuizIn, ctx=Depends(current_ctx)):
        sy = get_syllabus(sid)
        if sy is None or body.lesson not in sy.lesson_titles():
            raise HTTPException(404, "Урок не найден")
        with lock:
            if ctx.user.id in generating:
                raise HTTPException(409, "Ваш тест ещё создаётся")
            generating.add(ctx.user.id)
        try:
            material = services.lesson_context(sy, body.lesson)
            for path in services.books.paths(sy):
                if path:
                    cards = [c for c in services.books._read(path).get("cards", []) if c.get("topic") == body.lesson]
                    material += "\n" + "\n".join(f"{c['question']}\n{c['reference']}" for c in cards[:8])
            system = (
                "Составь 5 вопросов для проверки понимания урока. Пиши по-русски. "
                "У каждого вопроса 4 различных варианта и ровно один правильный. "
                "Опирайся на тему и материалы, избегай неоднозначных вопросов. "
                'Верни только JSON-массив: [{"question":"...", "options":["...","...","...","..."], '
                '"correct":0, "explanation":"Почему этот ответ верен"}]. correct — индекс от 0 до 3.'
            )
            filt, parts = ThinkFilter(), []
            for piece in services.textbook_llm().stream([
                {"role": "system", "content": system},
                {"role": "user", "content": f"Учебник: {sy.title}\nУрок: {body.lesson}\nМатериалы:\n{material[:16000]}"},
            ], temperature=0.4):
                parts.append(filt.feed(piece))
            parts.append(filt.flush())
            questions = validate_questions(parse_json_array("".join(parts)))
        except Exception as exc:
            raise HTTPException(502, f"Не удалось создать тест: {exc}") from exc
        finally:
            with lock:
                generating.discard(ctx.user.id)
        quiz_id, now = secrets.token_urlsafe(18), time.monotonic()
        with lock:
            for key in list(quizzes):
                if now - quizzes[key]["created"] > 7200:
                    del quizzes[key]
            if len(quizzes) >= 128:
                del quizzes[next(iter(quizzes))]
            quizzes[quiz_id] = {"owner": ctx.user.id, "created": now, "questions": questions}
        return {"id": quiz_id, "questions": [{"question": q["question"], "options": q["options"]} for q in questions]}

    @router.post("/api/lesson-quizzes/{quiz_id}/check")
    def check(quiz_id: str, body: QuizAnswers, ctx=Depends(current_ctx)):
        with lock:
            quiz = quizzes.get(quiz_id)
            if not quiz or quiz["owner"] != ctx.user.id or time.monotonic() - quiz["created"] > 7200:
                raise HTTPException(404, "Тест истёк или не найден. Создайте новый тест.")
            questions = quiz["questions"]
        if len(body.answers) != len(questions) or any(not 0 <= a < 4 for a in body.answers):
            raise HTTPException(422, "Выберите один ответ на каждый вопрос")
        results = [{"correct": q["correct"], "explanation": q["explanation"], "passed": a == q["correct"]}
                   for q, a in zip(questions, body.answers)]
        return {"score": sum(r["passed"] for r in results), "total": len(results), "results": results}

    return router
