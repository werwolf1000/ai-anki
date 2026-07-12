"""Theory and code card bank for Laravel fundamentals deck."""
from __future__ import annotations

THEORY: dict[str, list[tuple[str, str]]] = {
    "Основы": [
        ("Что такое Laravel?", "PHP-фреймворк для веб-приложений: роутинг, ORM Eloquent, Blade, очереди, тесты. Точка входа public/index.php, ядро — IoC-контейнер."),
        ("Структура каталогов Laravel?", "app/ — код приложения; routes/ — маршруты; resources/views — Blade; database/migrations; config/; bootstrap/; public/ — document root."),
        ("Назначение artisan?", "CLI Laravel: migrate, make:model, queue:work, route:list, tinker, schedule:run. Расширяется custom commands в app/Console/Commands."),
        ("Что делает composer.json scripts post-autoload-dump?", "Запускает @php artisan package:discover и обновляет bootstrap/cache/packages.php — автoregistration пакетов."),
        ("Файл .env и APP_KEY?", ".env — локальные секреты; php artisan key:generate создаёт APP_KEY для шифрования cookies/sessions."),
        ("config() vs env()?", "config() — из config/*.php с кэшем; env() только в config-файлах, не в коде приложения (иначе null после config:cache)."),
        ("bootstrap/app.php (Laravel 11+)?", "Конфигурация приложения: withRouting, withMiddleware, withExceptions — замена части Kernel bootstrap."),
        ("Service providers — роль?", "Регистрация bindings, routes, events в register()/boot(); auto-discovery через composer."),
        ("Публикация конфигов пакетов?", "php artisan vendor:publish --tag=config копирует config в приложение."),
        ("Homestead / Sail?", "Laravel Sail — Docker-окружение для dev; официальные образы PHP, MySQL, Redis, Mailpit."),
        ("Mix / Vite в Laravel?", "Сборка фронтенда: vite.config.js + @vite в Blade; npm run dev / build."),
        ("storage/ и bootstrap/cache/?", "storage/logs, framework/cache, sessions; bootstrap/cache — compiled config/routes (artisan optimize)."),
        ("php artisan about?", "Сводка версий Laravel, PHP, drivers cache/queue/session/database."),
        ("Maintenance mode?", "php artisan down / up; secret bypass token; prerender страница 503."),
        ("Named routes и URL generation?", "Route::name('posts.index'); route('posts.index') и redirect()->route()."),
    ],
    "Роутинг": [
        ("Где объявляются web-маршруты?", "routes/web.php — middleware web (session, CSRF). API — routes/api.php с prefix api и middleware api."),
        ("Route::get vs Route::match?", "HTTP-verb specific; match(['get','post'], ...) или Route::any."),
        ("Route parameters {id}?", "Route::get('/posts/{id}', ...); constraint Route::pattern('id', '[0-9]+')."),
        ("Optional parameters?", "{slug?} с default в closure/controller: function ($slug = null)."),
        ("Route groups?", "Route::prefix('admin')->middleware('auth')->group(function () { ... }); name(), domain(), namespace()."),
        ("Route model binding?", "Type-hint Post $post — Laravel resolve по id; custom binding в RouteServiceProvider/boot."),
        ("Implicit vs explicit binding?", "Implicit — по type-hint; explicit Route::bind('user', fn ($v) => User::where(...)->firstOrFail())."),
        ("Fallback routes?", "Route::fallback(fn () => view('404')) — catch-all в конце."),
        ("Rate limiting routes?", "Route::middleware('throttle:api'); RateLimiter::for in AppServiceProvider."),
        ("Signed URLs?", "URL::temporarySignedRoute('unsubscribe', now()->addDays(7), ['user' => 1]); middleware signed."),
        ("Route caching?", "php artisan route:cache — production; route:clear при изменении маршрутов."),
        ("Subdomain routing?", "Route::domain('{account}.example.com')->group(...)."),
        ("Resource routes?", "Route::resource('photos', PhotoController::class) — index, create, store, show, edit, update, destroy."),
        ("apiResource vs resource?", "apiResource без create/edit — JSON API CRUD."),
        ("Route::redirect?", "Route::redirect('/here', '/there', 301) без controller."),
    ],
    "Контроллеры": [
        ("Single action controllers?", "php artisan make:controller ShowProfileController --invokable — один __invoke."),
        ("Controller middleware?", "$this->middleware('auth')->only('store'); или в конструкторе — attribute Middleware в Laravel 11."),
        ("Form Request?", "php artisan make:request StorePostRequest — authorize() + rules(); type-hint в controller method."),
        ("authorize() в Form Request?", "return $this->user()->can('create', Post::class); — 403 до validation."),
        ("Dependency injection в controller?", "Constructor или method injection — Laravel resolve из container: public function store(PostService $svc)."),
        ("Resource controller methods?", "index, create, store, show, edit, update, destroy — REST соглашения."),
        ("API controller JSON?", "return PostResource::collection($posts) или response()->json($data)."),
        ("Controller vs Closure routes?", "Closure для простых; controllers для тестируемости и reuse."),
        ("Route::controller()?", "Группировка [Controller::class, 'method'] строками — legacy style."),
        ("Invokable controllers?", "Route::get('/profile', ProfileController::class) — один entry point."),
        ("abort() и abort_if()?", "abort(404); abort_if($user->banned, 403, 'Banned'); HTTP exceptions."),
        ("redirect()->with()?", "Flash data в session: redirect()->route('home')->with('status', 'Saved!')."),
        ("back() helper?", "redirect()->back() с input old() после validation errors."),
        ("old() helper?", "old('email') — repopulate form после failed validation."),
        ("View composers?", "View::composer('profile', fn ($view) => ...) — shared view data."),
    ],
    "Eloquent": [
        ("Active Record в Eloquent?", "Model class = таблица (posts); экземпляр = строка; Post::find(1), $post->save()."),
        ("Mass assignment fillable/guarded?", "$fillable = ['title','body']; $guarded = ['id']; без защиты — MassAssignmentException."),
        ("Eloquent relationships belongsTo?", "public function user(): BelongsTo { return $this->belongsTo(User::class); }"),
        ("hasMany / hasOne?", "User hasMany Post::class; hasOne Profile::class — foreign key на child."),
        ("belongsToMany pivot?", "attach, detach, sync; withPivot('expires_at'); timestamps на pivot."),
        ("Eager loading N+1?", "Post::with('user')->get(); — один запрос для relation вместо N."),
        ("Lazy eager load?", "$posts->load('comments'); после получения коллекции."),
        ("withCount?", "User::withCount('posts')->get(); — posts_count без загрузки posts."),
        ("Scopes local?", "scopePublished($query) { return $query->where('published', true); } Post::published()->get();"),
        ("Global scopes?", "booted() { static::addGlobalScope('active', fn ($q) => $q->where('active', 1)); }"),
        ("Soft deletes?", "use SoftDeletes; deleted_at; withTrashed(), onlyTrashed(), restore(), forceDelete()."),
        ("Casts attribute?", "protected $casts = ['options' => 'array', 'published_at' => 'datetime'];"),
        ("Accessors / mutators (Laravel 9+)?", "protected function title(): Attribute { return Attribute::make(get: fn ($v) => ucfirst($v)); }"),
        ("Query builder vs Eloquent?", "DB::table('users') — без model events; User::query() — Eloquent builder с scopes."),
        ("chunk() и cursor()?", "Обработка больших таблиц без загрузки всего: User::chunk(100, fn ($users) => ...); cursor() lazy generator."),
    ],
    "Миграции": [
        ("Создание migration?", "php artisan make:migration create_posts_table --create=posts / --table=posts."),
        ("Schema::create blueprint?", "Schema::create('posts', function (Blueprint $table) { $table->id(); $table->string('title'); $table->timestamps(); });"),
        ("Foreign keys?", "$table->foreignId('user_id')->constrained()->cascadeOnDelete();"),
        ("Индексы?", "$table->index('email'); $table->unique('slug'); composite index(['a','b'])."),
        ("Изменение колонок?", "php artisan make:migration add_status_to_posts — $table->string('status')->default('draft');"),
        ("rename column?", "$table->renameColumn('from', 'to'); doctrine/dbal historically required."),
        ("migrate / rollback?", "php artisan migrate; migrate:rollback --step=1; migrate:fresh --seed (dev only!)."),
        ("Seeds и factories?", "DatabaseSeeder calls ModelFactory; User::factory(10)->create();"),
        ("Factory states?", "User::factory()->admin()->create(); definition() + state methods."),
        ("Migration naming order?", "Timestamp prefix ensures order; не редактировать applied migrations в prod."),
        ("Schema::hasTable?", "Условная migration logic для совместимости."),
        ("JSON columns?", "$table->json('meta'); cast array в model."),
        ("Enum column?", "$table->enum('status', ['draft','published']); или string + PHP enum cast Laravel 9+."),
        ("Soft delete column?", "$table->softDeletes(); adds deleted_at nullable."),
        ("down() method?", "Schema::dropIfExists('posts'); — reverse migration."),
    ],
    "Blade": [
        ("Расширение .blade.php?", "Blade компилируется в PHP; views в resources/views; view('posts.index', compact('posts'))."),
        ("@extends и @section?", "@extends('layouts.app') @section('content') ... @endsection @yield('content') в layout."),
        ("@include и @each?", "@include('partials.errors'); @each('comment', $comments, 'comment')."),
        ("Components <x-alert>?", "php artisan make:component Alert; class + view resources/views/components/alert.blade.php."),
        ("Slot и attributes?", "<x-card title=\"...\"> slot content </x-card>; {{ $attributes->merge(['class' => ...]) }}."),
        ("@props в anonymous components?", "@props(['type' => 'info', 'message']) — входные props."),
        ("Blade stacks?", "@push('scripts') ... @endpush; @stack('scripts') в layout."),
        ("@once directive?", "Include/push один раз за render — assets dedup."),
        ("@csrf в forms?", "Hidden token для web middleware CSRF verification."),
        ("@method('PUT')?", "Spoof HTTP method для HTML forms: PUT/PATCH/DELETE."),
        ("Blade escaping {{ }}?", "Auto htmlspecialchars; {!! $html !!} unescaped — XSS risk."),
        ("@verbatim?", "Отключить Blade parsing для @{{ vue }} шаблонов."),
        ("Custom Blade directives?", "Blade::directive('datetime', fn ($expr) => ...); в AppServiceProvider."),
        ("View exists check?", "view()->exists('emails.welcome'); View::share global data."),
        ("Mail markdown templates?", "php artisan make:mail OrderShipped --markdown=emails.orders.shipped."),
    ],
    "Middleware": [
        ("Что такое middleware?", "HTTP pipeline filters: request → middleware chain → controller → response → middleware (terminate)."),
        ("Global vs route middleware?", "Kernel/bootstrap: append/prepend; alias 'auth' => Authenticate::class; Route::middleware(['auth'])."),
        ("Middleware groups web и api?", "web: session, cookie encryption, CSRF; api: throttle, bindings, stateless default."),
        ("Создание middleware?", "php artisan make:middleware EnsureUserIsAdmin; handle(Request $request, Closure $next)."),
        ("Middleware parameters?", "middleware('role:admin') — третий аргумент $role в handle после $next."),
        ("Before vs after middleware?", "handle до $next — до controller; код после $next($request) — после response."),
        ("SubstituteBindings?", "Route model binding middleware в группе web/api."),
        ("TrustProxies?", "Correct HTTPS behind load balancer — X-Forwarded-* headers."),
        ("PreventRequestsDuringMaintenance?", "503 when artisan down."),
        ("ValidateSignature?", "Signed URL middleware 'signed'."),
        ("ThrottleRequests?", "Rate limit by key — user id or IP."),
        ("Priority middleware?", "$middleware->priority([...]) порядок при конфликте."),
        ("Middleware в Laravel 11?", "bootstrap/app.php ->withMiddleware(function (Middleware $m) { $m->alias([...]); })."),
        ("Terminate middleware?", "Middleware с terminate() — после отправки response (logging)."),
        ("RedirectIfAuthenticated?", "Guest routes — redirect logged-in users from login/register."),
    ],
    "Валидация": [
        ("Validator facade?", "Validator::make($data, $rules, $messages); $validator->fails() / validated()."),
        ("Form Request rules()?", "return ['email' => 'required|email|unique:users', 'password' => 'required|min:8|confirmed'];"),
        ("Rule objects?", "Rule::unique('users')->ignore($user->id); Rule::in(['active','pending']);"),
        ("Custom validation rule?", "php artisan make:rule Uppercase; implements ValidationRule invoke method."),
        ("sometimes и nullable?", "Поле validate только если present; nullable — null allowed."),
        ("confirmed rule?", "password + password_confirmation fields."),
        ("array validation?", "'items.*.id' => 'required|integer' — nested arrays."),
        ("after:date / before?", "Date comparison rules; after_or_equal:today."),
        ("exists и unique?", "exists:users,email; unique:users,email,{id}."),
        ("Validation attributes?", "attributes() human names для error messages."),
        ("messages() custom?", "Override default 'required' => 'Email обязателен'."),
        ("stopOnFirstFailure?", "Validator::stopOnFirstFailure() — одна ошибка на field batch."),
        ("validateWithBag?", "Multiple error bags: $validator->validateWithBag('shipping')."),
        ("prepareForValidation?", "FormRequest hook normalize input before rules."),
        ("withValidator after hook?", "withValidator(fn ($v) => $v->after(function ($v) { ... }));"),
    ],
    "Аутентификация": [
        ("Laravel Breeze / Jetstream / Fortify?", "Starter kits: Breeze minimal; Jetstream teams/2FA; Fortify headless auth backend."),
        ("Sanctum SPA vs token?", "SPA cookie session + CSRF; API tokens HasApiTokens personal access tokens."),
        ("auth middleware?", "Route::middleware('auth'); guard web default config/auth.php."),
        ("Guards и providers?", "guards: web (session), sanctum; providers: eloquent User model."),
        ("Policy authorization?", "php artisan make:policy PostPolicy; $this->authorize('update', $post); Gate::authorize."),
        ("Gates?", "Gate::define('edit-settings', fn (User $u) => $u->isAdmin); @can blade."),
        ("Password hashing?", "Hash::make / bcrypt; cast 'password' => 'hashed' auto on set Laravel 10+."),
        ("Password reset flow?", "Notifications + tokens table password_reset_tokens; Password::sendResetLink."),
        ("Email verification?", "MustVerifyEmail contract; middleware verified; signed verification URL."),
        ("Auth::attempt?", "Auth::attempt(['email'=>$e,'password'=>$p], $remember); session regenerate."),
        ("Session fixation?", "Session::regenerate() after login."),
        ("Multi-auth guards?", "Auth::guard('admin')->attempt(...); separate provider model."),
        ("Socialite?", "OAuth GitHub/Google via laravel/socialite package."),
        ("Rate limit login?", "Fortify/Breeze throttle; LoginRateLimiter."),
        ("can middleware?", "Route::middleware('can:update,post') — policy check on route."),
    ],
    "Очереди": [
        ("Зачем queues?", "Async jobs: mail, webhooks, heavy processing — не блокировать HTTP response."),
        ("Job class?", "php artisan make:job ProcessPodcast; implements ShouldQueue; handle() method."),
        ("dispatch()?", "ProcessPodcast::dispatch($podcast); dispatch(new ProcessPodcast(...)); Queue::push."),
        ("Queue drivers?", "sync (dev), database, redis, sqs — config/queue.php QUEUE_CONNECTION."),
        ("queue:work?", "php artisan queue:work redis --tries=3 --timeout=90; supervisor in production."),
        ("Failed jobs?", "failed_jobs table; queue:failed, retry, flush; FailedJob event."),
        ("ShouldQueue interface?", "Job queued; без него — sync execution even if dispatched to queue."),
        ("SerializesModels trait?", "Eloquent models in jobs serialized by id; re-fetch on handle."),
        ("Job middleware?", "RateLimited, WithoutOverlapping — job pipeline."),
        ("Delayed dispatch?", "ProcessPodcast::dispatch()->delay(now()->addMinutes(10));"),
        ("Queue batches?", "Bus::batch([...])->then()->catch()->finally(); progress tracking."),
        ("Chain jobs?", "Bus::chain([new A, new B, new C])->dispatch(); sequential."),
        ("Horizon?", "Redis queue dashboard for Laravel — metrics, workers, failed jobs UI."),
        ("Unique jobs?", "ShouldBeUnique — prevent duplicate same job queued."),
        ("afterCommit dispatch?", "dispatch()->afterCommit() — только после DB transaction commit."),
    ],
    "События": [
        ("Event / Listener pattern?", "event(new OrderShipped($order)); EventServiceProvider listen array or discover."),
        ("Event discovery?", "app/Listeners auto-register if type-hint handle(OrderShipped $event)."),
        ("ShouldBroadcast?", "Real-time Echo/Pusher — broadcastOn() channels."),
        ("Queued listeners?", "Listener implements ShouldQueue — async handle."),
        ("Subscriber class?", "subscribe() returns event=>method map — multiple events one class."),
        ("Model events?", "creating, created, updating, updated, deleting — boot() callbacks or Observers."),
        ("Observer?", "php artisan make:observer UserObserver --model=User; register in AppServiceProvider."),
        ("dispatch helper?", "OrderShipped::dispatch($order) if event uses Dispatchable trait."),
        ("Event fake in tests?", "Event::fake(); Event::assertDispatched(OrderShipped::class);"),
        ("Wildcard listeners?", "Event::listen('order.*', ...); pattern matching."),
        ("Synchronous default?", "Listeners sync unless ShouldQueue — order matters."),
        ("Prevent duplicate listeners?", "ShouldHandleEventsAfterCommit — after DB commit."),
        ("Notification vs Event?", "Notifications user-facing channels; Events internal domain decoupling."),
        ("Event sourcing note?", "Laravel events not full event sourcing — use packages for audit log."),
        ("Closure listeners?", "Event::listen(fn (OrderShipped $e) => ...); quick prototyping."),
    ],
    "Тестирование": [
        ("PHPUnit / Pest?", "tests/Feature и tests/Unit; php artisan test; Pest expressive syntax optional."),
        ("RefreshDatabase trait?", "Migrate fresh each test — isolated DB state."),
        ("actingAs user?", "$this->actingAs($user)->get('/dashboard')->assertOk();"),
        ("HTTP tests?", "$this->post('/posts', $data)->assertRedirect(); assertSessionHasErrors."),
        ("assertJsonStructure?", "API testing JSON shape and values assertJson(['id' => 1])."),
        ("Database assertions?", "assertDatabaseHas('users', ['email' => 'a@b.c']); assertDatabaseMissing."),
        ("Model factories in tests?", "User::factory()->create(); make() without persist."),
        ("Mocking facades?", "Mail::fake(); Mail::assertSent(OrderShipped::class); Queue::fake()."),
        ("Http::fake?", "Http::fake(['api/*' => Http::response(['ok'], 200)]); outbound HTTP mock."),
        ("Livewire testing?", "Livewire::test(Counter::class)->set('count', 1)->call('increment')."),
        ("Coverage?", "php artisan test --coverage; Xdebug/pcov required."),
        ("Parallel testing?", "php artisan test --parallel — paratest package."),
        ("Dusk browser tests?", "Laravel Dusk — ChromeDriver E2E (legacy for many teams)."),
        ("Test environment .env.testing?", "APP_ENV=testing; array cache/session drivers often."),
        ("WithoutMiddleware trait?", "Disable middleware for isolated controller test — use cautiously."),
    ],
    "API": [
        ("API routes prefix?", "routes/api.php — /api/*; default throttle:api; no CSRF session."),
        ("API Resources?", "php artisan make:resource PostResource; toArray(Request $request) transform output."),
        ("Resource collections?", "PostResource::collection($posts); pagination preserve meta."),
        ("API versioning?", "Route::prefix('v1')->group(...); or Accept header versioning custom."),
        ("Sanctum token abilities?", "Token abilities/scopes $token->can('server:update')."),
        ("Rate limiting API?", "RateLimiter::for('api', fn ($req) => Limit::perMinute(60)->by($req->user()?->id ?: $req->ip()));"),
        ("CORS?", "config/cors.php; fruitcake/laravel-cors or built-in HandleCors middleware."),
        ("API authentication 401?", "Unauthenticated JSON { message: 'Unauthenticated.' } — Accept application/json."),
        ("Conditional requests?", "ETag / Last-Modified — optional middleware packages or custom."),
        ("Pagination API?", "Post::paginate(15); ResourceCollection with links meta."),
        ("API exception handling?", "Handler render JSON for ValidationException 422 unified errors."),
        ("Scribe / OpenAPI?", "Documentation generators from routes and FormRequests."),
        ("HATEOAS in Laravel?", "Not built-in — add links in API Resources manually."),
        ("JSON:API spec?", "Packages spatie/laravel-json-api or custom Resource structure."),
        ("Postman collection?", "Export from Scribe or OpenAPI for QA."),
    ],
    "Service Container": [
        ("IoC container Laravel?", "Resolve class dependencies automatically — bind interfaces to implementations."),
        ("App::bind vs singleton?", "bind — new instance each resolve; singleton — shared instance app lifecycle."),
        ("Service provider register vs boot?", "register — bindings only; boot — routes, views, after all providers registered."),
        ("Concrete auto-resolution?", "No binding needed if class concrete and dependencies resolvable."),
        ("Contextual binding?", "$this->app->when(PhotoController::class)->needs('$variable')->give(...);"),
        ("Instance binding?", "App::instance('stripe', $client) — pre-built object."),
        ("Deferred providers?", "Defer loading until service first requested — performance."),
        ("Contract binding?", "bind(PaymentGateway::class, StripeGateway::class); type-hint interface."),
        ("Closure binding?", "App::bind('config.custom', fn ($app) => new Custom(...));"),
        ("Method injection?", "Route/controller method params resolved from container."),
        ("Contextual attributes Laravel 11?", "#[Bind(...)] dependency injection attributes."),
        ("Tagged bindings?", "bind tag collections for multiple implementations strategy pattern."),
        ("Container make() with params?", "app()->makeWith(Class::class, ['param' => $value]);"),
        ("Service container facades?", "Facade root accessor resolves from container singleton."),
        ("Octane note?", "Singleton state persists between requests — avoid mutable state in bindings."),
    ],
    "Collections": [
        ("collect() helper?", "collect([1,2,3]) — Illuminate\\Support\\Collection wrapper array."),
        ("map filter reduce?", "$collection->map(fn ($i) => $i*2)->filter()->reduce(fn ($c,$i) => $c+$i, 0);"),
        ("pluck и keyBy?", "pluck('name', 'id'); keyBy('id') — reindex collection."),
        ("groupBy?", "$users->groupBy('role'); nested grouping callback."),
        ("Collection vs Eloquent Collection?", "Eloquent\\Collection extends Support\\Collection with model helpers load(), find()."),
        ("LazyCollection?", "stream large datasets — LazyCollection::make(function () { yield ...);"),
        ("Higher order messages?", "$users->each->markAsActive(); map spread operator."),
        ("pipe method?", "Pass collection through closure: ->pipe(fn ($c) => $c->sort())->all();"),
        ("when/unless?", "Conditional chaining: ->when($condition, fn ($c) => $c->where(...))."),
        ("toArray vs all?", "all() internal items; toArray() recursive array conversion."),
        ("Collection macros?", "Collection::macro('toUpper', fn () => ...); extend in ServiceProvider."),
        ("Arr helper vs Collection?", "Arr::get, Arr::wrap — static array utils; collect for chaining."),
        ("data_get / data_set?", "Dot notation nested array/object access."),
        ("Str helper?", "Str::slug, Str::uuid, Str::of('foo')->append('bar') fluent strings."),
        ("Enumerable contract?", "Common interface Collection and LazyCollection — consistent API."),
    ],
}

CODE_CARDS: list[tuple[str, str, str, str, str]] = [
    # question, task, buggy code, reference, topic
    (
        "Mass assignment в PostController",
        "Разреши mass assignment только title и body через fillable.",
        """class Post extends Model
{
    // users can mass assign anything
}""",
        """class Post extends Model
{
    protected $fillable = ['title', 'body'];
}""",
        "Eloquent",
    ),
    (
        "N+1 в списке постов",
        "Eager-load авторов при выборке постов.",
        """$posts = Post::all();
foreach ($posts as $post) {
    echo $post->user->name;
}""",
        """$posts = Post::with('user')->get();
foreach ($posts as $post) {
    echo $post->user->name;
}""",
        "Eloquent",
    ),
    (
        "Route без name",
        "Добавь именованный маршрут posts.index.",
        """Route::get('/posts', [PostController::class, 'index']);""",
        """Route::get('/posts', [PostController::class, 'index'])->name('posts.index');""",
        "Роутинг",
    ),
    (
        "CSRF в форме Blade",
        "Добавь CSRF-защиту в form.",
        """<form method="POST" action="/posts">
  <input name="title">
</form>""",
        """<form method="POST" action="/posts">
  @csrf
  <input name="title">
</form>""",
        "Blade",
    ),
    (
        "Validation в controller",
        "Перенеси правила в $request->validate([...]).",
        """public function store(Request $request)
{
    $title = $request->input('title');
    Post::create(['title' => $title]);
}""",
        """public function store(Request $request)
{
    $validated = $request->validate([
        'title' => 'required|string|max:255',
    ]);
    Post::create($validated);
}""",
        "Валидация",
    ),
    (
        "Middleware auth на route",
        "Защити маршрут middleware auth.",
        """Route::get('/dashboard', [DashboardController::class, 'index']);""",
        """Route::get('/dashboard', [DashboardController::class, 'index'])
    ->middleware('auth');""",
        "Middleware",
    ),
    (
        "Migration без timestamps",
        "Добавь created_at/updated_at.",
        """Schema::create('posts', function (Blueprint $table) {
    $table->id();
    $table->string('title');
});""",
        """Schema::create('posts', function (Blueprint $table) {
    $table->id();
    $table->string('title');
    $table->timestamps();
});""",
        "Миграции",
    ),
    (
        "Foreign key user_id",
        "Добавь constrained foreignId для user_id.",
        """Schema::create('posts', function (Blueprint $table) {
    $table->id();
    $table->unsignedBigInteger('user_id');
    $table->string('title');
    $table->timestamps();
});""",
        """Schema::create('posts', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->string('title');
    $table->timestamps();
});""",
        "Миграции",
    ),
    (
        "Policy check",
        "Добавь authorize update перед сохранением.",
        """public function update(Request $request, Post $post)
{
    $post->update($request->all());
}""",
        """public function update(Request $request, Post $post)
{
    $this->authorize('update', $post);
    $post->update($request->validated());
}""",
        "Аутентификация",
    ),
    (
        "Dispatch job",
        "Отправь ProcessOrder в очередь через dispatch.",
        """public function store(Request $request)
{
    ProcessOrder::handle($order);
}""",
        """public function store(Request $request)
{
    ProcessOrder::dispatch($order);
}""",
        "Очереди",
    ),
    (
        "Event dispatch",
        "Вызови event OrderPlaced после создания заказа.",
        """public function store(Request $request)
{
    $order = Order::create($validated);
    // notify warehouse
}""",
        """public function store(Request $request)
{
    $order = Order::create($validated);
    event(new OrderPlaced($order));
}""",
        "События",
    ),
    (
        "API Resource",
        "Верни PostResource вместо модели напрямую.",
        """public function show(Post $post)
{
    return $post;
}""",
        """public function show(Post $post)
{
    return new PostResource($post);
}""",
        "API",
    ),
    (
        "Service binding",
        "Зарегистрируй singleton PaymentGateway в register().",
        """public function register(): void
{
    //
}""",
        """public function register(): void
{
    $this->app->singleton(PaymentGateway::class, StripeGateway::class);
}""",
        "Service Container",
    ),
    (
        "Collection pipeline",
        "Используй collect для фильтрации активных пользователей.",
        """$active = [];
foreach ($users as $user) {
    if ($user->active) {
        $active[] = $user->email;
    }
}""",
        """$active = collect($users)
    ->filter(fn ($user) => $user->active)
    ->pluck('email')
    ->all();""",
        "Collections",
    ),
    (
        "env() в controller",
        "Используй config() вместо env() в runtime коде.",
        """public function index()
{
    $key = env('STRIPE_KEY');
}""",
        """public function index()
{
    $key = config('services.stripe.key');
}""",
        "Основы",
    ),
    (
        "Controller injection",
        "Type-hint PostService в конструкторе.",
        """class PostController extends Controller
{
    public function index()
    {
        $posts = Post::all();
    }
}""",
        """class PostController extends Controller
{
    public function __construct(private PostService $posts)
    {
    }

    public function index()
    {
        $posts = $this->posts->all();
    }
}""",
        "Контроллеры",
    ),
    (
        "Form Request usage",
        "Type-hint StorePostRequest вместо Request.",
        """public function store(Request $request)
{
    $validated = $request->validate(['title' => 'required']);
    Post::create($validated);
}""",
        """public function store(StorePostRequest $request)
{
    Post::create($request->validated());
}""",
        "Контроллеры",
    ),
    (
        "Soft delete query",
        "Включи удалённые записи через withTrashed.",
        """$user = User::find($id);""",
        """$user = User::withTrashed()->find($id);""",
        "Eloquent",
    ),
    (
        "Route model binding",
        "Используй implicit binding Post $post.",
        """public function show($id)
{
    $post = Post::findOrFail($id);
    return view('posts.show', compact('post'));
}""",
        """public function show(Post $post)
{
    return view('posts.show', compact('post'));
}""",
        "Роутинг",
    ),
    (
        "Blade component",
        "Замени дублированный alert на компонент x-alert.",
        """@if ($message)
  <div class="alert">{{ $message }}</div>
@endif""",
        """<x-alert :message="$message" />""",
        "Blade",
    ),
]

# Extra revision prompts per topic (expand to 500+)
REVISION_HINTS: dict[str, list[str]] = {
    "Основы": ["artisan", "service provider", "config cache", "env", "Vite", "maintenance mode"],
    "Роутинг": ["route groups", "model binding", "resource routes", "rate limiting", "signed URLs"],
    "Контроллеры": ["Form Request", "DI", "single action", "resource controller", "flash session"],
    "Eloquent": ["relationships", "eager loading", "scopes", "soft deletes", "casts"],
    "Миграции": ["foreign keys", "factories", "seeders", "rollback", "indexes"],
    "Blade": ["components", "layouts", "stacks", "CSRF", "directives"],
    "Middleware": ["auth", "guest", "throttle", "signed", "middleware groups"],
    "Валидация": ["Form Request", "custom rules", "Rule objects", "nested arrays", "messages"],
    "Аутентификация": ["Sanctum", "policies", "gates", "guards", "password reset"],
    "Очереди": ["ShouldQueue", "failed jobs", "Horizon", "batch", "delay"],
    "События": ["listeners", "observers", "broadcast", "ShouldQueue listener", "fake"],
    "Тестирование": ["RefreshDatabase", "actingAs", "Http::fake", "assertJson", "factories"],
    "API": ["API Resources", "Sanctum tokens", "pagination", "CORS", "versioning"],
    "Service Container": ["bind", "singleton", "provider", "contract", "resolve"],
    "Collections": ["map", "filter", "pluck", "groupBy", "LazyCollection"],
}
