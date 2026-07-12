"""Go flashcard bank — theory, code fixes, revision hints."""
from __future__ import annotations

THEORY: dict[str, list[tuple[str, str]]] = {
    "Основы": [
        ("Что такое Go (Golang)?", "Компилируемый статически типизированный язык от Google: простой синтаксис, сборщик мусора, встроенная конкурентность через goroutines."),
        ("Как объявить package?", "Первая строка файла: package main для исполняемого, package foo для библиотеки. Имя пакета совпадает с каталогом модуля (обычно)."),
        ("Точка входа main?", "func main() в пакете main — единственная точка входа программы."),
        ("Как импортировать пакеты?", "import \"fmt\" или блок import ( ... ). Неиспользуемый импорт — ошибка компиляции."),
        ("Короткое объявление переменной :=", "x := 10 — тип выводится компилятором. Только внутри функций."),
        ("var vs :=", "var x int = 10 — явный тип; var x = 10 — вывод типа; := — короткая форма в функции."),
        ("Нулевые значения (zero values)?", "int→0, string→\"\", bool→false, pointer/slice/map/channel/func/interface→nil."),
        ("Константы const?", "const Pi = 3.14; const (A=1; B=2). Без явного типа — untyped constant."),
        ("iota?", "Генератор последовательных untyped int констант в блоке const: const (A=iota; B; C) → 0,1,2."),
        ("if с коротким объявлением?", "if err := f(); err != nil { ... } — переменная в scope только if/else."),
        ("for — единственный цикл?", "Да: for {}, for i:=0; i<n; i++, for range. while через for condition."),
        ("switch в Go?", "Автоматический break; case может быть несколько значений; switch без выражения — как if-else chain."),
        ("switch с типом (type switch)?", "switch v := x.(type) { case int: ... } для проверки динамического типа interface{}."),
        ("fallthrough?", "Явный переход к следующему case в switch (редко, обычно не нужен)."),
        ("goto?", "Есть, но не рекомендуется; используется в generated code и редких low-level случаях."),
        ("Порядок инициализации?", "Пакеты: init() всех imported пакетов → init() текущего → main()."),
        ("fmt.Println vs Print?", "Println добавляет пробелы между аргументами и перевод строки."),
        ("fmt.Printf и verb %v?", "%v — default format; %+v struct с полями; %#v Go-syntax; %T тип."),
        ("Строки в Go?", "Immutable byte sequence (UTF-8). string ↔ []byte через []byte(s) и string(b)."),
        ("rune?", "Alias для int32 — кодовая точка Unicode. range по string даёт rune и index."),
        ("byte?", "Alias для uint8."),
        ("Арифметика int?", "int размер зависит от платформы (32/64 bit). Явно int32/int64 для переносимости."),
        ("Приведение типов?", "T(v) — явное; между числовыми типами только явно; нет implicit numeric promotion как в C."),
        ("Сравнение struct?", "Можно если все поля comparable. Slice/map/func нельзя сравнивать через ==."),
        ("Короткое объявление := и shadowing?", ":= создаёт новую переменную если хотя бы одно имя новое в блоке; иначе присваивание."),
        ("Blank identifier _?", "Игнорирует значение: _, err := f(). Импорт _ для side-effect init."),
        ("go fmt (gofmt)?", "Стандартный форматтер — обязательная практика; go fmt ./..."),
        ("go vet?", "Статический анализ подозрительных конструкций."),
        ("Комментарии // и /* */?", "Стандартные; godoc парсит комментарии перед exported symbols."),
        ("Exported vs unexported?", "Имя с большой буквы — exported (public), с маленькой — package-private."),
    ],
    "Типы и структуры": [
        ("array vs slice?", "Array [N]T — фиксированный размер, value type. Slice []T — descriptor (ptr,len,cap), reference view."),
        ("Как создать slice?", "[]int{}, make([]int, len), make([]int, len, cap), slice literal, arr[:] из array."),
        ("append?", "append(s, x) может реалллоцировать; нужно s = append(s, x). Variadic: append(s, others...)."),
        ("len vs cap slice?", "len — длина элементов; cap — ёмкость underlying array от offset."),
        ("slice s[low:high]?", "Half-open [low, high). Max high = cap(s). s[:0] — zero len, сохраняет cap."),
        ("copy?", "copy(dst, src) — копирует min(len(dst), len(src)) элементов, возвращает count."),
        ("map?", "make(map[K]V). Запись m[k]=v. Чтение v, ok := m[k]. delete(m,k). Nil map нельзя писать."),
        ("struct?", "type User struct { ID int; Name string }. Literal User{ID:1, Name:\"a\"} или positional."),
        ("Embedded struct (composition)?", "type Admin struct { User; Role string } — promotion полей User."),
        ("Указатели *T?", "&x — адрес, *p — dereference. new(T) — allocate zero value, возвращает *T."),
        ("new vs make?", "new(T) — *T zero value. make — только slice, map, channel; возвращает initialized value (not pointer)."),
        ("Pointer receiver и nil?", "Метод с pointer receiver можно вызвать на nil pointer (если метод проверяет nil)."),
        ("Comparable types?", "Можно использовать как map key: numbers, string, pointer, array (if elements comparable), struct (if fields comparable)."),
        ("Slice как map value?", "Да, но изменение slice in-place видно всем, кто держит тот же backing array."),
        ("strings.Builder?", "Эффективная конкатенация строк без лишних аллокаций."),
        ("strings.Split / Join?", "Split(s, sep) → []string; strings.Join(parts, sep)."),
        ("strconv.Itoa / Atoi?", "Конвертация int ↔ string. ParseInt, FormatInt для base/size."),
        ("byte slice и string sharing?", "[]byte(s) копирует; unsafe conversion возможна но не recommended без care."),
        ("struct tags?", "`json:\"name,omitempty\"` — metadata для encoding/json через reflection."),
        ("JSON marshal struct?", "encoding/json Marshal/Unmarshal. Exported fields only. json tag controls names."),
        ("Type alias vs type definition?", "type Alias = T — alias. type New T — новый distinct type с тем же underlying."),
        ("runes in string length?", "len(string) — bytes, not runes. utf8.RuneCountInString(s)."),
        ("Clear slice?", "s = s[:0] сохраняет cap; s = nil — discard. clear(s) Go 1.21+ для maps/slices."),
        ("maps iteration order?", "Randomized — не полагаться на порядок."),
        ("struct padding?", "Компилятор выравнивает поля; порядок полей влияет на размер struct."),
        ("Empty struct struct{}?", "Zero-size; используется как set member или signal в channel."),
        ("Slice tricks delete element?", "s = append(s[:i], s[i+1:]...) — O(n); для частых delete лучше другая структура."),
        ("2D slice?", "[][]int — slice of slices; rows могут иметь разную длину (jagged)."),
        ("Heap vs stack в Go?", "Escape analysis решает; compiler may allocate on heap if escapes."),
    ],
    "Функции и defer": [
        ("Объявление func?", "func name(params) returnType { }. Multiple returns: (int, error). Named returns allowed."),
        ("Multiple return values?", "Идиоматично (result, err). Caller: v, err := f()."),
        ("Variadic functions?", "func sum(nums ...int) — nums is []int inside. Call: sum(1,2,3)."),
        ("defer?", "Откладывает вызов до return функции; аргументы вычисляются сразу при defer statement."),
        ("Порядок defer?", "LIFO — последний defer выполняется первым."),
        ("defer и return?", "Deferred func видит named return values после их установки; может modify named returns."),
        ("defer для close?", "defer f.Close() — стандарт для files, bodies, rows."),
        ("defer recover?", "recover() только внутри deferred func — ловит panic."),
        ("panic?", "Немедленная остановка goroutine; unwinds stack running defers; если не recovered — crash program."),
        ("recover?", "Возвращает value passed to panic; nil если нет panic."),
        ("Когда panic vs error?", "error для expected failures; panic для programmer bugs / unrecoverable invariants."),
        ("Function as value?", "Functions are first-class: var fn func(int) int = square."),
        ("Closures?", "Anonymous func захватывает переменные из enclosing scope by reference."),
        ("Loop variable in closure trap?", "Go 1.22+ per-iteration vars; до 1.21 копируй i := i в loop body перед goroutine/closure."),
        ("init function?", "func init() — автоматический вызов при load пакета; нельзя вызвать явно."),
        ("main без args?", "os.Args через import \"os\" — не параметры main как в C."),
        ("Recursive functions?", "Allowed; watch stack overflow on deep recursion — prefer iteration or trampoline."),
        ("Method value?", "f := obj.Method — bound method value; later f(args) without receiver."),
        ("Method expression?", "f := Type.Method — needs receiver as first arg: f(obj, args)."),
        ("Blank return?", "return без значений при named returns — returns current named vars."),
        ("Function type alias?", "type Handler func(http.ResponseWriter, *http.Request)"),
        ("Inlining?", "Compiler inlines small functions; не полагаться для side effects order across packages."),
        ("go:noinline directive?", "//go:noinline — для benchmarking/debug (advanced)."),
        ("defer performance?", "Small overhead; в hot paths иногда explicit close, обычно defer ok."),
        ("Higher-order functions?", "Передача func как параметр: sort.Slice, http.HandlerFunc."),
        ("IIFE in Go?", "func(){ ... }() — immediately invoked func literal."),
        ("Return early pattern?", "if err != nil { return ..., err } — guard clauses, flat code."),
        ("Function documentation?", "Comment before func starting with func name — godoc."),
    ],
    "Методы и интерфейсы": [
        ("Method syntax?", "func (r Receiver) Name(args) return { } — receiver like parameter."),
        ("Pointer vs value receiver?", "Pointer — mutate state, avoid copy large struct, consistency. Value — small immutable types."),
        ("Interface?", "type Reader interface { Read(p []byte) (n int, err error) } — implicit satisfaction."),
        ("Implicit interfaces?", "No implements keyword — type satisfies interface if has all methods."),
        ("Empty interface any?", "interface{} / any — любой тип. Использовать sparingly; prefer generics/concrete types."),
        ("Type assertion?", "v := x.(T) panic if fail; v, ok := x.(T) safe."),
        ("Type switch?", "switch t := x.(type) { case int: ... default: ... }"),
        ("Interface nil gotcha?", "Interface nil only if type AND value nil. var p *T=nil; var i interface{}=p → i!=nil (typed nil)."),
        ("io.Reader / io.Writer?", "Core abstractions для streaming I/O; compose через wrappers."),
        ("fmt.Stringer?", "String() string — fmt prints it automatically."),
        ("error interface?", "type error interface { Error() string } — universal error type."),
        ("Comparable interface constraints?", "Go 1.18+ constraints for generics: comparable for ==."),
        ("Embedding interface?", "type ReadWriter interface { Reader; Writer } — embed other interfaces."),
        ("Method set pointer receiver?", "T satisfies interface with pointer methods only if *T used (or T addressable)."),
        ("Interface value representation?", "(type, data) pair — dynamic type + value pointer."),
        ("Polymorphism in Go?", "Through interfaces, not inheritance."),
        ("Composition over inheritance?", "Embed structs/interfaces instead of class hierarchies."),
        ("Small interfaces?", "Idiom: io.Reader one method — easier mocks and reuse (accept interfaces, return structs)."),
        ("Adapter pattern?", "type Logger interface; wrap third-party type with methods matching interface."),
        ("Mocking via interface?", "Define interface at consumer; test inject fake implementation."),
        ("errors.As / errors.Is?", "Unwrap error chains; check wrapped types and sentinel values."),
        ("io.Closer?", "Close() error — defer close pattern."),
        ("sort.Interface?", "Len, Less, Swap — legacy; prefer sort.Slice."),
        ("http.Handler?", "ServeHTTP(ResponseWriter, *Request) — net/http core interface."),
        ("Context interface?", "context.Context — Done, Err, Deadline, Value for cancellation/timeouts."),
        ("Unexported interface in package?", "Private interface for internal abstraction — can't be satisfied from outside accidentally."),
        ("Generics with interface constraint?", "type Stringer interface { String() string }; func F[T Stringer](v T)"),
        ("Satisfying interface compile-time check?", "var _ MyInterface = (*MyType)(nil) — assert *MyType implements MyInterface."),
        ("Method on non-local type?", "Cannot add methods to types from other packages — wrap type locally."),
    ],
    "Goroutines и каналы": [
        ("Goroutine?", "go f() — lightweight thread, multiplexed on OS threads by runtime."),
        ("GOMAXPROCS?", "Controls OS threads for Go code execution; default NumCPU."),
        ("Channel?", "make(chan T), make(chan T, buf). Send ch<-v, receive <-ch. Close closes channel."),
        ("Unbuffered channel?", "Synchronizes — send blocks until receive ready (handoff)."),
        ("Buffered channel?", "Send blocks when buffer full; receive when empty."),
        ("close channel?", "close(ch) — receivers get zero value + ok=false. Sender closes, not receiver."),
        ("Range over channel?", "for v := range ch { } until closed and drained."),
        ("select?", "select { case v:=<-ch1: case ch2<-x: default: } — multiplex; default non-blocking."),
        ("select with timeout?", "case <-time.After(d): ... or context cancellation."),
        ("Worker pool pattern?", "Fixed N goroutines reading jobs from channel."),
        ("Fan-in / fan-out?", "Merge multiple channels into one / distribute work from one to many."),
        ("Done channel pattern?", "close(done) broadcast shutdown to workers."),
        ("context.Context cancellation?", "ctx, cancel := context.WithCancel(parent); defer cancel(); <-ctx.Done()."),
        ("WaitGroup?", "wg.Add(n); go func(){ defer wg.Done(); ...}(); wg.Wait()."),
        ("Mutex sync.Mutex?", "Lock/Unlock protect shared memory; defer mu.Unlock()."),
        ("RWMutex?", "RLock for reads, Lock for writes."),
        ("sync.Once?", "once.Do(func()) — exactly once initialization (thread-safe)."),
        ("atomic package?", "atomic.AddInt64 etc. — lock-free primitives for simple counters/flags."),
        ("Race detector?", "go run -race — detects data races at runtime (testing/dev)."),
        ("Goroutine leak?", "Blocked forever on send/receive — use context, buffer, or ensure consumer."),
        ("Pipeline pattern?", "Stages connected by channels — each stage goroutine."),
        ("Buffered vs unbuffered tradeoff?", "Buffer decouples timing but hides backpressure; choose consciously."),
        ("nil channel behavior?", "Send/receive on nil channel block forever — sometimes used in select tricks."),
        ("Directional channel types?", "chan<- T send-only, <-chan T receive-only in function signatures."),
        ("time.Ticker / Timer?", "Ticker periodic; Timer one-shot; stop to release resources."),
        ("sync.Map?", "Concurrent map optimized for read-heavy caches; not default choice vs mutex+map."),
        ("errgroup?", "golang.org/x/sync/errgroup — goroutine group with first error cancel."),
        ("Semaphore via buffered channel?", "sem := make(chan struct{}, N); acquire sem<-struct{}{}; release <-sem."),
        ("Don't communicate by sharing memory?", "Go proverb — prefer channels; but mutex ok for simple shared state."),
    ],
    "Ошибки": [
        ("error — built-in interface?", "Error() string — return errors, don't throw (except panic for bugs)."),
        ("if err != nil?", "Universal idiom after calls returning error."),
        ("fmt.Errorf?", "Create error; %w wraps: fmt.Errorf(\"context: %w\", err) for unwrap chain."),
        ("errors.New?", "Simple static error: errors.New(\"not found\")."),
        ("Sentinel errors?", "var ErrNotFound = errors.New(\"not found\") — compare with errors.Is."),
        ("errors.Is?", "errors.Is(err, ErrNotFound) — works through wrapped errors."),
        ("errors.As?", "errors.As(err, &target) — find typed error in chain."),
        ("errors.Unwrap?", "Returns wrapped error from fmt.Errorf %w or custom Unwrap()."),
        ("Custom error type?", "type MyError struct { Code int }; func (e *MyError) Error() string"),
        ("Return error as last value?", "Convention: (T, error) or just error."),
        ("panic vs error in library?", "Library returns error; panic only for impossible internal state."),
        ("log.Fatal?", "Log and os.Exit(1) — not defer-friendly; avoid in libraries."),
        ("Multierror?", "errors.Join (Go 1.20+) combines multiple errors."),
        ("errors.Is vs ==", "Use Is for sentinel; == breaks with wrapping."),
        ("Handling HTTP errors?", "Check status code; decode body; wrap with context."),
        ("io.EOF?", "Not failure — end of stream; handle separately from real errors."),
        ("Context.Canceled / DeadlineExceeded?", "Standard context errors from ctx.Err()."),
        ("Error string capitalization?", "No trailing period; lowercase start unless proper noun (Go style guide)."),
        ("Don't ignore errors?", "_ = f() discouraged; handle or explicitly document why ignored."),
        ("errors in init?", "init can panic on misconfiguration; libraries prefer returning error from constructor."),
        ("Must functions?", "template.Must, regexp.MustCompile — panic on compile error at init."),
        ("Compare wrapped error messages?", "Avoid; use Is/As on sentinel/types."),
        ("errors.Join use case?", "Aggregate validation failures from multiple fields."),
        ("Temporary / timeout errors?", "net.Error Timeout(); os.IsTimeout(err) helpers."),
        ("Error handling in defer?", "Named return err; defer func(){ if e!=nil { err=...}}()"),
    ],
    "Stdlib": [
        ("os.Open / ReadFile?", "os.Open for streaming; os.ReadFile reads all bytes (Go 1.16+)."),
        ("io.Copy?", "Stream copy between Reader and Writer efficiently."),
        ("bufio.Scanner?", "Line/token scanning; Scan loop; Err() after false Scan."),
        ("path/filepath?", "Join, Clean, Base — OS-aware paths (not path for URLs)."),
        ("encoding/json?", "Marshal, Unmarshal, NewEncoder(w).Encode(v)."),
        ("net/http server?", "http.HandleFunc, http.ListenAndServe. Handler interface."),
        ("http.Client?", "client.Get(url); customize Timeout, Transport."),
        ("context in HTTP?", "r.Context(); pass to downstream; server shutdown with Server.Shutdown."),
        ("time package?", "time.Now(), Parse, Format layout reference Mon Jan 2 15:04:05 MST 2006."),
        ("time.Duration?", "time.Second, time.Millisecond; d := 5 * time.Second."),
        ("sort.Slice?", "sort.Slice(items, func(i,j int) bool { return items[i]<items[j] })"),
        ("slices package Go 1.21+?", "slices.Sort, Contains, Clone — generic slice helpers."),
        ("maps package Go 1.21+?", "maps.Clone, maps.Keys, maps.Values."),
        ("bytes.Buffer?", "In-memory buffer implementing Writer/Reader for building bytes."),
        ("regexp?", "Compile pattern; MatchString; FindStringSubmatch."),
        ("flag package?", "CLI flags for simple tools; flag.Parse()."),
        ("log package?", "log.Println; log.SetFlags; structured logging often via slog (Go 1.21+)."),
        ("log/slog?", "Structured leveled logging: slog.Info(\"msg\", \"key\", value)."),
        ("embed package?", "//go:embed files — compile-time embed FS in binary."),
        ("crypto/sha256?", "Hash data: sha256.Sum256(b) or New()+Write."),
        ("database/sql?", "sql.Open, db.Query, db.Exec, rows.Scan — generic SQL API."),
        ("html/template vs text/template?", "html/template auto-escapes — use for HTML output."),
        ("os.Getenv / LookupEnv?", "Environment variables; prefer explicit config injection in apps."),
        ("io/ioutil deprecated?", "Functions moved to io and os packages in Go 1.16."),
        ("net/url?", "Parse URLs; Query encoding/decoding."),
        ("strconv.ParseBool?", "Parse CLI/config string to bool with error handling."),
        ("testing/quick?", "Property-based random testing helper (legacy niche)."),
        ("runtime package?", "NumCPU, MemStats, Caller — introspection; rarely in app code."),
    ],
    "Generics": [
        ("Generics since Go version?", "Go 1.18 — type parameters in functions and types."),
        ("Generic function syntax?", "func Map[T, U any](in []T, f func(T) U) []U { ... }"),
        ("Type parameter constraint?", "[T comparable] or interface constraint listing methods/types."),
        ("any constraint?", "any means no constraint — equivalent unrestricted (interface{})."),
        ("comparable?", "Built-in constraint for == and != — needed for map keys in generic code."),
        ("Generic type definition?", "type Stack[T any] struct { items []T }"),
        ("Methods on generic types?", "Methods can use receiver type parameters (Go 1.18+)."),
        ("Type inference?", "Compiler infers T from arguments: Map([]int{1}, fn) without explicit T."),
        ("~ in constraints?", "T ~int means underlying type int — allows defined types based on int."),
        ("Union constraints?", "interface { int | float64 } — type must be one of (Go 1.18)."),
        ("constraints package?", "golang.org/x/exp/constraints — Integer, Ordered etc. (often copy locally)."),
        ("Generic slice helpers?", "Use slices package or write Min[T cmp.Ordered](a,b T) T with cmp package Go 1.21."),
        ("When NOT to use generics?", "Simple concrete code; premature abstraction; readability loss."),
        ("Type list in interface?", "interface { ~int | ~float64 } for union underlying types."),
        ("Generic map keys?", "Constraint must include comparable."),
        ("Instantiate generic type?", "var s Stack[int] — explicit type args when needed."),
        ("Generic interfaces?", "type Serializer[T any] interface { Serialize(T) []byte }"),
        ("Performance of generics?", "Monomorphization — specialized at compile time; no runtime boxing for type params in most cases."),
        ("Generic linked list example?", "type Node[T any] struct { Value T; Next *Node[T] }"),
        ("Compare with interface{}?", "Generics preserve type safety without type assertions."),
        ("Type parameters on methods?", "func (s *Stack[T]) Push(v T) — T from receiver definition."),
        ("constraints.Ordered?", "cmp.Ordered in std (Go 1.21) for < > on ordered types."),
        ("Generic min/max?", "Use built-in min/max Go 1.21+ or generic function with cmp.Ordered."),
        ("Limitations?", "No generic methods on non-generic types (historical); no specialization syntax; no default type params yet."),
        ("Testing generics?", "Same as normal functions — table tests with multiple type instantiations if needed."),
    ],
    "Тестирование": [
        ("testing package?", "import \"testing\"; func TestX(t *testing.T) { } in _test.go files."),
        ("File naming _test.go?", "Same package (white-box) or package_test (black-box external test)."),
        ("go test?", "go test ./... runs tests; -v verbose; -run regex filter."),
        ("t.Error vs t.Fatal?", "Error continues test; Fatal stops immediately."),
        ("Table-driven tests?", "cases := []struct{ name, in, want ...}{}; for _, tc := range cases { t.Run(...) }"),
        ("t.Run subtests?", "Subtests and parallel subtests t.Parallel() in subtest func."),
        ("Benchmark?", "func BenchmarkX(b *testing.B) { for i:=0; i<b.N; i++ { } }"),
        ("Example functions?", "func ExampleFoo() — documented by output // Output: comment."),
        ("httptest?", "net/http/httptest ResponseRecorder and test server for HTTP handlers."),
        ("TestMain?", "func TestMain(m *testing.M) { setup(); os.Exit(m.Run()) }"),
        ("Coverage?", "go test -cover; go test -coverprofile=c.out; go tool cover -html=c.out."),
        ("Race in tests?", "go test -race catches data races."),
        ("Temporary files in tests?", "t.TempDir() auto cleanup; os.CreateTemp deprecated pattern replaced."),
        ("Mocking?", "Interfaces + fake implementations; no built-in mock framework in stdlib."),
        ("Fuzz testing?", "func FuzzX(f *testing.F) — Go 1.18+ native fuzzing."),
        ("Skip test?", "t.Skip(\"reason\") or t.SkipNow()."),
        ("Helper?", "t.Helper() marks function as test helper for accurate line numbers."),
        ("Parallel tests?", "t.Parallel() — run concurrently; watch shared state."),
        ("Golden files?", "Compare output totestdata/expected.out — common pattern."),
        ("Integration vs unit?", "Unit fast isolated; integration needs DB/network — separate tags build tags."),
        ("Build tags in tests?", "//go:build integration at top of file."),
        ("assert libraries?", "testify/assert popular; stdlib prefers explicit if got != want { t.Errorf }. "),
        ("Cleanup?", "t.Cleanup(func(){ ... }) registers teardown like defer per subtest."),
        ("Benchmark memory?", "b.ReportAllocs() report allocations per op."),
        ("Testing unexported?", "Same package _test or export_test.go for alias."),
    ],
    "Модули и пакеты": [
        ("Go modules?", "go mod init module/path — dependency management via go.mod go.sum."),
        ("go.mod contents?", "module path, go version, require directives, replace/exclude."),
        ("go get?", "Add/update dependency: go get pkg@version."),
        ("go mod tidy?", "Add missing, remove unused modules in go.mod/sum."),
        ("Vendor?", "go mod vendor — copy deps to vendor/ for reproducible offline builds."),
        ("Minimum version selection?", "MVS algorithm picks minimum compatible versions satisfying all requires."),
        ("Package vs module?", "Module — deployable unit with go.mod; package — directory of .go files sharing package name."),
        ("Internal packages?", "directory internal/ — importable only from parent tree."),
        ("go.work workspace?", "Multi-module local development — go work init."),
        ("Semantic import versioning?", "v2+ module path includes /v2 suffix in import path."),
        ("Init side effects?", "import _ \"driver\" registers driver via init — explicit side-effect import."),
        ("Build constraints?", "//go:build linux at top (modern) vs old // +build comment."),
        ("Cross compile?", "GOOS=linux GOARCH=amd64 go build — easy cross compilation."),
        ("go install?", "Build and install binary to GOBIN/GOPATH/bin."),
        ("Module proxy?", "GOPROXY=https://proxy.golang.org default — module download cache."),
        ("Private modules?", "GOPRIVATE env skip proxy for private repos."),
        ("Replace directive?", "replace example.com/mod => ../localmod for local dev."),
        ("Sum verification?", "go.sum hashes ensure integrity of downloaded modules."),
        ("Package naming?", "Short, lowercase, no underscores; last element of import path often matches dir name."),
        ("Document exported API?", "All exported names need doc comment — godoc and linters."),
        ("Circular imports?", "Forbidden — refactor to third package or interfaces."),
        ("Main package location?", "cmd/myapp/main.go common layout pattern."),
        ("Standard project layout?", "Not official but cmd/, internal/, pkg/ conventions widely used."),
        ("go version in go.mod?", "Sets language version; toolchain directive Go 1.21+ for reproducible toolchain."),
        ("Retracted versions?", "Module retraction in go.mod protects from bad published versions."),
    ],
}

CODE_CARDS: list[tuple[str, str, str, str, str]] = [
    ("Slice append без присваивания", "Исправь — append должен сохраняться в s.", """package main

func addItem(s []int, v int) []int {
    append(s, v)
    return s
}""", """package main

func addItem(s []int, v int) []int {
    return append(s, v)
}""", "Типы и структуры"),
    ("Nil map write", "Исправь — map нужно инициализировать перед записью.", """package main

func setScore(scores map[string]int, user string, score int) {
    scores[user] = score
}""", """package main

func setScore(scores map[string]int, user string, score int) {
    if scores == nil {
        scores = make(map[string]int)
    }
    scores[user] = score
}""", "Типы и структуры"),
    ("Range loop goroutine capture", "Исправь — каждая goroutine должна печатать своё значение v (Go 1.21 style).", """package main

import "fmt"

func printAll(vals []int) {
    for _, v := range vals {
        go fmt.Println(v)
    }
}""", """package main

import "fmt"

func printAll(vals []int) {
    for _, v := range vals {
        go func(n int) {
            fmt.Println(n)
        }(v)
    }
}""", "Goroutines и каналы"),
    ("Defer закрывает не тот ресурс", "Исправь — defer должен закрывать f, а не переиспользовать err переменную неправильно.", """package main

import "os"

func readPath(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer os.Close(f)
    return os.ReadFile(path)
}""", """package main

import "io"
import "os"

func readPath(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    return io.ReadAll(f)
}""", "Функции и defer"),
    ("Pointer receiver copy", "Исправь Increment — счётчик должен увеличиваться на receiver.", """package main

type Counter struct{ n int }

func (c Counter) Increment() {
    c.n++
}""", """package main

type Counter struct{ n int }

func (c *Counter) Increment() {
    c.n++
}""", "Методы и интерфейсы"),
    ("Shadowing err", "Исправь — не теряй ошибку Open при повторном :=.", """package main

import "os"

func openBoth(a, b string) error {
    f1, err := os.Open(a)
    if err != nil {
        return err
    }
    defer f1.Close()
    f2, err := os.Open(b)
    if err != nil {
        return err
    }
    defer f2.Close()
    return nil
}""", """package main

import "os"

func openBoth(a, b string) error {
    f1, err := os.Open(a)
    if err != nil {
        return err
    }
    defer f1.Close()
    f2, err2 := os.Open(b)
    if err2 != nil {
        return err2
    }
    defer f2.Close()
    return nil
}""", "Ошибки"),
    ("Interface nil check wrong", "Исправь isEmpty — typed nil pointer не должен считаться non-empty interface.", """package main

type Node struct{}

func isEmpty(v interface{}) bool {
    return v == nil
}""", """package main

import "reflect"

func isEmpty(v interface{}) bool {
    if v == nil {
        return true
    }
    rv := reflect.ValueOf(v)
    return rv.Kind() == reflect.Ptr && rv.IsNil()
}""", "Методы и интерфейсы"),
    ("Channel send без goroutine deadlock", "Исправь — unbuffered send блокирует main; используй buffer или goroutine.", """package main

func ping(ch chan string) {
    ch <- "ping"
}""", """package main

func ping(ch chan string) {
    ch <- "ping"
}

func start() string {
    ch := make(chan string, 1)
    go ping(ch)
    return <-ch
}""", "Goroutines и каналы"),
    ("WaitGroup Add после Wait", "Исправь порядок WaitGroup.", """package main

import "sync"

func run(tasks []func()) {
    var wg sync.WaitGroup
    for _, task := range tasks {
        go func(fn func()) {
            fn()
            wg.Done()
        }(task)
    }
    wg.Add(len(tasks))
    wg.Wait()
}""", """package main

import "sync"

func run(tasks []func()) {
    var wg sync.WaitGroup
    wg.Add(len(tasks))
    for _, task := range tasks {
        go func(fn func()) {
            defer wg.Done()
            fn()
        }(task)
    }
    wg.Wait()
}""", "Goroutines и каналы"),
    ("JSON unexported fields", "Исправь — JSON должен сериализовать Name (export field).", """package main

type User struct {
    name string
    ID   int
}""", """package main

type User struct {
    Name string `json:"name"`
    ID   int    `json:"id"`
}""", "Типы и структуры"),
    ("String concat in loop", "Исправь — используй strings.Builder для эффективности.", """package main

func join(words []string) string {
    var s string
    for _, w := range words {
        s += w
    }
    return s
}""", """package main

import "strings"

func join(words []string) string {
    var b strings.Builder
    for _, w := range words {
        b.WriteString(w)
    }
    return b.String()
}""", "Stdlib"),
    ("Compare slices with ==", "Исправь equal — slices нельзя сравнивать через ==.", """package main

func equal(a, b []int) bool {
    return a == b
}""", """package main

import "bytes"

func equal(a, b []int) bool {
    if len(a) != len(b) {
        return false
    }
    for i := range a {
        if a[i] != b[i] {
            return false
        }
    }
    return true
}""", "Типы и структуры"),
    ("Missing comma in composite literal", "Исправь multiline slice literal — trailing comma.", """package main

func nums() []int {
    return []int{
        1
        2
    }
}""", """package main

func nums() []int {
    return []int{
        1,
        2,
    }
}""", "Основы"),
    ("Error wrap without %w", "Исправь wrap — используй %w для unwrap.", """package main

import "fmt"

func load() error {
    err := fmt.Errorf("disk")
    return fmt.Errorf("load failed: %v", err)
}""", """package main

import "fmt"

func load() error {
    err := fmt.Errorf("disk")
    return fmt.Errorf("load failed: %w", err)
}""", "Ошибки"),
    ("Context not passed", "Исправь fetch — передай ctx в http.NewRequestWithContext.", """package main

import (
    "context"
    "net/http"
)

func fetch(ctx context.Context, url string) (*http.Response, error) {
    req, err := http.NewRequest(http.MethodGet, url, nil)
    if err != nil {
        return nil, err
    }
    return http.DefaultClient.Do(req)
}""", """package main

import (
    "context"
    "net/http"
)

func fetch(ctx context.Context, url string) (*http.Response, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return nil, err
    }
    return http.DefaultClient.Do(req)
}""", "Stdlib"),
    ("Mutex unlock without defer", "Исправь — Unlock через defer, избегай забыть при return.", """package main

import "sync"

type Safe struct {
    mu sync.Mutex
    v  int
}

func (s *Safe) Add(n int) {
    s.mu.Lock()
    if n < 0 {
        return
    }
    s.v += n
    s.mu.Unlock()
}""", """package main

import "sync"

type Safe struct {
    mu sync.Mutex
    v  int
}

func (s *Safe) Add(n int) {
    s.mu.Lock()
    defer s.mu.Unlock()
    if n < 0 {
        return
    }
    s.v += n
}""", "Goroutines и каналы"),
    ("Generic min wrong constraint", "Исправь Min — используй cmp.Ordered (Go 1.21+).", """package main

func Min[T any](a, b T) T {
    if a < b {
        return a
    }
    return b
}""", """package main

import "cmp"

func Min[T cmp.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}""", "Generics"),
    ("Test comparison with ==", "Исправь TestSum — сравни got/want с понятным сообщением.", """package main

import "testing"

func TestSum(t *testing.T) {
    got := sum(2, 2)
    if got != 4 {
        t.Fail()
    }
}""", """package main

import "testing"

func TestSum(t *testing.T) {
    got := sum(2, 2)
    want := 4
    if got != want {
        t.Errorf("sum() = %d, want %d", got, want)
    }
}""", "Тестирование"),
    ("Import cycle hint package main", "Исправь — вынеси общий тип в отдельный пакет (комментарий в reference).", """package main

type Config struct {
    Host string
}""", """// Move shared types to a non-main package, e.g. package config:

package config

type Config struct {
    Host string
}""", "Модули и пакеты"),
    ("Close body leak", "Исправь — закрой resp.Body.", """package main

import "net/http"

func getURL(url string) error {
    resp, err := http.Get(url)
    if err != nil {
        return err
    }
    _ = resp.StatusCode
    return nil
}""", """package main

import (
    "io"
    "net/http"
)

func getURL(url string) error {
    resp, err := http.Get(url)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    _, _ = io.Copy(io.Discard, resp.Body)
    return nil
}""", "Stdlib"),
    ("switch без default #1", "Добавь default в switch.", """package main

// fix me
func example() {
    switch day := 0; day { case 1: return "Mon" }
}""", """package main

func example() {
    switch day := 0; day {
case 1:
    return "Mon"
default:
    return "Unknown"
}
}""", "Основы"),
    ("slice copy length #1", "copy должен учитывать длину dst.", """package main

// fix me
func example() {
    copy(dst, src)
}""", """package main

func example() {
    n := copy(dst, src)
_ = n
}""", "Типы и структуры"),
    ("named return shadow #1", "Используй named return err корректно.", """package main

// fix me
func example() {
    func f() error { return nil }
}""", """package main

func example() {
    func f() (err error) {
    defer func() { _ = err }()
    return nil
}
}""", "Функции и defer"),
    ("missing interface method #1", "Добавь Read для *Buffer.", """package main

// fix me
func example() {
    type Buffer struct{ data []byte }
}""", """package main

func example() {
    type Buffer struct{ data []byte }
func (b *Buffer) Read(p []byte) (int, error) { n := copy(p, b.data); return n, nil }
}""", "Методы и интерфейсы"),
    ("select default busy loop #1", "Убери busy loop — блокируй на receive.", """package main

// fix me
func example() {
    for { select { default: } }
}""", """package main

func example() {
    for range ch { }
}""", "Goroutines и каналы"),
    ("log and return #1", "Не глотай err — return после log.", """package main

// fix me
func example() {
    if err != nil { return nil }
}""", """package main

func example() {
    if err != nil {
    return nil, err
}
}""", "Ошибки"),
    ("filepath.Base #1", "Используй filepath.Base для имени файла.", """package main

// fix me
func example() {
    parts := strings.Split(path, "/"); return parts[len(parts)-1]
}""", """package main

func example() {
    return filepath.Base(path)
}""", "Stdlib"),
    ("missing constraint #1", "Добавь comparable для map key.", """package main

// fix me
func example() {
    func Keys[M map[K]V, K, V any](m M) []K
}""", """package main

func example() {
    func Keys[M ~map[K]V, K comparable, V any](m M) []K
}""", "Generics"),
    ("parallel without setup #1", "Вызови t.Parallel() в начале subtest.", """package main

// fix me
func example() {
    func TestX(t *testing.T) { }
}""", """package main

func example() {
    func TestX(t *testing.T) {
    t.Parallel()
}
}""", "Тестирование"),
    ("wrong module path import #1", "Импорт должен совпадать с go.mod module path.", """package main

// fix me
func example() {
    import "myapp/internal/foo"
}""", """package main

func example() {
    import "github.com/org/myapp/internal/foo"
}""", "Модули и пакеты"),
    ("switch без default #2", "Добавь default в switch.", """package main

// fix me
func example() {
    switch day := 0; day { case 1: return "Mon" }
}""", """package main

func example() {
    switch day := 0; day {
case 1:
    return "Mon"
default:
    return "Unknown"
}
}""", "Основы"),
    ("slice copy length #2", "copy должен учитывать длину dst.", """package main

// fix me
func example() {
    copy(dst, src)
}""", """package main

func example() {
    n := copy(dst, src)
_ = n
}""", "Типы и структуры"),
    ("named return shadow #2", "Используй named return err корректно.", """package main

// fix me
func example() {
    func f() error { return nil }
}""", """package main

func example() {
    func f() (err error) {
    defer func() { _ = err }()
    return nil
}
}""", "Функции и defer"),
    ("missing interface method #2", "Добавь Read для *Buffer.", """package main

// fix me
func example() {
    type Buffer struct{ data []byte }
}""", """package main

func example() {
    type Buffer struct{ data []byte }
func (b *Buffer) Read(p []byte) (int, error) { n := copy(p, b.data); return n, nil }
}""", "Методы и интерфейсы"),
    ("select default busy loop #2", "Убери busy loop — блокируй на receive.", """package main

// fix me
func example() {
    for { select { default: } }
}""", """package main

func example() {
    for range ch { }
}""", "Goroutines и каналы"),
    ("log and return #2", "Не глотай err — return после log.", """package main

// fix me
func example() {
    if err != nil { return nil }
}""", """package main

func example() {
    if err != nil {
    return nil, err
}
}""", "Ошибки"),
    ("filepath.Base #2", "Используй filepath.Base для имени файла.", """package main

// fix me
func example() {
    parts := strings.Split(path, "/"); return parts[len(parts)-1]
}""", """package main

func example() {
    return filepath.Base(path)
}""", "Stdlib"),
    ("missing constraint #2", "Добавь comparable для map key.", """package main

// fix me
func example() {
    func Keys[M map[K]V, K, V any](m M) []K
}""", """package main

func example() {
    func Keys[M ~map[K]V, K comparable, V any](m M) []K
}""", "Generics"),
    ("parallel without setup #2", "Вызови t.Parallel() в начале subtest.", """package main

// fix me
func example() {
    func TestX(t *testing.T) { }
}""", """package main

func example() {
    func TestX(t *testing.T) {
    t.Parallel()
}
}""", "Тестирование"),
    ("wrong module path import #2", "Импорт должен совпадать с go.mod module path.", """package main

// fix me
func example() {
    import "myapp/internal/foo"
}""", """package main

func example() {
    import "github.com/org/myapp/internal/foo"
}""", "Модули и пакеты"),
    ("switch без default #3", "Добавь default в switch.", """package main

// fix me
func example() {
    switch day := 0; day { case 1: return "Mon" }
}""", """package main

func example() {
    switch day := 0; day {
case 1:
    return "Mon"
default:
    return "Unknown"
}
}""", "Основы"),
    ("slice copy length #3", "copy должен учитывать длину dst.", """package main

// fix me
func example() {
    copy(dst, src)
}""", """package main

func example() {
    n := copy(dst, src)
_ = n
}""", "Типы и структуры"),
    ("named return shadow #3", "Используй named return err корректно.", """package main

// fix me
func example() {
    func f() error { return nil }
}""", """package main

func example() {
    func f() (err error) {
    defer func() { _ = err }()
    return nil
}
}""", "Функции и defer"),
    ("missing interface method #3", "Добавь Read для *Buffer.", """package main

// fix me
func example() {
    type Buffer struct{ data []byte }
}""", """package main

func example() {
    type Buffer struct{ data []byte }
func (b *Buffer) Read(p []byte) (int, error) { n := copy(p, b.data); return n, nil }
}""", "Методы и интерфейсы"),
    ("select default busy loop #3", "Убери busy loop — блокируй на receive.", """package main

// fix me
func example() {
    for { select { default: } }
}""", """package main

func example() {
    for range ch { }
}""", "Goroutines и каналы"),
    ("log and return #3", "Не глотай err — return после log.", """package main

// fix me
func example() {
    if err != nil { return nil }
}""", """package main

func example() {
    if err != nil {
    return nil, err
}
}""", "Ошибки"),
    ("filepath.Base #3", "Используй filepath.Base для имени файла.", """package main

// fix me
func example() {
    parts := strings.Split(path, "/"); return parts[len(parts)-1]
}""", """package main

func example() {
    return filepath.Base(path)
}""", "Stdlib"),
    ("missing constraint #3", "Добавь comparable для map key.", """package main

// fix me
func example() {
    func Keys[M map[K]V, K, V any](m M) []K
}""", """package main

func example() {
    func Keys[M ~map[K]V, K comparable, V any](m M) []K
}""", "Generics"),
    ("parallel without setup #3", "Вызови t.Parallel() в начале subtest.", """package main

// fix me
func example() {
    func TestX(t *testing.T) { }
}""", """package main

func example() {
    func TestX(t *testing.T) {
    t.Parallel()
}
}""", "Тестирование"),
    ("wrong module path import #3", "Импорт должен совпадать с go.mod module path.", """package main

// fix me
func example() {
    import "myapp/internal/foo"
}""", """package main

func example() {
    import "github.com/org/myapp/internal/foo"
}""", "Модули и пакеты"),
    ("switch без default #4", "Добавь default в switch.", """package main

// fix me
func example() {
    switch day := 0; day { case 1: return "Mon" }
}""", """package main

func example() {
    switch day := 0; day {
case 1:
    return "Mon"
default:
    return "Unknown"
}
}""", "Основы"),
    ("slice copy length #4", "copy должен учитывать длину dst.", """package main

// fix me
func example() {
    copy(dst, src)
}""", """package main

func example() {
    n := copy(dst, src)
_ = n
}""", "Типы и структуры"),
    ("named return shadow #4", "Используй named return err корректно.", """package main

// fix me
func example() {
    func f() error { return nil }
}""", """package main

func example() {
    func f() (err error) {
    defer func() { _ = err }()
    return nil
}
}""", "Функции и defer"),
    ("missing interface method #4", "Добавь Read для *Buffer.", """package main

// fix me
func example() {
    type Buffer struct{ data []byte }
}""", """package main

func example() {
    type Buffer struct{ data []byte }
func (b *Buffer) Read(p []byte) (int, error) { n := copy(p, b.data); return n, nil }
}""", "Методы и интерфейсы"),
    ("select default busy loop #4", "Убери busy loop — блокируй на receive.", """package main

// fix me
func example() {
    for { select { default: } }
}""", """package main

func example() {
    for range ch { }
}""", "Goroutines и каналы"),
    ("log and return #4", "Не глотай err — return после log.", """package main

// fix me
func example() {
    if err != nil { return nil }
}""", """package main

func example() {
    if err != nil {
    return nil, err
}
}""", "Ошибки"),
    ("filepath.Base #4", "Используй filepath.Base для имени файла.", """package main

// fix me
func example() {
    parts := strings.Split(path, "/"); return parts[len(parts)-1]
}""", """package main

func example() {
    return filepath.Base(path)
}""", "Stdlib"),
    ("missing constraint #4", "Добавь comparable для map key.", """package main

// fix me
func example() {
    func Keys[M map[K]V, K, V any](m M) []K
}""", """package main

func example() {
    func Keys[M ~map[K]V, K comparable, V any](m M) []K
}""", "Generics"),
    ("parallel without setup #4", "Вызови t.Parallel() в начале subtest.", """package main

// fix me
func example() {
    func TestX(t *testing.T) { }
}""", """package main

func example() {
    func TestX(t *testing.T) {
    t.Parallel()
}
}""", "Тестирование"),
    ("wrong module path import #4", "Импорт должен совпадать с go.mod module path.", """package main

// fix me
func example() {
    import "myapp/internal/foo"
}""", """package main

func example() {
    import "github.com/org/myapp/internal/foo"
}""", "Модули и пакеты"),
    ("switch без default #5", "Добавь default в switch.", """package main

// fix me
func example() {
    switch day := 0; day { case 1: return "Mon" }
}""", """package main

func example() {
    switch day := 0; day {
case 1:
    return "Mon"
default:
    return "Unknown"
}
}""", "Основы"),
    ("slice copy length #5", "copy должен учитывать длину dst.", """package main

// fix me
func example() {
    copy(dst, src)
}""", """package main

func example() {
    n := copy(dst, src)
_ = n
}""", "Типы и структуры"),
    ("named return shadow #5", "Используй named return err корректно.", """package main

// fix me
func example() {
    func f() error { return nil }
}""", """package main

func example() {
    func f() (err error) {
    defer func() { _ = err }()
    return nil
}
}""", "Функции и defer"),
    ("missing interface method #5", "Добавь Read для *Buffer.", """package main

// fix me
func example() {
    type Buffer struct{ data []byte }
}""", """package main

func example() {
    type Buffer struct{ data []byte }
func (b *Buffer) Read(p []byte) (int, error) { n := copy(p, b.data); return n, nil }
}""", "Методы и интерфейсы"),
    ("select default busy loop #5", "Убери busy loop — блокируй на receive.", """package main

// fix me
func example() {
    for { select { default: } }
}""", """package main

func example() {
    for range ch { }
}""", "Goroutines и каналы"),
    ("log and return #5", "Не глотай err — return после log.", """package main

// fix me
func example() {
    if err != nil { return nil }
}""", """package main

func example() {
    if err != nil {
    return nil, err
}
}""", "Ошибки"),
    ("filepath.Base #5", "Используй filepath.Base для имени файла.", """package main

// fix me
func example() {
    parts := strings.Split(path, "/"); return parts[len(parts)-1]
}""", """package main

func example() {
    return filepath.Base(path)
}""", "Stdlib"),
    ("missing constraint #5", "Добавь comparable для map key.", """package main

// fix me
func example() {
    func Keys[M map[K]V, K, V any](m M) []K
}""", """package main

func example() {
    func Keys[M ~map[K]V, K comparable, V any](m M) []K
}""", "Generics"),
    ("parallel without setup #5", "Вызови t.Parallel() в начале subtest.", """package main

// fix me
func example() {
    func TestX(t *testing.T) { }
}""", """package main

func example() {
    func TestX(t *testing.T) {
    t.Parallel()
}
}""", "Тестирование"),
    ("wrong module path import #5", "Импорт должен совпадать с go.mod module path.", """package main

// fix me
func example() {
    import "myapp/internal/foo"
}""", """package main

func example() {
    import "github.com/org/myapp/internal/foo"
}""", "Модули и пакеты"),
]

REVISION_HINTS: dict[str, list[str]] = {
    "Основы": ['package main', 'iota', 'gofmt', 'zero value', 'exported names', 'short variable declaration', 'range loop'],
    "Типы и структуры": ['slice append', 'map initialization', 'struct embedding', 'pointer vs value', 'json tags', 'make vs new', 'len and cap'],
    "Функции и defer": ['defer LIFO', 'panic recover', 'variadic functions', 'named returns', 'function closures', 'init order'],
    "Методы и интерфейсы": ['implicit interfaces', 'type assertion', 'pointer receiver', 'io.Reader', 'empty interface nil', 'composition'],
    "Goroutines и каналы": ['goroutine', 'channel buffer', 'select', 'WaitGroup', 'Mutex', 'context cancellation', 'race detector'],
    "Ошибки": ['errors.Is', 'errors.As', 'fmt.Errorf %w', 'sentinel errors', 'error wrapping', 'guard clauses'],
    "Stdlib": ['encoding/json', 'net/http', 'context', 'time formatting', 'os.ReadFile', 'sort.Slice', 'log/slog'],
    "Generics": ['type parameters', 'constraints', 'comparable', 'type inference', 'generic structs', 'cmp.Ordered'],
    "Тестирование": ['table-driven tests', 't.Run', 'benchmarks', 'httptest', 'coverage', 't.Helper', 'fuzzing'],
    "Модули и пакеты": ['go.mod', 'go test ./...', 'internal packages', 'semantic versioning', 'go mod tidy', 'cmd layout'],
}
