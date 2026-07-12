#!/usr/bin/env python3
"""Generate Laravel Live-coding deck."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from live_coding_card import live as _live
from live_coding_topics import assign_topics


def live(*args, **kwargs):
    kwargs.setdefault("lang", "php")
    return _live(*args, **kwargs)


def build_cards() -> list[dict]:
    return [
        live(
            "Route GET /health",
            'Зарегистрируй GET /health, возвращающий JSON {"status":"ok"}.',
            """Route::get('/health', function () {
    return response()->json(['status' => 'ok']);
});""",
            topic="Роутинг",
        ),
        live(
            "Named route profile",
            "GET /profile с именем route profile.show, closure возвращает 'Profile'.",
            """Route::get('/profile', fn () => 'Profile')->name('profile.show');""",
            topic="Роутинг",
        ),
        live(
            "Resource controller routes",
            "Route::resource posts PostController — только объявление маршрута.",
            """Route::resource('posts', PostController::class);""",
            topic="Роутинг",
        ),
        live(
            "PostController index",
            "Метод index(): все Post с eager load user, view posts.index.",
            """public function index()
{
    $posts = Post::with('user')->get();
    return view('posts.index', compact('posts'));
}""",
            topic="Контроллеры",
        ),
        live(
            "StorePostRequest rules",
            "Form Request: title required max 255, body required string.",
            """public function rules(): array
{
    return [
        'title' => ['required', 'string', 'max:255'],
        'body' => ['required', 'string'],
    ];
}""",
            topic="Контроллеры",
        ),
        live(
            "Post model fillable",
            "Model Post: fillable title, body, user_id; belongsTo User.",
            """class Post extends Model
{
    protected $fillable = ['title', 'body', 'user_id'];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}""",
            topic="Eloquent",
        ),
        live(
            "Scope published",
            "Local scope published() where published = true на Post.",
            """public function scopePublished($query)
{
    return $query->where('published', true);
}""",
            topic="Eloquent",
        ),
        live(
            "Migration posts",
            "Migration create posts: id, foreignId user_id constrained, title, timestamps.",
            """Schema::create('posts', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->cascadeOnDelete();
    $table->string('title');
    $table->timestamps();
});""",
            topic="Миграции",
        ),
        live(
            "Factory User",
            "UserFactory: name faker, email unique, password Hash::make('password').",
            """public function definition(): array
{
    return [
        'name' => fake()->name(),
        'email' => fake()->unique()->safeEmail(),
        'password' => Hash::make('password'),
    ];
}""",
            topic="Миграции",
        ),
        live(
            "Blade layout yield",
            "Layout app.blade.php: html skeleton + @yield('content').",
            """<!DOCTYPE html>
<html>
<head><title>App</title></head>
<body>
    @yield('content')
</body>
</html>""",
            topic="Blade",
        ),
        live(
            "Middleware EnsureAdmin",
            "Middleware: если !auth()->user()?->is_admin — abort 403, иначе $next.",
            """public function handle(Request $request, Closure $next)
{
    if (! $request->user()?->is_admin) {
        abort(403);
    }
    return $next($request);
}""",
            topic="Middleware",
        ),
        live(
            "Custom rule Uppercase",
            "ValidationRule: value must be strtoupper($value) === $value.",
            """public function validate(string $attribute, mixed $value, Closure $fail): void
{
    if (! is_string($value) || strtoupper($value) !== $value) {
        $fail('The :attribute must be uppercase.');
    }
}""",
            topic="Валидация",
        ),
        live(
            "PostPolicy update",
            "Policy update: user id === post user_id.",
            """public function update(User $user, Post $post): bool
{
    return $user->id === $post->user_id;
}""",
            topic="Аутентификация",
        ),
        live(
            "Job SendNewsletter",
            "Job ShouldQueue: handle() логирует 'Newsletter sent'.",
            """class SendNewsletter implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function handle(): void
    {
        logger('Newsletter sent');
    }
}""",
            topic="Очереди",
        ),
        live(
            "Event OrderShipped",
            "Event OrderShipped с public Order $order и Dispatchable.",
            """class OrderShipped
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public function __construct(public Order $order)
    {
    }
}""",
            topic="События",
        ),
        live(
            "Feature test posts",
            "Test: actingAs user POST /posts valid data assertRedirect assertDatabaseHas.",
            """public function test_user_can_create_post(): void
{
    $user = User::factory()->create();
    $response = $this->actingAs($user)->post('/posts', [
        'title' => 'Hello',
        'body' => 'World',
    ]);
    $response->assertRedirect();
    $this->assertDatabaseHas('posts', ['title' => 'Hello']);
}""",
            topic="Тестирование",
        ),
        live(
            "PostResource",
            "API Resource: id, title, created_at ISO string.",
            """public function toArray(Request $request): array
{
    return [
        'id' => $this->id,
        'title' => $this->title,
        'created_at' => $this->created_at?->toIso8601String(),
    ];
}""",
            topic="API",
        ),
        live(
            "Bind repository",
            "ServiceProvider register: singleton PostRepositoryInterface -> EloquentPostRepository.",
            """public function register(): void
{
    $this->app->singleton(
        PostRepositoryInterface::class,
        EloquentPostRepository::class,
    );
}""",
            topic="Service Container",
        ),
        live(
            "Collect active emails",
            "Функция activeEmails(array $users): array — collect filter active pluck email.",
            """function activeEmails(array $users): array
{
    return collect($users)
        ->filter(fn ($u) => $u->active)
        ->pluck('email')
        ->all();
}""",
            topic="Collections",
        ),
        live(
            "Artisan command inspire",
            "Command signature inspire — handle outputs quote to console.",
            """protected $signature = 'inspire';

public function handle(): int
{
    $this->comment('Simplicity is the ultimate sophistication.');
    return self::SUCCESS;
}""",
            topic="Основы",
        ),
    ]


def main() -> None:
    from laravel_live_bank import extra_cards

    cards = assign_topics(build_cards() + extra_cards(), "laravel")
    counts = Counter(c.get("topic") for c in cards)
    if len(counts) < 8:
        raise SystemExit(f"Too few topics: {counts}")
    deck = {"name": "Laravel Live-coding", "language": "php", "cards": cards}
    out = Path(__file__).with_name("laravel-live-coding.json")
    out.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(cards)} live_code cards -> {out}")
    print("Topics:", dict(counts))


if __name__ == "__main__":
    main()
