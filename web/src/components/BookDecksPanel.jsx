import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { BookOpenText, Shuffle, Sparkles, Square } from "lucide-react";
import { api } from "../lib/api";
import { Spinner, useToast } from "./ui";

/** Админ: колоды учебников — карточки по урокам, нехватка, догенерация и раскладка по смыслу. */
export default function BookDecksPanel() {
  const toast = useToast();
  const [st, setSt] = useState(null);
  const [busy, setBusy] = useState("");
  const running = useRef(false);

  const load = () => api("/api/books").then((r) => {
    setSt(r);
    running.current = r.job.running;
    return r;
  });
  useEffect(() => {
    let timer;
    let alive = true;
    const tick = () =>
      load()
        .then((r) => alive && (timer = setTimeout(tick, r.job.running || r.assign_status ? 3000 : 30000)))
        .catch(() => {});
    tick();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function call(key, fn) {
    setBusy(key);
    try {
      await fn();
      await load();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy("");
    }
  }

  if (!st) return null;
  const job = st.job;
  const totals = st.books.reduce((a, b) => ({ qa: a.qa + b.qa, live: a.live + b.live, thin: a.thin + b.thin, lessons: a.lessons + b.lessons }), { qa: 0, live: 0, thin: 0, lessons: 0 });
  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.19 }} className="glass p-5 sm:p-6">
      <h2 className="mb-1 flex items-center gap-2 font-semibold">
        <BookOpenText className="h-4 w-4 text-violet-300" /> Колоды учебников
      </h2>
      <p className="mb-4 text-xs leading-relaxed text-zinc-500">
        У каждого урока программы — свои карточки: вопросы, а для программирования и профессий ещё и практика. Норма на урок —{" "}
        {st.targets.qa} вопросов и {st.targets.live} задания; недостающее догенерирует выбранная модель по статье урока и документации.
        Программы правятся в разделе «Учебник» → «Править».
      </p>
      <div className="mb-4 grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
        {[["уроков", totals.lessons], ["вопросов", totals.qa], ["live-coding", totals.live], ["с нехваткой", totals.thin]].map(([l, v]) => (
          <div key={l} className="rounded-xl bg-white/[0.03] py-2.5">
            <div className={`text-lg font-bold tabular-nums ${l === "с нехваткой" && v ? "text-amber-300" : "text-white"}`}>{v}</div>
            <div className="text-[10px] uppercase tracking-wider text-zinc-500">{l}</div>
          </div>
        ))}
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        {job.running ? (
          <button className="btn-ghost" onClick={() => call("stop", () => api("/api/books/generate/stop", { method: "POST" }))}>
            <Square className="h-4 w-4" /> Остановить генерацию
          </button>
        ) : (
          <button className="btn-ghost" disabled={!!busy || !totals.thin} onClick={() => call("gen", async () => {
            const r = await api("/api/books/generate", { method: "POST", body: {} });
            toast(`Уроков в очереди: ${r.queued}`, "success");
          })}>
            {busy === "gen" ? <Spinner /> : <Sparkles className="h-4 w-4" />} Догенерировать во всех учебниках
          </button>
        )}
        <button
          className="btn-ghost"
          disabled={!!busy}
          title="Заново разложить перенесённые из прежних колод карточки по урокам — по смыслу (эмбеддинги Ollama)"
          onClick={() => call("reassign", async () => {
            const r = await api("/api/books/build", { method: "POST", body: { embeddings: true, reassign: true } });
            toast(`Раскладка запущена для учебников: ${r.started}. Ход — в этом блоке.`, "success");
          })}
        >
          {busy === "reassign" ? <Spinner /> : <Shuffle className="h-4 w-4" />} Переразложить карточки по смыслу
        </button>
      </div>
      {(st.assign_status || job.running || job.log.length > 0) && (
        <div className="mb-3 rounded-xl border border-white/[0.06] bg-ink-900/70 p-3 font-mono text-[11px] leading-relaxed text-zinc-400">
          {st.assign_status && <div className="text-cyan-300">{st.assign_status}</div>}
          {job.running && <div className="text-violet-300">{job.done}/{job.total} · {job.current} · +{job.added_qa} вопросов, +{job.added_live} live-coding</div>}
          {job.log.slice(-8).map((l, i) => <div key={i}>{l}</div>)}
          {job.error && <div className="text-rose-300">{job.error}</div>}
        </div>
      )}
      <div className="max-h-80 space-y-1 overflow-y-auto pr-1 text-xs">
        {st.books.map((b) => (
          <div key={b.id} className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-white/[0.03]">
            <span className="min-w-0 flex-1 truncate text-zinc-200">{b.title}</span>
            <span className="text-zinc-500">{b.chapters} гл. · {b.lessons} ур.</span>
            <span className="w-20 text-right tabular-nums text-zinc-300">{b.qa} вопр.</span>
            <span className="w-16 text-right tabular-nums text-zinc-400">{b.has_practice ? `${b.live} live` : "—"}</span>
            <span className={`w-24 text-right ${b.thin ? "text-amber-300" : "text-emerald-300"}`}>{b.thin ? `нехватка: ${b.thin}` : "норма"}</span>
            <span className="w-16 text-right text-[10px] text-zinc-600" title="Как разложены перенесённые карточки">{b.assigned === "topics" ? "по темам" : b.assigned === "words" ? "по словам" : "по смыслу"}</span>
            <button
              className="rounded px-2 py-1 text-violet-200 hover:bg-white/[0.06] disabled:opacity-30"
              disabled={job.running || !b.thin || !!busy}
              onClick={() => call(`g-${b.id}`, () => api("/api/books/generate", { method: "POST", body: { book: b.id } }))}
              title="Догенерировать карточки этого учебника"
            >
              <Sparkles className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </motion.section>
  );
}
