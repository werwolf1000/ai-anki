import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Activity, KeyRound, LogOut, Monitor, Save, Server, SlidersHorizontal, UserRound } from "lucide-react";
import { api, getServer } from "../lib/api";
import { isDesktop } from "../lib/desktop";
import { Spinner, useToast } from "../components/ui";

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
      const body = { code_editor_theme: form.code_editor_theme, asr_language: form.asr_language };
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
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="glass p-5 sm:p-6">
      <h2 className="mb-4 flex items-center gap-2 font-semibold">
        <Icon className="h-4 w-4 text-violet-300" /> {title}
      </h2>
      {children}
    </motion.section>
  );
}
