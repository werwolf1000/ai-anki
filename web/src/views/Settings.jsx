import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Activity, Database, DownloadCloud, KeyRound, LogOut, Monitor, Save, Server, SlidersHorizontal, Sparkles, Square, UserRound } from "lucide-react";
import { api, getServer } from "../lib/api";
import { isDesktop } from "../lib/desktop";
import { Spinner, useToast } from "../components/ui";
import VideoLibrary from "../components/VideoLibrary";
import BookDecksPanel from "../components/BookDecksPanel";
import LlmPanel from "../components/LlmPanel";
import { nextDelay, setIfChanged } from "../lib/poll";

const STUDY_FIELDS = [
  { key: "session_limit", label: "Карточек за сессию", min: 1, max: 50 },
  { key: "pass_score", label: "Порог зачёта", min: 50, max: 100 },
  { key: "max_follow_ups", label: "Уточнений / правок", min: 0, max: 5 },
  { key: "auto_advance_sec", label: "Автопереход, с (0 — выкл.)", min: 0, max: 10 },
];

const ADMIN_FIELDS = [
  { key: "ollama_url", label: "Ollama URL" },
  { key: "model", label: "Модель" },
  { key: "api_key", label: "API-ключ", type: "password" },
  { key: "timeout", label: "Таймаут, с", type: "number" },
  { key: "asr_url", label: "ASR URL (Whisper)" },
  { key: "asr_user", label: "ASR логин" },
  { key: "asr_password", label: "ASR пароль", type: "password" },
  { key: "embed_model", label: "Модель эмбеддингов (учебник)" },
  { key: "textbook_model", label: "Модель статей учебника (пусто — основная)" },
  { key: "video_min_sim", label: "Порог сходства видео с уроком (пусто — 0.45)" },
  { key: "video_language", label: "Язык видео для Whisper (пусто — авто, ru, en…)" },
];

export default function Settings({ user, setUser, config, setConfig, onLogout }) {
  const toast = useToast();
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [profile, setProfile] = useState(user.display_name || "");
  const [pw, setPw] = useState({ old_password: "", new_password: "" });

  useEffect(() => {
    if (config) setForm({ ...config });
  }, [config]);

  const set = (k, num) => (e) => setForm((f) => ({ ...f, [k]: num ? Number(e.target.value) : e.target.value }));

  async function save() {
    setSaving(true);
    try {
      const body = { code_editor_theme: form.code_editor_theme, asr_language: form.asr_language, asr_correct: form.asr_correct !== false };
      STUDY_FIELDS.forEach((f) => (body[f.key] = Math.max(f.min, Math.min(f.max, Number(form[f.key]) || 0))));
      if (user.is_admin) ADMIN_FIELDS.forEach((f) => (body[f.key] = f.type === "number" ? Number(form[f.key]) : String(form[f.key] ?? "").trim()));
      const r = await api("/api/config", { method: "POST", body });
      setConfig(r.config);
      toast("Настройки сохранены", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSaving(false);
    }
  }

  async function testOllama() {
    setTesting(true);
    try {
      const r = await api("/api/ollama/test", { method: "POST" });
      toast(r.detail, r.ok ? "success" : "error");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setTesting(false);
    }
  }

  async function saveProfile() {
    try {
      const r = await api("/api/account/profile", { method: "POST", body: { display_name: profile } });
      setUser(r.user);
      toast("Профиль обновлён", "success");
    } catch (e) {
      toast(e.message, "error");
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    try {
      await api("/api/account/password", { method: "POST", body: pw });
      setPw({ old_password: "", new_password: "" });
      toast("Пароль изменён", "success");
    } catch (err) {
      toast(err.message, "error");
    }
  }

  if (!form) return <div className="flex justify-center py-20"><Spinner className="h-6 w-6" /></div>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-extrabold tracking-tight">Настройки</h1>
        <p className="text-sm text-zinc-400">Параметры обучения — личные для вашего аккаунта и синхронизируются с приложением.</p>
      </header>

      <Section icon={SlidersHorizontal} title="Обучение" delay={0}>
        <div className="grid gap-4 sm:grid-cols-2">
          {STUDY_FIELDS.map((f) => (
            <div key={f.key}>
              <label className="label" htmlFor={f.key}>{f.label}</label>
              <div className="flex items-center gap-3">
                <input id={f.key} type="range" min={f.min} max={f.max} value={form[f.key] ?? f.min} onChange={set(f.key, true)} className="flex-1 accent-violet-500" />
                <input type="number" min={f.min} max={f.max} value={form[f.key] ?? f.min} onChange={set(f.key, true)} className="input w-20 text-center font-mono" />
              </div>
            </div>
          ))}
          <div>
            <label className="label" htmlFor="theme">Тема редактора кода</label>
            <select id="theme" className="input" value={form.code_editor_theme} onChange={set("code_editor_theme")}>
              <option value="dark">Тёмная</option>
              <option value="light">Светлая</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="asr_language">Язык распознавания речи</label>
            <input id="asr_language" className="input" value={form.asr_language || ""} onChange={set("asr_language")} placeholder="ru" />
          </div>
          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 sm:col-span-2">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 accent-violet-500"
              checked={form.asr_correct !== false}
              onChange={(e) => setForm((f) => ({ ...f, asr_correct: e.target.checked }))}
            />
            <span>
              <span className="block text-sm font-medium text-zinc-200">Исправлять распознанную речь с помощью ИИ</span>
              <span className="block text-xs text-zinc-500">
                Модель поправит неверно услышанные термины («эсквель» → SQL, «база донных» → база данных) и пунктуацию, не меняя смысл ответа. Добавляет несколько секунд.
              </span>
            </span>
          </label>
        </div>
      </Section>

      {user.is_admin && (
        <Section icon={Server} title="Сервер (только администратор)" delay={0.05}>
          <p className="mb-4 text-xs text-zinc-500">Общие для всех пользователей: модель, которая проверяет ответы, и распознавание речи.</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {ADMIN_FIELDS.map((f) => (
              <div key={f.key}>
                <label className="label" htmlFor={f.key}>{f.label}</label>
                <input id={f.key} type={f.type || "text"} className="input" value={form[f.key] ?? ""} onChange={set(f.key, f.type === "number")} autoComplete="off" />
              </div>
            ))}
          </div>
          <button className="btn-ghost mt-4" onClick={testOllama} disabled={testing}>
            {testing ? <Spinner /> : <Activity className="h-4 w-4" />} Проверить Ollama
          </button>
        </Section>
      )}

      <div className="sticky bottom-24 z-10 flex justify-end md:bottom-4">
        <motion.button whileTap={{ scale: 0.97 }} className="btn-primary px-6" onClick={save} disabled={saving}>
          {saving ? <Spinner /> : <Save className="h-4 w-4" />} Сохранить
        </motion.button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section icon={UserRound} title="Профиль" delay={0.1}>
          <div className="mb-3 text-sm text-zinc-400">Логин: <span className="font-mono text-zinc-200">{user.username}</span></div>
          <label className="label" htmlFor="profile">Отображаемое имя</label>
          <div className="flex gap-2">
            <input id="profile" className="input" value={profile} onChange={(e) => setProfile(e.target.value)} />
            <button className="btn-ghost" onClick={saveProfile}>Сохранить</button>
          </div>
          <button className="btn-ghost mt-5 text-rose-200 hover:bg-rose-500/10" onClick={onLogout}>
            <LogOut className="h-4 w-4" /> Выйти из аккаунта
          </button>
        </Section>

        <Section icon={KeyRound} title="Смена пароля" delay={0.15}>
          <form onSubmit={changePassword} className="space-y-3">
            <input type="password" className="input" placeholder="Текущий пароль" autoComplete="current-password" value={pw.old_password} onChange={(e) => setPw((p) => ({ ...p, old_password: e.target.value }))} required />
            <input type="password" className="input" placeholder="Новый пароль (от 6 символов)" autoComplete="new-password" minLength={6} value={pw.new_password} onChange={(e) => setPw((p) => ({ ...p, new_password: e.target.value }))} required />
            <button className="btn-ghost" type="submit">Изменить пароль</button>
          </form>
        </Section>
      </div>

      <LlmPanel user={user} />
      <KnowledgePanel isAdmin={user.is_admin} />
      {user.is_admin && <BookDecksPanel />}
      {user.is_admin && <VideoLibrary />}

      {isDesktop && (
        <Section icon={Monitor} title="Приложение" delay={0.2}>
          <div className="text-sm text-zinc-400">
            Подключено к серверу <span className="font-mono text-zinc-200">{getServer()}</span>. Чтобы сменить сервер, выйдите из аккаунта.
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({ icon: Icon, title, children, delay }) {
  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="glass cv-auto p-5 sm:p-6">
      <h2 className="mb-4 flex items-center gap-2 font-semibold">
        <Icon className="h-4 w-4 text-violet-300" /> {title}
      </h2>
      {children}
    </motion.section>
  );
}

function KnowledgePanel({ isAdmin }) {
  const toast = useToast();
  const [st, setSt] = useState(null);

  useEffect(() => {
    let timer;
    let alive = true;
    const load = () => {
      if (document.hidden) {
        timer = setTimeout(load, 10000);
        return;
      }
      api("/api/knowledge/status")
        .then((r) => {
          if (!alive) return;
          setIfChanged(setSt, r);
          timer = setTimeout(load, nextDelay(r.job.running || r.articles?.running ? 3000 : 20000));
        })
        .catch(() => {});
    };
    load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, []);

  async function rebuild(download, sourceId = "all") {
    try {
      await api("/api/knowledge/rebuild", { method: "POST", body: { source_id: sourceId, download } });
      toast(download ? "Индексация запущена" : "Векторизация продолжена", "success");
      const r = await api("/api/knowledge/status");
      setSt(r);
    } catch (e) {
      toast(e.message, "error");
    }
  }

  async function generateArticles() {
    try {
      const r = await api("/api/textbook/generate-all", { method: "POST", body: {} });
      toast(`В очереди тем: ${r.queued}`, "success");
      setSt(await api("/api/knowledge/status"));
    } catch (e) {
      toast(e.message, "error");
    }
  }

  async function stopArticles() {
    await api("/api/textbook/generate-all/stop", { method: "POST" }).catch(() => {});
    toast("Остановка после текущей темы", "success");
  }

  if (!st) return null;
  const job = st.job;
  return (
    <Section icon={Database} title="База знаний учебника (RAG)" delay={0.18}>
      <div className="space-y-4">
        {st.sources.map((s) => {
          const pct = s.chunks ? s.embedded / s.chunks : 0;
          return (
            <div key={s.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <a href={s.url} target="_blank" rel="noreferrer" className="font-semibold hover:text-violet-200">{s.title}</a>
                  <div className="mt-0.5 text-xs text-zinc-500">{s.description}</div>
                </div>
                <div className="flex items-start gap-3 text-right text-xs text-zinc-400">
                  <div>
                  {s.chunks ? (
                    <>
                      <div><b className="text-zinc-100">{s.pages}</b> страниц · <b className="text-zinc-100">{s.chunks}</b> фрагментов</div>
                      <div>векторов: {s.embedded}/{s.chunks}</div>
                    </>
                  ) : (
                    <span className="text-amber-300">не загружен</span>
                  )}
                  </div>
                  {isAdmin && (
                    <button
                      className="rounded-lg p-1.5 text-zinc-400 hover:bg-white/[0.06] hover:text-violet-200 disabled:opacity-40"
                      title={s.chunks ? "Обновить этот источник" : "Скачать этот источник"}
                      disabled={job.running}
                      onClick={() => rebuild(true, s.id)}
                    >
                      {job.running && job.source === s.id ? <Spinner /> : <DownloadCloud className="h-4 w-4" />}
                    </button>
                  )}
                </div>
              </div>
              {s.chunks > 0 && (
                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div className="h-full bg-gradient-to-r from-violet-500 to-rose-500" animate={{ width: `${pct * 100}%` }} />
                </div>
              )}
            </div>
          );
        })}

        {(job.running || job.error || job.log.length > 0) && (
          <div className="rounded-xl border border-white/[0.06] bg-ink-900/70 p-3 font-mono text-[11px] leading-relaxed text-zinc-400">
            {job.log.map((l, i) => <div key={i}>{l}</div>)}
            {job.running && job.total > 0 && <div className="text-violet-300">{job.stage}: {job.done}/{job.total}</div>}
            {job.error && <div className="text-rose-300">{job.error}</div>}
          </div>
        )}

        {st.articles && (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="font-semibold">Статьи учебника</div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  Готово <b className="text-zinc-200">{st.articles.topics_written}</b> из <b className="text-zinc-200">{st.articles.topics_total}</b> тем всех колод.
                  {" "}Пишутся моделью по базе знаний и карточкам; лучше запускать после загрузки источников.
                </div>
              </div>
              {isAdmin && (st.articles.running ? (
                <button className="btn-ghost" onClick={stopArticles}><Square className="h-4 w-4" /> Остановить</button>
              ) : (
                <button className="btn-ghost" disabled={st.articles.topics_written >= st.articles.topics_total} onClick={generateArticles}>
                  <Sparkles className="h-4 w-4" /> Написать недостающие
                </button>
              ))}
            </div>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
              <motion.div
                className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                animate={{ width: `${st.articles.topics_total ? (st.articles.topics_written / st.articles.topics_total) * 100 : 0}%` }}
              />
            </div>
            {(st.articles.running || st.articles.log.length > 0) && (
              <div className="mt-3 font-mono text-[11px] leading-relaxed text-zinc-400">
                {st.articles.running && (
                  <div className="text-emerald-300">
                    {st.articles.done}/{st.articles.total} · {st.articles.current}
                  </div>
                )}
                {st.articles.log.map((l, i) => <div key={i}>{l}</div>)}
                {st.articles.error && <div className="text-rose-300">{st.articles.error}</div>}
              </div>
            )}
          </div>
        )}

        <div className="text-xs text-zinc-500">
          Эмбеддинги: <span className="text-zinc-300">{st.embed_model}</span> · статьи: <span className="text-zinc-300">{st.textbook_model}</span>
        </div>

        {isAdmin && (
          <div className="flex flex-wrap gap-2">
            <button className="btn-ghost" disabled={job.running} onClick={() => rebuild(true)}>
              {job.running ? <Spinner /> : <DownloadCloud className="h-4 w-4" />} Скачать и проиндексировать всё
            </button>
            <button className="btn-ghost" disabled={job.running} onClick={() => rebuild(false)}>
              <Activity className="h-4 w-4" /> Довекторизовать
            </button>
          </div>
        )}
      </div>
    </Section>
  );
}
