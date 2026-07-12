"""Additional Laravel live-coding cards — explicit topics."""
from __future__ import annotations

from live_coding_card import live


def _cards(specs: list[tuple[str, str, str, str]]) -> list[dict]:
    """title, assignment, reference, topic"""
    return [
        live(title, assignment, reference, lang="php", topic=topic)
        for title, assignment, reference, topic in specs
    ]


def extra_cards() -> list[dict]:
    specs: list[tuple[str, str, str, str]] = []

    basics = [
        (
            "Config services stripe",
            "config/services.php ключ stripe: key из env STRIPE_KEY, secret из STRIPE_SECRET.",
            """return [
    'stripe' => [
        'key' => env('STRIPE_KEY'),
        'secret' => env('STRIPE_SECRET'),
    ],
];""",
            "Основы",
        ),
        (
            "AppServiceProvider boot view share",
            "View::share('appName', config('app.name')) в boot().",
            """public function boot(): void
{
    View::share('appName', config('app.name'));
}""",
            "Основы",
        ),
        (
            "Schedule daily command",
            "Kernel schedule: command inspire dailyAt 08:00.",
            """protected function schedule(Schedule $schedule): void
{
    $schedule->command('inspire')->dailyAt('08:00');
}""",
            "Основы",
        ),
        (
            "Custom helper app_version",
            "Функция app_version(): string возвращает config('app.version', '1.0.0').",
            """function app_version(): string
{
    return (string) config('app.version', '1.0.0');
}""",
            "Основы",
        ),
        (
            "Exception render JSON",
            "Handler render: ValidationException → 422 JSON errors для expectsJson.",
            """public function render($request, Throwable $e)
{
    if ($e instanceof ValidationException && $request->expectsJson()) {
        return response()->json(['errors' => $e->errors()], 422);
    }
    return parent::render($request, $e);
}""",
            "Основы",
        ),
        (
            "Storage put file",
            "Upload: Storage::disk('public')->put('avatars/'.$name, $contents).",
            """$path = Storage::disk('public')->put(
    'avatars/'.$request->file('avatar')->hashName(),
    $request->file('avatar')->getContent(),
);""",
            "Основы",
        ),
        (
            "Cache remember users",
            "Cache::remember('users.all', 3600, fn () => User::all()).",
            """$users = Cache::remember('users.all', 3600, fn () => User::all());""",
            "Основы",
        ),
        (
            "Log channel stack",
            "Log::channel('slack')->warning('Deploy failed', ['id' => $id]).",
            """Log::channel('slack')->warning('Deploy failed', ['id' => $deployId]);""",
            "Основы",
        ),
    ]
    specs.extend(basics)

    routing = [
        (
            "Route prefix admin",
            "Группа prefix admin, name admin., middleware auth — GET dashboard.",
            """Route::prefix('admin')->name('admin.')->middleware('auth')->group(function () {
    Route::get('/dashboard', [AdminDashboardController::class, 'index'])->name('dashboard');
});""",
            "Роутинг",
        ),
        (
            "Route where numeric id",
            "GET posts/{id} where id [0-9]+.",
            """Route::get('/posts/{id}', [PostController::class, 'show'])
    ->whereNumber('id');""",
            "Роутинг",
        ),
        (
            "API throttle group",
            "Route middleware throttle:api group GET /api/status.",
            """Route::middleware('throttle:api')->group(function () {
    Route::get('/status', fn () => ['ok' => true]);
});""",
            "Роутинг",
        ),
        (
            "Signed unsubscribe route",
            "GET unsubscribe/{user} middleware signed name unsubscribe.",
            """Route::get('/unsubscribe/{user}', UnsubscribeController::class)
    ->middleware('signed')
    ->name('unsubscribe');""",
            "Роутинг",
        ),
        (
            "Fallback 404 JSON",
            "Route fallback JSON message Not found 404.",
            """Route::fallback(fn () => response()->json(['message' => 'Not found'], 404));""",
            "Роутинг",
        ),
        (
            "Route redirect legacy",
            "Redirect /old-url to /new-url permanent 301.",
            """Route::redirect('/old-url', '/new-url', 301);""",
            "Роутинг",
        ),
        (
            "Implicit binding slug",
            "GET posts/{post:slug} — route key slug on Post model.",
            """public function getRouteKeyName(): string
{
    return 'slug';
}""",
            "Роутинг",
        ),
        (
            "Route apiResource posts",
            "apiResource posts PostController except create edit.",
            """Route::apiResource('posts', PostController::class);""",
            "Роутинг",
        ),
    ]
    specs.extend(routing)

    controllers = [
        (
            "Invokable HomeController",
            "Invokable controller __invoke returns view home.",
            """class HomeController extends Controller
{
    public function __invoke()
    {
        return view('home');
    }
}""",
            "Контроллеры",
        ),
        (
            "Controller authorize store",
            "store: authorize create Post, create validated data.",
            """public function store(StorePostRequest $request)
{
    $this->authorize('create', Post::class);
    Post::create($request->validated());
    return redirect()->route('posts.index');
}""",
            "Контроллеры",
        ),
        (
            "Destroy redirect flash",
            "destroy post: delete, redirect back with flash status.",
            """public function destroy(Post $post)
{
    $post->delete();
    return back()->with('status', 'Post deleted');
}""",
            "Контроллеры",
        ),
        (
            "Update validated",
            "update Post: fill validated, save, redirect show.",
            """public function update(UpdatePostRequest $request, Post $post)
{
    $post->update($request->validated());
    return redirect()->route('posts.show', $post);
}""",
            "Контроллеры",
        ),
        (
            "API index paginate",
            "index returns PostResource collection paginate 15.",
            """public function index()
{
    return PostResource::collection(Post::paginate(15));
}""",
            "Контроллеры",
        ),
        (
            "Form Request authorize false",
            "authorize returns auth()->check() for StoreCommentRequest.",
            """public function authorize(): bool
{
    return auth()->check();
}""",
            "Контроллеры",
        ),
        (
            "PrepareForValidation merge slug",
            "prepareForValidation merge slug from title Str::slug.",
            """protected function prepareForValidation(): void
{
    $this->merge([
        'slug' => Str::slug($this->input('title', '')),
    ]);
}""",
            "Контроллеры",
        ),
        (
            "Constructor inject Cache",
            "Inject Illuminate Cache Repository в PostController constructor.",
            """public function __construct(private Repository $cache)
{
}""",
            "Контроллеры",
        ),
    ]
    specs.extend(controllers)

    eloquent = [
        (
            "HasMany comments",
            "Post hasMany Comment ordered latest.",
            """public function comments(): HasMany
{
    return $this->hasMany(Comment::class)->latest();
}""",
            "Eloquent",
        ),
        (
            "BelongsToMany tags",
            "Post belongsToMany Tag withTimestamps.",
            """public function tags(): BelongsToMany
{
    return $this->belongsToMany(Tag::class)->withTimestamps();
}""",
            "Eloquent",
        ),
        (
            "Casts datetime bool",
            "casts published_at datetime, meta array, is_featured boolean.",
            """protected $casts = [
    'published_at' => 'datetime',
    'meta' => 'array',
    'is_featured' => 'boolean',
];""",
            "Eloquent",
        ),
        (
            "SoftDeletes trait",
            "Use SoftDeletes on Post model.",
            """class Post extends Model
{
    use SoftDeletes;
}""",
            "Eloquent",
        ),
        (
            "updateOrCreate post",
            "Post updateOrCreate slug + title/body.",
            """Post::updateOrCreate(
    ['slug' => $slug],
    ['title' => $title, 'body' => $body],
);""",
            "Eloquent",
        ),
        (
            "withCount comments",
            "Post published withCount comments get.",
            """$posts = Post::published()->withCount('comments')->get();""",
            "Eloquent",
        ),
        (
            "Accessor fullName",
            "User accessor fullName: first + last.",
            """protected function fullName(): Attribute
{
    return Attribute::get(fn () => trim($this->first_name.' '.$this->last_name));
}""",
            "Eloquent",
        ),
        (
            "Global scope Active",
            "Booted addGlobalScope active status active.",
            """protected static function booted(): void
{
    static::addGlobalScope('active', fn ($q) => $q->where('status', 'active'));
}""",
            "Eloquent",
        ),
    ]
    specs.extend(eloquent)

    migrations = [
        (
            "Add slug column",
            "Migration add slug unique string to posts after title.",
            """Schema::table('posts', function (Blueprint $table) {
    $table->string('slug')->unique()->after('title');
});""",
            "Миграции",
        ),
        (
            "Pivot table post_tag",
            "Create post_tag post_id tag_id foreign constrained unique pair.",
            """Schema::create('post_tag', function (Blueprint $table) {
    $table->foreignId('post_id')->constrained()->cascadeOnDelete();
    $table->foreignId('tag_id')->constrained()->cascadeOnDelete();
    $table->primary(['post_id', 'tag_id']);
});""",
            "Миграции",
        ),
        (
            "Seeder call factories",
            "DatabaseSeeder create 10 users each with 3 posts.",
            """User::factory(10)->create()->each(function (User $user) {
    Post::factory(3)->for($user)->create();
});""",
            "Миграции",
        ),
        (
            "Factory state admin",
            "UserFactory state admin is_admin true.",
            """public function admin(): static
{
    return $this->state(fn () => ['is_admin' => true]);
}""",
            "Миграции",
        ),
        (
            "Migration softDeletes",
            "Add softDeletes to comments table.",
            """Schema::table('comments', function (Blueprint $table) {
    $table->softDeletes();
});""",
            "Миграции",
        ),
        (
            "Index published_at",
            "Index published_at on posts table.",
            """Schema::table('posts', function (Blueprint $table) {
    $table->index('published_at');
});""",
            "Миграции",
        ),
    ]
    specs.extend(migrations)

    blade = [
        (
            "Blade @forelse",
            "@forelse posts as post ... @empty No posts @endforelse.",
            """@forelse ($posts as $post)
    <li>{{ $post->title }}</li>
@empty
    <p>No posts</p>
@endforelse""",
            "Blade",
        ),
        (
            "Blade @auth",
            "@auth show dashboard link @else login @endauth.",
            """@auth
    <a href="/dashboard">Dashboard</a>
@else
    <a href="/login">Login</a>
@endauth""",
            "Blade",
        ),
        (
            "Component alert props",
            "Anonymous component @props type message; div alert.",
            """@props(['type' => 'info', 'message'])
<div class="alert alert-{{ $type }}">{{ $message }}</div>""",
            "Blade",
        ),
        (
            "Form method spoof PUT",
            "Form POST @csrf @method PUT update post.",
            """<form method="POST" action="/posts/{{ $post->id }}">
    @csrf
    @method('PUT')
    <input name="title" value="{{ old('title', $post->title) }}">
</form>""",
            "Blade",
        ),
        (
            "Push scripts stack",
            "@push scripts chart.js @endpush in view.",
            """@push('scripts')
    <script src="/chart.js"></script>
@endpush""",
            "Blade",
        ),
    ]
    specs.extend(blade)

    middleware = [
        (
            "Alias middleware admin",
            "bootstrap middleware alias admin => EnsureUserIsAdmin.",
            """->withMiddleware(function (Middleware $middleware) {
    $middleware->alias(['admin' => EnsureUserIsAdmin::class]);
})""",
            "Middleware",
        ),
        (
            "TrustProxies at",
            "TrustProxies at * for AWS ELB.",
            """protected $proxies = '*';""",
            "Middleware",
        ),
        (
            "Append middleware web",
            "Append LogRequest middleware to web group.",
            """->withMiddleware(function (Middleware $middleware) {
    $middleware->appendToGroup('web', LogRequest::class);
})""",
            "Middleware",
        ),
        (
            "Middleware parameter locale",
            "SetLocale middleware handle($request, $next, string $locale).",
            """public function handle(Request $request, Closure $next, string $locale)
{
    App::setLocale($locale);
    return $next($request);
}""",
            "Middleware",
        ),
    ]
    specs.extend(middleware)

    validation = [
        (
            "Rule unique ignore",
            "Rule unique users email ignore user id on update.",
            """'email' => ['required', 'email', Rule::unique('users')->ignore($this->user()->id)],""",
            "Валидация",
        ),
        (
            "Password confirmed",
            "Rules password required min 8 confirmed.",
            """'password' => ['required', 'string', 'min:8', 'confirmed'],""",
            "Валидация",
        ),
        (
            "Array validation items",
            "Validate items array each id integer qty min 1.",
            """'items' => ['required', 'array'],
'items.*.id' => ['required', 'integer'],
'items.*.qty' => ['required', 'integer', 'min:1'],""",
            "Валидация",
        ),
        (
            "After today date",
            "published_at required date after:today.",
            """'published_at' => ['required', 'date', 'after:today'],""",
            "Валидация",
        ),
        (
            "Custom messages email",
            "messages email.required Email is required.",
            """public function messages(): array
{
    return ['email.required' => 'Email is required'];
}""",
            "Валидация",
        ),
    ]
    specs.extend(validation)

    auth = [
        (
            "Gate define manage-settings",
            "Gate define manage-settings user is_admin.",
            """Gate::define('manage-settings', fn (User $user) => $user->is_admin);""",
            "Аутентификация",
        ),
        (
            "Policy viewAny",
            "PostPolicy viewAny: user not null.",
            """public function viewAny(?User $user): bool
{
    return $user !== null;
}""",
            "Аутентификация",
        ),
        (
            "Sanctum token create",
            "User createToken api-token abilities read.",
            """$token = $user->createToken('api-token', ['read']);""",
            "Аутентификация",
        ),
        (
            "Logout invalidate session",
            "Logout guard web invalidate session regenerate token.",
            """Auth::guard('web')->logout();
$request->session()->invalidate();
$request->session()->regenerateToken();""",
            "Аутентификация",
        ),
        (
            "Middleware can update post",
            "Route middleware can:update,post on PATCH.",
            """Route::patch('/posts/{post}', [PostController::class, 'update'])
    ->middleware('can:update,post');""",
            "Аутентификация",
        ),
    ]
    specs.extend(auth)

    queues = [
        (
            "Job unique order",
            "ProcessOrder implements ShouldBeUnique uniqueId order id.",
            """public function uniqueId(): string
{
    return (string) $this->order->id;
}""",
            "Очереди",
        ),
        (
            "Job tries backoff",
            "public $tries=3; public function backoff(){ return [10,30,60]; }",
            """public int $tries = 3;

public function backoff(): array
{
    return [10, 30, 60];
}""",
            "Очереди",
        ),
        (
            "Chain jobs",
            "Bus chain ReleasePodcast then SendNotification dispatch.",
            """Bus::chain([
    new ReleasePodcast($podcast),
    new SendPodcastNotification($podcast),
])->dispatch();""",
            "Очереди",
        ),
        (
            "Batch jobs",
            "Bus batch import jobs name Imports allowFailures.",
            """Bus::batch($jobs)
    ->name('Imports')
    ->allowFailures()
    ->dispatch();""",
            "Очереди",
        ),
        (
            "dispatch afterResponse",
            "SendEmail dispatch afterResponse closure.",
            """SendEmail::dispatch($user)->afterResponse();""",
            "Очереди",
        ),
    ]
    specs.extend(queues)

    events = [
        (
            "Listener handle OrderShipped",
            "Listener SendShipmentNotification handle logs order id.",
            """public function handle(OrderShipped $event): void
{
    logger('Shipped order '.$event->order->id);
}""",
            "События",
        ),
        (
            "Observer creating Post",
            "PostObserver creating set user_id auth id.",
            """public function creating(Post $post): void
{
    $post->user_id ??= auth()->id();
}""",
            "События",
        ),
        (
            "Event Subscriber",
            "Subscriber subscribe maps OrderShipped to onOrderShipped.",
            """public function subscribe(Dispatcher $events): array
{
    return [OrderShipped::class => 'onOrderShipped'];
}""",
            "События",
        ),
        (
            "Queued listener",
            "Listener implements ShouldQueue for async handle.",
            """class SendShipmentNotification implements ShouldQueue
{
    public function handle(OrderShipped $event): void { /* ... */ }
}""",
            "События",
        ),
    ]
    specs.extend(events)

    testing = [
        (
            "Test assertForbidden",
            "Guest GET /dashboard assertForbidden.",
            """public function test_guest_cannot_view_dashboard(): void
{
    $this->get('/dashboard')->assertForbidden();
}""",
            "Тестирование",
        ),
        (
            "Mail fake assertSent",
            "Mail fake; action; Mail assertSent OrderShipped Mailable.",
            """Mail::fake();
// ... trigger mail
Mail::assertSent(OrderShipped::class);""",
            "Тестирование",
        ),
        (
            "Queue fake assertPushed",
            "Queue fake; assert ProcessOrder pushed once.",
            """Queue::fake();
// ...
Queue::assertPushed(ProcessOrder::class, 1);""",
            "Тестирование",
        ),
        (
            "Http fake external API",
            "Http fake github returns json; test service uses fake.",
            """Http::fake([
    'api.github.com/*' => Http::response(['ok' => true], 200),
]);""",
            "Тестирование",
        ),
        (
            "assertJsonValidationErrors",
            "POST invalid assertSessionHasErrors or assertJsonValidationErrors.",
            """$response = $this->postJson('/api/posts', []);
$response->assertJsonValidationErrors(['title']);""",
            "Тестирование",
        ),
    ]
    specs.extend(testing)

    api = [
        (
            "Sanctum auth route",
            "Route middleware auth:sanctum GET /api/user returns request user.",
            """Route::middleware('auth:sanctum')->get('/user', fn (Request $request) => $request->user());""",
            "API",
        ),
        (
            "Resource with whenLoaded",
            "PostResource user UserResource whenLoaded user.",
            """'user' => UserResource::make($this->whenLoaded('user')),""",
            "API",
        ),
        (
            "API paginate meta",
            "return PostResource collection Post paginate with query.",
            """return PostResource::collection(
    Post::query()->latest()->paginate(20)
);""",
            "API",
        ),
        (
            "Token ability middleware",
            "CheckScopes middleware or token can ability.",
            """if (! $request->user()->tokenCan('server:update')) {
    abort(403);
}""",
            "API",
        ),
    ]
    specs.extend(api)

    container = [
        (
            "Contextual binding Report",
            "When ReportController needs ReportGenerator bind PdfReportGenerator.",
            """$this->app->when(ReportController::class)
    ->needs(ReportGenerator::class)
    ->give(PdfReportGenerator::class);""",
            "Service Container",
        ),
        (
            "Instance binding config",
            "App instance custom.stripe with StripeClient.",
            """$this->app->instance('custom.stripe', new StripeClient(config('services.stripe.secret')));""",
            "Service Container",
        ),
        (
            "Deferred provider",
            "Provider implements DeferrableProvider provides returns Repository.",
            """public function provides(): array
{
    return [PostRepositoryInterface::class];
}""",
            "Service Container",
        ),
    ]
    specs.extend(container)

    collections = [
        (
            "groupBy role",
            "collect users groupBy role map names.",
            """$byRole = collect($users)->groupBy('role')->map->pluck('name');""",
            "Collections",
        ),
        (
            "LazyCollection file lines",
            "LazyCollection make read file lines filter empty.",
            """LazyCollection::make(function () {
    $handle = fopen($path, 'r');
    while (($line = fgets($handle)) !== false) {
        yield trim($line);
    }
    fclose($handle);
})->filter();""",
            "Collections",
        ),
        (
            "data_get nested",
            "data_get $array user.profile.name default Guest.",
            """$name = data_get($payload, 'user.profile.name', 'Guest');""",
            "Collections",
        ),
        (
            "Str slug title",
            "Str slug title language en separator dash.",
            """$slug = Str::slug($title, '-', 'en');""",
            "Collections",
        ),
        (
            "Collection macro",
            "Collection macro toSortedByName sortBy name values.",
            """Collection::macro('toSortedByName', function () {
    return $this->sortBy('name')->values();
});""",
            "Collections",
        ),
    ]
    specs.extend(collections)

    # Expand with numbered variants for volume (same pattern, different index in title)
    templates = [
        (
            "Query scope combo {n}",
            "Post published() whereDate created_at today get — напиши chain scope + whereDate.",
            """$posts = Post::published()->whereDate('created_at', today())->get();""",
            "Eloquent",
        ),
        (
            "Route name helper {n}",
            "redirect()->route('posts.index') with status flash.",
            """return redirect()->route('posts.index')->with('status', 'Saved');""",
            "Роутинг",
        ),
        (
            "Validate inline {n}",
            "Controller validate title required body sometimes nullable.",
            """$validated = $request->validate([
    'title' => 'required|string',
    'body' => 'nullable|string',
]);""",
            "Валидация",
        ),
    ]
    for n in range(1, 16):
        for title_tpl, assignment, reference, topic in templates:
            specs.append(
                (
                    title_tpl.format(n=n),
                    assignment + f" (вариант {n}).",
                    reference,
                    topic,
                )
            )

    return _cards(specs)
