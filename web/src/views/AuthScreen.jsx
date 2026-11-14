import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, Brain, Code2, Globe, KeyRound, Mic, Sigma, User } from "lucide-react";
import { api, DEFAULT_SERVER, getServer, setServer, setToken } from "../lib/api";
import { isDesktop } from "../lib/desktop";
import { Logo, Spinner } from "../components/ui";

const FEATURES = [
  { icon: Brain, title: "ИИ проверяет смысл", text: "Ollama оценивает ответ своими словами и задаёт уточняющие вопросы" },
  { icon: Code2, title: "Live-coding", text: "Редактор Monaco с подсветкой для PHP, Python, Go, TypeScript" },
  { icon: Sigma, title: "Формулы", text: "MathLive и KaTeX для высшей математики" },
  { icon: Mic, title: "Ответ голосом", text: "Распознавание речи через Whisper" },
];

export default function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [status, setStatus] = useState(null);
  const [form, setForm] = useState({ username: "", password: "", display_name: "", server: getServer() || DEFAULT_SERVER });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadStatus = () =>
    api("/api/auth/status")
      .then((s) => {
        setStatus(s);
        if (!s.has_users) setMode("register");
      })
      .catch((e) => setStatus({ error: e.message }));

  useEffect(() => {
    loadStatus();
  }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isDesktop) setServer(form.server);
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body = { username: form.username.trim(), password: form.password, client: isDesktop ? "desktop" : "web" };
      if (mode === "register") body.display_name = form.display_name.trim();
      const r = await api(path, { method: "POST", body });
      setToken(r.token);
      onAuth(r.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const canRegister = !status || status.registration_open;

  return (
    <div className="flex h-full w-full overflow-y-auto">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-5 py-10 lg:grid-cols-[1.1fr_1fr] lg:px-10">
        {/* Промо */}
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="hidden lg:block"
        >
          <div className="mb-8 flex items-center gap-3">
            <Logo size={44} />
            <div>
              <div className="text-2xl font-extrabold tracking-tight">AI Anki</div>
              <div className="text-sm text-zinc-400">Интервальные повторения с ИИ-экзаменатором</div>
            </div>
          </div>
          <h1 className="mb-5 text-5xl font-extrabold leading-[1.05] tracking-tight">
            Учите так, будто
            <br />
            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-rose-400 bg-clip-text text-transparent">
              вас спрашивает ментор
            </span>
          </h1>
          <p className="mb-10 max-w-md text-zinc-400">
            Отвечайте своими словами, пишите код и формулы — модель оценит, подскажет и вернёт карточку в нужный момент.
          </p>
          <div className="grid max-w-lg grid-cols-2 gap-3">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 + i * 0.08 }}
                className="glass p-4"
              >
                <f.icon className="mb-2 h-5 w-5 text-violet-300" />
                <div className="text-sm font-semibold">{f.title}</div>
                <div className="mt-1 text-xs leading-relaxed text-zinc-400">{f.text}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Форма */}
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="glass mx-auto w-full max-w-md p-7 sm:p-8"
        >
          <div className="mb-6 flex items-center gap-3 lg:hidden">
            <Logo />
            <div className="text-xl font-extrabold">AI Anki</div>
          </div>
          <div className="relative mb-6 grid grid-cols-2 rounded-xl bg-ink-900/80 p-1">
            {["login", "register"].map((m) => (
              <button
                key={m}
                type="button"
                disabled={m === "register" && !canRegister}
                onClick={() => {
                  setMode(m);
                  setError("");
                }}
                className={`relative z-10 py-2 text-sm font-semibold transition-colors disabled:opacity-40 ${mode === m ? "text-white" : "text-zinc-400 hover:text-zinc-200"}`}
              >
                {mode === m && (
                  <motion.span
                    layoutId="auth-tab"
                    className="absolute inset-0 -z-10 rounded-lg bg-gradient-to-r from-violet-600/80 to-rose-500/80"
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  />
                )}
                {m === "login" ? "Вход" : "Регистрация"}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.form
              key={mode}
              onSubmit={submit}
              initial={{ opacity: 0, x: mode === "login" ? -16 : 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mode === "login" ? 16 : -16 }}
              transition={{ duration: 0.22 }}
              className="space-y-4"
            >
              <div>
                <h2 className="text-xl font-bold">{mode === "login" ? "С возвращением" : "Создать аккаунт"}</h2>
                <p className="mt-1 text-sm text-zinc-400">
                  {mode === "login"
                    ? "Прогресс синхронизируется между браузером и приложением."
                    : status && !status.has_users
                      ? "Первый аккаунт станет администратором и получит существующий прогресс."
                      : "У каждого пользователя своя статистика и настройки."}
                </p>
              </div>

              {isDesktop && (
                <div>
                  <label className="label" htmlFor="server">Сервер</label>
                  <div className="relative">
                    <Globe className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
                    <input id="server" className="input pl-9" value={form.server} onChange={set("server")} onBlur={() => { setServer(form.server); loadStatus(); }} placeholder={DEFAULT_SERVER} />
                  </div>
                </div>
              )}

              {mode === "register" && (
                <div>
                  <label className="label" htmlFor="display_name">Имя</label>
                  <input id="display_name" className="input" value={form.display_name} onChange={set("display_name")} placeholder="Как к вам обращаться" autoComplete="name" />
                </div>
              )}
              <div>
                <label className="label" htmlFor="username">Логин</label>
                <div className="relative">
                  <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
                  <input id="username" className="input pl-9" value={form.username} onChange={set("username")} autoComplete="username" required minLength={3} autoFocus />
                </div>
              </div>
              <div>
                <label className="label" htmlFor="password">Пароль</label>
                <div className="relative">
                  <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
                  <input id="password" type="password" className="input pl-9" value={form.password} onChange={set("password")} autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={mode === "register" ? 6 : 1} />
                </div>
              </div>

              <AnimatePresence>
                {(error || status?.error) && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3.5 py-2.5 text-sm text-rose-200"
                  >
                    {error || status.error}
                  </motion.div>
                )}
              </AnimatePresence>

              <motion.button whileTap={{ scale: 0.98 }} type="submit" disabled={busy} className="btn-primary w-full py-3">
                {busy ? <Spinner /> : <>{mode === "login" ? "Войти" : "Зарегистрироваться"} <ArrowRight className="h-4 w-4" /></>}
              </motion.button>
            </motion.form>
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
