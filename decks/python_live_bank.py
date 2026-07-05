"""Extra Python live-coding cards for the Anki deck."""
from __future__ import annotations

from live_coding_card import live


def extra_cards() -> list[dict]:
    return [
        # --- Основы (algorithms & basics) ---
        live(
            "reverse_string",
            "Реализуйте функцию reverse_string(text: str) -> str, которая возвращает строку "
            "text в обратном порядке. Пустая строка должна вернуть ''. "
            "Не используйте срез [::-1] — пройдитесь по символам в цикле.",
            """def reverse_string(text: str) -> str:
    result: list[str] = []
    for ch in text:
        result.insert(0, ch)
    return ''.join(result)""",
            topic="Основы",
            requirements=["Сигнатура reverse_string(text: str) -> str", "Пустая строка -> ''"],
        ),
        live(
            "count_vowels",
            "Напишите count_vowels(text: str) -> int: количество гласных a, e, i, o, u "
            "(регистр не важен). Негласные и цифры не считаются. Пустая строка -> 0.",
            """def count_vowels(text: str) -> int:
    vowels = set('aeiou')
    return sum(1 for ch in text.lower() if ch in vowels)""",
            topic="Основы",
        ),
        live(
            "clamp",
            "Функция clamp(value: float, low: float, high: float) -> float ограничивает value "
            "диапазоном [low, high]. Если value < low — вернуть low; если value > high — high. "
            "Предполагайте low <= high.",
            """def clamp(value: float, low: float, high: float) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value""",
            topic="Основы",
        ),
        live(
            "running_sum",
            "Функция running_sum(numbers: list[int]) -> list[int] возвращает префиксные суммы: "
            "для [1, 2, 3] -> [1, 3, 6]. Пустой список -> [].",
            """def running_sum(numbers: list[int]) -> list[int]:
    result: list[int] = []
    total = 0
    for n in numbers:
        total += n
        result.append(total)
    return result""",
            topic="Основы",
        ),
        live(
            "second_largest",
            "Функция second_largest(numbers: list[int]) -> int | None возвращает второе по "
            "величине число без полной сортировки. Дубликаты учитываются: [5, 5, 1] -> 5. "
            "Меньше двух элементов -> None.",
            """def second_largest(numbers: list[int]) -> int | None:
    if len(numbers) < 2:
        return None
    first = second = float('-inf')
    for n in numbers:
        if n > first:
            second, first = first, n
        elif n > second and n != first:
            second = n
    return int(second) if second != float('-inf') else None""",
            topic="Основы",
            requirements=["Без sorted() всего списка", "None если элементов < 2"],
        ),
        live(
            "find_min_index",
            "Функция find_min_index(numbers: list[int]) -> int | None возвращает индекс "
            "минимального элемента. При нескольких минимумах — первый индекс. "
            "Пустой список -> None.",
            """def find_min_index(numbers: list[int]) -> int | None:
    if not numbers:
        return None
    min_idx = 0
    for i, n in enumerate(numbers):
        if n < numbers[min_idx]:
            min_idx = i
    return min_idx""",
            topic="Основы",
        ),
        live(
            "binary_search",
            "Реализуйте binary_search(sorted_items: list[int], target: int) -> int: "
            "индекс target в отсортированном списке или -1. Алгоритм O(log n), без bisect.",
            """def binary_search(sorted_items: list[int], target: int) -> int:
    left, right = 0, len(sorted_items) - 1
    while left <= right:
        mid = (left + right) // 2
        if sorted_items[mid] == target:
            return mid
        if sorted_items[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1""",
            topic="Основы",
            requirements=["O(log n)", "Вернуть -1 если не найден"],
        ),
        live(
            "bubble_sort",
            "Функция bubble_sort(items: list[int]) -> list[int] сортирует копию списка "
            "пузырьковой сортировкой. Исходный список не меняется.",
            """def bubble_sort(items: list[int]) -> list[int]:
    arr = items.copy()
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr""",
            topic="Основы",
        ),
        live(
            "two_sum",
            "Функция two_sum(numbers: list[int], target: int) -> tuple[int, int] | None "
            "возвращает индексы двух чисел, сумма которых равна target. "
            "Каждый элемент используется один раз. Нет пары -> None.",
            """def two_sum(numbers: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}
    for i, n in enumerate(numbers):
        need = target - n
        if need in seen:
            return seen[need], i
        seen[n] = i
    return None""",
            topic="Основы",
        ),
        live(
            "max_subarray",
            "Функция max_subarray(numbers: list[int]) -> int — максимальная сумма непрерывного "
            "подмассива (алгоритм Кадане). Пустой список -> 0.",
            """def max_subarray(numbers: list[int]) -> int:
    if not numbers:
        return 0
    best = current = numbers[0]
    for n in numbers[1:]:
        current = max(n, current + n)
        best = max(best, current)
    return best""",
            topic="Основы",
        ),
        live(
            "is_anagram",
            "Функция is_anagram(a: str, b: str) -> bool: True, если a и b — анаграммы "
            "(одинаковые буквы, регистр игнорируется, пробелы не учитываются).",
            """def is_anagram(a: str, b: str) -> bool:
    def key(s: str) -> list[str]:
        return sorted(ch.lower() for ch in s if ch.isalpha())
    return key(a) == key(b)""",
            topic="Основы",
        ),
        live(
            "interleave",
            "Функция interleave(a: list[int], b: list[int]) -> list[int] чередует элементы "
            "двух списков; если один длиннее — допишите остаток в конец.",
            """def interleave(a: list[int], b: list[int]) -> list[int]:
    result: list[int] = []
    i = 0
    while i < len(a) or i < len(b):
        if i < len(a):
            result.append(a[i])
        if i < len(b):
            result.append(b[i])
        i += 1
    return result""",
            topic="Основы",
        ),
        live(
            "rotate_right",
            "Функция rotate_right(items: list[int], k: int) -> list[int] циклически сдвигает "
            "список вправо на k позиций. k может быть больше len(items).",
            """def rotate_right(items: list[int], k: int) -> list[int]:
    if not items:
        return []
    k %= len(items)
    return items[-k:] + items[:-k]""",
            topic="Основы",
        ),
        live(
            "insert_sorted",
            "Функция insert_sorted(sorted_items: list[int], value: int) -> list[int] "
            "вставляет value в отсортированный список, сохраняя порядок. Без sort().",
            """def insert_sorted(sorted_items: list[int], value: int) -> list[int]:
    result = sorted_items.copy()
    for i, n in enumerate(result):
        if value <= n:
            result.insert(i, value)
            return result
    result.append(value)
    return result""",
            topic="Основы",
        ),
        live(
            "remove_adjacent_dupes",
            "Функция remove_adjacent_dupes(items: list[int]) -> list[int] удаляет "
            "соседние дубликаты: [1, 1, 2, 2, 3] -> [1, 2, 3].",
            """def remove_adjacent_dupes(items: list[int]) -> list[int]:
    if not items:
        return []
    result = [items[0]]
    for n in items[1:]:
        if n != result[-1]:
            result.append(n)
    return result""",
            topic="Основы",
        ),
        live(
            "title_case",
            "Функция title_case(text: str) -> str переводит каждое слово в Title Case "
            "(первая буква заглавная). Разделитель — пробел.",
            """def title_case(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.split())""",
            topic="Основы",
        ),
        live(
            "count_words",
            "Функция count_words(text: str) -> int считает слова, разделённые пробелами. "
            "Последовательности пробелов не создают пустых слов. '' -> 0.",
            """def count_words(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())""",
            topic="Основы",
        ),
        live(
            "strip_prefix",
            "Функция strip_prefix(text: str, prefix: str) -> str удаляет prefix из начала "
            "text один раз, если он там есть; иначе вернуть text без изменений.",
            """def strip_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text""",
            topic="Основы",
        ),
        live(
            "caesar_cipher",
            "Функция caesar_cipher(text: str, shift: int) -> str сдвигает латинские буквы "
            "на shift позиций в алфавите (a-z, регистр сохраняется). Не-буквы не меняются.",
            """def caesar_cipher(text: str, shift: int) -> str:
    result: list[str] = []
    for ch in text:
        if 'a' <= ch <= 'z':
            base = ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        elif 'A' <= ch <= 'Z':
            base = ord('A')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return ''.join(result)""",
            topic="Основы",
        ),
        live(
            "roman_to_int",
            "Функция roman_to_int(s: str) -> int конвертирует римское число (I, V, X, L, C, D, M) "
            "в int. Поддержите вычитательные пары: IV=4, IX=9, XL=40.",
            """def roman_to_int(s: str) -> int:
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev = 0
    for ch in reversed(s):
        val = values[ch]
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total""",
            topic="Основы",
        ),
        live(
            "validate_email_simple",
            "Функция validate_email_simple(email: str) -> bool: True, если есть ровно один '@', "
            "до и после него — непустые части без пробелов.",
            """def validate_email_simple(email: str) -> bool:
    if email.count('@') != 1:
        return False
    local, domain = email.split('@')
    return bool(local) and bool(domain) and ' ' not in local and ' ' not in domain""",
            topic="Основы",
        ),
        live(
            "parse_int_safe",
            "Функция parse_int_safe(raw: str, default: int = 0) -> int парсит int из строки; "
            "при ValueError вернуть default.",
            """def parse_int_safe(raw: str, default: int = 0) -> int:
    try:
        return int(raw.strip())
    except ValueError:
        return default""",
            topic="Основы",
        ),
        live(
            "matrix_transpose",
            "Функция transpose(matrix: list[list[int]]) -> list[list[int]] транспонирует "
            "прямоугольную матрицу. Пустая матрица -> [].",
            """def transpose(matrix: list[list[int]]) -> list[list[int]]:
    if not matrix:
        return []
    return [list(row) for row in zip(*matrix)]""",
            topic="Основы",
        ),
        live(
            "dedupe_sorted",
            "Функция dedupe_sorted(items: list[int]) -> list[int] удаляет дубликаты из "
            "отсортированного списка за один проход: [1, 1, 2, 3, 3] -> [1, 2, 3].",
            """def dedupe_sorted(items: list[int]) -> list[int]:
    if not items:
        return []
    result = [items[0]]
    for n in items[1:]:
        if n != result[-1]:
            result.append(n)
    return result""",
            topic="Основы",
        ),
        live(
            "longest_increasing",
            "Функция longest_increasing(numbers: list[int]) -> int — длина самой длинной "
            "строго возрастающей подпоследовательности. [] -> 0.",
            """def longest_increasing(numbers: list[int]) -> int:
    if not numbers:
        return 0
    tails: list[int] = []
    for n in numbers:
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < n:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(n)
        else:
            tails[lo] = n
    return len(tails)""",
            topic="Основы",
        ),
        # --- ООП ---
        live(
            "Stack class",
            "Класс Stack с методами push(x: int) -> None, pop() -> int, is_empty() -> bool. "
            "pop() на пустом стеке бросает IndexError.",
            """class Stack:
    def __init__(self) -> None:
        self._items: list[int] = []

    def push(self, x: int) -> None:
        self._items.append(x)

    def pop(self) -> int:
        if not self._items:
            raise IndexError('pop from empty stack')
        return self._items.pop()

    def is_empty(self) -> bool:
        return not self._items""",
            topic="ООП",
        ),
        live(
            "Queue class",
            "Класс Queue (FIFO) с enqueue(x: int), dequeue() -> int, is_empty() -> bool. "
            "dequeue на пустой очереди — IndexError.",
            """from collections import deque


class Queue:
    def __init__(self) -> None:
        self._items: deque[int] = deque()

    def enqueue(self, x: int) -> None:
        self._items.append(x)

    def dequeue(self) -> int:
        if not self._items:
            raise IndexError('dequeue from empty queue')
        return self._items.popleft()

    def is_empty(self) -> bool:
        return not self._items""",
            topic="ООП",
        ),
        live(
            "BankAccount class",
            "Класс BankAccount с deposit(amount), withdraw(amount) и balance() -> float. "
            "withdraw при недостатке средств бросает ValueError. Баланс не может быть отрицательным.",
            """class BankAccount:
    def __init__(self, initial: float = 0.0) -> None:
        self._balance = initial

    def deposit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError('amount must be non-negative')
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount < 0:
            raise ValueError('amount must be non-negative')
        if amount > self._balance:
            raise ValueError('insufficient funds')
        self._balance -= amount

    def balance(self) -> float:
        return self._balance""",
            topic="ООП",
        ),
        live(
            "Rectangle area",
            "Класс Rectangle(width: float, height: float) с методами area() -> float "
            "и perimeter() -> float.",
            """class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)""",
            topic="ООП",
        ),
        live(
            "Animal inheritance",
            "Базовый класс Animal с speak() -> str возвращающим '...'. "
            "Dog.speak() -> 'woof', Cat.speak() -> 'meow'.",
            """class Animal:
    def speak(self) -> str:
        return '...'


class Dog(Animal):
    def speak(self) -> str:
        return 'woof'


class Cat(Animal):
    def speak(self) -> str:
        return 'meow'""",
            topic="ООП",
        ),
        live(
            "classmethod from_dict",
            "Dataclass Product(id: int, name: str) с @classmethod from_dict(data: dict) -> Product, "
            "читающим ключи 'id' и 'name'.",
            """from dataclasses import dataclass


@dataclass
class Product:
    id: int
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        return cls(id=int(data['id']), name=str(data['name']))""",
            topic="ООП",
        ),
        live(
            "staticmethod validate",
            "Класс Email с @staticmethod is_valid(value: str) -> bool: один '@', "
            "непустые local и domain.",
            """class Email:
    @staticmethod
    def is_valid(value: str) -> bool:
        if value.count('@') != 1:
            return False
        local, domain = value.split('@')
        return bool(local.strip()) and bool(domain.strip())""",
            topic="ООП",
        ),
        live(
            "__repr__ Product",
            "Класс Product(name: str, price: float) с __repr__ -> str вида "
            "Product(name='apple', price=1.5).",
            """class Product:
    def __init__(self, name: str, price: float) -> None:
        self.name = name
        self.price = price

    def __repr__(self) -> str:
        return f'Product(name={self.name!r}, price={self.price!r})'""",
            topic="ООП",
        ),
        live(
            "__eq__ Point",
            "Класс Point(x: int, y: int) с __eq__: два Point равны, если совпадают x и y. "
            "Сравнение с не-Point -> False.",
            """class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y""",
            topic="ООП",
        ),
        live(
            "__add__ Vector2",
            "Класс Vector2(x, y) с __add__ для покомпонентного сложения и __mul__(scalar: float) "
            "для умножения на скаляр.",
            """class Vector2:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)""",
            topic="ООП",
        ),
        live(
            "__len__ Playlist",
            "Класс Playlist с add(title: str), tracks() -> list[str] и __len__ -> int "
            "(число треков).",
            """class Playlist:
    def __init__(self) -> None:
        self._tracks: list[str] = []

    def add(self, title: str) -> None:
        self._tracks.append(title)

    def tracks(self) -> list[str]:
        return list(self._tracks)

    def __len__(self) -> int:
        return len(self._tracks)""",
            topic="ООП",
        ),
        live(
            "__iter__ Range",
            "Класс Range(start, stop, step=1) итерируемый через __iter__, yielding int "
            "как range(start, stop, step).",
            """from collections.abc import Iterator


class Range:
    def __init__(self, start: int, stop: int, step: int = 1) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self) -> Iterator[int]:
        value = self.start
        while value < self.stop:
            yield value
            value += self.step""",
            topic="ООП",
        ),
        live(
            "__contains__ Bag",
            "Класс Bag хранит элементы str; __contains__(item) -> bool проверяет наличие. "
            "Метод add(item: str) добавляет элемент.",
            """class Bag:
    def __init__(self) -> None:
        self._items: set[str] = set()

    def add(self, item: str) -> None:
        self._items.add(item)

    def __contains__(self, item: object) -> bool:
        return isinstance(item, str) and item in self._items""",
            topic="ООП",
        ),
        live(
            "Dataclass Order total",
            "Dataclass OrderItem(name: str, price: float, qty: int) и Order(items: list[OrderItem]) "
            "с методом total() -> float.",
            """from dataclasses import dataclass, field


@dataclass
class OrderItem:
    name: str
    price: float
    qty: int


@dataclass
class Order:
    items: list[OrderItem] = field(default_factory=list)

    def total(self) -> float:
        return sum(item.price * item.qty for item in self.items)""",
            topic="ООП",
        ),
        live(
            "Enum Priority",
            "Enum Priority(IntEnum): LOW=1, MEDIUM=2, HIGH=3. Метод is_high() -> bool.",
            """from enum import IntEnum


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def is_high(self) -> bool:
        return self is Priority.HIGH""",
            topic="ООП",
        ),
        live(
            "LinkedList node",
            "Класс Node(value: int, next: Node | None = None) и LinkedList с append(value) "
            "и to_list() -> list[int].",
            """class Node:
    def __init__(self, value: int, next: 'Node | None' = None) -> None:
        self.value = value
        self.next = next


class LinkedList:
    def __init__(self) -> None:
        self.head: Node | None = None

    def append(self, value: int) -> None:
        node = Node(value)
        if self.head is None:
            self.head = node
            return
        current = self.head
        while current.next is not None:
            current = current.next
        current.next = node

    def to_list(self) -> list[int]:
        result: list[int] = []
        current = self.head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result""",
            topic="ООП",
        ),
        live(
            "Context manager file",
            "Класс ManagedFile(path, mode='r') как контекстный менеджер: __enter__ открывает "
            "файл и возвращает handle; __exit__ закрывает.",
            """class ManagedFile:
    def __init__(self, path: str, mode: str = 'r') -> None:
        self.path = path
        self.mode = mode
        self._handle = None

    def __enter__(self):
        self._handle = open(self.path, self.mode, encoding='utf-8')
        return self._handle

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._handle is not None:
            self._handle.close()""",
            topic="ООП",
        ),
        live(
            "Observer pattern",
            "Класс EventEmitter с subscribe(fn), unsubscribe(fn) и emit(value). "
            "emit вызывает все подписанные callable с value.",
            """from collections.abc import Callable


class EventEmitter:
    def __init__(self) -> None:
        self._listeners: list[Callable[[str], None]] = []

    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._listeners.append(fn)

    def unsubscribe(self, fn: Callable[[str], None]) -> None:
        self._listeners.remove(fn)

    def emit(self, value: str) -> None:
        for fn in list(self._listeners):
            fn(value)""",
            topic="ООП",
        ),
        # --- Функциональное ---
        live(
            "decorator timing",
            "Декоратор @timing печатает 'elapsed: X.XXs' после вызова обёрнутой функции "
            "(time.perf_counter). Сохраняйте имя через @wraps.",
            """from functools import wraps
import time
from collections.abc import Callable
from typing import TypeVar

F = TypeVar('F', bound=Callable)


def timing(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f'elapsed: {time.perf_counter() - start:.2f}s')
    return wrapper  # type: ignore[return-value]""",
            topic="Функциональное",
        ),
        live(
            "decorator retry",
            "Декоратор retry(times: int) повторяет вызов функции до times раз при "
            "исключении; если все попытки провалились — пробросить последнее.",
            """from functools import wraps


def retry(times: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for _ in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
            raise last_exc
        return wrapper
    return decorator""",
            topic="Функциональное",
        ),
        live(
            "memoize manual",
            "Функция make_memoize() возвращает декоратор, кеширующий результаты "
            "по tuple(args). Без functools.lru_cache.",
            """from collections.abc import Callable


def make_memoize():
    def decorator(fn: Callable):
        cache: dict[tuple, object] = {}

        def wrapper(*args):
            key = args
            if key not in cache:
                cache[key] = fn(*args)
            return cache[key]
        return wrapper
    return decorator""",
            topic="Функциональное",
        ),
        live(
            "compose functions",
            "Функция compose(f, g) возвращает h(x) = f(g(x)) для int -> int функций.",
            """from collections.abc import Callable


def compose(f: Callable[[int], int], g: Callable[[int], int]) -> Callable[[int], int]:
    def h(x: int) -> int:
        return f(g(x))
    return h""",
            topic="Функциональное",
        ),
        live(
            "map_keys",
            "Функция map_keys(data: dict[str, int], fn: Callable[[str], str]) -> dict[str, int] "
            "применяет fn к каждому ключу.",
            """from collections.abc import Callable


def map_keys(data: dict[str, int], fn: Callable[[str], str]) -> dict[str, int]:
    return {fn(key): value for key, value in data.items()}""",
            topic="Функциональное",
        ),
        live(
            "filter_dict",
            "Функция filter_dict(data: dict[str, int], predicate) -> dict[str, int] "
            "оставляет пары, где predicate(key, value) истинно.",
            """from collections.abc import Callable


def filter_dict(
    data: dict[str, int],
    predicate: Callable[[str, int], bool],
) -> dict[str, int]:
    return {k: v for k, v in data.items() if predicate(k, v)}""",
            topic="Функциональное",
        ),
        live(
            "reduce product",
            "Функция product(numbers: list[int]) -> int — произведение элементов через "
            "functools.reduce. Пустой список -> 1.",
            """from functools import reduce


def product(numbers: list[int]) -> int:
    return reduce(lambda a, b: a * b, numbers, 1)""",
            topic="Функциональное",
        ),
        live(
            "curry add",
            "Функция curry_add(a: int) возвращает функцию принимающую b: int и возвращающую a + b.",
            """from collections.abc import Callable


def curry_add(a: int) -> Callable[[int], int]:
    def add_b(b: int) -> int:
        return a + b
    return add_b""",
            topic="Функциональное",
        ),
        live(
            "generator batches",
            "Генератор batches(items: list[int], size: int) yield'ит подсписки длины size "
            "(последний может быть короче). size <= 0 -> ValueError.",
            """from collections.abc import Iterator


def batches(items: list[int], size: int) -> Iterator[list[int]]:
    if size <= 0:
        raise ValueError('size must be positive')
    for i in range(0, len(items), size):
        yield items[i:i + size]""",
            topic="Функциональное",
        ),
        live(
            "accumulate prefix",
            "Функция prefix_sums(numbers: list[int]) -> list[int] через itertools.accumulate.",
            """from itertools import accumulate


def prefix_sums(numbers: list[int]) -> list[int]:
    return list(accumulate(numbers))""",
            topic="Функциональное",
        ),
        live(
            "zip_longest pad",
            "Функция pad_zip(a: list[str], b: list[str], fill: str = '') -> list[tuple[str, str]] "
            "через itertools.zip_longest.",
            """from itertools import zip_longest


def pad_zip(a: list[str], b: list[str], fill: str = '') -> list[tuple[str, str]]:
    return list(zip_longest(a, b, fillvalue=fill))""",
            topic="Функциональное",
        ),
        live(
            "filter_none",
            "Функция compact(items: list[int | None]) -> list[int] удаляет None, сохраняя порядок.",
            """def compact(items: list[int | None]) -> list[int]:
    return [x for x in items if x is not None]""",
            topic="Функциональное",
        ),
        live(
            "closure counter factory",
            "Функция make_counter(start: int = 0) возвращает callable без аргументов, "
            "каждый вызов возвращает следующее int значение.",
            """from collections.abc import Callable


def make_counter(start: int = 0) -> Callable[[], int]:
    state = {'value': start}

    def next_value() -> int:
        current = state['value']
        state['value'] += 1
        return current
    return next_value""",
            topic="Функциональное",
        ),
        live(
            "decorator require_positive",
            "Декоратор @require_positive проверяет, что все int-позиционные аргументы > 0; "
            "иначе ValueError.",
            """from functools import wraps


def require_positive(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, int) and arg <= 0:
                raise ValueError('arguments must be positive')
        return fn(*args, **kwargs)
    return wrapper""",
            topic="Функциональное",
        ),
        live(
            "pipeline transform",
            "Функция pipeline(value: int, *funcs) последовательно применяет func(value) "
            "слева направо; funcs — Callable[[int], int].",
            """from collections.abc import Callable


def pipeline(value: int, *funcs: Callable[[int], int]) -> int:
    result = value
    for fn in funcs:
        result = fn(result)
    return result""",
            topic="Функциональное",
        ),
        live(
            "generator countdown",
            "Генератор countdown(n: int) yield'ит n, n-1, ..., 1. n < 1 -> пустой генератор.",
            """from collections.abc import Iterator


def countdown(n: int) -> Iterator[int]:
    while n >= 1:
        yield n
        n -= 1""",
            topic="Функциональное",
        ),
        live(
            "tee duplicate iter",
            "Функция split_iter(iterable) -> tuple[list[int], list[int]] материализует "
            "итератор в две независимые копии через itertools.tee.",
            """from itertools import tee


def split_iter(iterable) -> tuple[list[int], list[int]]:
    a, b = tee(iterable)
    return list(a), list(b)""",
            topic="Функциональное",
        ),
        live(
            "permutation count",
            "Функция count_permutations(items: list[int]) -> int — число перестановок "
            "без повторений через math.perm.",
            """from math import perm


def count_permutations(items: list[int]) -> int:
    return perm(len(items), len(items))""",
            topic="Функциональное",
        ),
        # --- Collections ---
        live(
            "OrderedDict LRU",
            "Класс SimpleLRU(maxsize: int) с get(key) -> int | None и put(key, value). "
            "При переполнении удаляйте самый старый ключ (OrderedDict).",
            """from collections import OrderedDict


class SimpleLRU:
    def __init__(self, maxsize: int) -> None:
        self.maxsize = maxsize
        self._data: OrderedDict[str, int] = OrderedDict()

    def get(self, key: str) -> int | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: int) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.maxsize:
            self._data.popitem(last=False)""",
            topic="Collections",
        ),
        live(
            "Counter letter freq",
            "Функция letter_freq(text: str) -> dict[str, int] считает частоту латинских букв "
            "(lower case) через Counter.",
            """from collections import Counter


def letter_freq(text: str) -> dict[str, int]:
    letters = [ch.lower() for ch in text if ch.isalpha()]
    return dict(Counter(letters))""",
            topic="Collections",
        ),
        live(
            "defaultdict nested",
            "Функция nested_default() -> defaultdict создаёт defaultdict, где отсутствующие "
            "ключи инициализируются пустым list.",
            """from collections import defaultdict


def nested_default() -> defaultdict[str, list[int]]:
    return defaultdict(list)""",
            topic="Collections",
        ),
        live(
            "deque maxlen",
            "Класс LastN хранит последние n int через deque(maxlen=n); метод add(x) и values() -> list[int].",
            """from collections import deque


class LastN:
    def __init__(self, n: int) -> None:
        self._items: deque[int] = deque(maxlen=n)

    def add(self, x: int) -> None:
        self._items.append(x)

    def values(self) -> list[int]:
        return list(self._items)""",
            topic="Collections",
        ),
        live(
            "ChainMap lookup",
            "Функция layered_get(maps: list[dict[str, int]], key: str) -> int | None "
            "ищет key в ChainMap слева направо.",
            """from collections import ChainMap


def layered_get(maps: list[dict[str, int]], key: str) -> int | None:
    chain = ChainMap(*maps)
    return chain.get(key)""",
            topic="Collections",
        ),
        live(
            "namedtuple parse coords",
            "NamedTuple Coord(x: int, y: int) и parse_coord(s: str) -> Coord для 'x,y'.",
            """from typing import NamedTuple


class Coord(NamedTuple):
    x: int
    y: int


def parse_coord(raw: str) -> Coord:
    x_str, y_str = raw.split(',', 1)
    return Coord(int(x_str.strip()), int(y_str.strip()))""",
            topic="Collections",
        ),
        live(
            "heapq merge sorted",
            "Функция merge_sorted(lists: list[list[int]]) -> list[int] через heapq.merge.",
            """import heapq


def merge_sorted(lists: list[list[int]]) -> list[int]:
    return list(heapq.merge(*lists))""",
            topic="Collections",
        ),
        live(
            "heapq top_k",
            "Функция top_k(numbers: list[int], k: int) -> list[int] — k наибольших "
            "элементов в порядке убывания (heapq.nlargest).",
            """import heapq


def top_k(numbers: list[int], k: int) -> list[int]:
    return heapq.nlargest(k, numbers)""",
            topic="Collections",
        ),
        live(
            "Counter subtract",
            "Функция bag_subtract(a: dict[str, int], b: dict[str, int]) -> dict[str, int] "
            "вычитает счётчики; отрицательные значения удаляются.",
            """from collections import Counter


def bag_subtract(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    result = Counter(a) - Counter(b)
    return {k: v for k, v in result.items() if v > 0}""",
            topic="Collections",
        ),
        live(
            "Counter normalize",
            "Функция normalize_counts(counts: dict[str, int]) -> dict[str, float] делит "
            "каждое значение на сумму всех (доли). Пустой dict -> {}.",
            """def normalize_counts(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in counts.items()}""",
            topic="Collections",
        ),
        live(
            "heap push pop",
            "Класс MinHeap с push(x: int) и pop() -> int (минимум). pop на пустой куче — IndexError.",
            """import heapq


class MinHeap:
    def __init__(self) -> None:
        self._data: list[int] = []

    def push(self, x: int) -> None:
        heapq.heappush(self._data, x)

    def pop(self) -> int:
        if not self._data:
            raise IndexError('pop from empty heap')
        return heapq.heappop(self._data)""",
            topic="Collections",
        ),
        live(
            "nested defaultdict tree",
            "Функция tree() возвращает defaultdict, создающий вложенные defaultdict(tree) "
            "для построения trie-подобной структуры dict.",
            """from collections import defaultdict


def tree():
    return defaultdict(tree)""",
            topic="Collections",
        ),
        live(
            "deque rotate bits",
            "Функция rotate_bits(value: int, width: int, k: int) -> int циклически сдвигает "
            "width-битное число влево на k (используйте deque над битами).",
            """from collections import deque


def rotate_bits(value: int, width: int, k: int) -> int:
    bits = deque(format(value & ((1 << width) - 1), f'0{width}b'))
    bits.rotate(-k % width)
    return int(''.join(bits), 2)""",
            topic="Collections",
        ),
        # --- Stdlib ---
        live(
            "pathlib read text",
            "Функция read_text_file(path: str) -> str читает UTF-8 текст через pathlib.Path.read_text.",
            """from pathlib import Path


def read_text_file(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')""",
            topic="Stdlib",
        ),
        live(
            "pathlib ensure dir",
            "Функция ensure_dir(path: str) -> Path создаёт каталог и родителей (mkdir parents=True, exist_ok=True).",
            """from pathlib import Path


def ensure_dir(path: str) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target""",
            topic="Stdlib",
        ),
        live(
            "pathlib find files",
            "Функция find_by_suffix(root: str, suffix: str) -> list[str] рекурсивно ищет "
            "файлы с suffix через Path.rglob; вернуть отсортированные строковые пути.",
            """from pathlib import Path


def find_by_suffix(root: str, suffix: str) -> list[str]:
    return sorted(str(p) for p in Path(root).rglob(f'*{suffix}'))""",
            topic="Stdlib",
        ),
        live(
            "json dump pretty",
            "Функция write_json(path: str, data: dict) -> None записывает JSON с indent=2 и ensure_ascii=False.",
            """import json
from pathlib import Path


def write_json(path: str, data: dict) -> None:
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + '\\n',
        encoding='utf-8',
    )""",
            topic="Stdlib",
        ),
        live(
            "csv write rows",
            "Функция write_csv(path: str, rows: list[list[str]]) -> None пишет CSV через "
            "csv.writer с newline=''.",
            """import csv


def write_csv(path: str, rows: list[list[str]]) -> None:
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)""",
            topic="Stdlib",
        ),
        live(
            "csv read dict",
            "Функция read_csv_dicts(path: str) -> list[dict[str, str]] читает CSV с заголовком "
            "через csv.DictReader.",
            """import csv


def read_csv_dicts(path: str) -> list[dict[str, str]]:
    with open(path, encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))""",
            topic="Stdlib",
        ),
        live(
            "sqlite insert row",
            "Функция insert_user(conn, name: str) -> int вставляет строку в users(name) "
            "и возвращает lastrowid.",
            """def insert_user(conn, name: str) -> int:
    cur = conn.execute('INSERT INTO users (name) VALUES (?)', (name,))
    conn.commit()
    return int(cur.lastrowid)""",
            topic="Stdlib",
        ),
        live(
            "sqlite create table",
            "Функция init_db(conn) -> None создаёт таблицу notes(id INTEGER PRIMARY KEY, text TEXT) "
            "если её нет.",
            """def init_db(conn) -> None:
    conn.execute(
        'CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)'
    )
    conn.commit()""",
            topic="Stdlib",
        ),
        live(
            "sqlite fetch all",
            "Функция fetch_all_names(conn) -> list[str] выполняет SELECT name FROM users "
            "ORDER BY name и возвращает список имён.",
            """def fetch_all_names(conn) -> list[str]:
    rows = conn.execute('SELECT name FROM users ORDER BY name').fetchall()
    return [row[0] for row in rows]""",
            topic="Stdlib",
        ),
        live(
            "argparse verbose flag",
            "Функция build_parser() -> ArgumentParser с флагом --verbose (store_true) "
            "и позиционным filename.",
            """import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('--verbose', action='store_true')
    return parser""",
            topic="Stdlib",
        ),
        live(
            "argparse subcommands",
            "Функция build_cli() -> ArgumentParser с subparsers: команда 'sum' с nargs='+' "
            "int аргументами.",
            """import argparse


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sum_cmd = sub.add_parser('sum')
    sum_cmd.add_argument('numbers', nargs='+', type=int)
    return parser""",
            topic="Stdlib",
        ),
        live(
            "tempfile directory",
            "Функция temp_workspace() -> Path создаёт TemporaryDirectory и возвращает Path "
            "к нему (каталог живёт до gc/явного cleanup — верните Path и сохраните ссылку на объект).",
            """from pathlib import Path
import tempfile


def temp_workspace() -> tuple[Path, tempfile.TemporaryDirectory[str]]:
    tmp = tempfile.TemporaryDirectory()
    return Path(tmp.name), tmp""",
            topic="Stdlib",
        ),
        live(
            "re extract digits",
            "Функция extract_digits(text: str) -> list[int] находит все целые числа "
            "в строке через re.findall.",
            """import re


def extract_digits(text: str) -> list[int]:
    return [int(match) for match in re.findall(r'\\d+', text)]""",
            topic="Stdlib",
        ),
        live(
            "re normalize spaces",
            "Функция normalize_spaces(text: str) -> str заменяет последовательности "
            "пробельных символов одним пробелом и обрезает края (re.sub).",
            """import re


def normalize_spaces(text: str) -> str:
    return re.sub(r'\\s+', ' ', text).strip()""",
            topic="Stdlib",
        ),
        live(
            "hashlib sha256 hex",
            "Функция sha256_hex(data: str) -> str возвращает SHA-256 hexdigest для UTF-8 строки.",
            """import hashlib


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()""",
            topic="Stdlib",
        ),
        live(
            "base64 encode decode",
            "Функции b64_encode(text: str) -> str и b64_decode(raw: str) -> str через base64 "
            "для UTF-8 строк.",
            """import base64


def b64_encode(text: str) -> str:
    return base64.b64encode(text.encode('utf-8')).decode('ascii')


def b64_decode(raw: str) -> str:
    return base64.b64decode(raw.encode('ascii')).decode('utf-8')""",
            topic="Stdlib",
        ),
        live(
            "urllib parse query",
            "Функция parse_query(url: str) -> dict[str, list[str]] парсит query string "
            "через urllib.parse.parse_qs.",
            """from urllib.parse import parse_qs, urlparse


def parse_query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)""",
            topic="Stdlib",
        ),
        live(
            "datetime parse iso",
            "Функция parse_iso_date(raw: str) -> str возвращает дату YYYY-MM-DD из ISO строки "
            "datetime.fromisoformat.",
            """from datetime import datetime


def parse_iso_date(raw: str) -> str:
    return datetime.fromisoformat(raw).date().isoformat()""",
            topic="Stdlib",
        ),
        live(
            "HTTP stub client",
            "Dataclass HttpRequest(method: str, url: str) и класс StubClient с get(url) -> HttpResponse "
            "(dataclass status=200, body='OK'). Без реального HTTP.",
            """from dataclasses import dataclass


@dataclass
class HttpRequest:
    method: str
    url: str


@dataclass
class HttpResponse:
    status: int
    body: str


class StubClient:
    def get(self, url: str) -> HttpResponse:
        return HttpResponse(status=200, body='OK')""",
            topic="Stdlib",
        ),
        live(
            "unittest assert raises",
            "Функция parse_positive(raw: str) -> int бросает ValueError для неположительных "
            "и нечисловых значений. Напишите parse_positive и helper assert_raises_value_error "
            "используя pytest-style try/except (без import pytest).",
            """def parse_positive(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise ValueError('must be positive')
    return value


def assert_raises_value_error(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False""",
            topic="Stdlib",
            requirements=["parse_positive и assert_raises_value_error в одном модуле"],
        ),
        live(
            "logging basic config",
            "Функция setup_logging(level: str = 'INFO') -> None вызывает logging.basicConfig "
            "с format='%(levelname)s:%(message)s'.",
            """import logging


def setup_logging(level: str = 'INFO') -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format='%(levelname)s:%(message)s')""",
            topic="Stdlib",
        ),
        live(
            "configparser read",
            "Функция read_setting(text: str, section: str, option: str) -> str | None "
            "парсит ini из строки через configparser.",
            """import configparser
from io import StringIO


def read_setting(text: str, section: str, option: str) -> str | None:
    parser = configparser.ConfigParser()
    parser.read_file(StringIO(text))
    if parser.has_option(section, option):
        return parser.get(section, option)
    return None""",
            topic="Stdlib",
        ),
        live(
            "copy deep nested",
            "Функция clone(data: dict) -> dict возвращает глубокую копию вложенного dict "
            "через copy.deepcopy.",
            """import copy


def clone(data: dict) -> dict:
    return copy.deepcopy(data)""",
            topic="Stdlib",
        ),
        live(
            "read_lines_strip",
            "Функция read_lines_strip(path: str) -> list[str] читает UTF-8 файл построчно "
            "и возвращает строки без trailing \\n и пробелов по краям.",
            """def read_lines_strip(path: str) -> list[str]:
    with open(path, encoding='utf-8') as fh:
        return [line.strip() for line in fh]""",
            topic="Stdlib",
        ),
        # --- Typing ---
        live(
            "TypeVar generic stack",
            "Generic класс TypedStack[T] с push(item: T) и pop() -> T. Пустой pop -> IndexError.",
            """from typing import Generic, TypeVar

T = TypeVar('T')


class TypedStack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError('empty stack')
        return self._items.pop()""",
            topic="Typing",
        ),
        live(
            "Literal method",
            "TypedDict Config с mode: Literal['dev', 'prod']. Функция is_prod(cfg: Config) -> bool.",
            """from typing import Literal, TypedDict


class Config(TypedDict):
    mode: Literal['dev', 'prod']


def is_prod(cfg: Config) -> bool:
    return cfg['mode'] == 'prod'""",
            topic="Typing",
        ),
        live(
            "Union coerce",
            "Функция coerce_number(value: int | float | str) -> float принимает int, float "
            "или str и возвращает float.",
            """def coerce_number(value: int | float | str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(value.strip())""",
            topic="Typing",
        ),
        live(
            "Optional default",
            "Функция greet_optional(name: str | None = None) -> str: None или '' -> 'Hello, guest!', "
            "иначе f'Hello, {name}!'.",
            """def greet_optional(name: str | None = None) -> str:
    if not name:
        return 'Hello, guest!'
    return f'Hello, {name}!'""",
            topic="Typing",
        ),
        live(
            "Callable filter",
            "Функция apply_if(value: int, pred: Callable[[int], bool], fn: Callable[[int], int]) -> int "
            "возвращает fn(value) если pred(value) else value.",
            """from collections.abc import Callable


def apply_if(
    value: int,
    pred: Callable[[int], bool],
    fn: Callable[[int], int],
) -> int:
    return fn(value) if pred(value) else value""",
            topic="Typing",
        ),
        live(
            "Generic Repository",
            "Generic класс Repository[T] с private list _items, add(item: T), all() -> list[T].",
            """from typing import Generic, TypeVar

T = TypeVar('T')


class Repository(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def add(self, item: T) -> None:
        self._items.append(item)

    def all(self) -> list[T]:
        return list(self._items)""",
            topic="Typing",
        ),
        live(
            "cast helper",
            "Функция as_str(value: object) -> str использует typing.cast для str после "
            "проверки isinstance.",
            """from typing import cast


def as_str(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError('expected str')
    return cast(str, value)""",
            topic="Typing",
        ),
        live(
            "overload parse",
            "Функция parse(raw: str) -> int и parse(raw: bytes) -> int с @overload; "
            "реализация принимает str | bytes.",
            """from typing import overload


@overload
def parse(raw: str) -> int: ...


@overload
def parse(raw: bytes) -> int: ...


def parse(raw: str | bytes) -> int:
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return int(raw.strip())""",
            topic="Typing",
        ),
        live(
            "Final constant",
            "Модуль с Final константой MAX_RETRIES: Final[int] = 3 и функцией attempts() -> int "
            "возвращающей MAX_RETRIES.",
            """from typing import Final

MAX_RETRIES: Final[int] = 3


def attempts() -> int:
    return MAX_RETRIES""",
            topic="Typing",
        ),
        live(
            "Annotated validator",
            "Type alias PositiveInt = Annotated[int, 'positive'] и функция ensure_positive(n: int) -> PositiveInt "
            "бросающая ValueError если n <= 0.",
            """from typing import Annotated

PositiveInt = Annotated[int, 'positive']


def ensure_positive(n: int) -> PositiveInt:
    if n <= 0:
        raise ValueError('must be positive')
    return n""",
            topic="Typing",
        ),
        live(
            "Protocol SupportsLen",
            "Protocol SupportsLen с __len__ -> int. Функция total_len(items: list[SupportsLen]) -> int "
            "суммирует len каждого элемента.",
            """from typing import Protocol


class SupportsLen(Protocol):
    def __len__(self) -> int: ...


def total_len(items: list[SupportsLen]) -> int:
    return sum(len(item) for item in items)""",
            topic="Typing",
        ),
        live(
            "TypedDict total",
            "TypedDict ProductRow с total=False: id обязателен, name опционален. "
            "Функция row_id(row: ProductRow) -> int.",
            """from typing import TypedDict


class ProductRow(TypedDict, total=False):
    id: int
    name: str


def row_id(row: ProductRow) -> int:
    return row['id']""",
            topic="Typing",
        ),
        # --- Async ---
        live(
            "async gather urls",
            "async def fetch_one(url: str) -> str возвращает url после await asyncio.sleep(0). "
            "async def fetch_all(urls: list[str]) -> list[str] через asyncio.gather.",
            """import asyncio


async def fetch_one(url: str) -> str:
    await asyncio.sleep(0)
    return url


async def fetch_all(urls: list[str]) -> list[str]:
    return list(await asyncio.gather(*(fetch_one(u) for u in urls)))""",
            topic="Async",
        ),
        live(
            "async timeout wrapper",
            "async def with_timeout(coro, seconds: float): оборачивает coroutine в "
            "asyncio.wait_for; TimeoutError -> None.",
            """import asyncio


async def with_timeout(coro, seconds: float):
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        return None""",
            topic="Async",
        ),
        live(
            "async queue worker",
            "async def worker(queue: asyncio.Queue[int], results: list[int]) -> None: "
            "while True: item = await queue.get(); если item is None — break; results.append(item * 2); queue.task_done().",
            """import asyncio


async def worker(queue: asyncio.Queue[int | None], results: list[int]) -> None:
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        results.append(item * 2)
        queue.task_done()""",
            topic="Async",
        ),
        live(
            "async lock counter",
            "Класс AsyncCounter с async increment(): используйте asyncio.Lock для "
            "безопасного увеличения self.value.",
            """import asyncio


class AsyncCounter:
    def __init__(self) -> None:
        self.value = 0
        self._lock = asyncio.Lock()

    async def increment(self) -> int:
        async with self._lock:
            self.value += 1
            return self.value""",
            topic="Async",
        ),
        live(
            "async sleep batch",
            "async def staggered(n: int) -> list[int] await'ит sleep(0) n раз и "
            "возвращает [0, 1, ..., n-1].",
            """import asyncio


async def staggered(n: int) -> list[int]:
    result: list[int] = []
    for i in range(n):
        await asyncio.sleep(0)
        result.append(i)
    return result""",
            topic="Async",
        ),
        live(
            "async generator range",
            "async def async_range(n: int) async-generates 0..n-1 с await asyncio.sleep(0) на шаг.",
            """import asyncio
from collections.abc import AsyncIterator


async def async_range(n: int) -> AsyncIterator[int]:
    for i in range(n):
        await asyncio.sleep(0)
        yield i""",
            topic="Async",
        ),
        live(
            "async context manager",
            "Класс async_timer с async __aenter__/__aexit__; __aenter__ записывает start, "
            "__aexit__ печатает elapsed (perf_counter).",
            """import asyncio
import time


class async_timer:
    async def __aenter__(self):
        self.start = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await asyncio.sleep(0)
        print(time.perf_counter() - self.start)""",
            topic="Async",
        ),
        live(
            "async semaphore limit",
            "async def run_limited(tasks: list, limit: int) -> list через Semaphore(limit) "
            "и gather; каждая задача await sleep(0) и возвращает свой индекс.",
            """import asyncio


async def run_limited(n: int, limit: int) -> list[int]:
    sem = asyncio.Semaphore(limit)
    results: list[int] = []

    async def one(i: int) -> None:
        async with sem:
            await asyncio.sleep(0)
            results.append(i)

    await asyncio.gather(*(one(i) for i in range(n)))
    return sorted(results)""",
            topic="Async",
        ),
        live(
            "async create task",
            "async def spawn_double(n: int) -> int создаёт asyncio.create_task для "
            "double(n) и await'ит результат. double await sleep(0) и return n * 2.",
            """import asyncio


async def double(n: int) -> int:
    await asyncio.sleep(0)
    return n * 2


async def spawn_double(n: int) -> int:
    task = asyncio.create_task(double(n))
    return await task""",
            topic="Async",
        ),
        live(
            "async event wait",
            "Класс AsyncGate с async wait_until_open(): ждёт asyncio.Event; метод open() "
            "устанавливает event.",
            """import asyncio


class AsyncGate:
    def __init__(self) -> None:
        self._event = asyncio.Event()

    def open(self) -> None:
        self._event.set()

    async def wait_until_open(self) -> None:
        await self._event.wait()""",
            topic="Async",
        ),
        live(
            "Custom exception chain",
            "Класс AppError(Exception) и функция load_config(raw: str) -> dict: "
            "JSONDecodeError оборачивается в AppError с сообщением 'invalid config'.",
            """import json


class AppError(Exception):
    pass


def load_config(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AppError('invalid config') from exc
    if not isinstance(data, dict):
        raise AppError('invalid config')
    return data""",
            topic="Основы",
            requirements=["Использовать raise ... from exc", "AppError при не-dict JSON"],
        ),
        live(
            "dataclass frozen",
            "Frozen dataclass Settings(debug: bool, port: int) и функция as_tuple(s: Settings) -> tuple[bool, int].",
            """from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    debug: bool
    port: int


def as_tuple(s: Settings) -> tuple[bool, int]:
    return s.debug, s.port""",
            topic="ООП",
        ),
        live(
            "slots frozen point",
            "Класс ImmutablePoint с __slots__ = ('x', 'y'), без __dict__. x, y — int; "
            "метод distance_sq() -> int возвращает x*x + y*y.",
            """class ImmutablePoint:
    __slots__ = ('x', 'y')

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def distance_sq(self) -> int:
        return self.x * self.x + self.y * self.y""",
            topic="ООП",
        ),
        live(
            "doctest add",
            "Функция add(a: int, b: int) -> int с docstring содержащим doctest примеры "
            ">>> add(2, 3)\\n5. Реализуйте add корректно.",
            """def add(a: int, b: int) -> int:
    \"\"\"Add two integers.

    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    \"\"\"
    return a + b""",
            topic="Stdlib",
        ),
        live(
            "mock patch stub",
            "Функция current_time() -> float импортирует time.perf_counter. "
            "Напишите fake_clock(fixed: float) -> context manager, подменяющий perf_counter "
            "на lambda: fixed (unittest.mock.patch).",
            """import time
from contextlib import contextmanager
from unittest.mock import patch


def current_time() -> float:
    return time.perf_counter()


@contextmanager
def fake_clock(fixed: float):
    with patch('time.perf_counter', return_value=fixed):
        yield""",
            topic="Stdlib",
        ),
        live(
            "email parse address",
            "Функция split_email(email: str) -> tuple[str, str] возвращает local, domain "
            "через email.utils.parseaddr не требуется — split по @ достаточно с валидацией.",
            """def split_email(email: str) -> tuple[str, str]:
    if email.count('@') != 1:
        raise ValueError('invalid email')
    local, domain = email.split('@')
    if not local or not domain:
        raise ValueError('invalid email')
    return local, domain""",
            topic="Stdlib",
        ),
        live(
            "selection sort",
            "Функция selection_sort(items: list[int]) -> list[int] — сортировка выбором "
            "на копии списка.",
            """def selection_sort(items: list[int]) -> list[int]:
    arr = items.copy()
    for i in range(len(arr)):
        min_idx = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr""",
            topic="Основы",
        ),
        live(
            "merge sorted lists",
            "Функция merge_two(a: list[int], b: list[int]) -> list[int] сливает два "
            "отсортированных списка в один отсортированный за O(n+m).",
            """def merge_two(a: list[int], b: list[int]) -> list[int]:
    i = j = 0
    result: list[int] = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result""",
            topic="Основы",
        ),
        live(
            "sliding window max",
            "Функция max_sum_window(numbers: list[int], k: int) -> int — максимальная сумма "
            "окна длины k. k <= 0 или len < k -> 0.",
            """def max_sum_window(numbers: list[int], k: int) -> int:
    if k <= 0 or len(numbers) < k:
        return 0
    window = sum(numbers[:k])
    best = window
    for i in range(k, len(numbers)):
        window += numbers[i] - numbers[i - k]
        best = max(best, window)
    return best""",
            topic="Основы",
        ),
        live(
            "graph bfs dist",
            "Функция bfs_dist(graph: dict[int, list[int]], start: int, target: int) -> int | None — "
            "кратчайшее число рёбер в невзвешенном графе; нет пути -> None.",
            """from collections import deque


def bfs_dist(graph: dict[int, list[int]], start: int, target: int) -> int | None:
    if start == target:
        return 0
    seen = {start}
    queue: deque[tuple[int, int]] = deque([(start, 0)])
    while queue:
        node, dist = queue.popleft()
        for nxt in graph.get(node, []):
            if nxt in seen:
                continue
            if nxt == target:
                return dist + 1
            seen.add(nxt)
            queue.append((nxt, dist + 1))
    return None""",
            topic="Основы",
        ),
    ]
