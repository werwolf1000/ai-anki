#!/usr/bin/env python3
"""Generate Python fundamentals deck with 500+ cards (theory + code)."""
from __future__ import annotations

import json
from pathlib import Path


def theory(q: str, ref: str) -> dict:
    return {"question": q, "reference": ref}


def code(q: str, task: str, snippet: str, ref: str) -> dict:
    return {
        "card_type": "code",
        "question": q,
        "task": task,
        "code": snippet.strip(),
        "reference": ref.strip(),
    }


def build_cards() -> list[dict]:
    cards: list[dict] = []

    basics = [
        theory("Что такое интерпретируемый язык?", "Python выполняется интерпретатором (CPython): код компилируется в bytecode и исполняется построчно/по объектам."),
        theory("Чем list отличается от tuple?", "list — изменяемый (mutable), tuple — неизменяемый (immutable). tuple часто для фиксированных наборов и ключей dict."),
        theory("Чем dict отличается от set?", "dict хранит пары ключ-значение; set — уникальные хешируемые элементы без порядка (до 3.7) / с insertion order как dict с 3.7+."),
        theory("Что такое PEP 8?", "Официальный стиль кода Python: отступы 4 пробела, snake_case для функций/переменных, PascalCase для классов."),
        theory("Что делает оператор //?", "Целочисленное деление: 7 // 2 == 3."),
        theory("Что делает оператор **?", "Возведение в степень: 2 ** 3 == 8."),
        theory("Что такое truthy и falsy?", "Falsy: False, None, 0, '', [], {}, set(). Остальное в bool() — True."),
        theory("Чем is отличается от ==?", "is сравнивает identity (один объект в памяти); == — equality по __eq__."),
        theory("Что такое None?", "Singleton «отсутствие значения». Часто default и маркер optional."),
        theory("Что такое id()?", "Уникальный идентификатор объекта в CPython (адрес), пока объект жив."),
        theory("Что такое mutable default argument trap?", "def f(x=[]): — один список на все вызовы. Использовать x=None и создавать внутри."),
        theory("Что такое LEGB для имён?", "Local → Enclosing → Global → Built-in — порядок поиска переменных."),
        theory("Что такое __name__ == '__main__'?", "Блок выполняется только при прямом запуске файла, не при import."),
        theory("Чем import module от import from?", "import math — math.sqrt; from math import sqrt — sqrt в namespace."),
        theory("Что такое virtual environment (venv)?", "Изолированный Python + pip пакеты для проекта без конфликтов с системой."),
        theory("Что такое pip?", "Менеджер пакетов PyPI: pip install requests."),
        theory("Что такое REPL?", "Read-Eval-Print Loop — интерактивный python в терминале."),
        theory("Что такое indentation в Python?", "Отступы определяют блоки кода вместо фигурных скобок."),
        theory("Что такое pass?", "Заглушка — ничего не делает, placeholder для пустого блока."),
        theory("Что такое del?", "Удаляет ссылку на имя; объект удалится GC когда refcount=0."),
        theory("Что такое slice?", "a[start:stop:step] — срез последовательности, stop не включается."),
        theory("Отрицательный индекс?", "a[-1] — последний элемент."),
        theory("Что такое unpacking?", "a, b = (1, 2); *rest, last = [1,2,3,4] — распаковка."),
        theory("Что такое walrus operator := ?", "Присваивание в выражении: if (n := len(data)) > 10: ... (Python 3.8+)."),
        theory("Что такое match/case?", "Structural pattern matching Python 3.10+: match value: case pattern: ..."),
        theory("Что такое f-string?", "f'Hello {name}' — форматирование строк, выражения в {}."),
        theory("Что такое docstring?", 'Строка сразу после def/class — __doc__, help(). Тройные кавычки.'),
        theory("Что такое type hints?", "Аннотации def foo(x: int) -> str — для статического анализа, не enforced runtime."),
        theory("Что такое __init__?", "Конструктор экземпляра класса, вызывается после __new__."),
        theory("Что такое self?", "Ссылка на текущий экземпляр в методах класса."),
        theory("Что такое @staticmethod?", "Метод без self/cls — обычная функция в namespace класса."),
        theory("Что такое @classmethod?", "Первый аргумент cls — альтернативные конструкторы, доступ к классу."),
        theory("Что такое @property?", "Геттер как атрибут: obj.x вместо obj.get_x()."),
        theory("Что такое наследование?", "class Child(Parent): — переиспользование и расширение поведения."),
        theory("MRO — что это?", "Method Resolution Order — порядок поиска методов при множественном наследовании (C3)."),
        theory("Что такое super()?", "Вызов метода родителя в наследнике с корректным MRO."),
        theory("Что такое dunder __str__ vs __repr__?", "__str__ — для пользователя; __repr__ — од однозначное repr для отладки."),
        theory("Что такое __eq__?", "Определяет поведение == для объектов."),
        theory("Что такое __hash__?", "Нужен для set/dict keys; если __eq__ — immutable objects должны иметь согласованный hash."),
        theory("Что такое исключение?", "Механизм ошибок: try/except/finally/else. raise ValueError('msg')."),
        theory("Что такое finally?", "Выполняется всегда — cleanup ресурсов."),
        theory("else в try?", "Выполняется если try завершился без except."),
        theory("Что такое generator?", "Функция с yield — ленивая итерация, сохраняет state между вызовами."),
        theory("yield from?", "Делегирование другому generator/iterable."),
        theory("Что такое iterator?", "Объект с __iter__ и __next__; StopIteration в конце."),
        theory("Что такое iterable?", "Объект с __iter__ — list, str, dict keys, generator."),
        theory("Что такое decorator?", "@decorator над функцией — wrapper, часто functools.wraps."),
        theory("Что такое closure?", "Внутренняя функция захватывает переменные enclosing scope."),
        theory("nonlocal vs global?", "nonlocal — изменить переменную enclosing; global — модульная."),
        theory("Что такое context manager?", "with open(...) as f: — __enter__/__exit__ или @contextmanager."),
        theory("Что такое list comprehension?", "[x*2 for x in range(10) if x % 2] — компактное создание списка."),
        theory("dict comprehension?", "{k: v for k, v in pairs}."),
        theory("set comprehension?", "{x for x in items}."),
        theory("Что такое lambda?", "Анонимная однострочная функция: lambda x: x*2."),
        theory("map/filter/zip?", "map(fn, iter), filter(pred, iter), zip(a,b) — итераторы; часто заменяются comprehensions."),
        theory("enumerate?", "for i, val in enumerate(items): — индекс + значение."),
        theory("range?", "range(stop) или range(start, stop, step) — lazy последовательность int."),
        theory("sorted vs list.sort?", "sorted возвращает новый list; .sort() in-place."),
        theory("copy vs deepcopy?", "copy.copy — shallow; copy.deepcopy — рекурсивная копия вложенных mutable."),
        theory("defaultdict?", "collections.defaultdict(factory) — auto default для missing keys."),
        theory("Counter?", "collections.Counter — подсчёт элементов, most_common()."),
        theory("namedtuple?", "collections.namedtuple — tuple с именованными полями."),
        theory("deque?", "collections.deque — быстрые append/pop с обоих концов."),
        theory("dataclass?", "@dataclass — автогенерация __init__, __repr__, сравнений."),
        theory("Enum?", "enum.Enum — именованные константы class Color(Enum): RED=1."),
        theory("pathlib Path?", "OOP пути: Path('a/b') / 'c.txt', .read_text(), .exists()."),
        theory("json.loads/dumps?", "Сериализация JSON; default=str для non-serializable."),
        theory("datetime vs date?", "datetime — дата+время; date — только дата; timezone-aware vs naive."),
        theory("logging vs print?", "logging — уровни, handlers, production; print — отладка."),
        theory("unittest vs pytest?", "unittest — stdlib; pytest — fixtures, parametrize, популярнее."),
        theory("Что такое GIL?", "Global Interpreter Lock — один поток bytecode в CPython; CPU-bound threading ограничен."),
        theory("threading vs multiprocessing?", "threading — I/O bound shared memory; multiprocessing — CPU bound отдельные процессы."),
        theory("asyncio?", "async/await cooperative concurrency для I/O; event loop."),
        theory("async def?", "Корутина — await на awaitable; asyncio.run(main())."),
        theory("__all__?", "Список public API при from module import *."),
        theory("__slots__?", "Ограничение атрибутов экземпляра — экономия памяти, фиксированные поля."),
        theory("ABC abstractmethod?", "abc.ABC + @abstractmethod — интерфейс с обязательной реализацией."),
        theory("Protocol typing?", "Structural subtyping — typing.Protocol для duck typing статически."),
        theory("Optional и Union?", "Optional[T] == Union[T, None]; Union[int, str] — несколько типов."),
        theory("list vs List typing?", "list[int] Python 3.9+; раньше List[int] from typing."),
        theory("TypeVar generics?", "T = TypeVar('T') для generic функций/классов."),
        theory("isinstance vs type?", "isinstance учитывает наследование; type(x) is int — exact type."),
        theory("getattr/setattr/hasattr?", "Динамический доступ к атрибутам по строковому имени."),
        theory("callable?", "callable(x) — можно ли вызвать x()."),
        theory("any/all?", "any(iter) — хотя бы один True; all(iter) — все True."),
        theory("min/max/sum?", "Агрегации; key= для custom compare."),
        theory("re module?", "regex: re.search, re.match, re.sub, raw strings r'\\d+'."),
        theory("os vs sys?", "os — файловая система, env; sys — interpreter argv, path, exit."),
        theory("subprocess?", "Запуск внешних команд без shell когда возможно."),
        theory("pickle?", "Сериализация Python objects — не безопасно для untrusted data."),
        theory("with open encoding?", "open(path, encoding='utf-8') — явная кодировка текстовых файлов."),
        theory("if __name__ guard зачем?", "Разделение importable module и script entry point."),
    ]
    cards.extend(basics)

    code_cards = [
        code(
            "Mutable default argument.",
            "Исправь — каждый вызов должен получать новый пустой список.",
            """def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket""",
            """def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket""",
        ),
        code(
            "IndexError при доступе к списку.",
            "Безопасно получи последний элемент или None.",
            """items = []
last = items[-1]""",
            """items = []
last = items[-1] if items else None
# или: last = next(iter(reversed(items)), None)""",
        ),
        code(
            "Сравнение строк и чисел.",
            "Исправь проверку возраста — age приходит строкой из input.",
            """age = input('Age: ')
if age >= 18:
    print('adult')""",
            """age = int(input('Age: '))
if age >= 18:
    print('adult')""",
        ),
        code(
            "Копирование вложенного списка.",
            "Исправь — изменение b не должно менять a.",
            """import copy
a = [[1], [2]]
b = copy.copy(a)
b[0].append(99)
# a тоже изменился""",
            """import copy
a = [[1], [2]]
b = copy.deepcopy(a)
b[0].append(99)""",
        ),
        code(
            "File not closed.",
            "Перепиши с context manager.",
            """f = open('data.txt')
data = f.read()
f.close()""",
            """with open('data.txt', encoding='utf-8') as f:
    data = f.read()""",
        ),
        code(
            "KeyError в dict.",
            "Получи значение с default без исключения.",
            """user = {'name': 'Ann'}
email = user['email']""",
            """email = user.get('email')
# или user.get('email', '')""",
        ),
        code(
            "Set unique wrong way.",
            "Оставь уникальные слова, сохранив порядок (Py3.7+ dict).",
            """words = ['a', 'b', 'a', 'c']
unique = list(set(words))""",
            """unique = list(dict.fromkeys(words))""",
        ),
        code(
            "Range off-by-one.",
            "Сгенерируй числа 1..10 включительно.",
            """nums = list(range(1, 10))
print(nums)""",
            """nums = list(range(1, 11))""",
        ),
        code(
            "String concatenation in loop.",
            "Эффективно собери строки.",
            """parts = ['a', 'b', 'c']
result = ''
for p in parts:
    result += p""",
            """result = ''.join(parts)""",
        ),
        code(
            "Exception too broad.",
            "Лови конкретное исключение и пробрасывай дальше при необходимости.",
            """try:
    value = int(text)
except:
    value = 0""",
            """try:
    value = int(text)
except ValueError:
    value = 0""",
        ),
        code(
            "Class attribute shared.",
            "Исправь — у каждого User свой список tags.",
            """class User:
    tags = []

    def add_tag(self, tag):
        self.tags.append(tag)""",
            """class User:
    def __init__(self):
        self.tags = []

    def add_tag(self, tag):
        self.tags.append(tag)""",
        ),
        code(
            "Missing return self in fluent API.",
            "Добавь return self в setter.",
            """class Query:
    def filter(self, **kwargs):
        self._filters.update(kwargs)

    def limit(self, n):
        self._limit = n
        return self""",
            """class Query:
    def filter(self, **kwargs):
        self._filters.update(kwargs)
        return self""",
        ),
        code(
            "Generator never yields.",
            "Допиши yield для чтения файла построчно.",
            """def read_lines(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            pass""",
            """def read_lines(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            yield line.rstrip('\\n')""",
        ),
        code(
            "Decorator loses metadata.",
            "Используй wraps.",
            """def logged(fn):
    def wrapper(*args, **kwargs):
        print('call', fn.__name__)
        return fn(*args, **kwargs)
    return wrapper""",
            """from functools import wraps

def logged(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print('call', fn.__name__)
        return fn(*args, **kwargs)
    return wrapper""",
        ),
        code(
            "List comprehension syntax.",
            "Квадраты чётных чисел 0..8.",
            """# result = ...""",
            """result = [x * x for x in range(10) if x % 2 == 0]""",
        ),
        code(
            "Dict merge Python 3.9+.",
            "Объедини defaults и overrides.",
            """defaults = {'a': 1, 'b': 2}
overrides = {'b': 99}
# merged =""",
            """merged = defaults | overrides
# или {**defaults, **overrides}""",
        ),
        code(
            "Enum comparison.",
            "Сравни статус с enum, не со строкой.",
            """from enum import Enum

class Status(Enum):
    ACTIVE = 'active'

if status == 'active':
    ...""",
            """if status == Status.ACTIVE:
    ...
# или status is Status.ACTIVE""",
        ),
        code(
            "Pathlib join.",
            "Собери путь config/settings.json от base.",
            """import os
base = '/var/app'
path = os.path.join(base, 'config', 'settings.json')""",
            """from pathlib import Path
path = Path('/var/app') / 'config' / 'settings.json'""",
        ),
        code(
            "JSON load file.",
            "Загрузи JSON с обработкой ошибок.",
            """import json
data = json.load(open('cfg.json'))""",
            """import json
from pathlib import Path

with Path('cfg.json').open(encoding='utf-8') as f:
    data = json.load(f)""",
        ),
        code(
            "Dataclass defaults.",
            "Исправь mutable default в dataclass.",
            """from dataclasses import dataclass

@dataclass
class Bag:
    items: list = []""",
            """from dataclasses import dataclass, field

@dataclass
class Bag:
    items: list = field(default_factory=list)""",
        ),
        code(
            "Type hint optional.",
            "Аннотируй name как optional str.",
            """def greet(name):
    return f'Hi {name or \"guest\"}'""",
            """def greet(name: str | None) -> str:
    return f'Hi {name or \"guest\"}'""",
        ),
        code(
            "Walrus in while.",
            "Прочитай строки пока не пустая (:=).",
            """while True:
    line = input()
    if line == '':
        break
    process(line)""",
            """while (line := input()) != '':
    process(line)""",
        ),
        code(
            "Match case 3.10.",
            "Перепиши if/elif chain на match по команде.",
            """cmd = 'quit'
if cmd == 'quit':
    stop()
elif cmd == 'save':
    save()
else:
    unknown()""",
            """match cmd:
    case 'quit':
        stop()
    case 'save':
        save()
    case _:
        unknown()""",
        ),
        code(
            "async await missing.",
            "Допиши await для fetch.",
            """import asyncio

async def main():
    data = fetch_url('https://example.com')
    print(data)

asyncio.run(main())""",
            """async def main():
    data = await fetch_url('https://example.com')
    print(data)""",
        ),
        code(
            "Sorting custom key.",
            "Отсортируй users по len(name).",
            """users = [{'name': 'bob'}, {'name': 'ann'}]
users.sort()""",
            """users.sort(key=lambda u: len(u['name']))""",
        ),
        code(
            "Counter most common.",
            "Топ-3 слова по частоте.",
            """from collections import Counter
words = ['a', 'b', 'a', 'c', 'a', 'b']
# top =""",
            """top = Counter(words).most_common(3)""",
        ),
        code(
            "is vs == None.",
            "Исправь проверку на None.",
            """if value == None:
    ...""",
            """if value is None:
    ...""",
        ),
        code(
            "Remove item while iterating.",
            "Безопасно убери нули из списка.",
            """nums = [1, 0, 2, 0, 3]
for n in nums:
    if n == 0:
        nums.remove(n)""",
            """nums = [n for n in nums if n != 0]
# или list comprehension / filter""",
        ),
        code(
            "Unpacking swap.",
            "Поменяй a и b без temp.",
            """a, b = 1, 2
temp = a
a = b
b = temp""",
            """a, b = 1, 2
a, b = b, a""",
        ),
        code(
            "f-string formatting.",
            "Выведи price с 2 знаками.",
            """price = 3.5
msg = 'Price: ' + str(round(price, 2))""",
            """msg = f'Price: {price:.2f}'""",
        ),
        code(
            "Context manager class.",
            "Допиши __exit__ для автоматического close.",
            """class Managed:
    def __enter__(self):
        self.resource = open_resource()
        return self.resource

    def __exit__(self, exc_type, exc, tb):
        pass""",
            """def __exit__(self, exc_type, exc, tb):
        self.resource.close()
        return False""",
        ),
        code(
            "Property setter.",
            "Добавь setter с валидацией age > 0.",
            """class Person:
    def __init__(self, age):
        self._age = age

    @property
    def age(self):
        return self._age""",
            """@age.setter
def age(self, value):
    if value <= 0:
        raise ValueError('age must be positive')
    self._age = value""",
        ),
        code(
            "Super init.",
            "Вызови родительский __init__.",
            """class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        self.breed = breed""",
            """class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed""",
        ),
        code(
            "Read env variable.",
            "Получи DATABASE_URL с default.",
            """import os
url = os.environ['DATABASE_URL']""",
            """url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')""",
        ),
        code(
            "Split lines.",
            "Разбей multiline string на непустые строки.",
            """text = 'a\\nb\\n\\nc'
lines = text.split('\\n')
result = [l for l in lines if l]""",
            """result = [line for line in text.splitlines() if line.strip()]""",
        ),
        code(
            "Zip dict.",
            "Собери dict из двух списков keys и values.",
            """keys = ['a', 'b']
values = [1, 2]
d = {}
for i in range(len(keys)):
    d[keys[i]] = values[i]""",
            """d = dict(zip(keys, values))""",
        ),
        code(
            "Reverse string.",
            "Идиоматичный reverse строки s.",
            """def rev(s):
    out = ''
    for ch in s:
        out = ch + out
    return out""",
            """def rev(s):
    return s[::-1]""",
        ),
        code(
            "Any all validation.",
            "Проверь что все числа > 0.",
            """nums = [1, 2, 3]
ok = True
for n in nums:
    if n <= 0:
        ok = False
        break""",
            """ok = all(n > 0 for n in nums)""",
        ),
        code(
            "Defaultdict grouping.",
            "Сгруппируй слова по первой букве.",
            """from collections import defaultdict

groups = defaultdict(list)
for word in words:
    key = word[0]
    if key not in groups:
        groups[key] = []
    groups[key].append(word)""",
            """groups = defaultdict(list)
for word in words:
    groups[word[0]].append(word)""",
        ),
        code(
            "Raise with message.",
            "Брось ValueError если x отрицательный.",
            """def sqrt_pos(x):
    return x ** 0.5""",
            """def sqrt_pos(x):
    if x < 0:
        raise ValueError('x must be non-negative')
    return x ** 0.5""",
        ),
        code(
            "Logging level.",
            "Настрой INFO и лог вместо print.",
            """print('Server started')""",
            """import logging
logging.basicConfig(level=logging.INFO)
logging.info('Server started')""",
        ),
    ]
    cards.extend(code_cards)

    topics_oop = [
        ("инкапсуляция", "Сокрытие деталей через _private и @property"),
        ("полиморфизм", "Один интерфейс — разные реализации duck typing"),
        ("абстракция", "ABC, Protocol — контракт без деталей реализации"),
        ("композиция vs наследование", "has-a часто лучше is-a для гибкости"),
        ("duck typing", "Если walk/quack как утка — не нужен общий базовый класс"),
        ("magic methods", "__len__, __contains__, __getitem__ для protocol objects"),
        ("descriptor", "__get__/__set__ — механизм property, ORM fields"),
        ("metaclass", "type или custom metaclass — редко, class creation hook"),
        ("__new__ vs __init__", "__new__ создаёт instance; __init__ инициализирует"),
        ("singleton antipattern", "Модуль-level object часто проще singleton class"),
    ]
    for name, desc in topics_oop:
        cards.append(theory(f"ООП Python: {name}?", desc))
        cards.append(theory(f"Пример использования {name} в Python?", desc))

    stdlib_modules = [
        ("json", "json.loads/dumps, load/dump files"),
        ("csv", "csv.reader/writer, DictReader"),
        ("pathlib", "Path объект для путей"),
        ("datetime", "datetime, date, timedelta, timezone"),
        ("collections", "Counter, defaultdict, deque, namedtuple"),
        ("itertools", "chain, product, permutations, groupby"),
        ("functools", "lru_cache, partial, wraps, reduce"),
        ("typing", "Optional, Union, Protocol, TypedDict"),
        ("dataclasses", "@dataclass, field, asdict"),
        ("enum", "Enum, IntEnum, auto"),
        ("re", "regex match search sub"),
        ("math", "ceil floor sqrt isnan"),
        ("random", "random, randint, choice, seed — не crypto"),
        ("secrets", "token_hex, choice — crypto random"),
        ("hashlib", "sha256 hexdigest"),
        ("hmac", "compare_digest message auth"),
        ("sqlite3", "DB-API connect cursor execute"),
        ("urllib", "request.urlopen parse"),
        ("http.client", "низкоуровневый HTTP"),
        ("socket", "TCP/UDP networking"),
        ("threading", "Thread, Lock, Event"),
        ("multiprocessing", "Process, Pool, Queue"),
        ("asyncio", "run, create_task, gather, sleep"),
        ("logging", "getLogger, handlers, formatters"),
        ("argparse", "CLI arguments parser"),
        ("configparser", "INI files"),
        ("tomllib", "TOML read Python 3.11+ stdlib"),
        ("pickle", "serialize — unsafe untrusted"),
        ("copy", "copy, deepcopy"),
        ("pprint", "pretty print structures"),
        ("textwrap", "wrap, dedent, indent"),
        ("string", "Template, ascii_letters"),
        ("decimal", "Decimal точная decimal arithmetic"),
        ("fractions", "Fraction rational numbers"),
        ("statistics", "mean median stdev"),
        ("heapq", "heap push pop nsmallest"),
        ("bisect", "sorted list insert search"),
        ("array", "typed array compact storage"),
        ("struct", "pack unpack binary"),
        ("gzip", "compress decompress files"),
        ("shutil", "copytree, rmtree, which"),
        ("tempfile", "TemporaryDirectory, NamedTemporaryFile"),
        ("glob", "pathname patterns"),
        ("fnmatch", "filename pattern match"),
        ("subprocess", "run Popen capture_output"),
        ("signal", "SIGINT handlers Unix"),
        ("contextlib", "contextmanager, suppress, ExitStack"),
        ("weakref", "WeakValueDictionary weak refs"),
        ("gc", "garbage collector debug"),
        ("inspect", "signature, getsource, iscoroutine"),
        ("ast", "parse Python source tree"),
        ("dis", "disassemble bytecode"),
        ("traceback", "format_exc exception chains"),
        ("warnings", "warn filterwarnings"),
        ("unittest.mock", "Mock patch MagicMock"),
        ("doctest", "test examples in docstrings"),
        ("pdb", "debugger break set_trace"),
        ("cProfile", "profile performance"),
        ("timeit", "micro benchmark snippets"),
        ("zoneinfo", "IANA timezones Python 3.9+"),
        ("uuid", "uuid4 unique ids"),
        ("base64", "encode decode bytes"),
        ("html", "escape unescape HTML"),
        ("xml.etree", "ElementTree parse XML"),
    ]
    for mod, desc in stdlib_modules:
        cards.append(theory(f"stdlib: модуль {mod} — зачем?", desc))
        cards.append(theory(f"Когда выбрать {mod} вместо альтернатив?", f"Использовать {mod} когда {desc}."))

    errors = [
        "SyntaxError", "IndentationError", "NameError", "TypeError", "ValueError",
        "KeyError", "IndexError", "AttributeError", "ImportError", "ModuleNotFoundError",
        "ZeroDivisionError", "FileNotFoundError", "PermissionError", "StopIteration",
        "RuntimeError", "NotImplementedError", "RecursionError", "MemoryError",
        "KeyboardInterrupt", "SystemExit", "AssertionError", "UnicodeDecodeError",
    ]
    for err in errors:
        cards.append(theory(f"Когда возникает {err}?", f"{err} — типичная ошибка Python; обрабатывать через try/except если recoverable."))

    builtins_funcs = [
        "len", "print", "input", "open", "range", "enumerate", "zip", "map", "filter",
        "sorted", "reversed", "sum", "min", "max", "abs", "round", "pow", "divmod",
        "bool", "int", "float", "str", "list", "dict", "set", "tuple", "type", "isinstance",
        "issubclass", "hasattr", "getattr", "setattr", "delattr", "callable", "iter", "next",
        "all", "any", "format", "repr", "ascii", "ord", "chr", "bin", "hex", "oct",
        "id", "hash", "help", "dir", "vars", "locals", "globals", "exec", "eval",
    ]
    for fn in builtins_funcs:
        cards.append(theory(f"Built-in: что делает {fn}()?", f"Встроенная функция Python {fn}. См. docs.python.org built-in functions."))

    code_templates = [
        ("list comp filter", "Список квадратов x>0", "[x*x for x in nums if x > 0]", "[x**2 for x in nums if x > 0]"),
        ("dict get default", "get с default", "d['k']", "d.get('k', 0)"),
        ("strip input", "strip input", "name = input()", "name = input().strip()"),
        ("main guard", "main guard", "run()", "if __name__ == '__main__': run()"),
        ("enum member", "Enum member", "STATUS = 'active'", "class S(Enum): ACTIVE='active'"),
        ("path exists", "Path exists", "os.path.exists(p)", "Path(p).exists()"),
        ("join paths", "Path join", "os.path.join(a,b)", "Path(a) / b"),
        ("read utf8", "encoding utf-8", "open(f)", "open(f, encoding='utf-8')"),
        ("except chain", "raise from", "raise e2", "raise e2 from e1"),
        ("lru cache", "functools cache", "def f(): pass", "@lru_cache\\ndef f(): pass"),
        ("partial", "partial apply", "lambda x: add(1,x)", "partial(add, 1)"),
        ("deque popleft", "queue BFS", "list.pop(0)", "deque.popleft()"),
        ("set lookup", "membership O(1)", "if x in list_big", "if x in set_big"),
        ("tuple unpack", "swap", "t=(a,b); a=t[1]; b=t[0]", "a, b = b, a"),
        ("chain lists", "extend flat", "for l in lists: for x in l", "from itertools import chain; list(chain.from_iterable(lists))"),
        ("groupby sorted", "group consecutive", "manual groups", "from itertools import groupby"),
        ("typed dict", "TypedDict", "d: dict", "class D(TypedDict): name: str"),
        ("optional arg", "None default", "def f(x=[]):", "def f(x=None):"),
        ("str methods", "startswith", "s[:5]=='hello'", "s.startswith('hello')"),
        ("format spec", "width pad", "'%5d' % n", "f'{n:5d}'"),
    ]
    for i, (name, task, broken, fixed) in enumerate(code_templates):
        for n in range(3):
            cards.append(code(
                f"Python основы [{name}] #{i}-{n}",
                task,
                broken,
                fixed,
            ))

    revision = [
        "типы данных", "операторы", "условия", "циклы", "функции", "args kwargs",
        "списки", "словари", "множества", "кортежи", "строки", "файлы", "исключения",
        "классы", "наследование", "декораторы", "генераторы", "итераторы", "comprehensions",
        "модули", "venv", "pip", "typing", "dataclass", "asyncio", "threading",
        "collections", "pathlib", "json", "datetime", "logging", "pytest",
        "list methods", "dict methods", "set methods", "str methods",
    ]
    for topic in revision:
        for i in range(5):
            cards.append(theory(
                f"Python основы [{topic}]: вопрос #{i + 1}",
                f"Повторите ключевые идеи темы «{topic}» в Python 3. Практикуйте на маленьких примерах в REPL.",
            ))

    py_versions = {
        "3.8": ["walrus :=", "positional-only /", "f'{x=}' debug"],
        "3.9": ["dict merge |", "list[str] builtins generics", "str.removeprefix"],
        "3.10": ["match case", "better errors", "ParamSpec"],
        "3.11": ["tomllib", "Exception groups", "speedup"],
        "3.12": ["f-string improvements", "type parameter syntax", "per-interpreter GIL experimental"],
    }
    for ver, feats in py_versions.items():
        for feat in feats:
            cards.append(theory(f"Python {ver}: {feat}?", f"Нововведение Python {ver}: {feat}."))

    list_methods = [
        "append", "extend", "insert", "remove", "pop", "clear", "index", "count",
        "sort", "reverse", "copy",
    ]
    for m in list_methods:
        cards.append(theory(f"list.{m}() — что делает?", f"Метод списка list.{m}. Изменяет или возвращает list in-place / новый объект."))

    dict_methods = [
        "get", "keys", "values", "items", "update", "pop", "popitem", "setdefault", "clear", "copy",
    ]
    for m in dict_methods:
        cards.append(theory(f"dict.{m}() — что делает?", f"Метод словаря dict.{m}."))

    str_methods = [
        "split", "join", "strip", "replace", "find", "startswith", "endswith",
        "lower", "upper", "title", "format", "partition", "removeprefix", "removesuffix",
    ]
    for m in str_methods:
        cards.append(theory(f"str.{m}() — когда использовать?", f"Строковый метод str.{m} — типичные задачи обработки текста."))

    seen: set[str] = set()
    unique: list[dict] = []
    for card in cards:
        key = card.get("question", "") + card.get("code", "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(card)
    return unique


def main() -> None:
    cards = build_cards()
    if len(cards) < 500:
        raise SystemExit(f"Only {len(cards)} cards, need 500+")
    code_n = sum(1 for c in cards if c.get("card_type") == "code" or c.get("code"))
    deck = {"name": "Python — основы", "cards": cards}
    out = Path(__file__).with_name("python-basics.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} cards ({code_n} code) -> {out}")


if __name__ == "__main__":
    main()
