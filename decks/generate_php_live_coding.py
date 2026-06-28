#!/usr/bin/env python3
"""Generate PHP Live-coding deck (write code from scratch)."""
from __future__ import annotations

import json
from pathlib import Path


def live(q: str, task: str, ref: str, *, lang: str = "php") -> dict:
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
            "Напиши функцию greet(string $name): string, возвращающую \"Hello, {$name}!\".",
            """<?php
declare(strict_types=1);

function greet(string $name): string
{
    return "Hello, {$name}!";
}""",
        ),
        live(
            "Сумма массива",
            "Функция total(array $numbers): int — сумма элементов (без array_sum).",
            """<?php
declare(strict_types=1);

function total(array $numbers): int
{
    $sum = 0;
    foreach ($numbers as $n) {
        $sum += $n;
    }
    return $sum;
}""",
        ),
        live(
            "array_map — квадраты",
            "Функция squares(array $numbers): array — квадраты каждого int.",
            """<?php
declare(strict_types=1);

function squares(array $numbers): array
{
    return array_map(fn (int $n): int => $n * $n, $numbers);
}""",
        ),
        live(
            "array_filter чётные",
            "Функция evens(array $numbers): array — только чётные числа.",
            """<?php
declare(strict_types=1);

function evens(array $numbers): array
{
    return array_values(array_filter($numbers, fn (int $n): bool => $n % 2 === 0));
}""",
        ),
        live(
            "Constructor property promotion",
            "Класс User с promoted properties public int $id и public string $email.",
            """<?php
declare(strict_types=1);

final class User
{
    public function __construct(
        public int $id,
        public string $email,
    ) {
    }
}""",
        ),
        live(
            "Readonly class DTO",
            "Readonly class Money с полями int $amount и string $currency (PHP 8.2+).",
            """<?php
declare(strict_types=1);

readonly class Money
{
    public function __construct(
        public int $amount,
        public string $currency,
    ) {
    }
}""",
        ),
        live(
            "match HTTP status",
            "Функция statusLabel(int $code): string через match: 200->'OK', 404->'Not Found', default 'Unknown'.",
            """<?php
declare(strict_types=1);

function statusLabel(int $code): string
{
    return match ($code) {
        200 => 'OK',
        404 => 'Not Found',
        default => 'Unknown',
    };
}""",
        ),
        live(
            "Nullsafe operator",
            "Функция userCity(?User $user): ?string — вернуть $user?->address?->city.",
            """<?php
declare(strict_types=1);

function userCity(?User $user): ?string
{
    return $user?->address?->city;
}""",
        ),
        live(
            "Backed enum Status",
            "Enum Status: string с case Active='active', Archived='archived'.",
            """<?php
declare(strict_types=1);

enum Status: string
{
    case Active = 'active';
    case Archived = 'archived';
}""",
        ),
        live(
            "Named arguments",
            "Функция createUser(string $email, int $id = 0): User — вызов с named args id и email в примере комментария.",
            """<?php
declare(strict_types=1);

function createUser(string $email, int $id = 0): User
{
    return new User(id: $id, email: $email);
}

// createUser(id: 1, email: 'a@b.c');""",
        ),
        live(
            "Interface + implementation",
            "Interface Logger с log(string $message): void; класс EchoLogger.",
            """<?php
declare(strict_types=1);

interface Logger
{
    public function log(string $message): void;
}

final class EchoLogger implements Logger
{
    public function log(string $message): void
    {
        echo $message, PHP_EOL;
    }
}""",
        ),
        live(
            "PDO prepared SELECT",
            "Функция fetchUserName(PDO $pdo, int $id): ?string — SELECT name FROM users WHERE id = ?.",
            """<?php
declare(strict_types=1);

function fetchUserName(PDO $pdo, int $id): ?string
{
    $stmt = $pdo->prepare('SELECT name FROM users WHERE id = ?');
    $stmt->execute([$id]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    return $row['name'] ?? null;
}""",
        ),
        live(
            "JSON encode/decode",
            "Функция toJson(array $data): string через json_encode с JSON_THROW_ON_ERROR.",
            """<?php
declare(strict_types=1);

function toJson(array $data): string
{
    return json_encode($data, JSON_THROW_ON_ERROR);
}""",
        ),
        live(
            "Custom exception",
            "Класс ValidationException extends Exception; validateNonEmpty(string $value, string $field): string.",
            """<?php
declare(strict_types=1);

final class ValidationException extends Exception
{
    public function __construct(public readonly string $field, string $message)
    {
        parent::__construct($message);
    }
}

function validateNonEmpty(string $value, string $field): string
{
    if (trim($value) === '') {
        throw new ValidationException($field, 'must not be empty');
    }
    return $value;
}""",
        ),
        live(
            "Arrow function pipeline",
            "Функция positiveSquares(array $numbers): array — квадраты положительных через array_filter + array_map.",
            """<?php
declare(strict_types=1);

function positiveSquares(array $numbers): array
{
    $positive = array_filter($numbers, fn (int $n): bool => $n > 0);
    return array_map(fn (int $n): int => $n * $n, $positive);
}""",
        ),
        live(
            "First-class callable",
            "Класс Calculator с add(int $a, int $b): int; переменная $fn = $calc->add(...).",
            """<?php
declare(strict_types=1);

final class Calculator
{
    public function add(int $a, int $b): int
    {
        return $a + $b;
    }
}

$calc = new Calculator();
$fn = $calc->add(...);""",
        ),
        live(
            "Trait Timestampable",
            "Trait Timestampable с protected ?DateTimeImmutable $createdAt и методом touch(): void.",
            """<?php
declare(strict_types=1);

trait Timestampable
{
    protected ?DateTimeImmutable $createdAt = null;

    public function touch(): void
    {
        $this->createdAt = new DateTimeImmutable();
    }
}""",
        ),
        live(
            "Attribute Route",
            "Атрибут #[Route('/api/users')] над методом listUsers().",
            """<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_METHOD)]
final class Route
{
    public function __construct(public string $path)
    {
    }
}

final class UserController
{
    #[Route('/api/users')]
    public function listUsers(): array
    {
        return [];
    }
}""",
        ),
        live(
            "Union type parseId",
            "Функция parseId(int|string $value): int — если string, (int)$value.",
            """<?php
declare(strict_types=1);

function parseId(int|string $value): int
{
    return is_int($value) ? $value : (int) $value;
}""",
        ),
        live(
            "Generator rangeStep",
            "Generator function rangeStep(int $start, int $stop, int $step = 1): Generator.",
            """<?php
declare(strict_types=1);

function rangeStep(int $start, int $stop, int $step = 1): Generator
{
    for ($value = $start; $value < $stop; $value += $step) {
        yield $value;
    }
}""",
        ),
        live(
            "Closure counter",
            "Функция makeCounter(): Closure возвращает closure, увеличивающий внутренний счётчик.",
            """<?php
declare(strict_types=1);

function makeCounter(): Closure
{
    $count = 0;
    return function () use (&$count): int {
        return ++$count;
    };
}""",
        ),
        live(
            "str_contains helper",
            "Функция contains(string $haystack, string $needle): bool через str_contains().",
            """<?php
declare(strict_types=1);

function contains(string $haystack, string $needle): bool
{
    return str_contains($haystack, $needle);
}""",
        ),
        live(
            "DateTime format",
            "Функция formatToday(string $format = 'Y-m-d'): string через new DateTimeImmutable('today').",
            """<?php
declare(strict_types=1);

function formatToday(string $format = 'Y-m-d'): string
{
    return (new DateTimeImmutable('today'))->format($format);
}""",
        ),
        live(
            "SplFileObject read lines",
            "Функция readLines(string $path): array читает файл построчно через SplFileObject.",
            """<?php
declare(strict_types=1);

function readLines(string $path): array
{
    $file = new SplFileObject($path);
    $lines = [];
    foreach ($file as $line) {
        if ($line === false) {
            continue;
        }
        $lines[] = rtrim($line, "\\r\\n");
    }
    return $lines;
}""",
        ),
        live(
            "Namespace autoload class",
            "Namespace App\\Service; final class Greeter с методом hello(string $name): string.",
            """<?php
declare(strict_types=1);

namespace App\\Service;

final class Greeter
{
    public function hello(string $name): string
    {
        return "Hi, {$name}";
    }
}""",
        ),
        live(
            "Static factory",
            "Класс Email с private __construct и static fromString(string $raw): self.",
            """<?php
declare(strict_types=1);

final class Email
{
    private function __construct(public readonly string $value)
    {
    }

    public static function fromString(string $raw): self
    {
        return new self(trim($raw));
    }
}""",
        ),
        live(
            "Array combine",
            "Функция combine(array $keys, array $values): array через array_combine (одинаковая длина).",
            """<?php
declare(strict_types=1);

function combine(array $keys, array $values): array
{
    return array_combine($keys, $values);
}""",
        ),
        live(
            "Spread merge arrays",
            "Функция mergeArrays(array ...$parts): array через array_merge.",
            """<?php
declare(strict_types=1);

function mergeArrays(array ...$parts): array
{
    return array_merge(...$parts);
}""",
        ),
        live(
            "Enum method label",
            "Backed enum Priority: int (Low=1, High=2) с методом label(): string.",
            """<?php
declare(strict_types=1);

enum Priority: int
{
    case Low = 1;
    case High = 2;

    public function label(): string
    {
        return match ($this) {
            self::Low => 'low',
            self::High => 'high',
        };
    }
}""",
        ),
        live(
            "Readonly promotion Order",
            "Readonly class Order с promoted properties string $id и float $total.",
            """<?php
declare(strict_types=1);

readonly class Order
{
    public function __construct(
        public string $id,
        public float $total,
    ) {
    }
}""",
        ),
        live(
            "Throw expression",
            "Функция requirePositive(int $n): int с $n > 0 ?: throw new InvalidArgumentException().",
            """<?php
declare(strict_types=1);

function requirePositive(int $n): int
{
    return $n > 0 ? $n : throw new InvalidArgumentException('must be positive');
}""",
        ),
        live(
            "htmlspecialchars helper",
            "Функция e(string $value): string — htmlspecialchars с ENT_QUOTES и UTF-8.",
            """<?php
declare(strict_types=1);

function e(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}""",
        ),
        live(
            "Password hash verify",
            "Функции hashPassword(string $plain): string и verifyPassword(string $plain, string $hash): bool.",
            """<?php
declare(strict_types=1);

function hashPassword(string $plain): string
{
    return password_hash($plain, PASSWORD_DEFAULT);
}

function verifyPassword(string $plain, string $hash): bool
{
    return password_verify($plain, $hash);
}""",
        ),
        live(
            "Simple router",
            "Класс Router с методами get(string $path, callable $handler): void и dispatch(string $method, string $path).",
            """<?php
declare(strict_types=1);

final class Router
{
    /** @var array<string, callable> */
    private array $routes = [];

    public function get(string $path, callable $handler): void
    {
        $this->routes['GET ' . $path] = $handler;
    }

    public function dispatch(string $method, string $path): mixed
    {
        $key = $method . ' ' . $path;
        if (!isset($this->routes[$key])) {
            throw new RuntimeException('Not found');
        }
        return ($this->routes[$key])();
    }
}""",
        ),
        live(
            "Value object Email validate",
            "Класс EmailValue с private string $value, конструктор валидирует filter_var FILTER_VALIDATE_EMAIL.",
            """<?php
declare(strict_types=1);

final class EmailValue
{
    public function __construct(private readonly string $value)
    {
        if (filter_var($value, FILTER_VALIDATE_EMAIL) === false) {
            throw new InvalidArgumentException('Invalid email');
        }
    }

    public function toString(): string
    {
        return $this->value;
    }
}""",
        ),
        live(
            "Fibonacci generator",
            "Generator function fibonacci(int $count): Generator — первые $count чисел Фибоначчи.",
            """<?php
declare(strict_types=1);

function fibonacci(int $count): Generator
{
    $a = 0;
    $b = 1;
    for ($i = 0; $i < $count; $i++) {
        yield $a;
        [$a, $b] = [$b, $a + $b];
    }
}""",
        ),
        live(
            "Palindrome check",
            "Функция isPalindrome(string $text): bool — игнорировать регистр и не-буквы.",
            """<?php
declare(strict_types=1);

function isPalindrome(string $text): bool
{
    $clean = strtolower(preg_replace('/[^a-z0-9]/i', '', $text) ?? '');
    return $clean === strrev($clean);
}""",
        ),
        live(
            "HttpClient stub",
            "Класс HttpResponse с promoted int $status, string $body и методом isSuccessful(): bool.",
            """<?php
declare(strict_types=1);

final class HttpResponse
{
    public function __construct(
        public int $status,
        public string $body,
    ) {
    }

    public function isSuccessful(): bool
    {
        return $this->status >= 200 && $this->status < 300;
    }
}""",
        ),
    ]


def main() -> None:
    cards = build_cards()
    deck = {"name": "PHP Live-coding", "cards": cards}
    out = Path(__file__).with_name("php-live-coding.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} live_code cards -> {out}")


if __name__ == "__main__":
    main()
