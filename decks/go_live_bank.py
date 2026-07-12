"""Additional Go live-coding cards — explicit topics."""
from __future__ import annotations

from live_coding_card import live


def _cards(specs: list[tuple[str, str, str, str]]) -> list[dict]:
    return [
        live(title, assignment, reference, lang="go", topic=topic)
        for title, assignment, reference, topic in specs
    ]


def extra_cards() -> list[dict]:
    specs: list[tuple[str, str, str, str]] = [
        ('Max of two ints', 'func Max(a, b int) int возвращает большее.', """func Max(a, b int) int {
    if a > b {
        return a
    }
    return b
}""", 'Основы'),
        ('Abs int', 'func Abs(n int) int — модуль числа.', """func Abs(n int) int {
    if n < 0 {
        return -n
    }
    return n
}""", 'Основы'),
        ('Is empty string', 'func IsEmpty(s string) bool.', """func IsEmpty(s string) bool {
    return s == ""
}""", 'Основы'),
        ('Repeat string', 'func Repeat(s string, n int) string — повтор s n раз.', """func Repeat(s string, n int) string {
    if n <= 0 {
        return ""
    }
    out := ""
    for i := 0; i < n; i++ {
        out += s
    }
    return out
}""", 'Основы'),
        ('Switch weekday', 'func weekdayName(d int) string через switch: 1→Mon ... 7→Sun, default Unknown.', """func weekdayName(d int) string {
    switch d {
    case 1:
        return "Mon"
    case 2:
        return "Tue"
    case 3:
        return "Wed"
    case 4:
        return "Thu"
    case 5:
        return "Fri"
    case 6:
        return "Sat"
    case 7:
        return "Sun"
    default:
        return "Unknown"
    }
}""", 'Основы'),
        ('Constants iota', 'const (KB=1<<(10*iota); MB; GB) — объявить KB, MB, GB.', """const (
    _  = iota
    KB = 1 << (10 * iota)
    MB
    GB
)""", 'Основы'),
        ('Count to n', 'func countTo(n int) []int возвращает [1..n].', """func countTo(n int) []int {
    out := make([]int, n)
    for i := range out {
        out[i] = i + 1
    }
    return out
}""", 'Основы'),
        ('Last rune', 'func lastRune(s string) rune — последний rune строки (assume non-empty).', """func lastRune(s string) rune {
    r, _ := utf8.DecodeLastRuneInString(s)
    return r
}""", 'Основы'),
        ('Reverse slice', 'func reverseInts(nums []int) — reverse in-place.', """func reverseInts(nums []int) {
    for i, j := 0, len(nums)-1; i < j; i, j = i+1, j-1 {
        nums[i], nums[j] = nums[j], nums[i]
    }
}""", 'Типы и структуры'),
        ('Unique strings', 'func unique(in []string) []string сохраняет порядок первого вхождения.', """func unique(in []string) []string {
    seen := make(map[string]struct{})
    out := make([]string, 0, len(in))
    for _, s := range in {
        if _, ok := seen[s]; ok {
            continue
        }
        seen[s] = struct{}{}
        out = append(out, s)
    }
    return out
}""", 'Типы и структуры'),
        ('Struct Rectangle Area', 'type Rectangle struct { W, H float64 }; метод Area() float64.', """type Rectangle struct {
    W, H float64
}

func (r Rectangle) Area() float64 {
    return r.W * r.H
}""", 'Типы и структуры'),
        ('Embedded Person Employee', 'type Person struct { Name string }; type Employee struct { Person; ID int }.', """type Person struct {
    Name string
}

type Employee struct {
    Person
    ID int
}""", 'Типы и структуры'),
        ('Clone map', 'func cloneMap(m map[string]int) map[string]int.', """func cloneMap(m map[string]int) map[string]int {
    out := make(map[string]int, len(m))
    for k, v := range m {
        out[k] = v
    }
    return out
}""", 'Типы и структуры'),
        ('Stack push pop', 'type Stack struct { items []int }; Push(v int); Pop() (int, bool).', """type Stack struct {
    items []int
}

func (s *Stack) Push(v int) {
    s.items = append(s.items, v)
}

func (s *Stack) Pop() (int, bool) {
    if len(s.items) == 0 {
        return 0, false
    }
    v := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return v, true
}""", 'Типы и структуры'),
        ('Pointer swap', 'func swap(a, b *int) меняет значения по указателям.', """func swap(a, b *int) {
    *a, *b = *b, *a
}""", 'Типы и структуры'),
        ('Matrix rows', 'func newMatrix(rows, cols int) [][]int инициализирует 2D slice нулями.', """func newMatrix(rows, cols int) [][]int {
    m := make([][]int, rows)
    for i := range m {
        m[i] = make([]int, cols)
    }
    return m
}""", 'Типы и структуры'),
        ('Closure counter', 'func makeCounter() func() int.', """func makeCounter() func() int {
    n := 0
    return func() int {
        n++
        return n
    }
}""", 'Функции и defer'),
        ('Defer stack', 'func deferOrder() int демонстрирует LIFO defers, return 3.', """func deferOrder() int {
    defer func() {}
    defer func() {}
    return 3
}""", 'Функции и defer'),
        ('Named returns', 'func splitSum(nums []int) (sum int, count int).', """func splitSum(nums []int) (sum int, count int) {
    for _, n := range nums {
        sum += n
        count++
    }
    return
}""", 'Функции и defer'),
        ('Variadic sum', 'func sumAll(nums ...int) int.', """func sumAll(nums ...int) int {
    s := 0
    for _, n := range nums {
        s += n
    }
    return s
}""", 'Функции и defer'),
        ('Recover handler', 'func runSafe(fn func()) (panicked bool).', """func runSafe(fn func()) (panicked bool) {
    defer func() {
        if recover() != nil {
            panicked = true
        }
    }()
    fn()
    return false
}""", 'Функции и defer'),
        ('Middleware chain', 'type Handler func(); func chain(h Handler, wrappers ...func(Handler) Handler) Handler.', """func chain(h func(), wrappers ...func(func()) func()) func() {
    wrapped := h
    for i := len(wrappers) - 1; i >= 0; i-- {
        wrapped = wrappers[i](wrapped)
    }
    return wrapped
}""", 'Функции и defer'),
        ('io.Reader from string', 'type stringReader struct { s string; i int }; Read(p []byte) (int, error).', """type stringReader struct {
    s string
    i int
}

func (r *stringReader) Read(p []byte) (int, error) {
    if r.i >= len(r.s) {
        return 0, io.EOF
    }
    n := copy(p, r.s[r.i:])
    r.i += n
    return n, nil
}""", 'Методы и интерфейсы'),
        ('Shape interface', 'interface Shape { Area() float64 }; Circle с Radius float64.', """type Shape interface {
    Area() float64
}

type Circle struct {
    Radius float64
}

func (c Circle) Area() float64 {
    return math.Pi * c.Radius * c.Radius
}""", 'Методы и интерфейсы'),
        ('Assert stringer', 'func printString(v any) string использует fmt.Stringer если есть.', """func printString(v any) string {
    if s, ok := v.(fmt.Stringer); ok {
        return s.String()
    }
    return fmt.Sprint(v)
}""", 'Методы и интерфейсы'),
        ('Compose readers', 'type multiReader — упрощённо concat двух []byte в Read.', """type byteReader struct {
    data []byte
}

func (b *byteReader) Read(p []byte) (int, error) {
    if len(b.data) == 0 {
        return 0, io.EOF
    }
    n := copy(p, b.data)
    b.data = b.data[n:]
    return n, nil
}""", 'Методы и интерфейсы'),
        ('Validate interface', 'type Validator interface { Validate() error }; Email struct.', """type Validator interface {
    Validate() error
}

type Email struct {
    Value string
}

func (e Email) Validate() error {
    if e.Value == "" {
        return errors.New("empty email")
    }
    return nil
}""", 'Методы и интерфейсы'),
        ('Compile-time interface check', 'var _ http.Handler = (*handler)(nil) pattern for type handler struct{}.', """type handler struct{}

func (h handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
}

var _ http.Handler = (*handler)(nil)""", 'Методы и интерфейсы'),
        ('Fan-in', 'func fanIn(chs ...<-chan int) <-chan int merge.', """func fanIn(chs ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    wg.Add(len(chs))
    for _, ch := range chs {
        go func(c <-chan int) {
            defer wg.Done()
            for v := range c {
                out <- v
            }
        }(ch)
    }
    go func() {
        wg.Wait()
        close(out)
    }()
    return out
}""", 'Goroutines и каналы'),
        ('Semaphore', 'type Sem struct { ch chan struct{} }; Acquire/Release.', """type Sem struct {
    ch chan struct{}
}

func NewSem(n int) *Sem {
    return &Sem{ch: make(chan struct{}, n)}
}

func (s *Sem) Acquire() { s.ch <- struct{}{} }
func (s *Sem) Release() { <-s.ch }""", 'Goroutines и каналы'),
        ('Once init', 'var once sync.Once; func initConfig() *Config lazy.', """var (
    cfg  *Config
    once sync.Once
)

func getConfig() *Config {
    once.Do(func() {
        cfg = &Config{Port: 8080}
    })
    return cfg
}""", 'Goroutines и каналы'),
        ('Pipeline double', 'func double(in <-chan int) <-chan int stage.', """func double(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for v := range in {
            out <- v * 2
        }
    }()
    return out
}""", 'Goroutines и каналы'),
        ('RWMutex cache', 'type Cache struct { mu sync.RWMutex; m map[string]string }; Get/Set.', """type Cache struct {
    mu sync.RWMutex
    m  map[string]string
}

func (c *Cache) Get(k string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    v, ok := c.m[k]
    return v, ok
}

func (c *Cache) Set(k, v string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    if c.m == nil {
        c.m = make(map[string]string)
    }
    c.m[k] = v
}""", 'Goroutines и каналы'),
        ('Context worker', 'func worker(ctx context.Context, jobs <-chan int, out chan<- int).', """func worker(ctx context.Context, jobs <-chan int, out chan<- int) {
    for {
        select {
        case <-ctx.Done():
            return
        case j, ok := <-jobs:
            if !ok {
                return
            }
            out <- j * j
        }
    }
}""", 'Goroutines и каналы'),
        ('Join errors', 'func validateAll(errs ...error) error через errors.Join (Go 1.20).', """func validateAll(errs ...error) error {
    return errors.Join(errs...)
}""", 'Ошибки'),
        ('Is not found', 'func isNotFound(err error) bool через errors.Is(ErrNotFound).', """func isNotFound(err error) bool {
    return errors.Is(err, ErrNotFound)
}""", 'Ошибки'),
        ('As typed error', 'type OpError struct { Op string }; func asOpError(err error) (*OpError, bool).', """type OpError struct {
    Op string
}

func (e *OpError) Error() string { return e.Op }

func asOpError(err error) (*OpError, bool) {
    var target *OpError
    ok := errors.As(err, &target)
    return target, ok
}""", 'Ошибки'),
        ('Multi step pipeline err', 'func step() error возвращает fmt.Errorf wrap на каждом шаге.', """func step() error {
    if err := do(); err != nil {
        return fmt.Errorf("step: %w", err)
    }
    return nil
}""", 'Ошибки'),
        ('Custom validation', 'func requireNonEmpty(field, value string) error.', """func requireNonEmpty(field, value string) error {
    if strings.TrimSpace(value) == "" {
        return fmt.Errorf("%s must not be empty", field)
    }
    return nil
}""", 'Ошибки'),
        ('Read file lines', 'func readLines(path string) ([]string, error) bufio.Scanner.', """func readLines(path string) ([]string, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var lines []string
    sc := bufio.NewScanner(f)
    for sc.Scan() {
        lines = append(lines, sc.Text())
    }
    return lines, sc.Err()
}""", 'Stdlib'),
        ('URL query', 'func getQuery(u, key string) string через url.Parse.', """func getQuery(raw, key string) string {
    u, err := url.Parse(raw)
    if err != nil {
        return ""
    }
    return u.Query().Get(key)
}""", 'Stdlib'),
        ('Sort ints', 'func sortInts(nums []int) { sort.Ints(nums) }', """func sortInts(nums []int) {
    sort.Ints(nums)
}""", 'Stdlib'),
        ('Template execute', 'func render(name string) (string, error) простейший text/template.', """func render(name string) (string, error) {
    var b strings.Builder
    tpl := template.Must(template.New("t").Parse("Hello, {{.}}!"))
    if err := tpl.Execute(&b, name); err != nil {
        return "", err
    }
    return b.String(), nil
}""", 'Stdlib'),
        ('Slog info', 'func logUser(id int) { slog.Info(\\"user\\", \\"id\\", id) }', """func logUser(id int) {
    slog.Info("user", "id", id)
}""", 'Stdlib'),
        ('Parse JSON file', 'func decodeJSON(r io.Reader, v any) error json.NewDecoder.', """func decodeJSON(r io.Reader, v any) error {
    return json.NewDecoder(r).Decode(v)
}""", 'Stdlib'),
        ('Filter generic', 'func Filter[T any](in []T, pred func(T) bool) []T.', """func Filter[T any](in []T, pred func(T) bool) []T {
    out := make([]T, 0)
    for _, v := range in {
        if pred(v) {
            out = append(out, v)
        }
    }
    return out
}""", 'Generics'),
        ('Reduce sum', 'func Reduce[T any](in []T, init T, fn func(T, T) T) T.', """func Reduce[T any](in []T, init T, fn func(T, T) T) T {
    acc := init
    for _, v := range in {
        acc = fn(acc, v)
    }
    return acc
}""", 'Generics'),
        ('Pair struct generic', 'type Pair[A, B any] struct { First A; Second B }.', """type Pair[A, B any] struct {
    First  A
    Second B
}""", 'Generics'),
        ('Min ordered', 'func Min[T cmp.Ordered](a, b T) T.', """func Min[T cmp.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}""", 'Generics'),
        ('Set generic', 'type Set[T comparable] map[T]struct{}; Add/Has.', """type Set[T comparable] map[T]struct{}

func (s Set[T]) Add(v T) {
    s[v] = struct{}{}
}

func (s Set[T]) Has(v T) bool {
    _, ok := s[v]
    return ok
}""", 'Generics'),
        ('Subtest table', 'TestParse с t.Run subtests.', """func TestParse(t *testing.T) {
    tests := []struct{ in, want string }{{"a", "a"}}
    for _, tc := range tests {
        t.Run(tc.in, func(t *testing.T) {
            if got := parse(tc.in); got != tc.want {
                t.Fatalf("got %q want %q", got, tc.want)
            }
        })
    }
}""", 'Тестирование'),
        ('httptest handler', 'TestHealth проверяет handler health через httptest.', """func TestHealth(t *testing.T) {
    rr := httptest.NewRecorder()
    health(rr, httptest.NewRequest(http.MethodGet, "/health", nil))
    if rr.Code != http.StatusOK {
        t.Fatalf("status %d", rr.Code)
    }
}""", 'Тестирование'),
        ('Test cleanup', 'Пример t.Cleanup closing resource.', """func TestResource(t *testing.T) {
    r := acquire()
    t.Cleanup(func() { r.Close() })
}""", 'Тестирование'),
        ('Helper assert', 'func assertEqual(t *testing.T, got, want int) { t.Helper(); ... }', """func assertEqual(t *testing.T, got, want int) {
    t.Helper()
    if got != want {
        t.Errorf("got %d want %d", got, want)
    }
}""", 'Тестирование'),
        ('cmd main stub', 'package main in cmd/app/main.go calling config.Default().', """package main

import "example.com/app/config"

func main() {
    _ = config.Default()
}""", 'Модули и пакеты'),
        ('internal pkg', 'package internal/auth PasswordHash(password string) string stub.', """package auth

func PasswordHash(password string) string {
    return password
}""", 'Модули и пакеты'),
        ('Build tag file', 'Комментарий //go:build linux в начале файла.', """//go:build linux

package main""", 'Модули и пакеты'),
        ('go.mod module', 'Объяви module github.com/acme/widget в go.mod (комментарий в reference).', """module github.com/acme/widget

go 1.22""", 'Модули и пакеты'),
        ('Replace directive', 'Комментарий replace example.com/lib => ../lib в go.mod для локальной разработки.', """replace example.com/lib => ../lib""", 'Модули и пакеты'),
        ('Export doc comment', 'Exported функция Parse с godoc комментарием Parse reads config.', """// Parse reads config from raw string.
func Parse(raw string) (Config, error) {
    return Config{}, nil
}""", 'Модули и пакеты'),
    ]
    return _cards(specs)
