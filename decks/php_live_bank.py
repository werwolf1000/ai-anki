"""Additional PHP live-coding cards for deck expansion."""
from __future__ import annotations

from live_coding_card import live


def extra_cards() -> list[dict]:
    return [
        # --- Основы (15) ---
        live(
            "Типизированные константы",
            "Объявите класс AppConfig с публичной типизированной константой string VERSION = '1.0.0'. "
            "Добавьте статический метод version(): string, возвращающий значение константы.",
            """<?php
declare(strict_types=1);

final class AppConfig
{
    public const string VERSION = '1.0.0';

    public static function version(): string
    {
        return self::VERSION;
    }
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте typed class constant (PHP 8.3+).", "Класс final."],
        ),
        live(
            "Проверка типа is_*",
            "Напишите функцию describeValue(mixed $value): string. "
            "Для int верните 'int', для string — 'string', для bool — 'bool', иначе 'other'.",
            """<?php
declare(strict_types=1);

function describeValue(mixed $value): string
{
    return match (true) {
        is_int($value) => 'int',
        is_string($value) => 'string',
        is_bool($value) => 'bool',
        default => 'other',
    };
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте match.", "Параметр mixed."],
        ),
        live(
            "Switch с строгим сравнением",
            "Функция httpMethodLabel(string $method): string через switch. "
            "GET → 'read', POST → 'create', PUT → 'update', DELETE → 'delete', иначе 'unknown'.",
            """<?php
declare(strict_types=1);

function httpMethodLabel(string $method): string
{
    return match (strtoupper($method)) {
        'GET' => 'read',
        'POST' => 'create',
        'PUT' => 'update',
        'DELETE' => 'delete',
        default => 'unknown',
    };
}""",
            lang="php",
            topic="Основы",
            requirements=["Нормализуйте метод через strtoupper.", "Покройте default-ветку."],
        ),
        live(
            "Цикл foreach с ключом",
            "Функция invertMap(array $map): array меняет местами строковые ключи и int-значения. "
            "Пример: ['a' => 1, 'b' => 2] → [1 => 'a', 2 => 'b'].",
            """<?php
declare(strict_types=1);

function invertMap(array $map): array
{
    $result = [];
    foreach ($map as $key => $value) {
        $result[$value] = $key;
    }
    return $result;
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте foreach.", "Верните новый массив."],
        ),
        live(
            "Do-while минимум один проход",
            "Функция readUntilEmpty(array $items): int считает, сколько раз можно взять элемент через array_shift, "
            "пока массив не опустеет. Используйте do-while для хотя бы одной итерации при непустом входе.",
            """<?php
declare(strict_types=1);

function readUntilEmpty(array $items): int
{
    $count = 0;
    if ($items === []) {
        return 0;
    }
    do {
        array_shift($items);
        $count++;
    } while ($items !== []);
    return $count;
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте do-while.", "Пустой массив → 0."],
        ),
        live(
            "Глобальная функция с default",
            "Функция repeat(string $text, int $times = 3): string возвращает строку, повторённую $times раз через str_repeat. "
            "При $times <= 0 верните пустую строку.",
            """<?php
declare(strict_types=1);

function repeat(string $text, int $times = 3): string
{
    if ($times <= 0) {
        return '';
    }
    return str_repeat($text, $times);
}""",
            lang="php",
            topic="Основы",
            requirements=["Значение по умолчанию для $times.", "Обработайте неположительный $times."],
        ),
        live(
            "Ссылочный параметр swap",
            "Функция swap(int &$a, int &$b): void меняет значения двух переменных местами без временного массива.",
            """<?php
declare(strict_types=1);

function swap(int &$a, int &$b): void
{
    $tmp = $a;
    $a = $b;
    $b = $tmp;
}""",
            lang="php",
            topic="Основы",
            requirements=["Оба параметра по ссылке.", "Тип void."],
        ),
        live(
            "Variadic sum",
            "Функция sumAll(int ...$values): int возвращает сумму всех переданных целых. "
            "Без аргументов верните 0.",
            """<?php
declare(strict_types=1);

function sumAll(int ...$values): int
{
    return array_sum($values);
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте variadic ...$values.", "Пустой вызов → 0."],
        ),
        live(
            "Константа уровня файла",
            "Объявите константу MAX_ITEMS = 100 и функцию isWithinLimit(int $count): bool, "
            "возвращающую true, если $count <= MAX_ITEMS.",
            """<?php
declare(strict_types=1);

const MAX_ITEMS = 100;

function isWithinLimit(int $count): bool
{
    return $count <= MAX_ITEMS;
}""",
            lang="php",
            topic="Основы",
            requirements=["Константа на уровне файла.", "Строгое сравнение не требуется для <=."],
        ),
        live(
            "Heredoc шаблон",
            "Функция renderBanner(string $title): string возвращает многострочный баннер через heredoc "
            "с подстановкой $title в отдельной строке.",
            """<?php
declare(strict_types=1);

function renderBanner(string $title): string
{
    return <<<BANNER
=== {$title} ===
Welcome!
BANNER;
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте heredoc.", "Включите $title в текст."],
        ),
        live(
            "Оператор ??=",
            "Функция ensureDefault(?string &$value, string $default = 'guest'): string "
            "присваивает $default через ??=, если $value равно null, и возвращает итог.",
            """<?php
declare(strict_types=1);

function ensureDefault(?string &$value, string $default = 'guest'): string
{
    $value ??= $default;
    return $value;
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте оператор ??=.", "Параметр по ссылке."],
        ),
        live(
            "Проверка callable",
            "Функция invokeIfCallable(mixed $target, string $method, mixed ...$args): mixed "
            "вызывает [$target, $method](...$args), если callable, иначе возвращает null.",
            """<?php
declare(strict_types=1);

function invokeIfCallable(mixed $target, string $method, mixed ...$args): mixed
{
    $callable = [$target, $method];
    if (!is_callable($callable)) {
        return null;
    }
    return $callable(...$args);
}""",
            lang="php",
            topic="Основы",
            requirements=["Проверка is_callable.", "Variadic args."],
        ),
        live(
            "Compact и extract",
            "Функция buildUserRow(string $name, int $age): array возвращает ассоциативный массив "
            "через compact('name', 'age').",
            """<?php
declare(strict_types=1);

function buildUserRow(string $name, int $age): array
{
    return compact('name', 'age');
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте compact.", "Ключи name и age."],
        ),
        live(
            "list деструктуризация",
            "Функция firstAndLast(array $items): array возвращает [первый, последний] элемент "
            "через list() / деструктуризацию. Пустой массив → [null, null].",
            """<?php
declare(strict_types=1);

function firstAndLast(array $items): array
{
    if ($items === []) {
        return [null, null];
    }
    $first = $items[0];
    $last = $items[array_key_last($items)];
    return [$first, $last];
}""",
            lang="php",
            topic="Основы",
            requirements=["Обработайте пустой массив.", "Используйте array_key_last."],
        ),
        live(
            "goto cleanup pattern",
            "Функция processResource(bool $fail): string открывает логическую секцию try и при $fail "
            "переходит через goto cleanup к возврату 'failed', иначе 'ok'.",
            """<?php
declare(strict_types=1);

function processResource(bool $fail): string
{
    $status = 'ok';
    if ($fail) {
        $status = 'failed';
        goto cleanup;
    }
    cleanup:
    return $status;
}""",
            lang="php",
            topic="Основы",
            requirements=["Используйте goto cleanup.", "Два возможных результата."],
        ),
        # --- PHP 8+ (15) ---
        live(
            "Intersection type CountableIterator",
            "Класс InMemoryCollection implements Iterator, Countable с полем private array $items. "
            "Реализуйте current, key, next, rewind, valid, count.",
            """<?php
declare(strict_types=1);

final class InMemoryCollection implements Iterator, Countable
{
    private int $position = 0;

    public function __construct(private array $items)
    {
    }

    public function current(): mixed
    {
        return $this->items[$this->position];
    }

    public function key(): int
    {
        return $this->position;
    }

    public function next(): void
    {
        $this->position++;
    }

    public function rewind(): void
    {
        $this->position = 0;
    }

    public function valid(): bool
    {
        return isset($this->items[$this->position]);
    }

    public function count(): int
    {
        return count($this->items);
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Iterator + Countable.", "Храните данные в private array."],
        ),
        live(
            "Standalone type true",
            "Функция alwaysTrue(): true всегда возвращает литерал true (тип возврата true, PHP 8.2+).",
            """<?php
declare(strict_types=1);

function alwaysTrue(): true
{
    return true;
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Тип возврата true.", "Без других веток."],
        ),
        live(
            "Standalone type false",
            "Функция alwaysFalse(): false всегда возвращает литерал false.",
            """<?php
declare(strict_types=1);

function alwaysFalse(): false
{
    return false;
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Тип возврата false.", "Один return."],
        ),
        live(
            "Readonly property promotion",
            "Класс Product с promoted readonly string $sku и readonly float $price в конструкторе.",
            """<?php
declare(strict_types=1);

final class Product
{
    public function __construct(
        public readonly string $sku,
        public readonly float $price,
    ) {
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Оба поля readonly promoted.", "Класс final."],
        ),
        live(
            "Const в trait",
            "Trait HasVersion с public const string VERSION = 'v2' и методом version(): string.",
            """<?php
declare(strict_types=1);

trait HasVersion
{
    public const string VERSION = 'v2';

    public function version(): string
    {
        return self::VERSION;
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Typed const в trait.", "Метод version()."],
        ),
        live(
            "Dynamic properties deprecated guard",
            "Класс StrictModel с #[\\AllowDynamicProperties] не используйте — наоборот, объявите "
            "public string $name и __get для неизвестных свойств с LogicException.",
            """<?php
declare(strict_types=1);

final class StrictModel
{
    public string $name = '';

    public function __get(string $name): never
    {
        throw new LogicException("Unknown property: {$name}");
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Явное поле name.", "__get бросает LogicException."],
        ),
        live(
            "Fibers stub",
            "Функция runInFiber(callable $fn): mixed создаёт Fiber, передаёт $fn в start и возвращает get() "
            "(заглушка однопоточного запуска).",
            """<?php
declare(strict_types=1);

function runInFiber(callable $fn): mixed
{
    $fiber = new Fiber($fn);
    $fiber->start();
    return $fiber->get();
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Используйте класс Fiber.", "Верните результат get()."],
        ),
        live(
            "enum в match",
            "Unit enum Color { Red, Green, Blue } и функция colorCode(Color $color): int "
            "возвращает 0xFF0000, 0x00FF00, 0x0000FF соответственно.",
            """<?php
declare(strict_types=1);

enum Color
{
    case Red;
    case Green;
    case Blue;
}

function colorCode(Color $color): int
{
    return match ($color) {
        Color::Red => 0xFF0000,
        Color::Green => 0x00FF00,
        Color::Blue => 0x0000FF,
    };
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Unit enum Color.", "match по всем case."],
        ),
        live(
            "Partial application pipe",
            "Функция pipe(int $value, callable ...$steps): int последовательно применяет callable к значению.",
            """<?php
declare(strict_types=1);

function pipe(int $value, callable ...$steps): int
{
    foreach ($steps as $step) {
        $value = $step($value);
    }
    return $value;
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Variadic callable steps.", "Тип int на входе и выходе."],
        ),
        live(
            "Stringable interface",
            "Класс Label implements Stringable с private string $text и __toString(): string.",
            """<?php
declare(strict_types=1);

final class Label implements Stringable
{
    public function __construct(private string $text)
    {
    }

    public function __toString(): string
    {
        return $this->text;
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["implements Stringable.", "Приватное поле text."],
        ),
        live(
            "WeakMap кэш",
            "Класс ObjectCache с private WeakMap $cache и методами get(object $key, callable $factory): mixed.",
            """<?php
declare(strict_types=1);

final class ObjectCache
{
    private WeakMap $cache;

    public function __construct()
    {
        $this->cache = new WeakMap();
    }

    public function get(object $key, callable $factory): mixed
    {
        if (!$this->cache->offsetExists($key)) {
            $this->cache->offsetSet($key, $factory());
        }
        return $this->cache->offsetGet($key);
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Используйте WeakMap.", "Ленивое создание через factory."],
        ),
        live(
            "json_validate PHP 8.3",
            "Функция isValidJson(string $raw): bool использует json_validate без декодирования.",
            """<?php
declare(strict_types=1);

function isValidJson(string $raw): bool
{
    return json_validate($raw);
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Только json_validate.", "Без json_decode."],
        ),
        live(
            "Override attribute",
            "Базовый класс BaseWorker с virtual log(): void и наследник ChildWorker "
            "с #[\\Override] public function log(): void, пишущим 'child'.",
            """<?php
declare(strict_types=1);

class BaseWorker
{
    public function log(): void
    {
        echo 'base', PHP_EOL;
    }
}

final class ChildWorker extends BaseWorker
{
    #[\\Override]
    public function log(): void
    {
        echo 'child', PHP_EOL;
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Атрибут #[\\Override].", "Переопределите log()."],
        ),
        live(
            "Randomizer getBytes",
            "Функция secureToken(int $length = 16): string генерирует hex-токен через Random\\Randomizer и getBytes.",
            """<?php
declare(strict_types=1);

function secureToken(int $length = 16): string
{
    $randomizer = new Random\\Randomizer();
    return bin2hex($randomizer->getBytes($length));
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Класс Random\\Randomizer.", "Верните hex-строку."],
        ),
        live(
            "Closure bindTo",
            "Функция boundGreeting(object $obj, string $name): string создаёт closure, "
            "возвращающую \"Hi, {$name}\", и привязывает к $obj через bindTo.",
            """<?php
declare(strict_types=1);

function boundGreeting(object $obj, string $name): string
{
    $fn = function () use ($name): string {
        return "Hi, {$name}";
    };
    $bound = $fn->bindTo($obj, $obj::class);
    return $bound();
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Используйте bindTo.", "Верните строку приветствия."],
        ),
        live(
            "DNF types в property",
            "Класс Payload с promoted public int|string|null $id в конструкторе и методом isNumeric(): bool.",
            """<?php
declare(strict_types=1);

final class Payload
{
    public function __construct(public int|string|null $id)
    {
    }

    public function isNumeric(): bool
    {
        return is_int($this->id);
    }
}""",
            lang="php",
            topic="PHP 8+",
            requirements=["Union int|string|null.", "Метод isNumeric()."],
        ),
        # --- ООП (15) ---
        live(
            "Композиция Engine",
            "Класс Car с private Engine $engine и методом start(): string, делегирующим $this->engine->ignite(). "
            "Engine::ignite(): string возвращает 'vroom'.",
            """<?php
declare(strict_types=1);

final class Engine
{
    public function ignite(): string
    {
        return 'vroom';
    }
}

final class Car
{
    public function __construct(private Engine $engine)
    {
    }

    public function start(): string
    {
        return $this->engine->ignite();
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Композиция, не наследование.", "Делегирование ignite()."],
        ),
        live(
            "Late static binding",
            "Класс Model с static create(): static и наследник User, переопределяющий create() "
            "для возврата new self(...).",
            """<?php
declare(strict_types=1);

class Model
{
    public static function create(): static
    {
        return new static();
    }
}

final class User extends Model
{
    public static function create(): static
    {
        return new self();
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["static create(): static.", "User возвращает new self()."],
        ),
        live(
            "Final override method",
            "Класс Base с public function id(): string и final class Child extends Base "
            "с id(): string возвращающим 'child'.",
            """<?php
declare(strict_types=1);

class Base
{
    public function id(): string
    {
        return 'base';
    }
}

final class Child extends Base
{
    public function id(): string
    {
        return 'child';
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Наследование Base → Child.", "Переопределите id()."],
        ),
        live(
            "Magic __call",
            "Класс DynamicApi с __call(string $name, array $arguments): string "
            "возвращает \"called {$name}\".",
            """<?php
declare(strict_types=1);

final class DynamicApi
{
    public function __call(string $name, array $arguments): string
    {
        return "called {$name}";
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Метод __call.", "Игнорируйте $arguments в ответе."],
        ),
        live(
            "Magic __invoke",
            "Класс Multiplier с __construct(private int $factor) и __invoke(int $value): int.",
            """<?php
declare(strict_types=1);

final class Multiplier
{
    public function __construct(private int $factor)
    {
    }

    public function __invoke(int $value): int
    {
        return $value * $this->factor;
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Объект вызываемый как функция.", "Умножение на factor."],
        ),
        live(
            "Clone с __clone",
            "Класс Box с public array $items и __clone(), выполняющим $this->items = [...$this->items].",
            """<?php
declare(strict_types=1);

final class Box
{
    public function __construct(public array $items)
    {
    }

    public function __clone(): void
    {
        $this->items = [...$this->items];
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Глубокое копирование items.", "Используйте spread в __clone."],
        ),
        live(
            "Serializable __serialize",
            "Класс SessionData с private string $token и парами __serialize/__unserialize "
            "для сохранения только token.",
            """<?php
declare(strict_types=1);

final class SessionData
{
    public function __construct(private string $token)
    {
    }

    public function __serialize(): array
    {
        return ['token' => $this->token];
    }

    public function __unserialize(array $data): void
    {
        $this->token = $data['token'];
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["__serialize и __unserialize.", "Храните token."],
        ),
        live(
            "Interface segregation",
            "Интерфейсы Readable { read(): string } и Writable { write(string $data): void }; "
            "класс MemoryStream implements оба.",
            """<?php
declare(strict_types=1);

interface Readable
{
    public function read(): string;
}

interface Writable
{
    public function write(string $data): void;
}

final class MemoryStream implements Readable, Writable
{
    private string $buffer = '';

    public function read(): string
    {
        return $this->buffer;
    }

    public function write(string $data): void
    {
        $this->buffer .= $data;
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Два интерфейса.", "Буфер в памяти."],
        ),
        live(
            "Abstract template method",
            "Abstract class Exporter с final export(): string вызывающим serialize($this->data()) "
            "и abstract protected data(): array. JsonExporter возвращает ['ok' => true].",
            """<?php
declare(strict_types=1);

abstract class Exporter
{
    final public function export(): string
    {
        return json_encode($this->data(), JSON_THROW_ON_ERROR);
    }

    abstract protected function data(): array;
}

final class JsonExporter extends Exporter
{
    protected function data(): array
    {
        return ['ok' => true];
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Template method export().", "JsonExporter с data()."],
        ),
        live(
            "Static counter",
            "Класс RequestId с private static int $seq и static next(): int, инкрементирующим счётчик.",
            """<?php
declare(strict_types=1);

final class RequestId
{
    private static int $seq = 0;

    public static function next(): int
    {
        return ++self::$seq;
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Статическое поле seq.", "Метод next()."],
        ),
        live(
            "Private constructor singleton",
            "Класс ConfigStore — singleton: private __construct, static getInstance(): self, "
            "поле private static ?self $instance.",
            """<?php
declare(strict_types=1);

final class ConfigStore
{
    private static ?self $instance = null;

    private function __construct()
    {
    }

    public static function getInstance(): self
    {
        return self::$instance ??= new self();
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Приватный конструктор.", "Один экземпляр getInstance()."],
        ),
        live(
            "Covariant return stub",
            "Класс Animal с makeSound(): string и Dog extends Animal с makeSound(): string возвращающим 'woof'.",
            """<?php
declare(strict_types=1);

class Animal
{
    public function makeSound(): string
    {
        return '...';
    }
}

final class Dog extends Animal
{
    public function makeSound(): string
    {
        return 'woof';
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Наследник Dog.", "Переопределите makeSound()."],
        ),
        live(
            "Delegation __get",
            "Класс ProxyConfig с __construct(private object $inner) и __get, "
            "читающим свойства $inner.",
            """<?php
declare(strict_types=1);

final class ProxyConfig
{
    public function __construct(private object $inner)
    {
    }

    public function __get(string $name): mixed
    {
        return $this->inner->$name;
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Делегируйте чтение inner.", "Метод __get."],
        ),
        live(
            "Comparable equals",
            "Класс Uuid с private string $value, __construct и equals(self $other): bool через === значений.",
            """<?php
declare(strict_types=1);

final class Uuid
{
    public function __construct(private string $value)
    {
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["Типизированный параметр self.", "Сравнение приватных value."],
        ),
        live(
            "Protected constructor base",
            "Abstract class Entity с protected __construct(public readonly int $id) "
            "и final class User extends Entity без своего конструктора — публичный __construct вызывает parent.",
            """<?php
declare(strict_types=1);

abstract class Entity
{
    protected function __construct(public readonly int $id)
    {
    }
}

final class User extends Entity
{
    public function __construct(int $id)
    {
        parent::__construct($id);
    }
}""",
            lang="php",
            topic="ООП",
            requirements=["protected конструктор в базе.", "User вызывает parent."],
        ),
        # --- Массивы (15) ---
        live(
            "array_reduce product",
            "Функция product(array $numbers): int — произведение int через array_reduce. "
            "Пустой массив → 1.",
            """<?php
declare(strict_types=1);

function product(array $numbers): int
{
    if ($numbers === []) {
        return 1;
    }
    return array_reduce($numbers, fn (int $carry, int $n): int => $carry * $n, 1);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_reduce.", "Пустой массив → 1."],
        ),
        live(
            "array_walk_by_reference",
            "Функция doubleInPlace(array &$numbers): void удваивает каждый элемент через array_walk.",
            """<?php
declare(strict_types=1);

function doubleInPlace(array &$numbers): void
{
    array_walk($numbers, function (int &$value): void {
        $value *= 2;
    });
}""",
            lang="php",
            topic="Массивы",
            requirements=["Изменение по ссылке.", "array_walk."],
        ),
        live(
            "array_unique strict",
            "Функция uniqueInts(array $values): array возвращает уникальные int через array_unique(SORT_REGULAR) "
            "с переиндексацией.",
            """<?php
declare(strict_types=1);

function uniqueInts(array $values): array
{
    return array_values(array_unique($values, SORT_REGULAR));
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_unique.", "array_values для сброса ключей."],
        ),
        live(
            "array_flip lookup",
            "Функция invertLabels(array $labels): array строит карту значение→ключ через array_flip. "
            "Дубликаты значений — последний ключ побеждает (поведение array_flip).",
            """<?php
declare(strict_types=1);

function invertLabels(array $labels): array
{
    return array_flip($labels);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_flip.", "Верните массив."],
        ),
        live(
            "array_intersect_key",
            "Функция commonKeys(array $a, array $b): array возвращает элементы $a, "
            "чьи ключи есть в $b, через array_intersect_key.",
            """<?php
declare(strict_types=1);

function commonKeys(array $a, array $b): array
{
    return array_intersect_key($a, $b);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_intersect_key.", "Сохраните значения из $a."],
        ),
        live(
            "array_diff_assoc",
            "Функция diffByValueAndKey(array $left, array $right): array — array_diff_assoc($left, $right).",
            """<?php
declare(strict_types=1);

function diffByValueAndKey(array $left, array $right): array
{
    return array_diff_assoc($left, $right);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_diff_assoc.", "Два входных массива."],
        ),
        live(
            "uksort custom",
            "Функция sortKeysAlpha(array $map): array сортирует ключи через uksort и strcmp.",
            """<?php
declare(strict_types=1);

function sortKeysAlpha(array $map): array
{
    uksort($map, fn (string $a, string $b): int => strcmp($a, $b));
    return $map;
}""",
            lang="php",
            topic="Массивы",
            requirements=["uksort.", "strcmp для ключей."],
        ),
        live(
            "array_pad",
            "Функция padRight(array $items, int $size, mixed $fill = 0): array дополняет массив "
            "до $size элементов справа.",
            """<?php
declare(strict_types=1);

function padRight(array $items, int $size, mixed $fill = 0): array
{
    return array_pad($items, $size, $fill);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_pad.", "Параметр fill с default."],
        ),
        live(
            "array_slice page",
            "Функция paginate(array $items, int $page, int $perPage = 10): array "
            "возвращает срез для страницы (page с 1).",
            """<?php
declare(strict_types=1);

function paginate(array $items, int $page, int $perPage = 10): array
{
    $offset = max(0, ($page - 1) * $perPage);
    return array_slice($items, $offset, $perPage);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_slice.", "Нумерация page с 1."],
        ),
        live(
            "array_replace_recursive",
            "Функция mergeDefaults(array $data, array $defaults): array через array_replace_recursive.",
            """<?php
declare(strict_types=1);

function mergeDefaults(array $data, array $defaults): array
{
    return array_replace_recursive($defaults, $data);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_replace_recursive.", "defaults как база."],
        ),
        live(
            "array_key_exists vs isset",
            "Функция hasKey(array $map, string $key): bool возвращает true, если ключ есть, "
            "даже когда значение null — используйте array_key_exists.",
            """<?php
declare(strict_types=1);

function hasKey(array $map, string $key): bool
{
    return array_key_exists($key, $map);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_key_exists, не isset.", "Ключ string."],
        ),
        live(
            "SplFixedArray",
            "Класс FixedBuffer оборачивает SplFixedArray: __construct(int $size), set(int $i, int $v), get(int $i): int.",
            """<?php
declare(strict_types=1);

final class FixedBuffer
{
    private SplFixedArray $data;

    public function __construct(int $size)
    {
        $this->data = new SplFixedArray($size);
    }

    public function set(int $index, int $value): void
    {
        $this->data[$index] = $value;
    }

    public function get(int $index): int
    {
        return (int) $this->data[$index];
    }
}""",
            lang="php",
            topic="Массивы",
            requirements=["SplFixedArray внутри.", "Методы set/get."],
        ),
        live(
            "array_count_values",
            "Функция frequency(array $tokens): array считает частоту строк через array_count_values.",
            """<?php
declare(strict_types=1);

function frequency(array $tokens): array
{
    return array_count_values($tokens);
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_count_values.", "Вход — массив строк."],
        ),
        live(
            "natsort strings",
            "Функция naturalSort(array $files): array сортирует строки естественным порядком через natsort "
            "и возвращает массив.",
            """<?php
declare(strict_types=1);

function naturalSort(array $files): array
{
    natsort($files);
    return array_values($files);
}""",
            lang="php",
            topic="Массивы",
            requirements=["natsort.", "array_values после сортировки."],
        ),
        live(
            "array_multisort",
            "Функция sortByScoreThenName(array $rows): array сортирует массив строк "
            "по полям score (desc) и name (asc) через array_multisort.",
            """<?php
declare(strict_types=1);

function sortByScoreThenName(array $rows): array
{
    $scores = array_column($rows, 'score');
    $names = array_column($rows, 'name');
    array_multisort($scores, SORT_DESC, $names, SORT_ASC, $rows);
    return $rows;
}""",
            lang="php",
            topic="Массивы",
            requirements=["array_multisort.", "Два поля сортировки."],
        ),
        # --- Строки и JSON (14) ---
        live(
            "mb_strlen",
            "Функция charCount(string $text): int возвращает количество символов в UTF-8 через mb_strlen.",
            """<?php
declare(strict_types=1);

function charCount(string $text): int
{
    return mb_strlen($text, 'UTF-8');
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["mb_strlen с UTF-8.", "Тип int."],
        ),
        live(
            "mb_substr excerpt",
            "Функция excerpt(string $text, int $max = 50): string обрезает UTF-8 строку через mb_substr "
            "и добавляет '…', если длиннее $max.",
            """<?php
declare(strict_types=1);

function excerpt(string $text, int $max = 50): string
{
    if (mb_strlen($text, 'UTF-8') <= $max) {
        return $text;
    }
    return mb_substr($text, 0, $max, 'UTF-8') . '…';
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["mb_substr и mb_strlen.", "Многоточие при обрезке."],
        ),
        live(
            "mb_strtolower",
            "Функция normalizeTitle(string $title): string приводит UTF-8 к нижнему регистру через mb_strtolower.",
            """<?php
declare(strict_types=1);

function normalizeTitle(string $title): string
{
    return mb_strtolower($title, 'UTF-8');
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["mb_strtolower.", "Кодировка UTF-8."],
        ),
        live(
            "NumberFormatter currency",
            "Функция formatRub(int $amount): string форматирует копейки как рубли через NumberFormatter "
            "(LOCALE ru_RU, CURRENCY).",
            """<?php
declare(strict_types=1);

function formatRub(int $amount): string
{
    $fmt = new NumberFormatter('ru_RU', NumberFormatter::CURRENCY);
    return $fmt->formatCurrency($amount / 100, 'RUB');
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["NumberFormatter.", "Валюта RUB."],
        ),
        live(
            "IntlDateFormatter",
            "Функция formatRuDate(DateTimeImmutable $dt): string форматирует дату по-русски "
            "через IntlDateFormatter(MEDIUM, NONE).",
            """<?php
declare(strict_types=1);

function formatRuDate(DateTimeImmutable $dt): string
{
    $formatter = new IntlDateFormatter(
        'ru_RU',
        IntlDateFormatter::MEDIUM,
        IntlDateFormatter::NONE,
    );
    return $formatter->format($dt);
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["IntlDateFormatter.", "Локаль ru_RU."],
        ),
        live(
            "sprintf padding",
            "Функция padLeft(string $value, int $width = 8): string дополняет строку нулями слева через sprintf.",
            """<?php
declare(strict_types=1);

function padLeft(string $value, int $width = 8): string
{
    return sprintf('%0' . $width . 's', $value);
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["sprintf с zero-padding.", "Ширина настраиваемая."],
        ),
        live(
            "preg_replace_callback",
            "Функция maskDigits(string $text): string заменяет каждую цифру на '*' "
            "через preg_replace_callback('/\\d/').",
            """<?php
declare(strict_types=1);

function maskDigits(string $text): string
{
    return preg_replace_callback('/\\d/', fn (): string => '*', $text) ?? $text;
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["preg_replace_callback.", "Маскируйте все цифры."],
        ),
        live(
            "preg_split tokens",
            "Функция tokenize(string $text): array разбивает по пробелам через preg_split('/\\s+/').",
            """<?php
declare(strict_types=1);

function tokenize(string $text): array
{
    $parts = preg_split('/\\s+/', trim($text)) ?: [];
    return array_values(array_filter($parts, fn (string $p): bool => $p !== ''));
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["preg_split.", "Уберите пустые токены."],
        ),
        live(
            "json_encode flags",
            "Функция toPrettyJson(array $data): string кодирует JSON с PRETTY_PRINT | UNESCAPED_UNICODE "
            "и JSON_THROW_ON_ERROR.",
            """<?php
declare(strict_types=1);

function toPrettyJson(array $data): string
{
    return json_encode(
        $data,
        JSON_THROW_ON_ERROR | JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE,
    );
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["JSON_PRETTY_PRINT.", "JSON_THROW_ON_ERROR."],
        ),
        live(
            "json_decode depth",
            "Функция parsePayload(string $raw): array декодирует JSON в ассоциативный массив "
            "с json_decode(..., true, 512, JSON_THROW_ON_ERROR).",
            """<?php
declare(strict_types=1);

function parsePayload(string $raw): array
{
    $data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
    return is_array($data) ? $data : [];
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["Ассоциативный массив.", "JSON_THROW_ON_ERROR."],
        ),
        live(
            "strtr translation",
            "Функция leetSpeak(string $text): string заменяет a→4, e→3, i→1, o→0 через strtr.",
            """<?php
declare(strict_types=1);

function leetSpeak(string $text): string
{
    return strtr($text, ['a' => '4', 'e' => '3', 'i' => '1', 'o' => '0']);
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["strtr с картой замен.", "Четыре гласные."],
        ),
        live(
            "hash_equals timing safe",
            "Функция safeEquals(string $known, string $user): bool сравнивает строки через hash_equals.",
            """<?php
declare(strict_types=1);

function safeEquals(string $known, string $user): bool
{
    return hash_equals($known, $user);
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["hash_equals.", "Тип bool."],
        ),
        live(
            "bin2hex random",
            "Функция randomHex(int $bytes = 8): string генерирует случайные байты random_bytes "
            "и кодирует bin2hex.",
            """<?php
declare(strict_types=1);

function randomHex(int $bytes = 8): string
{
    return bin2hex(random_bytes($bytes));
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["random_bytes.", "bin2hex."],
        ),
        live(
            "sscanf parse",
            "Функция parsePoint(string $raw): array парсит '(x,y)' через sscanf и возвращает [x, y] как int.",
            """<?php
declare(strict_types=1);

function parsePoint(string $raw): array
{
    $matched = sscanf($raw, '(%d,%d)', $x, $y);
    if ($matched !== 2) {
        return [0, 0];
    }
    return [(int) $x, (int) $y];
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["sscanf.", "При ошибке [0, 0]."],
        ),
        # --- Enums и Attributes (14) ---
        live(
            "Backed enum tryFrom",
            "Enum Role: string (Admin='admin', User='user') и функция parseRole(string $raw): ?Role "
            "через Role::tryFrom.",
            """<?php
declare(strict_types=1);

enum Role: string
{
    case Admin = 'admin';
    case User = 'user';
}

function parseRole(string $raw): ?Role
{
    return Role::tryFrom($raw);
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Backed enum.", "tryFrom без исключения."],
        ),
        live(
            "Enum cases list",
            "Enum Color: string (Red='red', Green='green') и функция allColors(): array "
            "возвращает массив значений из Color::cases().",
            """<?php
declare(strict_types=1);

enum Color: string
{
    case Red = 'red';
    case Green = 'green';
}

function allColors(): array
{
    return array_map(fn (Color $c): string => $c->value, Color::cases());
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Color::cases().", "Верните строковые value."],
        ),
        live(
            "Enum from throws",
            "Enum Level: int (Info=1, Error=2) и функция requireLevel(int $raw): Level через Level::from.",
            """<?php
declare(strict_types=1);

enum Level: int
{
    case Info = 1;
    case Error = 2;
}

function requireLevel(int $raw): Level
{
    return Level::from($raw);
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Level::from.", "int backed enum."],
        ),
        live(
            "Unit enum method",
            "Unit enum Direction { North, South } с методом opposite(): self.",
            """<?php
declare(strict_types=1);

enum Direction
{
    case North;
    case South;

    public function opposite(): self
    {
        return match ($this) {
            self::North => self::South,
            self::South => self::North,
        };
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Unit enum.", "Метод opposite()."],
        ),
        live(
            "Attribute Deprecated",
            "Класс LegacyApi с методом oldEndpoint(), помеченным #[\\Deprecated] (PHP 8.4+) "
            "или комментарием @deprecated и trigger_error(E_USER_DEPRECATED) внутри.",
            """<?php
declare(strict_types=1);

final class LegacyApi
{
    public function oldEndpoint(): void
    {
        trigger_error('oldEndpoint is deprecated', E_USER_DEPRECATED);
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["trigger_error E_USER_DEPRECATED.", "Публичный метод oldEndpoint()."],
        ),
        live(
            "Repeatable attribute",
            "Атрибут #[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)] class Tag { "
            "public function __construct(public string $name) {} } и метод с двумя #[Tag].",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
final class Tag
{
    public function __construct(public string $name)
    {
    }
}

final class TaggedService
{
    #[Tag('cache')]
    #[Tag('metrics')]
    public function run(): void
    {
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["IS_REPEATABLE.", "Два Tag на одном методе."],
        ),
        live(
            "Attribute reader",
            "Функция readRoutePath(object $object, string $method): ?string читает первый атрибут Route "
            "через ReflectionMethod::getAttributes(Route::class).",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_METHOD)]
final class Route
{
    public function __construct(public string $path)
    {
    }
}

function readRoutePath(object $object, string $method): ?string
{
    $ref = new ReflectionMethod($object, $method);
    $attrs = $ref->getAttributes(Route::class);
    if ($attrs === []) {
        return null;
    }
    return $attrs[0]->newInstance()->path;
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["ReflectionMethod.", "Верните path или null."],
        ),
        live(
            "Backed enum json serialize",
            "Enum Status: string (Ok='ok', Fail='fail') и функция statusToJson(Status $s): string "
            "кодирующая ['status' => $s->value].",
            """<?php
declare(strict_types=1);

enum Status: string
{
    case Ok = 'ok';
    case Fail = 'fail';
}

function statusToJson(Status $status): string
{
    return json_encode(['status' => $status->value], JSON_THROW_ON_ERROR);
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["JSON с value enum.", "Backed enum Status."],
        ),
        live(
            "Property attribute",
            "Атрибут #[Column('email')] на promoted property string $email в readonly class UserRecord.",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_PROPERTY)]
final class Column
{
    public function __construct(public string $name)
    {
    }
}

readonly class UserRecord
{
    public function __construct(
        #[Column('email')]
        public string $email,
    ) {
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Attribute на property.", "readonly class."],
        ),
        live(
            "Class attribute Target",
            "Атрибут #[Entity('users')] на классе UserEntity с методом table(): string, "
            "читающим имя из ReflectionClass.",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_CLASS)]
final class Entity
{
    public function __construct(public string $table)
    {
    }
}

#[Entity('users')]
final class UserEntity
{
    public function table(): string
    {
        $ref = new ReflectionClass(self::class);
        $attrs = $ref->getAttributes(Entity::class);
        return $attrs[0]->newInstance()->table;
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["TARGET_CLASS.", "ReflectionClass в table()."],
        ),
        live(
            "Enum interface pattern",
            "Interface Labelable { public function label(): string; } и enum Size: string implements Labelable "
            "(S='s', M='m') с label() возвращающим value в upper.",
            """<?php
declare(strict_types=1);

interface Labelable
{
    public function label(): string;
}

enum Size: string implements Labelable
{
    case S = 's';
    case M = 'm';

    public function label(): string
    {
        return strtoupper($this->value);
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["enum implements interface.", "label() в upper case."],
        ),
        live(
            "Parameter attribute",
            "Атрибут #[Valid('email')] и функция validate(#[Valid('email')] string $email): string "
            "возвращающая trim($email) (атрибут только объявите).",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_PARAMETER)]
final class Valid
{
    public function __construct(public string $rule)
    {
    }
}

function validate(#[Valid('email')] string $email): string
{
    return trim($email);
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["TARGET_PARAMETER.", "Атрибут на параметре."],
        ),
        live(
            "Flags enum bit",
            "Enum Permission: int (Read=1, Write=2, Execute=4) и функция hasFlag(int $mask, Permission $p): bool.",
            """<?php
declare(strict_types=1);

enum Permission: int
{
    case Read = 1;
    case Write = 2;
    case Execute = 4;
}

function hasFlag(int $mask, Permission $permission): bool
{
    return ($mask & $permission->value) === $permission->value;
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Битовая маска.", "Строгое сравнение ===."],
        ),
        live(
            "Attribute constructor promote",
            "Атрибут CacheTtl с promoted public int $seconds и использование #[CacheTtl(60)] на методе.",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_METHOD)]
final class CacheTtl
{
    public function __construct(public int $seconds)
    {
    }
}

final class ReportService
{
    #[CacheTtl(60)]
    public function build(): array
    {
        return [];
    }
}""",
            lang="php",
            topic="Enums и Attributes",
            requirements=["Promoted property в атрибуте.", "Пример на методе."],
        ),
        # --- PDO и HTTP (14) ---
        live(
            "PDO transaction",
            "Функция transfer(PDO $pdo, int $from, int $to, int $amount): void открывает транзакцию, "
            "выполняет два UPDATE и commit; при PDOException — rollBack и проброс.",
            """<?php
declare(strict_types=1);

function transfer(PDO $pdo, int $from, int $to, int $amount): void
{
    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ?');
        $stmt->execute([$amount, $from]);
        $stmt = $pdo->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?');
        $stmt->execute([$amount, $to]);
        $pdo->commit();
    } catch (PDOException $e) {
        $pdo->rollBack();
        throw $e;
    }
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["beginTransaction/commit.", "rollBack в catch."],
        ),
        live(
            "PDO INSERT lastInsertId",
            "Функция createUser(PDO $pdo, string $email): int вставляет строку в users(email) "
            "и возвращает (int) lastInsertId().",
            """<?php
declare(strict_types=1);

function createUser(PDO $pdo, string $email): int
{
    $stmt = $pdo->prepare('INSERT INTO users (email) VALUES (?)');
    $stmt->execute([$email]);
    return (int) $pdo->lastInsertId();
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["Prepared INSERT.", "lastInsertId()."],
        ),
        live(
            "PDO FETCH_CLASS",
            "Класс UserRow с public int $id, string $email и функция fetchUser(PDO $pdo, int $id): ?UserRow "
            "через PDO::FETCH_CLASS.",
            """<?php
declare(strict_types=1);

final class UserRow
{
    public int $id;
    public string $email;
}

function fetchUser(PDO $pdo, int $id): ?UserRow
{
    $stmt = $pdo->prepare('SELECT id, email FROM users WHERE id = ?');
    $stmt->execute([$id]);
    $stmt->setFetchMode(PDO::FETCH_CLASS, UserRow::class);
    $row = $stmt->fetch();
    return $row instanceof UserRow ? $row : null;
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["FETCH_CLASS.", "nullable возврат."],
        ),
        live(
            "PDO emulate prepares off",
            "Функция configurePdo(PDO $pdo): void отключает эмуляцию prepared statements "
            "через setAttribute(PDO::ATTR_EMULATE_PREPARES, false).",
            """<?php
declare(strict_types=1);

function configurePdo(PDO $pdo): void
{
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["ATTR_EMULATE_PREPARES false.", "Тип void."],
        ),
        live(
            "Curl GET stub",
            "Класс CurlClient с методом get(string $url): string использующим curl_init/curl_exec/curl_close "
            "(заглушка без реального URL в тесте).",
            """<?php
declare(strict_types=1);

final class CurlClient
{
    public function get(string $url): string
    {
        $handle = curl_init($url);
        curl_setopt($handle, CURLOPT_RETURNTRANSFER, true);
        $body = curl_exec($handle);
        curl_close($handle);
        return is_string($body) ? $body : '';
    }
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["curl_init/exec/close.", "CURLOPT_RETURNTRANSFER."],
        ),
        live(
            "HTTP response headers",
            "Функция buildJsonResponse(array $data, int $status = 200): void отправляет header Content-Type "
            "и http_response_code, затем echo json_encode.",
            """<?php
declare(strict_types=1);

function buildJsonResponse(array $data, int $status = 200): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_THROW_ON_ERROR);
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["http_response_code.", "JSON Content-Type."],
        ),
        live(
            "Session start handler",
            "Функция startSecureSession(): void вызывает session_start() после ini_set session.cookie_httponly=1.",
            """<?php
declare(strict_types=1);

function startSecureSession(): void
{
    ini_set('session.cookie_httponly', '1');
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["session_start.", "cookie_httponly."],
        ),
        live(
            "Session flash message",
            "Функции flash(string $key, string $message): void сохраняют в $_SESSION[$key] "
            "и takeFlash(string $key): ?string читает и удаляет значение.",
            """<?php
declare(strict_types=1);

function flash(string $key, string $message): void
{
    $_SESSION[$key] = $message;
}

function takeFlash(string $key): ?string
{
    if (!isset($_SESSION[$key])) {
        return null;
    }
    $value = (string) $_SESSION[$key];
    unset($_SESSION[$key]);
    return $value;
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["Запись в $_SESSION.", "takeFlash удаляет ключ."],
        ),
        live(
            "setcookie signature",
            "Функция setRememberCookie(string $token, int $ttl = 86400): void вызывает setcookie "
            "с HttpOnly, Secure, SameSite=Strict (массив options PHP 7.3+).",
            """<?php
declare(strict_types=1);

function setRememberCookie(string $token, int $ttl = 86400): void
{
    setcookie('remember', $token, [
        'expires' => time() + $ttl,
        'path' => '/',
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["setcookie с массивом опций.", "HttpOnly и SameSite."],
        ),
        live(
            "File upload stub",
            "Функция validateUpload(array $file): string проверяет UPLOAD_ERR_OK и mime через finfo_file, "
            "возвращая расширение 'pdf' или бросая InvalidArgumentException.",
            """<?php
declare(strict_types=1);

function validateUpload(array $file): string
{
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) {
        throw new InvalidArgumentException('Upload failed');
    }
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mime = $finfo->file($file['tmp_name']);
    if ($mime !== 'application/pdf') {
        throw new InvalidArgumentException('Only PDF allowed');
    }
    return 'pdf';
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["Проверка error.", "finfo MIME pdf."],
        ),
        live(
            "stream_context HTTP",
            "Функция fetchWithTimeout(string $url, int $seconds = 5): string создаёт stream_context "
            "с timeout и file_get_contents.",
            """<?php
declare(strict_types=1);

function fetchWithTimeout(string $url, int $seconds = 5): string
{
    $context = stream_context_create([
        'http' => ['timeout' => $seconds],
    ]);
    $body = file_get_contents($url, false, $context);
    return is_string($body) ? $body : '';
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["stream_context_create.", "file_get_contents."],
        ),
        live(
            "php://memory stream",
            "Функция writeToMemory(string $data): string пишет $data в php://memory через fopen/fwrite/stream_get_contents.",
            """<?php
declare(strict_types=1);

function writeToMemory(string $data): string
{
    $handle = fopen('php://memory', 'r+');
    fwrite($handle, $data);
    rewind($handle);
    $contents = stream_get_contents($handle);
    fclose($handle);
    return is_string($contents) ? $contents : '';
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["php://memory.", "rewind перед чтением."],
        ),
        live(
            "filter_input GET",
            "Функция readPageParam(): int читает GET page через filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT) "
            "или 1 по умолчанию.",
            """<?php
declare(strict_types=1);

function readPageParam(): int
{
    $page = filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT);
    return is_int($page) && $page > 0 ? $page : 1;
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["filter_input INPUT_GET.", "Default 1."],
        ),
        live(
            "Request method guard",
            "Функция requirePost(): void бросает RuntimeException, если $_SERVER['REQUEST_METHOD'] !== 'POST'.",
            """<?php
declare(strict_types=1);

function requirePost(): void
{
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') {
        throw new RuntimeException('POST required');
    }
}""",
            lang="php",
            topic="PDO и HTTP",
            requirements=["Проверка REQUEST_METHOD.", "RuntimeException."],
        ),
        # --- Паттерны (14) ---
        live(
            "Strategy pricing",
            "Интерфейс PricingStrategy с amount(int $qty): int; классы FixedPrice и TenPercentDiscount.",
            """<?php
declare(strict_types=1);

interface PricingStrategy
{
    public function amount(int $qty): int;
}

final class FixedPrice implements PricingStrategy
{
    public function __construct(private int $unit)
    {
    }

    public function amount(int $qty): int
    {
        return $this->unit * $qty;
    }
}

final class TenPercentDiscount implements PricingStrategy
{
    public function __construct(private PricingStrategy $inner)
    {
    }

    public function amount(int $qty): int
    {
        $base = $this->inner->amount($qty);
        return (int) round($base * 0.9);
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Интерфейс Strategy.", "Декоратор скидки."],
        ),
        live(
            "Factory method",
            "Abstract class NotificationFactory с abstract create(): Notification "
            "и EmailNotificationFactory возвращающий new EmailNotification().",
            """<?php
declare(strict_types=1);

interface Notification
{
    public function send(): void;
}

final class EmailNotification implements Notification
{
    public function send(): void
    {
        echo 'email', PHP_EOL;
    }
}

abstract class NotificationFactory
{
    abstract public function create(): Notification;
}

final class EmailNotificationFactory extends NotificationFactory
{
    public function create(): Notification
    {
        return new EmailNotification();
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Abstract factory.", "EmailNotification."],
        ),
        live(
            "Repository stub",
            "Интерфейс UserRepository { findById(int $id): ?UserRow } и InMemoryUserRepository "
            "с private array $store.",
            """<?php
declare(strict_types=1);

final class UserRow
{
    public function __construct(public int $id, public string $email)
    {
    }
}

interface UserRepository
{
    public function findById(int $id): ?UserRow;
}

final class InMemoryUserRepository implements UserRepository
{
    /** @var array<int, UserRow> */
    private array $store = [];

    public function add(UserRow $user): void
    {
        $this->store[$user->id] = $user;
    }

    public function findById(int $id): ?UserRow
    {
        return $this->store[$id] ?? null;
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Интерфейс Repository.", "In-memory реализация."],
        ),
        live(
            "Event dispatcher",
            "Класс EventDispatcher с listen(string $event, callable $handler): void "
            "и dispatch(string $event, mixed $payload = null): void вызывающим все обработчики.",
            """<?php
declare(strict_types=1);

final class EventDispatcher
{
    /** @var array<string, list<callable>> */
    private array $listeners = [];

    public function listen(string $event, callable $handler): void
    {
        $this->listeners[$event][] = $handler;
    }

    public function dispatch(string $event, mixed $payload = null): void
    {
        foreach ($this->listeners[$event] ?? [] as $handler) {
            $handler($payload);
        }
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["listen + dispatch.", "Несколько обработчиков на событие."],
        ),
        live(
            "Middleware pipeline",
            "Класс MiddlewarePipeline с pipe(callable $middleware): self и handle(mixed $request): mixed, "
            "где каждый middleware — fn($req, $next).",
            """<?php
declare(strict_types=1);

final class MiddlewarePipeline
{
    /** @var list<callable> */
    private array $stack = [];

    public function pipe(callable $middleware): self
    {
        $this->stack[] = $middleware;
        return $this;
    }

    public function handle(mixed $request): mixed
    {
        $runner = array_reduce(
            array_reverse($this->stack),
            fn (callable $next, callable $mw): callable => fn (mixed $req): mixed => $mw($req, $next),
            fn (mixed $req): mixed => $req,
        );
        return $runner($request);
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Onion middleware.", "pipe возвращает self."],
        ),
        live(
            "Value object Money",
            "Класс Money с private int $cents и string $currency; сложение add(Money $other): self "
            "только при одинаковой валюте, иначе InvalidArgumentException.",
            """<?php
declare(strict_types=1);

final class Money
{
    public function __construct(private int $cents, private string $currency)
    {
    }

    public function add(self $other): self
    {
        if ($this->currency !== $other->currency) {
            throw new InvalidArgumentException('Currency mismatch');
        }
        return new self($this->cents + $other->cents, $this->currency);
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Приватные поля.", "Проверка валюты."],
        ),
        live(
            "Command bus",
            "Интерфейс CommandHandler { handle(object $command): void } и CommandBus "
            "с register(string $class, CommandHandler $handler) и dispatch(object $command).",
            """<?php
declare(strict_types=1);

interface CommandHandler
{
    public function handle(object $command): void;
}

final class CommandBus
{
    /** @var array<string, CommandHandler> */
    private array $handlers = [];

    public function register(string $commandClass, CommandHandler $handler): void
    {
        $this->handlers[$commandClass] = $handler;
    }

    public function dispatch(object $command): void
    {
        $class = $command::class;
        if (!isset($this->handlers[$class])) {
            throw new RuntimeException("No handler for {$class}");
        }
        $this->handlers[$class]->handle($command);
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["register по классу команды.", "dispatch вызывает handler."],
        ),
        live(
            "Observer SPL",
            "Класс JobSubject implements SplSubject с attach/detach/notify и JobObserver implements SplObserver.",
            """<?php
declare(strict_types=1);

final class JobSubject implements SplSubject
{
    /** @var SplObjectStorage<SplObserver, null> */
    private SplObjectStorage $observers;

    public function __construct()
    {
        $this->observers = new SplObjectStorage();
    }

    public function attach(SplObserver $observer): void
    {
        $this->observers->attach($observer);
    }

    public function detach(SplObserver $observer): void
    {
        $this->observers->detach($observer);
    }

    public function notify(): void
    {
        foreach ($this->observers as $observer) {
            $observer->update($this);
        }
    }
}

final class JobObserver implements SplObserver
{
    public function update(SplSubject $subject): void
    {
        echo 'updated', PHP_EOL;
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["SplSubject/SplObserver.", "SplObjectStorage."],
        ),
        live(
            "Specification pattern",
            "Интерфейс Specification { isSatisfiedBy(int $value): bool } и классы EvenSpec и GreaterThanSpec.",
            """<?php
declare(strict_types=1);

interface Specification
{
    public function isSatisfiedBy(int $value): bool;
}

final class EvenSpec implements Specification
{
    public function isSatisfiedBy(int $value): bool
    {
        return $value % 2 === 0;
    }
}

final class GreaterThanSpec implements Specification
{
    public function __construct(private int $min)
    {
    }

    public function isSatisfiedBy(int $value): bool
    {
        return $value > $this->min;
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Интерфейс Specification.", "Две реализации."],
        ),
        live(
            "Adapter legacy",
            "Класс LegacyLogger с logRaw(string $msg) и Adapter implements LoggerInterface "
            "с log($level, $message) делегирующим logRaw.",
            """<?php
declare(strict_types=1);

final class LegacyLogger
{
    public function logRaw(string $message): void
    {
        echo $message, PHP_EOL;
    }
}

interface LoggerInterface
{
    public function log(string $level, string $message): void;
}

final class LoggerAdapter implements LoggerInterface
{
    public function __construct(private LegacyLogger $legacy)
    {
    }

    public function log(string $level, string $message): void
    {
        $this->legacy->logRaw("[{$level}] {$message}");
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Adapter оборачивает LegacyLogger.", "Метод log(level, message)."],
        ),
        live(
            "DTO mapper",
            "Readonly class AddressDto(string $city, string $zip) и AddressMapper::fromRow(array $row): AddressDto.",
            """<?php
declare(strict_types=1);

readonly class AddressDto
{
    public function __construct(public string $city, public string $zip)
    {
    }
}

final class AddressMapper
{
    public function fromRow(array $row): AddressDto
    {
        return new AddressDto(
            (string) ($row['city'] ?? ''),
            (string) ($row['zip'] ?? ''),
        );
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["readonly DTO.", "Mapper fromRow."],
        ),
        live(
            "Null object pattern",
            "Интерфейс Cache { get(string $key): ?string } и NullCache всегда возвращающий null.",
            """<?php
declare(strict_types=1);

interface Cache
{
    public function get(string $key): ?string;
}

final class NullCache implements Cache
{
    public function get(string $key): ?string
    {
        return null;
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Null object Cache.", "get всегда null."],
        ),
        live(
            "Builder step",
            "Класс QueryBuilder с select(string $cols): self, from(string $table): self и build(): string.",
            """<?php
declare(strict_types=1);

final class QueryBuilder
{
    private string $columns = '*';
    private string $table = '';

    public function select(string $columns): self
    {
        $this->columns = $columns;
        return $this;
    }

    public function from(string $table): self
    {
        $this->table = $table;
        return $this;
    }

    public function build(): string
    {
        return "SELECT {$this->columns} FROM {$this->table}";
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Fluent interface.", "build() возвращает SQL."],
        ),
        live(
            "Chain of responsibility",
            "Abstract class Handler с setNext(Handler $next) и handle(int $n): ?int; "
            "EvenHandler возвращает $n/2 если чётное, иначе передаёт дальше.",
            """<?php
declare(strict_types=1);

abstract class Handler
{
    private ?Handler $next = null;

    public function setNext(Handler $handler): Handler
    {
        $this->next = $handler;
        return $handler;
    }

    public function handle(int $value): ?int
    {
        return $this->next?->handle($value);
    }
}

final class EvenHandler extends Handler
{
    public function handle(int $value): ?int
    {
        if ($value % 2 === 0) {
            return (int) ($value / 2);
        }
        return parent::handle($value);
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["setNext chain.", "EvenHandler обрабатывает чётные."],
        ),
        # --- Extra cross-topic (4) to reach ~116 ---
        live(
            "Exception hierarchy",
            "Классы DomainException extends RuntimeException и UserNotFoundException extends DomainException; "
            "функция findOrFail(?UserRow $user): UserRow бросает UserNotFoundException если null.",
            """<?php
declare(strict_types=1);

final class UserRow
{
    public function __construct(public int $id, public string $email)
    {
    }
}

class DomainException extends RuntimeException
{
}

final class UserNotFoundException extends DomainException
{
}

function findOrFail(?UserRow $user): UserRow
{
    if ($user === null) {
        throw new UserNotFoundException('User not found');
    }
    return $user;
}""",
            lang="php",
            topic="ООП",
            requirements=["Иерархия исключений.", "findOrFail бросает UserNotFoundException."],
        ),
        live(
            "SplStack undo",
            "Класс UndoStack с private SplStack $stack, push(string $state): void и pop(): ?string.",
            """<?php
declare(strict_types=1);

final class UndoStack
{
    private SplStack $stack;

    public function __construct()
    {
        $this->stack = new SplStack();
    }

    public function push(string $state): void
    {
        $this->stack->push($state);
    }

    public function pop(): ?string
    {
        if ($this->stack->isEmpty()) {
            return null;
        }
        return $this->stack->pop();
    }
}""",
            lang="php",
            topic="Массивы",
            requirements=["SplStack.", "pop на пустом → null."],
        ),
        live(
            "filter_var validation",
            "Класс UrlValue с конструктором, принимающим string $url и бросающим InvalidArgumentException, "
            "если filter_var($url, FILTER_VALIDATE_URL) === false.",
            """<?php
declare(strict_types=1);

final class UrlValue
{
    public function __construct(public readonly string $value)
    {
        if (filter_var($value, FILTER_VALIDATE_URL) === false) {
            throw new InvalidArgumentException('Invalid URL');
        }
    }
}""",
            lang="php",
            topic="Строки и JSON",
            requirements=["filter_var FILTER_VALIDATE_URL.", "readonly property value."],
        ),
        live(
            "SOLID DIP",
            "Интерфейс Mailer { send(string $to, string $body): void } и класс UserService "
            "получающий Mailer в конструкторе (dependency injection), метод notify(UserRow $user).",
            """<?php
declare(strict_types=1);

final class UserRow
{
    public function __construct(public int $id, public string $email)
    {
    }
}

interface Mailer
{
    public function send(string $to, string $body): void;
}

final class UserService
{
    public function __construct(private Mailer $mailer)
    {
    }

    public function notify(UserRow $user): void
    {
        $this->mailer->send($user->email, 'Welcome!');
    }
}""",
            lang="php",
            topic="Паттерны",
            requirements=["Зависимость от интерфейса Mailer.", "Конструкторная инъекция."],
        ),
    ]
