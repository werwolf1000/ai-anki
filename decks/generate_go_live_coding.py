#!/usr/bin/env python3
"""Generate Go Live-coding deck (write code from scratch)."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from go_topics import TOPICS
from live_coding_card import live as _live
from live_coding_topics import assign_topics


def live(*args, **kwargs):
    kwargs.setdefault("lang", "go")
    return _live(*args, **kwargs)


def build_cards() -> list[dict]:
    return [
        live(
            "Функция greet",
            "Напиши функцию greet(name string) string, возвращающую \"Hello, \" + name + \"!\".",
            """package main

func greet(name string) string {
    return "Hello, " + name + "!"
}""",
            topic="Основы",
        ),
        live(
            "Сумма слайса",
            "Функция sum(nums []int) int — сумма элементов без использования встроенных reduce.",
            """package main

func sum(nums []int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}""",
            topic="Типы и структуры",
        ),
        live(
            "Filter evens",
            "Функция evens(nums []int) []int возвращает только чётные числа, сохраняя порядок.",
            """package main

func evens(nums []int) []int {
    out := make([]int, 0, len(nums))
    for _, n := range nums {
        if n%2 == 0 {
            out = append(out, n)
        }
    }
    return out
}""",
            topic="Типы и структуры",
        ),
        live(
            "Map word count",
            "Функция wordCount(words []string) map[string]int считает частоту каждого слова.",
            """package main

func wordCount(words []string) map[string]int {
    counts := make(map[string]int)
    for _, w := range words {
        counts[w]++
    }
    return counts
}""",
            topic="Типы и структуры",
        ),
        live(
            "Struct User",
            "Тип User с полями ID int и Name string; конструктор NewUser(id int, name string) User.",
            """package main

type User struct {
    ID   int
    Name string
}

func NewUser(id int, name string) User {
    return User{ID: id, Name: name}
}""",
            topic="Типы и структуры",
        ),
        live(
            "Defer close pattern",
            "Функция readAll(r io.Reader) ([]byte, error) читает через io.ReadAll (defer не нужен для ReadAll, но обработай err).",
            """package main

import "io"

func readAll(r io.Reader) ([]byte, error) {
    return io.ReadAll(r)
}""",
            topic="Функции и defer",
        ),
        live(
            "Fibonacci",
            "Функция fib(n int) int возвращает n-ое число Фибоначчи (n >= 0), итеративно.",
            """package main

func fib(n int) int {
    if n < 2 {
        return n
    }
    a, b := 0, 1
    for i := 2; i <= n; i++ {
        a, b = b, a+b
    }
    return b
}""",
            topic="Функции и defer",
        ),
        live(
            "Method String on Point",
            "Struct Point { X, Y int } с методом String() string формата \"(x,y)\" для fmt.",
            """package main

import "fmt"

type Point struct {
    X, Y int
}

func (p Point) String() string {
    return fmt.Sprintf("(%d,%d)", p.X, p.Y)
}""",
            topic="Методы и интерфейсы",
        ),
        live(
            "Interface Greeter",
            "Interface Greeter с Hello(name string) string; struct EnglishGreeter реализует его.",
            """package main

type Greeter interface {
    Hello(name string) string
}

type EnglishGreeter struct{}

func (EnglishGreeter) Hello(name string) string {
    return "Hello, " + name
}""",
            topic="Методы и интерфейсы",
        ),
        live(
            "Type switch",
            "Функция describe(v any) string: int→\"int\", string→\"string\", default→\"other\".",
            """package main

func describe(v any) string {
    switch v.(type) {
    case int:
        return "int"
    case string:
        return "string"
    default:
        return "other"
    }
}""",
            topic="Методы и интерфейсы",
        ),
        live(
            "Goroutine ping",
            "Функция ping() string: goroutine отправляет \"pong\" в канал, main получает.",
            """package main

func ping() string {
    ch := make(chan string, 1)
    go func() { ch <- "pong" }()
    return <-ch
}""",
            topic="Goroutines и каналы",
        ),
        live(
            "Worker sum",
            "Функция parallelSum(nums []int, workers int) int: workers goroutines суммируют части slice через канал.",
            """package main

func parallelSum(nums []int, workers int) int {
    if workers < 1 {
        workers = 1
    }
    chunk := (len(nums) + workers - 1) / workers
    out := make(chan int, workers)
    for w := 0; w < workers; w++ {
        start := w * chunk
        end := start + chunk
        if start >= len(nums) {
            break
        }
        if end > len(nums) {
            end = len(nums)
        }
        part := nums[start:end]
        go func(p []int) {
            s := 0
            for _, n := range p {
                s += n
            }
            out <- s
        }(part)
    }
    total := 0
    for i := 0; i < workers && i*chunk < len(nums); i++ {
        total += <-out
    }
    return total
}""",
            topic="Goroutines и каналы",
        ),
        live(
            "Select timeout",
            "Функция withTimeout(ch <-chan int, d time.Duration) (int, bool) — select с time.After.",
            """package main

import "time"

func withTimeout(ch <-chan int, d time.Duration) (int, bool) {
    select {
    case v := <-ch:
        return v, true
    case <-time.After(d):
        return 0, false
    }
}""",
            topic="Goroutines и каналы",
        ),
        live(
            "Wrap error",
            "Функция loadConfig(path string) error читает файл и оборачивает ошибку fmt.Errorf(\"config: %w\", err).",
            """package main

import (
    "fmt"
    "os"
)

func loadConfig(path string) error {
    _, err := os.ReadFile(path)
    if err != nil {
        return fmt.Errorf("config: %w", err)
    }
    return nil
}""",
            topic="Ошибки",
        ),
        live(
            "Sentinel ErrNotFound",
            "var ErrNotFound = errors.New(\"not found\"); функция find(id int) error возвращает ErrNotFound при id < 0.",
            """package main

import "errors"

var ErrNotFound = errors.New("not found")

func find(id int) error {
    if id < 0 {
        return ErrNotFound
    }
    return nil
}""",
            topic="Ошибки",
        ),
        live(
            "JSON marshal User",
            "Struct User { Name string `json:\"name\"`; Age int `json:\"age\"` }; toJSON(u User) (string, error).",
            """package main

import "encoding/json"

type User struct {
    Name string `json:"name"`
    Age  int    `json:"age"`
}

func toJSON(u User) (string, error) {
    b, err := json.Marshal(u)
    return string(b), err
}""",
            topic="Stdlib",
        ),
        live(
            "HTTP handler health",
            "http.HandlerFunc health возвращает 200 и тело \"ok\".",
            """package main

import "net/http"

func health(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    _, _ = w.Write([]byte("ok"))
}""",
            topic="Stdlib",
        ),
        live(
            "Context cancel",
            "Функция sleepUntilCancel(ctx context.Context) error ждёт ctx.Done() и возвращает ctx.Err().",
            """package main

import "context"

func sleepUntilCancel(ctx context.Context) error {
    <-ctx.Done()
    return ctx.Err()
}""",
            topic="Stdlib",
        ),
        live(
            "Generic Contains",
            "Функция Contains[T comparable](slice []T, value T) bool.",
            """package main

func Contains[T comparable](slice []T, value T) bool {
    for _, v := range slice {
        if v == value {
            return true
        }
    }
    return false
}""",
            topic="Generics",
        ),
        live(
            "Generic Map",
            "Функция Map[T, U any](in []T, f func(T) U) []U.",
            """package main

func Map[T, U any](in []T, f func(T) U) []U {
    out := make([]U, len(in))
    for i, v := range in {
        out[i] = f(v)
    }
    return out
}""",
            topic="Generics",
        ),
        live(
            "Table test add",
            "TestAdd с table-driven cases: (1,1,2), (2,3,5). Функция add(a,b int) int.",
            """package main

import "testing"

func add(a, b int) int { return a + b }

func TestAdd(t *testing.T) {
    cases := []struct {
        a, b, want int
    }{
        {1, 1, 2},
        {2, 3, 5},
    }
    for _, tc := range cases {
        if got := add(tc.a, tc.b); got != tc.want {
            t.Errorf("add(%d,%d)=%d want %d", tc.a, tc.b, got, tc.want)
        }
    }
}""",
            topic="Тестирование",
        ),
        live(
            "Benchmark reverse",
            "BenchmarkReverse для функции reverse(s []byte) reversing in-place.",
            """package main

import "testing"

func reverse(s []byte) {
    for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
        s[i], s[j] = s[j], s[i]
    }
}

func BenchmarkReverse(b *testing.B) {
    data := []byte("hello world benchmark")
    for i := 0; i < b.N; i++ {
        buf := append([]byte(nil), data...)
        reverse(buf)
    }
}""",
            topic="Тестирование",
        ),
        live(
            "Package config",
            "Package config (не main): type Settings struct { Port int }; Default() Settings с Port 8080.",
            """package config

type Settings struct {
    Port int
}

func Default() Settings {
    return Settings{Port: 8080}
}""",
            topic="Модули и пакеты",
        ),
        live(
            "Internal helper",
            "Package util (в module app): функция Ptr[T any](v T) *T возвращает указатель на копию v.",
            """package util

func Ptr[T any](v T) *T {
    return &v
}""",
            topic="Generics",
        ),
        live(
            "Mutex counter",
            "Type SafeCounter с Inc() и Value(); защита sync.Mutex.",
            """package main

import "sync"

type SafeCounter struct {
    mu sync.Mutex
    n  int
}

func (c *SafeCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.n++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.n
}""",
            topic="Goroutines и каналы",
        ),
        live(
            "strings.Builder join",
            "Функция join(words []string, sep string) string через strings.Builder.",
            """package main

import "strings"

func join(words []string, sep string) string {
    var b strings.Builder
    for i, w := range words {
        if i > 0 {
            b.WriteString(sep)
        }
        b.WriteString(w)
    }
    return b.String()
}""",
            topic="Stdlib",
        ),
        live(
            "Parse duration",
            "Функция parseSeconds(raw string) (time.Duration, error) парсит \"1500ms\" через time.ParseDuration.",
            """package main

import "time"

func parseSeconds(raw string) (time.Duration, error) {
    return time.ParseDuration(raw)
}""",
            topic="Stdlib",
        ),
        live(
            "Recover middleware",
            "Функция safeCall(fn func()) (recovered bool) — defer recover, true если был panic.",
            """package main

func safeCall(fn func()) (recovered bool) {
    defer func() {
        if recover() != nil {
            recovered = true
        }
    }()
    fn()
    return false
}""",
            topic="Функции и defer",
        ),
        live(
            "Comparable Keys",
            "Generic Keys[M ~map[K]V, K comparable, V any](m M) []K возвращает ключи map (порядок random).",
            """package main

func Keys[M ~map[K]V, K comparable, V any](m M) []K {
    keys := make([]K, 0, len(m))
    for k := range m {
        keys = append(keys, k)
    }
    return keys
}""",
            topic="Generics",
        ),
    ]


def main() -> None:
    from go_live_bank import extra_cards

    cards = assign_topics(build_cards() + extra_cards(), "go")
    topics = Counter(c.get("topic", "?") for c in cards)
    if len(topics) < 8:
        raise SystemExit(f"Only {len(topics)} topics, need 8+")

    missing = [t for t in TOPICS if topics.get(t, 0) < 5]
    if missing:
        raise SystemExit(f"Topics with <5 live cards: {missing}")

    deck = {"name": "Go Live-coding", "language": "go", "cards": cards}
    out = Path(__file__).with_name("go-live-coding.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} live_code cards -> {out}")
    print("Topics:", dict(topics))


if __name__ == "__main__":
    main()
