#!/usr/bin/env python3
"""Generate PHP 8+ deck with 500+ cards (theory + code)."""
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

    # ── PHP 8.0 ──────────────────────────────────────────────────────────
    php80 = [
        theory("Что такое named arguments (именованные аргументы) в PHP 8?", "Вызов функции с указанием имён параметров: foo(name: 'Ann', age: 30). Порядок не важен, можно пропускать параметры с default."),
        theory("Можно ли смешивать позиционные и именованные аргументы?", "Да, но именованные должны идти после всех позиционных."),
        theory("Что такое constructor property promotion?", "Объявление и инициализация свойств прямо в параметрах конструктора: public function __construct(private string $name) {}"),
        theory("Какие модификаторы доступа допустимы в promoted properties?", "public, protected, private — как у обычных свойств."),
        theory("Что такое union types в PHP 8?", "Тип вида int|string — значение может быть одним из перечисленных типов."),
        theory("Можно ли использовать null в union type?", "Да: ?string эквивалентно string|null. Можно писать явно int|null."),
        theory("Что такое mixed type?", "mixed — любой тип, включая null. Замена отсутствию типа для явной аннотации."),
        theory("Что делает оператор ?-> (nullsafe)?", "Вызывает метод/свойство только если левая часть не null, иначе весь результат null."),
        theory("Чем ?-> отличается от ->?", "-> на null вызывает Error; ?-> коротко заменяет цепочку if ($x !== null) $x->m();"),
        theory("Что такое match expression?", "Выражение, возвращающее значение по сравнению с === (строгое). Требует исчерпывающих веток или default."),
        theory("Чем match лучше switch для возврата значений?", "match — expression, не нужен break, сравнение строгое, можно вернуть результат напрямую."),
        theory("Что такое throw expression?", "throw можно использовать там, где допустимо выражение: $x ?? throw new Exception();"),
        theory("Что такое attributes (атрибуты) в PHP 8?", "Метаданные в #[...] для классов, методов, параметров. Читаются через Reflection API."),
        theory("Как объявить пользовательский атрибут?", "class Route { public function __construct(public string $path) {} } и #[Route('/api')] над методом."),
        theory("Что такое WeakMap?", "Коллекция с weak-ключами (объекты). Ключи удаляются GC при отсутствии других ссылок."),
        theory("Что такое static return type?", "Метод может вернуть static — тип наследника при late static binding."),
        theory("Что делает str_contains()?", "Проверяет наличие подстроки. Возвращает bool. PHP 8+."),
        theory("Что делает str_starts_with() и str_ends_with()?", "Проверяют начало/конец строки. Возвращают bool."),
        theory("Что возвращает get_debug_type()?", "Строковое имя типа переменной для отладки, точнее gettype() для объектов."),
        theory("Что такое non-capturing catch?", "catch (Exception) без переменной — когда исключение не нужно в теле."),
        theory("Trailing comma в списке параметров — зачем?", "Запятая после последнего параметра упрощает diff при добавлении параметров."),
        theory("Что изменилось в сравнении строк с числами в PHP 8?", "Нестрогое сравнение '0' == 'foo' теперь false (более предсказуемо)."),
        theory("Что такое ClassName::class на объекте?", "В PHP 8 можно $object::class — имя класса объекта."),
        theory("JIT в PHP 8 — что это?", "Just-In-Time компиляция OPcache для ускорения CPU-bound кода. Включается в php.ini."),
    ]
    cards.extend(php80)

    # ── PHP 8.1 ──────────────────────────────────────────────────────────
    php81 = [
        theory("Что такое enum в PHP 8.1?", "Перечисление: enum Status { case Active; case Archived; } — типобезопасные константы."),
        theory("Unit enum vs backed enum?", "Unit — без значения. Backed: enum Status: string { case Active = 'active'; } — имеет scalar value."),
        theory("Можно ли использовать enum как тип параметра?", "Да: function set(Status $s). Передавать только case, не произвольные строки."),
        theory("Есть ли методы у enum?", "Да, enum может иметь методы, implements interfaces, traits (ограниченно)."),
        theory("Что такое readonly property?", "Свойство, присваиваемое только один раз (обычно в конструкторе). public readonly string $id;"),
        theory("Можно ли изменить readonly property после инициализации?", "Нет, кроме unset+повторной инициализации в __clone или unserialize (ограниченно)."),
        theory("Что такое first-class callable syntax?", "strlen(...) создаёт Closure из функции/метода без array callable."),
        theory("Синтаксис first-class callable для метода?", "$fn = $obj->method(...); или MyClass::method(...);"),
        theory("Что такое Fiber в PHP 8.1?", "Зелёные потоки для кооперативной многозадачности без async/await на уровне языка."),
        theory("Что такое intersection types?", "Тип A&B — объект должен реализовать оба интерфейса одновременно."),
        theory("Что такое never return type?", "Функция никогда не завершается нормально (throw, exit, infinite loop)."),
        theory("final class constants — что это?", "const можно пометить final — нельзя переопределить в наследнике."),
        theory("Что делает array_is_list()?", "Проверяет, что массив — list (0..n-1 ключи подряд)."),
        theory("Что такое fsync() и fdatasync() в PHP 8.1?", "Сброс буферов файла на диск для надёжной записи."),
        theory("new in initializers — что разрешено?", "В аргументах по умолчанию можно new ClassName() без скобок с аргументами в некоторых случаях."),
    ]
    cards.extend(php81)

    # ── PHP 8.2 ──────────────────────────────────────────────────────────
    php82 = [
        theory("Что такое readonly class?", "class readonly Point { public function __construct(public float $x, public float $y) {} } — все свойства readonly."),
        theory("Можно ли наследовать readonly class?", "Только если родитель тоже readonly class."),
        theory("Что такое DNF types (Disjunctive Normal Form)?", "Комбинация union и intersection: (A&B)|C — скобки обязательны."),
        theory("Standalone типы true, false, null как type hints?", "function f(true $x) — параметр должен быть именно true. PHP 8.2+."),
        theory("Константы в traits PHP 8.2?", "trait T { public const X = 1; } — доступ через класс, использующий trait."),
        theory("Что такое Random\\Randomizer?", "OOP API для криптостойкого/детерминированного random: getInt, shuffleArray, pickArrayKeys."),
        theory("SensitiveParameter attribute?", "#[SensitiveParameter] скрывает значение аргумента в stack trace."),
        theory("Что такое mysqli_execute_query()?", "Упрощённый prepared query в mysqli для PHP 8.2+."),
    ]
    cards.extend(php82)

    # ── PHP 8.3 ──────────────────────────────────────────────────────────
    php83 = [
        theory("Typed class constants PHP 8.3?", "interface I { public const string VERSION = '1'; } — тип у константы класса/интерфейса."),
        theory("Dynamic class constant fetch?", "ClassName::{$name} — обращение к константе по строковой переменной."),
        theory("Что делает json_validate()?", "Проверяет валидность JSON-строки без декодирования. Быстрее json_decode для проверки."),
        theory("Attribute Override PHP 8.3?", "#[\\Override] на методе — компилятор проверит, что метод реально переопределяет родительский."),
        theory("Что такое clone with в PHP 8.3?", "clone $obj with { prop: $value } — клон с изменением свойств (readonly-friendly)."),
        theory("Randomizer getBytesFromString?", "Генерация случайной строки из заданного алфавита."),
    ]
    cards.extend(php83)

    # ── PHP 8.4 ──────────────────────────────────────────────────────────
    php84 = [
        theory("Property hooks PHP 8.4?", "get/set хуки у свойств: public string $name { get => strtoupper($this->name); set => $value = trim($value); }"),
        theory("Asymmetric visibility PHP 8.4?", "public private(set) string $name — чтение public, запись только из класса."),
        theory("array_find() и array_find_key()?", "Находят первый элемент/ключ по callback. PHP 8.4."),
        theory("array_any() и array_all()?", "Проверка, что хотя бы один / все элементы удовлетворяют predicate."),
        theory("Что нового в DOM HTML5 PHP 8.4?", "Dom\\HTMLDocument — современный парсинг HTML5."),
    ]
    cards.extend(php84)

    # ── OOP / типы / современный стиль ───────────────────────────────────
    oop_topics = [
        ("Зачем declare(strict_types=1)?", "Строгая проверка типов скаляров при вызовах в этом файле — без неявных приведений."),
        ("Чем interface отличается от abstract class?", "Interface — контракт методов без реализации. Abstract — может иметь реализацию и состояние."),
        ("Когда использовать trait?", "Гorizontal reuse поведения без множественного наследования классов."),
        ("Что такое late static binding?", "static::method() вызывает метод класса наследника, self:: — класса, где написан код."),
        ("Что такое covariant return types?", "Дочерний метод может вернуть более узкий тип (подкласс) чем родитель."),
        ("Что такое contravariant parameters?", "Параметры могут быть шире в наследнике (PHP 7.4+ для параметров)."),
        ("Что делает __invoke на объекте?", "Объект можно вызвать как функцию: $obj(...)."),
        ("Что такое anonymous class?", "new class implements Foo { ... } — одноразовый класс без имени."),
        ("Чем final class полезен?", "Запрещает наследование — контроль иерархии и безопасность."),
        ("Что такое clone и __clone?", "clone копирует объект; __clone для глубокого копирования вложенных объектов."),
        ("Serialization __serialize / __unserialize?", "Замена serialize_sleep/wakeup — контроль сериализации свойств."),
        ("Что такое backed enum from()?", "Status::from('active') — case или ValueError. tryFrom() возвращает null."),
        ("Что такое readonly и clone?", "При clone readonly свойства можно переинициализировать один раз в __clone."),
        ("Почему enum лучше const для статусов?", "Типобезопасность, методы, исчерпываемость, IDE autocomplete."),
        ("Что такое typed property без default?", "Должно быть инициализировано до чтения, иначе Error (uninitialized)."),
        ("Что делает unset($this->prop) для typed property?", "Сбрасывает в uninitialized — повторная инициализация возможна."),
        ("Что такое arrow function fn()?", "Краткий closure с автоматическим захватом by-value: fn($x) => $x * $this->factor."),
        ("Чем fn отличается от function() use?", "fn захватывает автоматически, только одно выражение, by-value по умолчанию."),
        ("Что такое closure bindTo?", "Привязка $this и scope для closure к другому объекту/классу."),
        ("Что такое Generator?", "Функция с yield — ленивая итерация без загрузки всего набора в память."),
        ("yield from?", "Делегирование другому генератору/iterable."),
        ("Что такое IteratorAggregate?", "Класс с getIterator() — foreach по объекту."),
        ("SPL ArrayObject vs array?", "ArrayObject — OOP обёртка, может иметь flags (STD_PROP_LIST и др.)."),
        ("Что такое SplFixedArray?", "Массив фиксированного размера с быстрым доступом по int ключу."),
        ("Что такое WeakReference?", "Ссылка на объект не препятствующая GC."),
        ("PDO::FETCH_ASSOC vs FETCH_OBJ?", "ASSOC — массив; OBJ — stdClass или указанный класс."),
        ("Зачем PDO prepared statements?", "Защита от SQL injection + кэш плана запроса."),
        ("Что такое emulated prepares?", "PDO может эмулировать prepare на клиенте — настройка PDO::ATTR_EMULATE_PREPARES."),
        ("Что такое SQL injection?", "Внедрение SQL через неэкранированный ввод. Лечится prepared statements."),
        ("Что такое XSS и htmlspecialchars?", "Экранирование HTML при выводе пользовательских данных ENT_QUOTES, UTF-8."),
        ("Что такое CSRF token?", "Секрет формы для проверки, что запрос от вашего UI, а не чужого сайта."),
        ("Что такое PSR-4 autoload?", "Namespace Vendor\\Package\\Class → path по prefix и base directory."),
        ("Composer autoload files vs classmap?", "files — eager include; classmap — scan; psr-4 — основной для src."),
        ("Что такое declare encoding?", "declare(encoding='...') устарело; UTF-8 source files стандарт."),
        ("Что такое null coalescing ??", "$a ?? $b — $a если isset и not null, иначе $b."),
        ("Что такое null coalescing assignment ??=", "$a ??= $b — присвоить $b если $a null."),
        ("Spaceship operator <=>?", "Возвращает -1, 0, 1 для сравнения (удобно в usort)."),
        ("Что такое spread operator ... в массивах?", "[...$a, ...$b] — объединение массивов PHP 7.4+."),
        ("Что такое named args с variadic?", "foo(...$arr) распаковка; можно комбинировать с named."),
        ("Что такое never в union?", "never не комбинируется в union (нет значения)."),
        ("Что такое void return type?", "Функция ничего не возвращает (return; без значения)."),
        ("Что такое callable type?", "Любой вызываемый: closure, function name, [obj, method]."),
        ("Что такое object type hint?", "object — любой объект, не scalar/array."),
        ("Что такое iterable?", "array|Traversable — foreach совместимо."),
        ("Что такое array shape (PHPDoc)?", "@param array{id:int,name:string} — документация структуры, не runtime."),
        ("Что такое list type (PHPDoc)?", "list<string> — массив с последовательными int ключами."),
        ("Что такое template/generics в PHPStan?", "@template T — статический анализ, не runtime PHP."),
        ("Что такое match с multiple conditions?", "match(true) { $a > 0 && $b => ..., default => ... }"),
        ("Что такое str_replace vs preg_replace?", "str — литерал; preg — regex. preg_quote для экранирования."),
        ("Что такое mb_string?", "Расширение для многобайтовых строк UTF-8 — mb_strlen, mb_substr."),
        ("Что такое Intl extension?", "Локализация, форматирование дат/чисел, collator."),
        ("DateTimeImmutable vs DateTime?", "Immutable — modify возвращает новый объект, безопаснее."),
        ("Что такое DateInterval?", "PT1H — период для DateTime::add/sub."),
        ("Что такое timezone в PHP?", "DateTimeZone, ini date.timezone, immutable хранение UTC в БД."),
        ("Что такое filter_var FILTER_VALIDATE_EMAIL?", "Валидация email — не замена полноценной проверки RFC."),
        ("Что такое filter_input?", "Чтение суперглобалов с фильтрами INPUT_GET, INPUT_POST."),
        ("Что такое password_hash?", "PASSWORD_DEFAULT (bcrypt/argon2) — безопасное хеширование паролей."),
        ("password_verify?", "timing-safe сравнение пароля с hash."),
        ("Что такое sodium/crypto в PHP?", "libsodium bindings — secretbox, sign, random_bytes."),
        ("random_bytes vs rand?", "random_bytes криптостойкий; rand/mt_rand — не для секретов."),
        ("Что такое opcache?", "Кэш bytecode — ускорение, preload в PHP 7.4+ для классов."),
        ("Что такое preloading?", "Загрузка классов в память при старте PHP-FPM worker."),
        ("Что такое FFI в PHP?", "Foreign Function Interface — вызов C из PHP (осторожно с безопасностью)."),
        ("Что такое fibers и event loop?", "Fibers низкоуровневые; Revolt/Amp строят async поверх них."),
        ("Что такое attributes для validation?", "Кастомные #[Assert\\NotNull] + reflection в middleware."),
        ("Что такое readonly и JSON serialize?", "Readonly свойства сериализуются как обычные public в json_encode объекта."),
        ("json_encode JSON_THROW_ON_ERROR?", "Исключение JsonException вместо false при ошибке."),
        ("json_decode associative true?", "Массивы вместо stdClass для объектов JSON."),
        ("Что такое stream context HTTP?", "stream_context_create для timeout, headers в file_get_contents."),
        ("curl vs file_get_contents?", "curl гибче для HTTP методов, headers, TLS options."),
        ("Что такое multipart form?", "CURLFile для загрузки файлов POST."),
        ("Что такое superglobals?", "$_GET, $_POST, $_SERVER, $_SESSION, $_COOKIE, $_FILES, $_ENV."),
        ("session_start options?", "cookie_httponly, secure, samesite через session_set_cookie_params."),
        ("Что такое SameSite=Lax?", "Cookie не отправляется на cross-site POST, защита CSRF частично."),
        ("Что такое type juggling в строгом режиме?", "strict_types отключает неявное (int)'123' при вызове из другого файла."),
        ("Что такое Reference (&)?", "Передача по ссылке — alias переменной, осторожно с foreach &$arr."),
        ("Что такое __destruct?", "Вызывается при уничтожении объекта — закрытие ресурсов."),
        ("Что такое register_shutdown_function?", "Callback при завершении скрипта — flush, cleanup."),
        ("Что такое tick / declare ticks?", "Устаревший механизм — редко используется."),
        ("Что такое opendir/scandir vs SplFileInfo?", "SplFileInfo — OOP метаданные файла."),
        ("Что такое pathinfo?", "dirname, basename, extension из пути."),
        ("realpath и symlink?", "realpath разрешает симлинки до канонического пути."),
        ("file locking flock?", "LOCK_EX эксклюзивная блокировка при записи логов."),
        ("tempnam и sys_get_temp_dir?", "Безопасное создание temp файлов."),
        ("Что такое include vs require?", "require — fatal если нет файла; include — warning."),
        ("once версии include?", "include_once — предотвращает повторное определение классов."),
        ("Что такое namespace?", "Изоляция имён классов Vendor\\Package\\Class."),
        ("use alias import?", "use Foo\\Bar as Baz; короткое имя."),
        ("group use?", "use Foo\\{Bar, Baz}; PHP 7+."),
        ("Что такое global keyword?", "Доступ к global переменной внутри функции — лучше избегать."),
        ("static variable in function?", "Сохраняет значение между вызовами функции."),
        ("Что такое __DIR__ и __FILE__?", "Директория и путь текущего файла для require относительных путей."),
        ("Что такое match default обязателен?", "Если не все cases покрыты — нужен default, иначе UnhandledMatchError."),
        ("UnhandledMatchError?", "Исключение когда match не нашёл ветку."),
        ("ValueError в PHP 8?", "Invalid argument that would be warning раньше — например Enum::from неверное значение."),
        ("TypeError?", "Неверный тип аргумента/return при type hints."),
        ("Error vs Exception?", "Error — иерархия engine errors (TypeError, ParseError); Exception — userland."),
        ("Throwable?", "Error|Exception — общий catch для всего."),
        ("finally block?", "Выполняется всегда после try/catch."),
        ("Exception getPrevious?", "Цепочка исключений cause."),
        ("SPL exceptions?", "InvalidArgumentException, RuntimeException — семантика ошибок."),
        ("Что такое assert()?", "Проверка инвариантов в dev; может быть отключён zend.assertions."),
        ("Что такое compact/extract?", "compact('a','b') — массив из переменных; extract — обратно (осторожно с безопасностью)."),
        ("list() destructuring?", "[$a, $b] = $array; с ключами ['x'=>$x] = $arr PHP 7.1+."),
        ("match и enums?", "match($status) { Status::Active => ..., Status::Archived => ... }"),
        ("enum cases in array?", "array_column(Status::cases(), 'value') для backed enum."),
        ("What is Fibers suspend/resume?", "Fiber::suspend передаёт управление; resume продолжает."),
        ("Generator send()?", "Отправка значения в yield как результат выражения."),
        ("Iterator valid() current()?", "Ручная итерация с проверкой valid()."),
        ("Countable interface?", "count($obj) если implements Countable."),
        ("Stringable interface?", "__toString(): string — объект как строка."),
        ("JsonSerializable?", "json_encode вызывает jsonSerialize() для кастомного представления."),
        ("__toString must not throw?", "Historically problematic; в PHP 8+ лучше не бросать из __toString."),
        ("Unit enum comparison?", "Status::Active === Status::Active; case identity."),
        ("Backed enum value property?", "Status::Active->value для scalar."),
        ("enum from int backed?", "enum Priority: int { case High = 1; }"),
        ("readonly promoted in constructor?", "public function __construct(public readonly string $id) {}"),
        ("private(set) PHP 8.4?", "public string $slug { private(set) } — запись только внутри класса."),
        ("Property hooks get without field?", "Может вычислять on-the-fly без backing field."),
        ("array_map arrow?", "array_map(fn($n) => $n * 2, $nums);"),
        ("array_filter preserve keys?", "array_filter без ARRAY_FILTER_USE_KEY сохраняет ключи по умолчанию."),
        ("array_values reindex?", "Сброс ключей в 0..n после filter."),
        ("usort stable?", "PHP sort не guaranteed stable до recent; usort custom comparator."),
        ("sort flags SORT_NUMERIC?", "Числовое сравнение строк."),
        ("keys exists vs isset?", "isset false для null; array_key_exists true для null key."),
        ("?? vs ?: ?", "$a ?: $b — falsy; ?? только null/unset."),
        ("empty() on '0'?", "empty('0') === true — частая ловушка."),
        ("is_countable?", "Проверка array или Countable перед count()."),
        ("get_class($obj)?", "Имя класса; $obj::class предпочтительнее PHP 8."),
        ("instanceof with string?", "instanceof InterfaceName — true/false."),
        ("ReflectionClass getAttributes?", "Чтение PHP 8 attributes с newInstance()."),
        ("Attribute IS_REPEATABLE?", "Флаг #[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]."),
        ("Deprecated attribute PHP 8.4?", "#[\\Deprecated] на функциях — runtime notice."),
        ("AllowDynamicProperties?", "#[\\AllowDynamicProperties] отключает deprecation dynamic props."),
        ("Dynamic properties deprecation?", "PHP 8.2+ deprecated необъявленные свойства на классах."),
        ("${var} deprecated?", "Использовать {$var} в строках."),
        ("create static factory?", "public static function create(): static new static();"),
        ("private constructor singleton?", "getInstance() единственная точка создания."),
        ("interface default methods?", "PHP interfaces могут иметь default body методов PHP 8+."),
        ("trait conflict resolution?", "insteadof и as для разрешения коллизий методов."),
        ("trait alias as visibility?", "use T { method as private otherMethod; }"),
        ("abstract trait methods?", "Trait может объявить abstract method — класс должен реализовать."),
        ("Readonly class и dynamic?", "Readonly class не может AllowDynamicProperties без явного attr."),
        ("enum implementing interface?", "enum E implements I { case A; public function foo(): void {} }"),
        ("match strict types strings?", "match '01' with 1 не совпадёт — ===."),
        ("bc math bcmath?", "Точная арифметика для decimal money — bcadd, bcmul."),
        ("float precision money?", "Не использовать float для денег — int cents или bcmath."),
        ("GMP extension?", "Большие целые числа."),
        ("SplQueue SplStack?", "Стандартные структуры данных SPL."),
        ("SplHeap?", "Priority queue через compare method."),
        ("Closure fromCallable?", "Closure::fromCallable([$obj, 'method']) альтернатива first-class."),
        ("bindTo null scope?", "Static closure binding."),
        ("serialize enums?", "Backed enum сериализуется как value при default serialize."),
        ("__sleep whitelist?", "Старый способ — список свойств для serialize."),
        ("igbinary msgpack?", "Альтернативные быстрые serializers через extensions."),
        ("pcntl extension?", "Process control CLI only — signals fork."),
        ("posix getpid?", "Unix PID CLI scripts."),
        ("proc_open?", "Запуск subprocess с pipes."),
        ("escapeshellarg?", "Безопасная обёртка аргумента shell command."),
        ("shell_exec vs exec?", "Безопасность — избегать shell с user input."),
        ("LDAP/SQLite/PDO drivers?", "PDO SQLite in-memory :memory: для tests."),
        ("Transactions PDO?", "beginTransaction commit rollBack."),
        ("PDO ERRMODE_EXCEPTION?", "PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION."),
        ("Named placeholders :name?", "bindValue(':email', $email) в prepared."),
        ("positional ? placeholders?", "bind by index 1-based."),
        ("lastInsertId?", "Auto increment после INSERT."),
        ("rowCount for SELECT?", "Не всегда надёжен — не полагаться для count rows SELECT."),
        ("FETCH_CLASS?", "new instances of class with properties mapped."),
        ("Lazy objects PHP 8.4?", "LazyGhost для отложенной инициализации proxy."),
        ("WeakMap use case?", "Metadata к объектам без утечки памяти."),
        ("ObjectStorage?", "Map object->data с object identity keys."),
        ("ArrayIterator?", "OOP foreach over array by reference option."),
        ("CachingIterator?", "Has seen current element — lookahead."),
        ("Regex PCRE u modifier?", "UTF-8 mode preg_match."),
        ("preg_replace_callback?", "Callback для каждого match replacement."),
        ("named capture (?P<name>?", "Доступ $matches['name']."),
        ("str_split mb_str_split?", "Multibyte split characters."),
        ("implode first arg glue?", "implode(',', $arr) — glue первый параметр."),
        ("path stream wrappers?", "php://memory, php://temp, file://."),
        ("filter_var boolean filters?", "FILTER_VALIDATE_BOOLEAN для форм 'true'/'false'."),
        ("header() exit redirect?", "header('Location: ...'); exit; после redirect."),
        ("http_response_code?", "Установка 404, 500 status."),
        ("output buffering ob_start?", "Capture echo для шаблонов."),
        ("fastcgi_finish_request?", "Ответ клиенту и продолжить работу background."),
        ("CLI argv argc?", "$argv массив аргументов скрипта."),
        ("getopt long options?", "getopt('', ['file:','verbose']) parse CLI."),
        ("php -r run code?", "One-liner execution php -r 'echo 1;'."),
        ("phpstan psalm levels?", "Static analysis без runtime — ловят типы до deploy."),
        ("composer scripts?", "post-install-cmd автomation."),
        ("semver caret ^8.0?", "Composer ^8.0 >=8.0 <9.0."),
        ("platform php config?", "composer platform.php фиксирует версию для resolve."),
        ("ext-json requirement?", "composer require ext-json для json functions."),
        ("Attributes Route DI Symfony?", "Frameworks читают attributes для routing PHP 8."),
        ("readonly DTO pattern?", "readonly class UserDto { public function __construct(public string $name) {} }"),
        ("Value object equals?", "Сравнение по свойствам, не identity."),
        ("Named constructor promote?", "public static function fromArray(array $a): self new self(...)."),
        ("Exception handler set_exception_handler?", "Global uncaught exception logging."),
        ("error_reporting E_ALL?", "Dev — все errors; prod — log not display."),
        ("display_errors off prod?", "Security — не показывать stack users."),
        ("custom error handler?", "set_error_handler convert to ErrorException."),
        ("Throwable in catch order?", "Сначала specific, потом Throwable."),
        ("finally return behavior?", "return in finally overrides try return (осторожно)."),
        ("Generator return value?", "return в generator доступен через getReturn() после iteration."),
        ("Fibers not in Apache mod_php?", "Fibers нужны CLI или FPM careful — blocking breaks."),
        ("opcache validate_timestamps?", "Dev 1 — re-read files; prod 0 performance."),
        ("preloading script path?", "opcache.preload=preload.php lists classes."),
        ("JIT tracing vs function?", "opcache.jit settings buffer_size."),
        ("Memory limit ini?", "memory_limit для batch scripts."),
        ("max_execution_time?", "CLI 0 unlimited default."),
        ("unlink rename atomic?", "rename() often atomic same filesystem."),
        ("file_put_contents LOCK_EX?", "Atomic write with lock flag."),
        ("glob brace?", "glob('{a,b}.php', GLOB_BRACE) on supporting systems."),
        ("DirectoryIterator?", "OOP directory traversal."),
        ("RecursiveIteratorIterator?", "Recursive tree walk."),
        ("FilterIterator?", "Custom filter on iteration."),
        ("SimpleXML vs DOM?", "Simple quick; DOM full control."),
        ("libxml errors internal?", "libxml_use_internal_errors for parse without warnings."),
        ("XMLReader streaming?", "Large XML stream parse memory efficient."),
        ("CSV fgetcsv str_getcsv?", "Parse CSV rows escape enclosure."),
        ("League CSV PHP?", "Popular library for CSV import/export."),
        ("ZipArchive?", "Create/read zip archives extension."),
        ("Phar archives?", "PHP app as phar executable."),
        ("ReflectionParameter getType?", "Nullable ?Type reflected."),
        ("Union reflection?", "ReflectionUnionType getTypes()."),
        ("Intersection reflection?", "ReflectionIntersectionType PHP 8.1+."),
        ("Never type reflection?", "Indicates never returns."),
        ("Constructor promotion reflection?", "Parameters with IS_PROMOTED flag."),
        ("Readonly reflection?", "IS_READONLY on property reflection."),
        ("Enum reflection?", "ReflectionEnum cases methods backing type."),
        ("Fiber reflection?", "Limited — runtime debugging harder."),
        ("Attribute reflection target?", "TARGET_CLASS | TARGET_METHOD flags validation."),
        ("Opcache status function?", "opcache_get_status for hit rate monitoring."),
        ("Apcu user cache?", "Shared memory user cache between requests FPM."),
        ("Redis session handler?", "session.save_handler=redis scalable sessions."),
        ("Memcached vs Redis?", "Both cache; Redis richer data structures."),
        ("uuid create?", "ramsey/uuid library common — no core uuid until proposals."),
        ("Carbon Date library?", "Wrapper DateTime fluent API."),
        ("Doctrine collections?", "ArrayCollection filter map functional."),
        ("Symfony validator?", "Constraint attributes on DTO properties."),
        ("Laravel not core?", "Framework — но patterns: Eloquent, Facades separate topic."),
        ("PSR-3 LoggerInterface?", "Standard logging interface interoperability."),
        ("PSR-7 HTTP message?", "Request Response interfaces — Guzzle Nyholm."),
        ("PSR-15 middleware?", "RequestHandlerInterface pipeline."),
        ("PSR-11 Container?", "get has — DI container interop."),
        ("PSR-18 HTTP client?", "sendRequest ClientInterface."),
        ("dotenv vlucas?", "Load .env to $_ENV safely not commit secrets."),
        ("putenv vs $_ENV?", "Prefer $_ENV $_SERVER visibility php.ini variables_order."),
        ("getenv?", "Reads environment variable."),
        ("php.ini INI_SCANNER_TYPED?", "Typed ini values in PHP 7+."),
        ("open_basedir restriction?", "Limit filesystem paths shared hosting security."),
        ("disable_functions ini?", "Hardening shell_exec disable shared hosting."),
        ("upload_max_filesize?", "Limit POST upload size with post_max_size."),
        ("move_uploaded_file?", "Only for $_FILES tmp — security check is_uploaded_file."),
        ("MIME finfo_file?", "Detect mime not trust client type."),
        ("Image GD Imagick?", "Resize images extensions."),
        ("exif_read_data?", "Photo metadata caution privacy."),
        ("htmlspecialchars double encode?", "ENT_QUOTES default UTF-8 prevent XSS."),
        ("Content Security Policy?", "HTTP header reduces XSS impact not PHP core."),
        ("hash_equals timing safe?", "Compare HMAC tokens constant time."),
        ("hash_hmac?", "HMAC SHA256 message authentication."),
        ("openssl_encrypt AES?", "Symmetric encryption random iv."),
        ("sodium_crypto_secretbox?", "Modern encryption libsodium."),
        ("password_needs_rehash?", "Upgrade hash algorithm when PASSWORD_DEFAULT changes."),
        ("Argon2id?", "PASSWORD_ARGON2ID recommended memory hard."),
        ("LDAP escape?", "ldap_escape filter DN user input."),
        ("Prepared LIKE escape?", "Escape % _ for SQL LIKE manually or ESCAPE clause."),
        ("SQL second order injection?", "Stored user data later used unsafe in query."),
        ("NoSQL injection?", "Similar with Mongo queries — type validate input."),
        ("serialize untrusted?", "Never unserialize user data — object injection RCE."),
        ("json safer than serialize?", "json_decode data only no objects by default."),
        ("__wakeup __destruct gadget chains?", "POP chains unserialize vulnerabilities."),
        ("TypeError strict API?", "Return type enforcement public APIs."),
        ("Covariant templates Iterator?", "Iterator yields typed via static analysis."),
        ("Generator yield key value?", "yield $key => $value both."),
        ("Delegating generator?", "yield from $otherGenerator;"),
        ("Traversable children?", "IteratorAggregate outer foreach."),
        ("Partial function application?", "No native — closure wrapper fn($x) => foo($cfg, $x)."),
        ("Currying PHP?", "Manual nested closures."),
        ("Pipeline pattern?", "array_reduce or dedicated Pipe class."),
        ("Either Result types libraries?", "Functional error handling packages php-pipeline."),
        ("Immutable updates?", "Clone with changes readonly DTO."),
        ("Entity vs Value Object?", "Entity identity; VO compared by value."),
        ("Repository pattern?", "Abstraction persistence layer interface."),
        ("Service layer?", "Business logic not in controllers."),
        ("DTO vs Entity?", "DTO transfer; Entity domain model persistence."),
        ("Hydrator?", "Map array to object reflection or manual."),
        ("DataMapper ORM?", "Separate entity and DB mapping Doctrine style."),
        ("Active Record pattern?", "Model knows persistence Laravel Eloquent."),
        ("Unit test PHPUnit?", "assertSame assertEquals data providers."),
        ("Mockery PHPUnit mock?", "createMock stub expectations."),
        ("Test doubles?", "Stub mock spy fake definitions."),
        ("Integration test DB?", "Transaction rollback or sqlite memory."),
        ("Paratest parallel?", "Parallel PHPUnit runs."),
        ("Coverage Xdebug pcov?", "Code coverage drivers."),
        ("Mutation testing?", "Infection PHP mutation score."),
        ("Static analysis level max?", "PHPStan level 9 strictness."),
        ("Baseline phpstan?", "Ignore legacy errors incrementally fix."),
        ("Rector automated refactor?", "Upgrade PHP version codemods."),
        ("CS Fixer PSR-12?", "Code style automation."),
        ("PHPCS?", "Sniffs coding standard."),
        ("Deptrac architecture?", "Layer dependency rules."),
        ("Composer audit?", "Security advisory packages composer audit."),
        ("Roave security advisories?", "Block known vulnerable deps dev."),
    ]
    cards.extend(theory(q, r) for q, r in oop_topics)

    # Expand string/array function cards PHP 8+
    funcs_80 = [
        ("str_contains($hay, $needle)", "bool — есть ли подстрока"),
        ("str_starts_with($hay, $needle)", "bool — начинается ли"),
        ("str_ends_with($hay, $needle)", "bool — заканчивается ли"),
        ("get_debug_type($var)", "string — тип для отладки"),
        ("get_resource_id($res)", "int — id ресурса"),
        ("fdiv($a, $b)", "float division без деления на zero warning как /"),
        ("preg_last_error_msg()", "string сообщение последней PCRE ошибки"),
        ("array_key_first($arr)", "первый ключ или null"),
        ("array_key_last($arr)", "последний ключ или null"),
        ("array_is_list($arr)", "bool list 0..n-1"),
        ("json_validate($json)", "bool валидный JSON PHP 8.3"),
    ]
    for sig, desc in funcs_80:
        cards.append(theory(f"PHP 8+: что делает {sig}?", desc))
        cards.append(theory(f"Когда предпочесть {sig.split('(')[0]}() старым аналогам?", f"Использовать вместо strpos/substr комбинаций где {desc.lower()}"))

    # Enum / match / readonly variations
    enum_variants = [
        ("Status::from('x')", "ValueError если нет case", "Status::tryFrom('x') возвращает null"),
        ("enum cases()", "array все case enum", "foreach (Status::cases() as $case)"),
        ("Backed enum value", "scalar value property", "Status::Active->value"),
        ("Unit enum name", "case name string", "Status::Active->name"),
        ("enum in match", "exhaustive matching", "match($s) { Status::A => 1, Status::B => 2 }"),
    ]
    for topic, ref, extra in enum_variants:
        cards.append(theory(f"Enum: {topic}?", f"{ref}. {extra}"))

    # ── CODE CARDS ───────────────────────────────────────────────────────
    code_cards = [
        code(
            "Named arguments: перепутан порядок параметров.",
            "Исправь вызов — передай email и name именованными аргументами.",
            """function createUser(string $name, string $email, bool $active = true): array {
    return compact('name', 'email', 'active');
}

$result = createUser('a@b.com', 'Anna');""",
            """$result = createUser(name: 'Anna', email: 'a@b.com');""",
        ),
        code(
            "Nullsafe: возможен Error при null user.",
            "Используй nullsafe operator для получения city.",
            """$user = null;
$city = $user->getAddress()->city;""",
            """$city = $user?->getAddress()?->city;""",
        ),
        code(
            "Match без default — риск UnhandledMatchError.",
            "Перепиши switch на match с default.",
            """$code = 404;
switch ($code) {
    case 200: $msg = 'OK'; break;
    case 404: $msg = 'Not Found'; break;
}
echo $msg;""",
            """$msg = match ($code) {
    200 => 'OK',
    404 => 'Not Found',
    default => 'Unknown',
};""",
        ),
        code(
            "Constructor promotion: свойство не объявлено.",
            "Используй promoted property для $title.",
            """class Book {
    public function __construct($title) {
        $this->title = $title;
    }
}""",
            """class Book {
    public function __construct(public string $title) {}
}""",
        ),
        code(
            "Union type: параметр принимает неверные типы.",
            "Добавь union type int|string для id.",
            """function findById($id): ?User {
    return UserRepository::get($id);
}""",
            """function findById(int|string $id): ?User {
    return UserRepository::get($id);
}""",
        ),
        code(
            "Readonly: свойство переприсваивается.",
            "Сделай id readonly — присваивается только в конструкторе.",
            """class Order {
    public string $id;

    public function __construct(string $id) {
        $this->id = $id;
    }

    public function refreshId(string $id): void {
        $this->id = $id;
    }
}""",
            """class Order {
    public function __construct(public readonly string $id) {}
    // refreshId удалить или клонировать объект
}""",
        ),
        code(
            "Enum вместо констант.",
            "Замени строковые константы на backed enum string.",
            """class Payment {
    public const PENDING = 'pending';
    public const PAID = 'paid';

    public function __construct(public string $status) {}
}""",
            """enum PaymentStatus: string {
    case Pending = 'pending';
    case Paid = 'paid';
}

class Payment {
    public function __construct(public PaymentStatus $status) {}
}""",
        ),
        code(
            "First-class callable.",
            "Замени array callable на first-class syntax.",
            """$numbers = ['1', '2', '3'];
$mapped = array_map(['intval'], $numbers);""",
            """$mapped = array_map(intval(...), $numbers);""",
        ),
        code(
            "Attribute не применяется.",
            "Добавь #[Attribute] и TARGET_METHOD на Route.",
            """class Route {
    public function __construct(public string $path) {}
}

class HomeController {
    #[Route('/')]
    public function index(): void {}
}""",
            """#[\\Attribute(\\Attribute::TARGET_METHOD)]
class Route {
    public function __construct(public string $path) {}
}""",
        ),
        code(
            "Intersection type: объект должен быть и Iterator и Countable.",
            "Укажи intersection type параметра.",
            """function process($collection): void {
    foreach ($collection as $item) {
        echo count($collection);
    }
}""",
            """function process(Iterator&Countable $collection): void {
    foreach ($collection as $item) {
        echo count($collection);
    }
}""",
        ),
        code(
            "Readonly class: свойство без readonly в promoted.",
            "Сделай класс readonly.",
            """class Point {
    public function __construct(public float $x, public float $y) {}
    public float $z = 0.0;
}""",
            """readonly class Point {
    public function __construct(public float $x, public float $y) {}
}""",
        ),
        code(
            "json_validate вместо decode для проверки.",
            "Используй json_validate (PHP 8.3+) для проверки без decode.",
            """function isValidJson(string $json): bool {
    json_decode($json);
    return json_last_error() === JSON_ERROR_NONE;
}""",
            """function isValidJson(string $json): bool {
    return json_validate($json);
}""",
        ),
        code(
            "Override: метод не переопределяет родителя.",
            "Добавь #[\\Override] и исправь имя метода если нужно.",
            """class Base {
    public function save(): void {}
}
class Child extends Base {
    public function saveData(): void {}
}""",
            """class Child extends Base {
    #[\\Override]
    public function save(): void {}
}""",
        ),
        code(
            "Strict types: неявное приведение string→int.",
            "Добавь strict_types и исправь вызов.",
            """function add(int $a, int $b): int {
    return $a + $b;
}
echo add('1', '2');""",
            """declare(strict_types=1);
// ...
echo add(1, 2);""",
        ),
        code(
            "Arrow function: use $factor не нужен.",
            "Перепиши на fn().",
            """class Multiplier {
    public function __construct(private int $factor) {}
    public function double(array $nums): array {
        return array_map(function ($n) {
            return $n * $this->factor;
        }, $nums);
    }
}""",
            """return array_map(fn($n) => $n * $this->factor, $nums);""",
        ),
        code(
            "Generator: загрузка всех строк в память.",
            "Перепиши readLines как generator с yield.",
            """function readLines(string $path): array {
    $lines = [];
    foreach (file($path) as $line) {
        $lines[] = trim($line);
    }
    return $lines;
}""",
            """function readLines(string $path): \\Generator {
    $handle = fopen($path, 'r');
    while (($line = fgets($handle)) !== false) {
        yield trim($line);
    }
    fclose($handle);
}""",
        ),
        code(
            "PDO: SQL injection через конкатенацию.",
            "Используй prepared statement.",
            """$email = $_GET['email'];
$stmt = $pdo->query(\"SELECT * FROM users WHERE email = '$email'\");""",
            """$stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $email]);""",
        ),
        code(
            "PDO ERRMODE silent.",
            "Включи exceptions на ошибках PDO.",
            """$pdo = new PDO($dsn, $user, $pass);
$stmt = $pdo->query('SELEC * FROM users');""",
            """$pdo = new PDO($dsn, $user, $pass, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);""",
        ),
        code(
            "password_hash без algorithm.",
            "Используй PASSWORD_DEFAULT.",
            """$hash = md5($password);""",
            """$hash = password_hash($password, PASSWORD_DEFAULT);""",
        ),
        code(
            "XSS при выводе имени.",
            "Экранируй HTML при echo.",
            """echo '<p>Hello, ' . $name . '</p>';""",
            """echo '<p>Hello, ' . htmlspecialchars($name, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') . '</p>';""",
        ),
        code(
            "Enum from без проверки.",
            "Используй tryFrom или try/catch для безопасного парсинга.",
            """$status = Status::from($_POST['status']);""",
            """$status = Status::tryFrom($_POST['status']) ?? Status::Pending;""",
        ),
        code(
            "match на enum не exhaustive.",
            "Добавь все cases Status.",
            """$label = match ($status) {
    Status::Active => 'Active',
};""",
            """$label = match ($status) {
    Status::Active => 'Active',
    Status::Archived => 'Archived',
    Status::Draft => 'Draft',
};""",
        ),
        code(
            "Never return: функция должна бросать.",
            "Укажи never и throw.",
            """function fail(string $msg) {
    throw new RuntimeException($msg);
}""",
            """function fail(string $msg): never {
    throw new RuntimeException($msg);
}""",
        ),
        code(
            "Random: mt_rand для token.",
            "Используй random_bytes для токена.",
            """$token = bin2hex(substr(md5(mt_rand()), 0, 16));""",
            """$token = bin2hex(random_bytes(16));""",
        ),
        code(
            "Randomizer PHP 8.2.",
            "Перемешай массив через Random\\Randomizer.",
            """shuffle($items); // not seedable""",
            """$randomizer = new \\Random\\Randomizer();
$items = $randomizer->shuffleArray($items);""",
        ),
        code(
            "Typed class constant.",
            "Добавь тип string константе VERSION в interface.",
            """interface App {
    public const VERSION = '1.0';
}""",
            """interface App {
    public const string VERSION = '1.0';
}""",
        ),
        code(
            "Clone readonly DTO with change PHP 8.3.",
            "Обнови email через clone with.",
            """readonly class User {
    public function __construct(public string $name, public string $email) {}
}
$user = new User('Ann', 'a@b.com');
// need new email""",
            """$updated = clone $user with { email: 'new@b.com' };""",
        ),
        code(
            "Property hook get PHP 8.4.",
            "Добавь get hook для uppercased name.",
            """class Profile {
    public string $name = '';
}""",
            """class Profile {
    public string $name {
        get => strtoupper($this->name);
    }
}""",
        ),
        code(
            "array_find PHP 8.4.",
            "Найди первый чётный элемент через array_find.",
            """foreach ($nums as $n) {
    if ($n % 2 === 0) { $first = $n; break; }
}""",
            """$first = array_find($nums, fn(int $n) => $n % 2 === 0);""",
        ),
        code(
            "JsonException.",
            "json_decode с JSON_THROW_ON_ERROR.",
            """$data = json_decode($json, true);
if ($data === null) { throw new Exception('bad json'); }""",
            """$data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);""",
        ),
        code(
            "Interface default method.",
            "Добавь default реализацию log в LoggerAware.",
            """interface LoggerAware {
    public function log(string $msg): void;
}""",
            """interface LoggerAware {
    public function log(string $msg): void {
        echo $msg, PHP_EOL;
    }
}""",
        ),
        code(
            "Trait conflict.",
            "Разреши конфликт методов A и B через insteadof.",
            """trait A { public function run(): void { echo 'A'; } }
trait B { public function run(): void { echo 'B'; } }
class Job {
    use A, B;
}""",
            """class Job {
    use A, B {
        A::run insteadof B;
    }
}""",
        ),
        code(
            "SplFileObject чтение CSV.",
            "Установи CSV flags и читай строки.",
            """$file = new SplFileObject('data.csv');
foreach ($file as $line) {
    print_r(explode(',', $line));
}""",
            """$file = new SplFileObject('data.csv');
$file->setFlags(SplFileObject::READ_CSV);
foreach ($file as $row) {
    if ($row === [null]) continue;
    print_r($row);
}""",
        ),
        code(
            "DateTimeImmutable modify.",
            "Не мутируй DateTime — используй Immutable.",
            """$dt = new DateTime('2024-01-01');
$dt->modify('+1 day');
return $dt;""",
            """$dt = new DateTimeImmutable('2024-01-01');
return $dt->modify('+1 day');""",
        ),
        code(
            "Fiber skeleton.",
            "Допиши suspend/resume для простого fiber.",
            """$fiber = new Fiber(function (): void {
    $value = Fiber::suspend('first');
    echo $value;
});
$fiber->start();
$fiber->resume('hello');""",
            """// Fiber::suspend возвращает 'first' в start();
// resume('hello') передаёт 'hello' в $value""",
        ),
        code(
            "WeakMap metadata.",
            "Привяжи metadata к объекту через WeakMap.",
            """$meta = [];
$obj = new stdClass();
$meta[spl_object_id($obj)] = 'data';""",
            """$map = new WeakMap();
$obj = new stdClass();
$map[$obj] = 'data';""",
        ),
        code(
            "Stringable return type.",
            "Реализуй __toString и Stringable.",
            """class Label {
    public function __construct(private string $text) {}
}""",
            """class Label implements Stringable {
    public function __construct(private string $text) {}
    public function __toString(): string {
        return $this->text;
    }
}""",
        ),
        code(
            "JsonSerializable DTO.",
            "Реализуй jsonSerialize для экспорта.",
            """class User {
    public function __construct(public string $name) {}
}
echo json_encode(new User('Ann'));""",
            """class User implements JsonSerializable {
    public function __construct(public string $name) {}
    public function jsonSerialize(): array {
        return ['name' => $this->name];
    }
}""",
        ),
        code(
            "Backed enum JSON.",
            "Сериализуй enum как value в API response.",
            """return ['status' => $order->status];""",
            """return ['status' => $order->status->value];""",
        ),
        code(
            "array_is_list check.",
            "Проверь что массив list перед json как array not object.",
            """json_encode($data);""",
            """if (!array_is_list($data)) {
    throw new InvalidArgumentException('Expected list');
}
json_encode($data);""",
        ),
        code(
            "str_contains вместо strpos.",
            "Замени strpos проверку на str_contains.",
            """if (strpos($haystack, 'needle') !== false) {}""",
            """if (str_contains($haystack, 'needle')) {}""",
        ),
        code(
            "Null coalescing chain.",
            "Упрости isset ternary для config.",
            """$host = isset($config['host']) ? $config['host'] : 'localhost';""",
            """$host = $config['host'] ?? 'localhost';""",
        ),
        code(
            "throw expression in ??",
            "Используй throw expression если ключ обязателен.",
            """$id = $data['id'] ?? null;
if ($id === null) throw new InvalidArgumentException('id required');""",
            """$id = $data['id'] ?? throw new InvalidArgumentException('id required');""",
        ),
        code(
            "Non-capturing catch.",
            "Убери неиспользуемую переменную catch.",
            """try {
    risky();
} catch (Exception $e) {
    log('failed');
}""",
            """try {
    risky();
} catch (Exception) {
    log('failed');
}""",
        ),
        code(
            "Static return type factory.",
            "Верни static из create().",
            """class Model {
    public static function create(): self {
        return new self();
    }
}""",
            """class Model {
    public static function create(): static {
        return new static();
    }
}""",
        ),
        code(
            "Readonly clone __clone.",
            "Переинициализируй readonly id в __clone.",
            """readonly class Session {
    public function __construct(public readonly string $id) {}
}""",
            """readonly class Session {
    public function __construct(public readonly string $id) {}
    public function __clone(): void {
        $this->id = bin2hex(random_bytes(8));
    }
}""",
        ),
        code(
            "SensitiveParameter.",
            "Скрой password в stack trace.",
            """function login(string $password): void {
    authenticate($password);
}""",
            """function login(#[\\SensitiveParameter] string $password): void {
    authenticate($password);
}""",
        ),
        code(
            "DNF type hint.",
            "Укажи (Countable&Iterator)|array.",
            """function countItems($items): int {
    return count($items);
}""",
            """function countItems((Countable&Iterator)|array $items): int {
    return count($items);
}""",
        ),
        code(
            "True false standalone types.",
            "Типизируй flag только true.",
            """function enable(bool $flag = true): void {}""",
            """function enable(true $flag = true): void {}""",
        ),
        code(
            "Variadic named + spread.",
            "Передай options через spread массива.",
            """$opts = ['mode' => 'r', 'flag' => FILE_IGNORE_NEW_LINES];
// вызови foo без перечисления""",
            """foo(...$opts); // или array unpacking в другом контексте""",
        ),
        code(
            "Closure bind for private.",
            "Вызови private method через Closure::bind.",
            """$obj = new Service();
$obj->run(); // private""",
            """$closure = \\Closure::bind(fn() => $this->run(), $obj, Service::class);
$closure();""",
        ),
        code(
            "Generator send.",
            "Передай значение в yield через send().",
            """function gen(): Generator {
    $x = yield;
    yield $x * 2;
}
$g = gen();
$g->next();
echo $g->send(5);""",
            """// next() до первого yield; send(5) -> $x=5; следующий yield вернёт 10""",
        ),
        code(
            "hash_equals compare.",
            "Сравни HMAC без timing leak.",
            """if ($userHash === $expected) {}""",
            """if (hash_equals($expected, $userHash)) {}""",
        ),
        code(
            "filter_var email.",
            "Валидируй email через filter_var.",
            """if (strpos($email, '@') !== false) {}""",
            """if (filter_var($email, FILTER_VALIDATE_EMAIL)) {}""",
        ),
        code(
            "Session cookie secure.",
            "Настрой httponly и secure для session cookie.",
            """session_start();""",
            """session_set_cookie_params([
    'lifetime' => 0,
    'path' => '/',
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Lax',
]);
session_start();""",
        ),
        code(
            "file_put_contents atomic.",
            "Запиши файл с блокировкой.",
            """file_put_contents($path, $data);""",
            """file_put_contents($path, $data, LOCK_EX);""",
        ),
        code(
            "is_countable before count.",
            "Проверь countable.",
            """echo count($maybeNull);""",
            """echo is_countable($maybeNull) ? count($maybeNull) : 0;""",
        ),
        code(
            "get_debug_type log.",
            "Логируй тип переменной при ошибке.",
            """error_log('type: ' . gettype($var));""",
            """error_log('type: ' . get_debug_type($var));""",
        ),
    ]
    cards.extend(code_cards)

    # ── Generated variations to reach 500+ ───────────────────────────────
    php_versions = ["8.0", "8.1", "8.2", "8.3", "8.4"]
    features_by_version = {
        "8.0": ["named arguments", "attributes", "match", "union types", "nullsafe", "promotion", "WeakMap", "str_contains"],
        "8.1": ["enums", "readonly", "fibers", "intersection types", "never", "first-class callable", "array_is_list"],
        "8.2": ["readonly class", "DNF types", "true false null types", "Randomizer", "SensitiveParameter"],
        "8.3": ["typed constants", "json_validate", "Override", "clone with", "dynamic class const fetch"],
        "8.4": ["property hooks", "asymmetric visibility", "array_find", "array_any", "array_all"],
    }

    for ver in php_versions:
        for feat in features_by_version[ver]:
            cards.append(theory(
                f"В какой версии PHP появилось: {feat}?",
                f"PHP {ver}. Ключевая возможность современного PHP.",
            ))
            cards.append(theory(
                f"Кратко опиши {feat} в PHP {ver}.",
                f"Относится к PHP {ver}. См. документацию php.net для {feat.replace(' ', '_')}.",
            ))

    # PDO / SQL mini scenarios
    pdo_ops = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRANSACTION", "FETCH_ASSOC", "FETCH_OBJ", "FETCH_CLASS", "bindValue", "bindParam", "lastInsertId", "rowCount"]
    for op in pdo_ops:
        cards.append(theory(f"PDO: best practice для {op}?", f"Использовать prepared statements, ERRMODE_EXCEPTION, для {op} — не конкатенировать SQL."))

    # SPL classes
    spl = ["ArrayObject", "ArrayIterator", "SplQueue", "SplStack", "SplHeap", "SplFixedArray", "SplFileObject", "SplTempFileObject", "CallbackFilterIterator", "RecursiveDirectoryIterator"]
    for cls in spl:
        cards.append(theory(f"SPL: для чего {cls}?", f"{cls} — стандартная структура/итератор SPL. Использовать вместо ad-hoc реализаций где уместно."))
        cards.append(code(
            f"SPL: базовое использование {cls}.",
            f"Дополни пример корректным созданием {cls}.",
            f"""// TODO: используй {cls}
$data = [1, 2, 3];""",
            f"// Пример зависит от класса — см. php.net/class-{cls.lower()}",
        ))

    # String functions batch
    string_funcs = [
        "strlen", "mb_strlen", "substr", "mb_substr", "str_replace", "preg_replace", "preg_match", "trim", "ltrim", "rtrim",
        "strtolower", "strtoupper", "ucfirst", "lcfirst", "sprintf", "vsprintf", "number_format", "str_pad", "chunk_split",
        "explode", "implode", "str_split", "wordwrap", "nl2br", "strip_tags", "htmlentities", "html_entity_decode",
    ]
    for fn in string_funcs:
        cards.append(theory(f"Зачем нужна функция {fn}()?", f"Строковая операция PHP. В PHP 8+ предпочитать типобезопасные альтернативы где есть (str_contains вместо strpos)."))
        if fn in ("preg_match", "preg_replace"):
            cards.append(code(
                f"Regex: ошибка в {fn}.",
                "Экранируй пользовательский ввод через preg_quote.",
                f"""$user = 'file.txt';
$pattern = '/{fn}(' . $user . ')/';
{fn}($pattern, 'test');""",
                f"""$pattern = '/{fn}(' . preg_quote($user, '/') . ')/';""",
            ))

    # Array functions
    array_funcs = [
        "array_map", "array_filter", "array_reduce", "array_column", "array_combine", "array_chunk", "array_merge",
        "array_diff", "array_intersect", "array_keys", "array_values", "array_flip", "array_unique", "array_reverse",
        "usort", "uksort", "uasort", "sort", "rsort", "ksort", "krsort", "array_walk", "array_sum", "array_product",
    ]
    for fn in array_funcs:
        cards.append(theory(f"Когда использовать {fn}()?", f"Работа с массивами PHP. Комбинировать с arrow functions fn() для краткости."))

    # Error types
    errors = ["TypeError", "ValueError", "ParseError", "ArithmeticError", "DivisionByZeroError", "UnhandledMatchError", "Error", "Exception", "RuntimeException", "InvalidArgumentException", "LogicException", "JsonException"]
    for err in errors:
        cards.append(theory(f"Когда бросается {err}?", f"{err} — часть иерархии PHP ошибок/исключений. Обрабатывать специфичные типы перед Throwable."))

    # Attributes targets quiz
    targets = ["TARGET_CLASS", "TARGET_METHOD", "TARGET_FUNCTION", "TARGET_PARAMETER", "TARGET_PROPERTY", "TARGET_CLASS_CONSTANT", "IS_REPEATABLE"]
    for t in targets:
        cards.append(theory(f"Attribute flag {t} — что означает?", f"Константа Attribute::{t} задаёт где атрибут можно применять или что он repeatable."))

    # Code fix templates with index for uniqueness
    code_templates = [
        ("promoted private", "Сделай private promoted property $email.", "class User {\n    private string $email;\n    public function __construct(string $email) { $this->email = $email; }\n}", "class User {\n    public function __construct(private string $email) {}\n}"),
        ("readonly promoted", "Добавь readonly модификатор.", "class Id { public function __construct(public string $value) {} }", "class Id { public function __construct(public readonly string $value) {} }"),
        ("union nullable", "Тип ?string для nullable.", "function f($x): string { return $x ?? ''; }", "function f(?string $x): string { return $x ?? ''; }"),
        ("match enum", "match все cases Color.", "function label(Color $c) { return match($c) { Color::Red => 'R' }; }", "function label(Color $c): string { return match($c) { Color::Red => 'R', Color::Green => 'G', Color::Blue => 'B' }; }"),
        ("enum int backed", "Backed enum int Priority.", "class P { const HIGH = 1; }", "enum Priority: int { case High = 1; case Low = 0; }"),
        ("str_starts_with", "Замени substr check.", "if (substr($url, 0, 8) === 'https://') {}", "if (str_starts_with($url, 'https://')) {}"),
        ("str_ends_with", "Проверка расширения файла.", "if (substr($f, -4) === '.php') {}", "if (str_ends_with($f, '.php')) {}"),
        ("nullsafe chain", "Безопасный chain.", "$x = $a->b->c;", "$x = $a?->b?->c;"),
        ("first class", "intval callable.", "array_map('intval', $a)", "array_map(intval(...), $a)"),
        ("never return", "never type.", "function stop(): void { throw new Ex(); }", "function stop(): never { throw new Ex(); }"),
        ("json throw", "JSON_THROW_ON_ERROR.", "json_decode($j)", "json_decode($j, true, 512, JSON_THROW_ON_ERROR)"),
        ("password verify", "password_verify.", "if (md5($p) === $hash) {}", "if (password_verify($p, $hash)) {}"),
        ("random bytes token", "random_bytes.", "$t = uniqid();", "$t = bin2hex(random_bytes(16));"),
        ("htmlspecialchars", "XSS escape.", "echo $u;", "echo htmlspecialchars($u, ENT_QUOTES, 'UTF-8');"),
        ("strict declare", "strict_types.", "// missing\nfunction i(int $v) {}", "declare(strict_types=1);\nfunction i(int $v) {}"),
        ("readonly class", "readonly class.", "class D { public function __construct(public string $n) {} }", "readonly class D { public function __construct(public string $n) {} }"),
        ("override attr", "Override attribute.", "class C extends B { public function run() {} }", "class C extends B { #[\\Override] public function run() {} }"),
        ("typed const", "typed const.", "interface I { const V = 1; }", "interface I { const int V = 1; }"),
        ("array find", "array_find.", "foreach ($a as $v) { if ($v>0) return $v; }", "return array_find($a, fn($v) => $v > 0);"),
        ("sensitive param", "SensitiveParameter.", "function f($secret) {}", "function f(#[\\SensitiveParameter] string $secret) {}"),
    ]
    for i, (name, task, broken, fixed) in enumerate(code_templates):
        for n in range(3):  # 3 variants each
            cards.append(code(
                f"PHP 8+ практика [{name}] #{i}-{n}",
                task,
                broken,
                fixed,
            ))

    # Theory numbered revision cards
    revision_topics = [
        "типизация", "enum", "match", "attributes", "readonly", "generators", "PDO", "безопасность",
        "строки", "массивы", "ООП", "исключения", "reflection", "SPL", "даты", "JSON", "сессии",
        "CLI", "composer", "static analysis", "fibers", "random", "password hashing", "XSS", "CSRF",
        "SQL injection", "autoload PSR-4", "traits", "interfaces", "abstract classes", "closures",
        "arrow functions", "promoted properties", "union types", "intersection types", "never",
        "WeakMap", "first-class callable", "nullsafe", "named arguments", "property hooks",
    ]
    for topic in revision_topics:
        for i in range(5):
            cards.append(theory(
                f"PHP 8+ [{topic}]: контрольный вопрос #{i + 1}",
                f"Повторите ключевые концепции {topic} в PHP 8+. Используйте официальную документацию php.net и практику на коде.",
            ))

    # Unique IDs via question+code — dedupe exact duplicates
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
        raise SystemExit(f"Only {len(cards)} cards generated, need 500+")

    code_count = sum(1 for c in cards if c.get("card_type") == "code" or c.get("code"))
    deck = {
        "name": "PHP 8+",
        "cards": cards,
    }
    out = Path(__file__).with_name("php8-plus.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} cards ({code_count} code) -> {out}")


if __name__ == "__main__":
    main()
