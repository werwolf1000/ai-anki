#!/usr/bin/env python3
"""Generate Python Live-coding deck (write code from scratch)."""
from __future__ import annotations

import json
from pathlib import Path


def live(q: str, task: str, ref: str, *, lang: str = "python") -> dict:
    return {
        "card_type": "live_code",
        "question": q,
        "task": task,
        "reference": ref.strip(),
        "language": lang,
    }


def build_cards() -> list[dict]:
    return [
        live(
            "Функция greet",
            "Напиши функцию greet(name: str) -> str, возвращающую f'Hello, {name}!'.",
            """def greet(name: str) -> str:
    return f'Hello, {name}!'""",
        ),
        live(
            "Сумма списка",
            "Функция total(numbers: list[int]) -> int — сумма элементов (без sum()).",
            """def total(numbers: list[int]) -> int:
    result = 0
    for n in numbers:
        result += n
    return result""",
        ),
        live(
            "List comprehension — квадраты",
            "Функция squares(n: int) -> list[int] возвращает [0, 1, 4, ... (n-1)^2].",
            """def squares(n: int) -> list[int]:
    return [i * i for i in range(n)]""",
        ),
        live(
            "Фильтр чётных",
            "Функция evens(numbers: list[int]) -> list[int] — только чётные числа.",
            """def evens(numbers: list[int]) -> list[int]:
    return [n for n in numbers if n % 2 == 0]""",
        ),
        live(
            "Dict comprehension",
            "Функция invert_unique(items: list[str]) -> dict[str, int] — слово -> длина (уникальные ключи).",
            """def invert_unique(items: list[str]) -> dict[str, int]:
    return {word: len(word) for word in items}""",
        ),
        live(
            "Класс Counter",
            "Класс Counter с методами increment() -> int и value() -> int (внутренний счётчик).",
            """class Counter:
    def __init__(self) -> None:
        self._count = 0

    def increment(self) -> int:
        self._count += 1
        return self._count

    def value(self) -> int:
        return self._count""",
        ),
        live(
            "Dataclass User",
            "Dataclass User с полями id: int, email: str и методом domain() -> str (часть после @).",
            """from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str

    def domain(self) -> str:
        return self.email.split('@', 1)[1]""",
        ),
        live(
            "Property full_name",
            "Класс Person(first: str, last: str) с @property full_name -> str.",
            """class Person:
    def __init__(self, first: str, last: str) -> None:
        self.first = first
        self.last = last

    @property
    def full_name(self) -> str:
        return f'{self.first} {self.last}'""",
        ),
        live(
            "Контекстный менеджер",
            "Функция write_lines(path: str, lines: list[str]) записывает строки в файл через with open(..., 'w').",
            """def write_lines(path: str, lines: list[str]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\\n')""",
        ),
        live(
            "Чтение JSON",
            "Функция load_json(path: str) -> dict читает UTF-8 JSON из файла.",
            """import json


def load_json(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)""",
        ),
        live(
            "Декоратор uppercase",
            "Декоратор @uppercase оборачивает функцию, возвращающую str, и возвращает результат в upper().",
            """from functools import wraps
from typing import Callable


def uppercase(fn: Callable[[], str]) -> Callable[[], str]:
    @wraps(fn)
    def wrapper() -> str:
        return fn().upper()

    return wrapper""",
        ),
        live(
            "Generator range_step",
            "Генератор range_step(start, stop, step) — как range, но yield.",
            """from collections.abc import Iterator


def range_step(start: int, stop: int, step: int = 1) -> Iterator[int]:
    value = start
    while value < stop:
        yield value
        value += step""",
        ),
        live(
            "*args сумма",
            "Функция add_all(*values: int) -> int — сумма произвольного числа аргументов.",
            """def add_all(*values: int) -> int:
    return sum(values)""",
        ),
        live(
            "**kwargs merge",
            "Функция merge_dicts(**kwargs) -> dict возвращает копию kwargs.",
            """def merge_dicts(**kwargs) -> dict:
    return dict(kwargs)""",
        ),
        live(
            "Custom exception",
            "Класс ValidationError(Exception) с полем field: str; raise при пустой строке validate_non_empty(s, field).",
            """class ValidationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def validate_non_empty(value: str, field: str) -> str:
    if not value.strip():
        raise ValidationError(field, 'must not be empty')
    return value""",
        ),
        live(
            "match HTTP status",
            "Функция status_label(code: int) -> str через match: 200->'OK', 404->'Not Found', иначе 'Unknown'.",
            """def status_label(code: int) -> str:
    match code:
        case 200:
            return 'OK'
        case 404:
            return 'Not Found'
        case _:
            return 'Unknown'""",
        ),
        live(
            "Enum Status",
            "Enum Status со значениями ACTIVE='active', ARCHIVED='archived' (str enum).",
            """from enum import Enum


class Status(str, Enum):
    ACTIVE = 'active'
    ARCHIVED = 'archived'""",
        ),
        live(
            "Pathlib list py",
            "Функция list_py_files(directory: str) -> list[str] — имена *.py в каталоге через pathlib.",
            """from pathlib import Path


def list_py_files(directory: str) -> list[str]:
    return sorted(p.name for p in Path(directory).glob('*.py'))""",
        ),
        live(
            "defaultdict группировка",
            "Функция group_by_first_letter(words: list[str]) -> dict[str, list[str]].",
            """from collections import defaultdict


def group_by_first_letter(words: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for word in words:
        if word:
            groups[word[0].lower()].append(word)
    return dict(groups)""",
        ),
        live(
            "Counter частоты",
            "Функция word_freq(text: str) -> dict[str, int] — частота слов (split по пробелам, lower).",
            """from collections import Counter


def word_freq(text: str) -> dict[str, int]:
    return dict(Counter(word.lower() for word in text.split()))""",
        ),
        live(
            "zip pairs",
            "Функция to_pairs(keys: list[str], values: list[int]) -> list[tuple[str, int]] через zip.",
            """def to_pairs(keys: list[str], values: list[int]) -> list[tuple[str, int]]:
    return list(zip(keys, values, strict=True))""",
        ),
        live(
            "sorted unique",
            "Функция unique_sorted(items: list[int]) -> list[int] — уникальные отсортированные.",
            """def unique_sorted(items: list[int]) -> list[int]:
    return sorted(set(items))""",
        ),
        live(
            "partial apply",
            "Функция make_adder(n: int) возвращает lambda x: x + n.",
            """def make_adder(n: int):
    return lambda x: x + n""",
        ),
        live(
            "map/filter pipeline",
            "Функция positive_squares(numbers: list[int]) -> list[int] — квадраты положительных.",
            """def positive_squares(numbers: list[int]) -> list[int]:
    return [n * n for n in numbers if n > 0]""",
        ),
        live(
            "Abstract base",
            "ABC Storage с abstractmethod save(key: str, value: str) -> None; класс MemoryStorage с dict.",
            """from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    def save(self, key: str, value: str) -> None:
        ...


class MemoryStorage(Storage):
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def save(self, key: str, value: str) -> None:
        self._data[key] = value""",
        ),
        live(
            "Context manager class",
            "Класс Timer с __enter__/__exit__ и полем elapsed (заглушка: elapsed=0.0).",
            """class Timer:
    def __enter__(self) -> 'Timer':
        self.elapsed = 0.0
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None""",
        ),
        live(
            "sqlite fetchone",
            "Функция fetch_user_name(conn, user_id: int) -> str | None — SELECT name FROM users WHERE id=?.",
            """def fetch_user_name(conn, user_id: int) -> str | None:
    row = conn.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
    return row[0] if row else None""",
        ),
        live(
            "TypedDict UserRow",
            "TypedDict UserRow с id: int, name: str; функция as_row(id, name) -> UserRow.",
            """from typing import TypedDict


class UserRow(TypedDict):
    id: int
    name: str


def as_row(user_id: int, name: str) -> UserRow:
    return {'id': user_id, 'name': name}""",
        ),
        live(
            "async fetch stub",
            "async def fetch_status(code: int) -> str — await asyncio.sleep(0); return status_label(code).",
            """import asyncio


async def fetch_status(code: int) -> str:
    await asyncio.sleep(0)
    return status_label(code)


def status_label(code: int) -> str:
    return 'OK' if code == 200 else 'Error'""",
        ),
        live(
            "unittest style assert",
            "Функция is_palindrome(s: str) -> bool — игнорировать регистр и пробелы.",
            """def is_palindrome(text: str) -> bool:
    cleaned = ''.join(ch.lower() for ch in text if ch.isalnum())
    return cleaned == cleaned[::-1]""",
        ),
        live(
            "parse key=value",
            "Функция parse_kv(line: str) -> tuple[str, str] для строки 'key=value' (один =).",
            """def parse_kv(line: str) -> tuple[str, str]:
    key, value = line.split('=', 1)
    return key.strip(), value.strip()""",
        ),
        live(
            "CLI argparse stub",
            "Функция build_parser() -> ArgumentParser с аргументом --limit type=int default=10.",
            """import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=10)
    return parser""",
        ),
        live(
            "NamedTuple Point",
            "NamedTuple Point(x: int, y: int) и функция distance_origin(p: Point) -> float.",
            """from math import hypot
from typing import NamedTuple


class Point(NamedTuple):
    x: int
    y: int


def distance_origin(p: Point) -> float:
    return hypot(p.x, p.y)""",
        ),
        live(
            "Slots class",
            "Класс Card с __slots__ = ('rank', 'suit') и методом label() -> str.",
            """class Card:
    __slots__ = ('rank', 'suit')

    def __init__(self, rank: str, suit: str) -> None:
        self.rank = rank
        self.suit = suit

    def label(self) -> str:
        return f'{self.rank} of {self.suit}'""",
        ),
        live(
            "Walrus read lines",
            "Функция first_long_line(path) -> str | None — первая строка длиннее 10 символов (:=).",
            """def first_long_line(path: str) -> str | None:
    with open(path, encoding='utf-8') as f:
        while line := f.readline():
            if len(line.strip()) > 10:
                return line.strip()
    return None""",
        ),
        live(
            "Protocol Printable",
            "Protocol Printable с def __str__ -> str; функция print_all(items: list[Printable]).",
            """from typing import Protocol


class Printable(Protocol):
    def __str__(self) -> str: ...


def print_all(items: list[Printable]) -> None:
    for item in items:
        print(str(item))""",
        ),
        live(
            "Reduce factorial",
            "Функция factorial(n: int) -> int через цикл (n >= 0).",
            """def factorial(n: int) -> int:
    if n < 0:
        raise ValueError('n must be non-negative')
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result""",
        ),
        live(
            "Deque rotate",
            "Функция rotate_left(items: list[int], k: int) -> list[int] с collections.deque.",
            """from collections import deque


def rotate_left(items: list[int], k: int) -> list[int]:
    d = deque(items)
    d.rotate(-k)
    return list(d)""",
        ),
        live(
            "HTTP stub dataclass",
            "Dataclass HttpResponse(status: int, body: str) и метод is_ok() -> bool (200 <= status < 300).",
            """from dataclasses import dataclass


@dataclass
class HttpResponse:
    status: int
    body: str

    def is_ok(self) -> bool:
        return 200 <= self.status < 300""",
        ),
    ]


def main() -> None:
    cards = build_cards()
    deck = {"name": "Python Live-coding", "cards": cards}
    out = Path(__file__).with_name("python-live-coding.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} live_code cards -> {out}")


if __name__ == "__main__":
    main()
