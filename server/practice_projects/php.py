from server.practice_projects import project, text

PROJECTS = [
    project("php-cart", "Корзина интернет-магазина", "php", [1, 2, 3],
            "Практика PHP 8: строгие типы, классы, исключения и деньги в целых копейках.", "php", {
                "src/Cart.php": text('''
                    <?php
                    declare(strict_types=1);

                    final class Cart {
                        private array $items = [];

                        public function add(string $name, int $price, int $quantity): void {
                            // TODO(human): проверить имя, цену >= 0 и количество > 0.
                            throw new LogicException('Добавление товара');
                        }

                        public function total(): int {
                            // TODO(human): сумма price * quantity, в копейках.
                            throw new LogicException('Расчёт суммы');
                        }

                        public function receipt(): array {
                            // TODO(human): ['items' => список, 'total' => сумма].
                            throw new LogicException('Чек');
                        }
                    }
                '''),
                "main.php": text('''
                    <?php
                    declare(strict_types=1);
                    require __DIR__ . '/src/Cart.php';
                    $cart = new Cart();
                    $cart->add('Книга', 120000, 2);
                    $cart->add('Карандаш', 5000, 3);
                    echo json_encode($cart->receipt(), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), PHP_EOL;
                '''),
            }, [
                ("Описать товар", "В Cart::add проверьте название, цену и количество; неверный ввод — InvalidArgumentException. Храните name, price, quantity; имя обрезайте trim."),
                ("Посчитать сумму", "Реализуйте total(). Используйте целые копейки: товар 19900 × 2 и 5000 × 1 дают 44800. Пустая корзина — 0."),
                ("Сформировать чек", "В receipt верните массив items и total. Проверьте, что изменение полученного массива не меняет содержимое корзины."),
            ], '''
                <?php
                declare(strict_types=1);
                require getcwd() . '/src/Cart.php';
                function check(bool $ok, string $why): void { if (!$ok) throw new RuntimeException($why); }
                $stage = (int)$argv[1];
                $cart = new Cart();
                foreach ([['', 10, 1], ['x', -1, 1], ['x', 1, 0]] as $row) {
                    try { $cart->add(...$row); throw new RuntimeException('Ожидается InvalidArgumentException'); }
                    catch (InvalidArgumentException $e) {}
                }
                $cart->add('  Book  ', 19900, 2);
                $cart->add('Pen', 5000, 1);
                if ($stage >= 1) {
                    check($cart->total() === 44800, 'Неверная сумма');
                    check((new Cart())->total() === 0, 'Пустая корзина');
                }
                if ($stage >= 2) {
                    $receipt = $cart->receipt();
                    check($receipt['total'] === 44800 && $receipt['items'][0]['name'] === 'Book', 'Неверный чек');
                    $receipt['items'][0]['price'] = 0;
                    check($cart->total() === 44800, 'Корзина изменена извне');
                }
                echo "AI_ANKI_CHECK_OK:$stage\n";
            ''', {"src/Cart.php": text('''
                <?php
                declare(strict_types=1);
                final class Cart {
                    private array $items = [];
                    public function add(string $name, int $price, int $quantity): void {
                        $name = trim($name);
                        if ($name === '' || $price < 0 || $quantity < 1) throw new InvalidArgumentException('Неверный товар');
                        $this->items[] = compact('name', 'price', 'quantity');
                    }
                    public function total(): int {
                        return array_sum(array_map(fn($item) => $item['price'] * $item['quantity'], $this->items));
                    }
                    public function receipt(): array { return ['items' => $this->items, 'total' => $this->total()]; }
                }
            ''')}),
    project("php-expenses", "Учёт расходов на PDO", "php", [4, 8],
            "Создайте SQLite-хранилище расходов с подготовленными выражениями и отчётом по категориям.", "php", {
                "src/Expenses.php": text('''
                    <?php
                    declare(strict_types=1);
                    final class Expenses {
                        public function __construct(private PDO $db) {
                            $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                            $db->exec('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, category TEXT NOT NULL, amount INTEGER NOT NULL)');
                        }
                        public function add(string $category, int $amount): int {
                            // TODO(human): trim, валидация, prepare/execute, вернуть id.
                            throw new LogicException('Добавление расхода');
                        }
                        public function totals(): array {
                            // TODO(human): category -> SUM(amount), ORDER BY category.
                            throw new LogicException('Группировка');
                        }
                    }
                '''),
                "main.php": text('''
                    <?php
                    declare(strict_types=1);
                    require __DIR__ . '/src/Expenses.php';
                    if (!is_dir('artifacts')) mkdir('artifacts');
                    $expenses = new Expenses(new PDO('sqlite:artifacts/expenses.sqlite'));
                    $expenses->add('Еда', 45000);
                    $expenses->add('Транспорт', 6500);
                    $report = json_encode($expenses->totals(), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
                    file_put_contents('artifacts/report.json', $report);
                    echo $report, PHP_EOL;
                '''),
            }, [
                ("Записать расход", "Реализуйте add: непустая категория и положительная сумма в копейках. Ошибки ввода — InvalidArgumentException. Только подготовленный INSERT; верните целочисленный id."),
                ("Собрать отчёт", "Реализуйте totals одним SELECT с GROUP BY. Верните ассоциативный массив category => целочисленная сумма."),
                ("Проверить сохранность", "Убедитесь, что кавычки в категории не меняют SQL, а данные доступны после открытия нового PDO к тому же файлу. Запустите и скачайте отчёт."),
            ], '''
                <?php
                declare(strict_types=1);
                require getcwd() . '/src/Expenses.php';
                function check(bool $ok, string $why): void { if (!$ok) throw new RuntimeException($why); }
                $stage = (int)$argv[1];
                $path = tempnam(sys_get_temp_dir(), 'expenses');
                try {
                    $db = new PDO('sqlite:' . $path);
                    $service = new Expenses($db);
                    try { $service->add('', 10); throw new RuntimeException('Пустая категория принята'); }
                    catch (InvalidArgumentException $e) {}
                    check($service->add(' Food ', 100) > 0, 'Ожидается id');
                    $service->add('Food', 250);
                    if ($stage >= 1) check($service->totals() === ['Food' => 350], 'Неверная сумма');
                    if ($stage >= 2) {
                        $category = "x'); DROP TABLE expenses;--";
                        $service->add($category, 10);
                        $other = new Expenses(new PDO('sqlite:' . $path));
                        check($other->totals()[$category] === 10 && $other->totals()['Food'] === 350, 'Нарушена сохранность данных');
                    }
                } finally { @unlink($path); }
                echo "AI_ANKI_CHECK_OK:$stage\n";
            ''', {"src/Expenses.php": text('''
                <?php
                declare(strict_types=1);
                final class Expenses {
                    public function __construct(private PDO $db) {
                        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                        $db->exec('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, category TEXT NOT NULL, amount INTEGER NOT NULL)');
                    }
                    public function add(string $category, int $amount): int {
                        $category = trim($category);
                        if ($category === '' || $amount <= 0) throw new InvalidArgumentException('Неверный расход');
                        $statement = $this->db->prepare('INSERT INTO expenses(category, amount) VALUES (?, ?)');
                        $statement->execute([$category, $amount]);
                        return (int)$this->db->lastInsertId();
                    }
                    public function totals(): array {
                        $result = [];
                        foreach ($this->db->query('SELECT category, SUM(amount) AS total FROM expenses GROUP BY category ORDER BY category') as $row) {
                            $result[$row['category']] = (int)$row['total'];
                        }
                        return $result;
                    }
                }
            ''')}),
    project("php-api", "JSON API каталога", "php", [5, 9],
            "Разделите HTTP-маршрутизацию и логику каталога. Проверьте методы, статусы и JSON-контракт.", "php", {
                "src/api.php": text('''
                    <?php
                    declare(strict_types=1);
                    function dispatch(string $method, string $path, array $body, array &$products): array {
                        // TODO(human): вернуть ['status' => int, 'body' => array].
                        // GET /products, POST /products, 405 для иных методов; неизвестный путь -> 404.
                        return ['status' => 501, 'body' => ['error' => 'Маршрут не реализован']];
                    }
                '''),
                "public/index.php": text('''
                    <?php
                    declare(strict_types=1);
                    require __DIR__ . '/../src/api.php';
                    $products = [];
                    $body = json_decode(file_get_contents('php://input'), true);
                    $response = dispatch($_SERVER['REQUEST_METHOD'], parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), is_array($body) ? $body : [], $products);
                    http_response_code($response['status']);
                    header('Content-Type: application/json; charset=utf-8');
                    echo json_encode($response['body'], JSON_UNESCAPED_UNICODE);
                '''),
                "main.php": text('''
                    <?php
                    declare(strict_types=1);
                    require __DIR__ . '/src/api.php';
                    $products = [];
                    foreach ([['POST', '/products', ['name' => 'Книга', 'price' => 500]], ['GET', '/products', []]] as $request) {
                        echo json_encode(dispatch(...[...$request, &$products]), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), PHP_EOL;
                    }
                '''),
                "README.md": "# Каталог\n\nmain.php проверяет обработчик без сети. public/index.php — HTTP-точка входа.\nЭтот учебный этап хранит товары в массиве; следующий шаг — подключить PDO из проекта расходов.\n",
            }, [
                ("Прочитать каталог", "GET /products должен возвращать status=200 и body со списком товаров. Неизвестный путь — 404, неподдерживаемый метод на /products — 405."),
                ("Проверить запрос", "POST /products принимает непустое строковое name и целочисленный price >= 0. Неверные данные — 422, исходный каталог при ошибке не меняется."),
                ("Создать товар", "При успешном POST добавьте товар с id=max(id)+1, обрезанным name и price. Верните 201 и новый товар. Последующий GET должен видеть результат."),
            ], '''
                <?php
                declare(strict_types=1);
                require getcwd() . '/src/api.php';
                function check(bool $ok, string $why): void { if (!$ok) throw new RuntimeException($why); }
                $stage = (int)$argv[1]; $items = [];
                check(dispatch('GET', '/products', [], $items) === ['status'=>200, 'body'=>[]], 'GET');
                check(dispatch('GET', '/missing', [], $items)['status'] === 404, '404');
                check(dispatch('DELETE', '/products', [], $items)['status'] === 405, '405');
                if ($stage >= 1) {
                    foreach ([[], ['name'=>'', 'price'=>1], ['name'=>'x', 'price'=>'1'], ['name'=>'x', 'price'=>-1]] as $body) {
                        check(dispatch('POST', '/products', $body, $items)['status'] === 422 && $items === [], 'Валидация');
                    }
                }
                if ($stage >= 2) {
                    $response = dispatch('POST', '/products', ['name'=>' Book ', 'price'=>100], $items);
                    check($response === ['status'=>201, 'body'=>['id'=>1, 'name'=>'Book', 'price'=>100]], 'Создание');
                    check(dispatch('GET', '/products', [], $items)['body'] === [$response['body']], 'Чтение после записи');
                }
                echo "AI_ANKI_CHECK_OK:$stage\n";
            ''', {"src/api.php": text('''
                <?php
                declare(strict_types=1);
                function dispatch(string $method, string $path, array $body, array &$products): array {
                    if ($path !== '/products') return ['status'=>404, 'body'=>['error'=>'Not found']];
                    if ($method === 'GET') return ['status'=>200, 'body'=>$products];
                    if ($method !== 'POST') return ['status'=>405, 'body'=>['error'=>'Method not allowed']];
                    if (!isset($body['name'], $body['price']) || !is_string($body['name']) || trim($body['name']) === '' || !is_int($body['price']) || $body['price'] < 0) {
                        return ['status'=>422, 'body'=>['error'=>'Invalid product']];
                    }
                    $item = ['id'=>max(array_merge([0], array_column($products, 'id'))) + 1, 'name'=>trim($body['name']), 'price'=>$body['price']];
                    $products[] = $item;
                    return ['status'=>201, 'body'=>$item];
                }
            ''')}),
    project("php-mvc", "Мини-приложение MVC", "php", [2, 8, 12],
            "Соберите каталог книг: репозиторий, контроллер и HTML-шаблон с безопасным выводом.", "php", {
                "src/catalog.php": text('''
                    <?php
                    declare(strict_types=1);
                    function findBooks(array $books, string $query): array {
                        // TODO(human): фильтр по подстроке без учёта регистра, пустой запрос -> все.
                        throw new LogicException('Поиск');
                    }
                    function renderCatalog(array $books): string {
                        // TODO(human): собрать HTML через templates/catalog.php и output buffering.
                        throw new LogicException('Шаблон');
                    }
                    function catalogPage(array $books, string $query): string {
                        // TODO(human): связать поиск и представление.
                        throw new LogicException('Контроллер');
                    }
                '''),
                "templates/catalog.php": "<!doctype html><html lang=\"ru\"><meta charset=\"utf-8\"><title>Книги</title><style>body{font:18px system-ui;padding:32px}li{padding:8px}</style><h1>Каталог книг</h1><ul><?php foreach ($books as $book): ?><li><?php /* TODO(human): экранированный title */ ?></li><?php endforeach; ?></ul></html>\n",
                "main.php": text('''
                    <?php
                    declare(strict_types=1);
                    require __DIR__ . '/src/catalog.php';
                    $html = catalogPage([['title'=>'PHP Patterns'], ['title'=>'Python Basics']], 'php');
                    if (!is_dir('artifacts')) mkdir('artifacts');
                    file_put_contents('artifacts/preview.html', $html);
                    echo 'HTML-страница сохранена. Откройте предпросмотр.', PHP_EOL;
                '''),
            }, [
                ("Отфильтровать книги", "В findBooks выберите книги, title которых содержит trim(query), без учёта регистра. Для пустого запроса верните все. Сохраните порядок и последовательные индексы."),
                ("Собрать HTML", "В renderCatalog подключите шаблон через output buffering. Выведите заголовки через htmlspecialchars с ENT_QUOTES | ENT_SUBSTITUTE и UTF-8."),
                ("Связать слои", "Реализуйте catalogPage через findBooks и renderCatalog. Проверьте поиск и экранирование, затем откройте HTML-предпросмотр."),
            ], '''
                <?php
                declare(strict_types=1);
                require getcwd() . '/src/catalog.php';
                function check(bool $ok, string $why): void { if (!$ok) throw new RuntimeException($why); }
                $stage = (int)$argv[1];
                $books = [['title'=>'PHP Patterns'], ['title'=>'Python Basics']];
                check(findBooks($books, ' php ') === [$books[0]], 'Поиск');
                check(findBooks($books, '') === $books, 'Пустой запрос');
                if ($stage >= 1) {
                    $html = renderCatalog([['title'=>'<script>alert(1)</script>']]);
                    check(str_contains($html, '&lt;script&gt;') && !str_contains($html, '<script>'), 'Экранирование');
                }
                if ($stage >= 2) {
                    $html = catalogPage($books, 'php');
                    check(str_contains($html, 'PHP Patterns') && !str_contains($html, 'Python Basics'), 'Контроллер');
                }
                echo "AI_ANKI_CHECK_OK:$stage\n";
            ''', {
                "src/catalog.php": text('''
                    <?php
                    declare(strict_types=1);
                    function findBooks(array $books, string $query): array {
                        $query = trim($query);
                        return array_values(array_filter($books, fn($book) => $query === '' || stripos($book['title'], $query) !== false));
                    }
                    function renderCatalog(array $books): string {
                        ob_start();
                        require __DIR__ . '/../templates/catalog.php';
                        return ob_get_clean();
                    }
                    function catalogPage(array $books, string $query): string {
                        return renderCatalog(findBooks($books, $query));
                    }
                '''),
                "templates/catalog.php": "<!doctype html><html lang=\"ru\"><meta charset=\"utf-8\"><title>Книги</title><style>body{font:18px system-ui;padding:32px}li{padding:8px}</style><h1>Каталог книг</h1><ul><?php foreach ($books as $book): ?><li><?= htmlspecialchars($book['title'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') ?></li><?php endforeach; ?></ul></html>\n",
            }, preview=True),
]
