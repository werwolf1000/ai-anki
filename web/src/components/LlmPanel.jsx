import { useCallback, useEffect, useState } from "react";
import { motion } from "motion/react";
import { Bot, CheckCircle2, Cpu, Laptop, Pencil, Plug, Plus, Trash2, XCircle } from "lucide-react";
import { api } from "../lib/api";
import { desktop, isDesktop } from "../lib/desktop";
import { Spinner, useToast } from "./ui";
import { setIfChanged } from "../lib/poll";

/** Модели ИИ: свой выбор для проверки ответов, локальная модель через приложение, провайдеры (админ). */
export default function LlmPanel({ user }) {
  const toast = useToast();
  const [st, setSt] = useState(null);
  const [form, setForm] = useState(null); // правка/добавление провайдера
  const [tests, setTests] = useState({}); // id → результат проверки

  const load = useCallback(() => api("/api/llm").then((r) => setIfChanged(setSt, r)).catch((e) => toast(e.message, "error")), [toast]);
  useEffect(() => {
    load();
    const t = setInterval(() => !document.hidden && load(), 15000); // статус локальных моделей (в скрытом окне — пауза)
    return () => clearInterval(t);
  }, [load]);

  async function select(body) {
    try {
      await api("/api/llm/select", { method: "POST", body });
      toast("Сохранено", "success");
      load();
    } catch (e) {
      toast(e.message, "error");
    }
  }

  async function test(provider, model = "") {
    setTests((t) => ({ ...t, [provider]: { busy: true } }));
    const r = await api("/api/llm/test", { method: "POST", body: { provider, model } }).catch((e) => ({ ok: false, error: e.message }));
    setTests((t) => ({ ...t, [provider]: r }));
  }

  async function remove(p) {
    if (!confirm(`Удалить «${p.name}»?`)) return;
    await api(`/api/llm/providers/${p.id}`, { method: "DELETE" }).catch((e) => toast(e.message, "error"));
    load();
  }

  if (!st) return null;
  const options = [
    ...st.providers.map((p) => ({ id: p.id, label: `${p.name}${p.model ? ` · ${p.model}` : ""}` })),
    ...(st.bridges || []).map((b) => ({ id: b.id, label: `Локальная модель: ${b.user}${b.info?.model ? ` · ${b.info.model}` : ""}` })),
  ];
  const checkName = options.find((o) => o.id === st.check)?.label || st.check;

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.17 }} className="glass p-5 sm:p-6">
      <h2 className="mb-1 flex items-center gap-2 font-semibold">
        <Bot className="h-4 w-4 text-violet-300" /> Модели ИИ
      </h2>
      <p className="mb-4 text-xs leading-relaxed text-zinc-500">
        Помимо Ollama можно подключить DeepSeek, Алису AI (YandexGPT), любой OpenAI-совместимый сервер и локальную модель
        на своём компьютере (например, Strata) — через десктоп-приложение.
      </p>

      {/* своя модель для проверки ответов */}
      <div className="mb-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
        <div className="mb-2 text-sm font-semibold">Проверка моих ответов в занятиях</div>
        <select className="input text-sm" value={st.my} onChange={(e) => select({ my: e.target.value })}>
          <option value="">Как на сервере — {checkName}</option>
          {st.providers.map((p) => (
            <option key={p.id} value={p.id}>{p.name}{p.model ? ` · ${p.model}` : ""}</option>
          ))}
          <option value="bridge:me">Моя локальная модель (через десктоп-приложение){st.bridge.online ? ` · ${st.bridge.info?.model || ""}` : " — не подключена"}</option>
        </select>
        <div className="mt-1.5 text-[11px] text-zinc-500">
          Экзамены и собеседования профессий всегда проверяет модель сервера — чтобы сертификаты были сопоставимы.
        </div>
      </div>

      {isDesktop && desktop?.bridge && <LocalModelCard online={st.bridge.online} onChanged={load} />}

      {user.is_admin && (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="label">Проверка ответов, подсказки, экзамены</span>
              <select className="input text-sm" value={st.check} onChange={(e) => select({ check: e.target.value })}>
                {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
              </select>
            </label>
            <label className="block">
              <span className="label">Учебник: статьи и генерация карточек</span>
              <select className="input text-sm" value={st.textbook} onChange={(e) => select({ textbook: e.target.value })}>
                {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
              </select>
            </label>
          </div>
          {(st.check.startsWith("bridge:") || st.textbook.startsWith("bridge:")) && (
            <div className="rounded-lg border border-amber-500/25 bg-amber-500/[0.06] p-2.5 text-[11px] text-amber-200">
              Локальная модель работает, только пока на том компьютере открыто приложение AI Anki и запущена модель.
            </div>
          )}

          <div>
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm font-semibold">Подключения</div>
              <div className="flex flex-wrap gap-1.5">
                {st.presets.map((p) => (
                  <button key={p.preset} className="btn-ghost px-2.5 py-1 text-xs" onClick={() => setForm({ ...p, id: "", api_key: "", folder: "" })} title={p.hint}>
                    <Plus className="h-3 w-3" /> {p.name}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              {st.providers.map((p) => {
                const t = tests[p.id];
                return (
                  <div key={p.id} className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-xs">
                    <div className="flex flex-wrap items-center gap-2">
                      <Cpu className="h-3.5 w-3.5 text-zinc-500" />
                      <span className="font-semibold text-zinc-200">{p.name}</span>
                      <span className="text-zinc-500">{p.model || "—"}</span>
                      <span className="min-w-0 flex-1 truncate font-mono text-[10px] text-zinc-600">{p.base_url}</span>
                      {(st.check === p.id || st.textbook === p.id) && (
                        <span className="chip text-[10px]">{[st.check === p.id && "проверка", st.textbook === p.id && "учебник"].filter(Boolean).join(" · ")}</span>
                      )}
                      <button className="btn-ghost px-2 py-1 text-xs" onClick={() => test(p.id)} disabled={t?.busy}>
                        {t?.busy ? <Spinner className="h-3 w-3" /> : <Plug className="h-3 w-3" />} Проверить
                      </button>
                      {!p.builtin && (
                        <>
                          <button className="rounded p-1 text-zinc-500 hover:text-white" title="Изменить" onClick={() => setForm({ ...p, api_key: "" })}><Pencil className="h-3.5 w-3.5" /></button>
                          <button className="rounded p-1 text-zinc-500 hover:text-rose-300" title="Удалить" onClick={() => remove(p)}><Trash2 className="h-3.5 w-3.5" /></button>
                        </>
                      )}
                    </div>
                    {t && !t.busy && <TestLine t={t} />}
                  </div>
                );
              })}
              {(st.bridges || []).map((b) => {
                const t = tests[b.id];
                return (
                  <div key={b.id} className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.04] px-3 py-2 text-xs">
                    <div className="flex flex-wrap items-center gap-2">
                      <Laptop className="h-3.5 w-3.5 text-emerald-300" />
                      <span className="font-semibold text-zinc-200">Локальная модель: {b.user}</span>
                      <span className="flex-1 text-zinc-500">{b.info?.model} · через приложение</span>
                      <button className="btn-ghost px-2 py-1 text-xs" onClick={() => test(b.id)} disabled={t?.busy}>
                        {t?.busy ? <Spinner className="h-3 w-3" /> : <Plug className="h-3 w-3" />} Проверить
                      </button>
                    </div>
                    {t && !t.busy && <TestLine t={t} />}
                  </div>
                );
              })}
            </div>
          </div>
          {form && <ProviderForm form={form} setForm={setForm} onSaved={() => { setForm(null); load(); }} />}
        </div>
      )}
    </motion.section>
  );
}

function TestLine({ t }) {
  return t.ok ? (
    <div className="mt-1 flex items-center gap-1.5 text-emerald-300">
      <CheckCircle2 className="h-3.5 w-3.5" /> «{t.text}» · {t.model} · {(t.ms / 1000).toFixed(1)} с
    </div>
  ) : (
    <div className="mt-1 flex items-start gap-1.5 text-rose-300">
      <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {t.error}
    </div>
  );
}

function ProviderForm({ form, setForm, onSaved }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [models, setModels] = useState(null);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const isYandex = /yandex/i.test(form.base_url);

  async function save() {
    setBusy(true);
    try {
      const r = await api("/api/llm/providers", {
        method: "POST",
        body: { id: form.id || "", name: form.name, type: "openai", base_url: form.base_url, api_key: form.api_key || null, model: form.model || "", folder: form.folder || "" },
      });
      toast("Подключение сохранено", "success");
      setForm((f) => ({ ...f, id: r.id }));
      onSaved();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function loadModels() {
    if (!form.id) return toast("Сначала сохраните подключение", "info");
    try {
      setModels((await api("/api/llm/models", { method: "POST", body: { provider: form.id } })).models);
    } catch (e) {
      toast(e.message, "error");
    }
  }

  return (
    <div className="rounded-xl border border-violet-500/25 bg-violet-500/[0.05] p-4 text-sm">
      <div className="mb-3 font-semibold">{form.id ? `Изменить: ${form.name}` : `Новое подключение: ${form.name}`}</div>
      {form.hint && <div className="mb-3 text-xs text-zinc-400">{form.hint}</div>}
      <div className="grid gap-3 sm:grid-cols-2">
        <label><span className="label">Название</span><input className="input" value={form.name} onChange={set("name")} /></label>
        <label><span className="label">Адрес API (…/v1)</span><input className="input font-mono text-xs" value={form.base_url} onChange={set("base_url")} /></label>
        <label>
          <span className="label">API-ключ {form.has_key && "(сохранён — оставьте пустым, чтобы не менять)"}</span>
          <input className="input" type="password" autoComplete="off" value={form.api_key || ""} onChange={set("api_key")} />
        </label>
        <label>
          <span className="label">Модель</span>
          <div className="flex gap-2">
            <input className="input" list="llm-models" value={form.model || ""} onChange={set("model")} placeholder="deepseek-chat, gpt://…/yandexgpt/latest" />
            <button className="btn-ghost shrink-0 px-2.5 text-xs" onClick={loadModels} title="Список моделей сервера">Список</button>
          </div>
          <datalist id="llm-models">{(models || []).map((m) => <option key={m} value={m} />)}</datalist>
        </label>
        {(isYandex || form.folder) && (
          <label><span className="label">Каталог Yandex Cloud (folder id)</span><input className="input font-mono text-xs" value={form.folder || ""} onChange={set("folder")} /></label>
        )}
      </div>
      <div className="mt-3 flex gap-2">
        <button className="btn-primary" onClick={save} disabled={busy || !form.name || !form.base_url}>{busy ? <Spinner /> : null} Сохранить</button>
        <button className="btn-ghost" onClick={() => setForm(null)}>Закрыть</button>
      </div>
    </div>
  );
}

const STATUS = {
  off: ["выключена", "text-zinc-500"],
  login: ["войдите в аккаунт", "text-amber-300"],
  connecting: ["подключение…", "text-zinc-400"],
  online: ["подключена — сервер может отправлять ей запросы", "text-emerald-300"],
  busy: ["отвечает на запрос", "text-violet-300"],
  nomodel: ["модель на этом компьютере не отвечает", "text-amber-300"],
  error: ["ошибка", "text-rose-300"],
};

/** Десктоп: локальная модель на этом компьютере (Strata и др.), мост к серверу. */
function LocalModelCard({ online, onChanged }) {
  const toast = useToast();
  const [b, setB] = useState(null);
  const [cfg, setCfg] = useState(null);
  const [test, setTest] = useState(null);

  useEffect(() => {
    desktop.bridge.get().then((s) => {
      setB(s);
      setCfg({ ...s.config, apiKey: "" });
    });
    return desktop.bridge.onState((s) => setB(s));
  }, []);

  if (!b || !cfg) return null;
  const [label, cls] = STATUS[b.state.status] || STATUS.off;
  const set = (k) => (e) => setCfg((c) => ({ ...c, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  async function save(patch = {}) {
    const next = { ...cfg, ...patch };
    const s = await desktop.bridge.set({ enabled: next.enabled, url: next.url, model: next.model, noThink: next.noThink, apiKey: next.apiKey || null });
    setB(s);
    setCfg((c) => ({ ...c, ...patch, apiKey: "" }));
    toast(next.enabled ? "Локальная модель включена" : "Локальная модель выключена", "success");
    setTimeout(onChanged, 1500);
  }

  async function runTest() {
    setTest({ busy: true });
    setTest(await desktop.bridge.test());
  }

  return (
    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Laptop className="h-4 w-4 text-emerald-300" /> Локальная модель на этом компьютере
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-xs">
          <input type="checkbox" checked={!!cfg.enabled} onChange={(e) => save({ enabled: e.target.checked })} />
          {cfg.enabled ? "включена" : "выключена"}
        </label>
      </div>
      <p className="mb-3 text-[11px] leading-relaxed text-zinc-500">
        Strata, LM Studio, llama.cpp — любой OpenAI-совместимый сервер. Приложение само забирает запросы с сервера AI Anki
        и передаёт их модели, поэтому открывать её в сеть не нужно. Работает, пока приложение открыто.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label><span className="label">Адрес (…/v1)</span><input className="input font-mono text-xs" value={cfg.url} onChange={set("url")} /></label>
        <label>
          <span className="label">Модель (пусто — загруженная, из /v1/models)</span>
          <input className="input text-xs" value={cfg.model || ""} onChange={set("model")} placeholder={b.state.model || "qwen3.8-flash-next-…"} />
        </label>
        <label>
          <span className="label">API-ключ {cfg.hasKey ? "(сохранён)" : "(если задан в Strata)"}</span>
          <input className="input" type="password" autoComplete="off" value={cfg.apiKey || ""} onChange={set("apiKey")} />
        </label>
        <label className="flex items-end gap-2 pb-2 text-xs text-zinc-300">
          <input type="checkbox" checked={!!cfg.noThink} onChange={set("noThink")} /> Без рассуждений (быстрее: enable_thinking=false)
        </label>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button className="btn-primary" onClick={() => save()}>Сохранить</button>
        <button className="btn-ghost" onClick={runTest} disabled={test?.busy}>
          {test?.busy ? <Spinner /> : <Plug className="h-4 w-4" />} Проверить модель
        </button>
        <span className={`text-xs ${cls}`}>
          ● {label}
          {b.state.model && b.state.status !== "off" ? ` · ${b.state.model}` : ""}
          {b.state.jobs ? ` · запросов: ${b.state.jobs}` : ""}
          {online ? " · сервер видит" : ""}
        </span>
      </div>
      {b.state.error && <div className="mt-2 text-[11px] text-rose-300">{b.state.error}</div>}
      {test && !test.busy && <TestLine t={{ ...test, model: test.model || "" }} />}
    </div>
  );
}
