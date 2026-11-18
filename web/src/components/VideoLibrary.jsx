import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { AlertTriangle, CheckCircle2, Clapperboard, FileText, FolderSearch, RotateCcw, Search, Trash2, Upload, X } from "lucide-react";
import { api, getToken, serverUrl } from "../lib/api";
import { Spinner, useToast } from "./ui";
import { nextDelay, setIfChanged } from "../lib/poll";

export function fmtTime(sec) {
  const s = Math.max(0, Math.floor(sec || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${r}` : `${m}:${r}`;
}

export function videoFileUrl(id) {
  return serverUrl(`/api/videos/${id}/file?token=${encodeURIComponent(getToken() || "")}`);
}

const PAGE = 60; // строк видеотеки на экран: дальше — поиск и «Показать ещё»
// Каждая строка — <select> со всеми учебниками, поэтому полный список из сотен видео
// стоит десятки тысяч узлов и подвешивает окно при открытии вкладки.

const STATUS = {
  queued: { label: "в очереди", cls: "text-zinc-400" },
  processing: { label: "расшифровка", cls: "text-violet-300" },
  done: { label: "в базе знаний", cls: "text-emerald-300" },
  error: { label: "ошибка", cls: "text-rose-300" },
  missing: { label: "файл пропал", cls: "text-amber-300" },
  skipped: { label: "исключено", cls: "text-zinc-600" },
};

/** Видеотека (админ): папки, загрузка, очередь расшифровки, привязка к учебникам. */
export default function VideoLibrary() {
  const toast = useToast();
  const [st, setSt] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [upload, setUpload] = useState(null); // {name, pct}
  const [folder, setFolder] = useState("");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [shown, setShown] = useState(PAGE);
  const fileRef = useRef(null);
  const [listRef] = useAutoAnimate({ duration: 200 });
  const [transcript, setTranscript] = useState(null); // видео, чью расшифровку смотрим

  const load = () => api("/api/videos").then((r) => (setIfChanged(setSt, r), r)).catch((e) => toast(e.message, "error"));
  useEffect(() => {
    let timer;
    let alive = true;
    const tick = () => {
      if (document.hidden) {
        timer = setTimeout(tick, 10000); // окно скрыто — не грузим процессор
        return;
      }
      api("/api/videos")
        .then((r) => {
          if (!alive) return;
          setIfChanged(setSt, r); // ответ не изменился → список не перерисовывается
          const busy = r.videos.some((v) => v.status === "processing" || v.status === "queued");
          timer = setTimeout(tick, nextDelay(busy ? 2500 : 30000));
        })
        .catch(() => {});
    };
    tick();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, []);

  async function scan() {
    setScanning(true);
    try {
      const r = await api("/api/videos/scan", { method: "POST" });
      toast(
        r.media === 0
          ? "В папках не найдено ни одного видео — смотрите подсказку у папки"
          : `Видео в папках: ${r.media}. Новых: ${r.added}, изменённых: ${r.changed}${r.missing ? `, пропало: ${r.missing}` : ""}`,
        r.media === 0 ? "error" : "success",
      );
      await load();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setScanning(false);
    }
  }

  function uploadFiles(files) {
    const list = [...files];
    const next = (i) => {
      if (i >= list.length) {
        setUpload(null);
        load();
        return;
      }
      const f = list[i];
      const fd = new FormData();
      fd.append("file", f);
      fd.append("folder", folder);
      const xhr = new XMLHttpRequest();
      xhr.open("POST", serverUrl("/api/videos/upload"));
      xhr.setRequestHeader("Authorization", `Bearer ${getToken()}`);
      xhr.upload.onprogress = (e) => e.lengthComputable && setUpload({ name: f.name, pct: e.loaded / e.total, n: i + 1, of: list.length });
      xhr.onload = () => {
        if (xhr.status >= 300) toast(`${f.name}: ${xhr.responseText.slice(0, 160)}`, "error");
        next(i + 1);
      };
      xhr.onerror = () => {
        toast(`${f.name}: ошибка загрузки`, "error");
        next(i + 1);
      };
      setUpload({ name: f.name, pct: 0, n: i + 1, of: list.length });
      xhr.send(fd);
    };
    next(0);
  }

  async function act(v, kind, body) {
    try {
      if (kind === "book") await api(`/api/videos/${v.id}`, { method: "PATCH", body });
      if (kind === "reindex") await api(`/api/videos/${v.id}/reindex`, { method: "POST" });
      if (kind === "delete") {
        if (!confirm(v.uploaded ? `Удалить «${v.title}» вместе с файлом?` : `Исключить «${v.title}» из базы знаний? Файл останется на месте.`)) return;
        await api(`/api/videos/${v.id}`, { method: "DELETE" });
      }
      await load();
    } catch (e) {
      toast(e.message, "error");
    }
  }

  const videos = useMemo(() => {
    const all = st?.videos || [];
    const q = query.trim().toLowerCase();
    const byStatus =
      filter === "all" ? all : filter === "nobook" ? all.filter((v) => !v.book && v.status !== "skipped") : all.filter((v) => v.status === filter);
    if (!q) return byStatus;
    return byStatus.filter((v) => (v.title + " " + v.folder).toLowerCase().includes(q));
  }, [st, filter, query]);
  const visible = useMemo(() => videos.slice(0, shown), [videos, shown]);
  useEffect(() => setShown(PAGE), [filter, query]);

  if (!st) return null;
  const counts = {};
  for (const v of st.videos) counts[v.status] = (counts[v.status] || 0) + 1;
  const hours = st.videos.filter((v) => v.status === "done").reduce((a, v) => a + v.duration, 0) / 3600;
  const bookTitle = Object.fromEntries(st.books.map((b) => [b.id, b.title]));

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass p-5 sm:p-6">
      <h2 className="mb-1 flex items-center gap-2 font-semibold">
        <Clapperboard className="h-4 w-4 text-violet-300" /> Видеотека учебника
      </h2>
      <p className="mb-4 text-xs leading-relaxed text-zinc-500">
        Из видео извлекается звук, Whisper делает расшифровку с таймкодами, фрагменты попадают в базу знаний. Статьи цитируют
        их и встраивают плеер с нужного момента. Новые файлы в папках находятся автоматически (раз в 30 минут) или по кнопке.
      </p>

      {(!st.ffmpeg || !st.asr) && (
        <div className="mb-4 flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            {!st.ffmpeg && <div>На сервере не найден ffmpeg — пересоберите Docker-образ.</div>}
            {!st.asr && <div>Не задан «ASR URL (Whisper)» в настройках сервера — расшифровка невозможна.</div>}
          </div>
        </div>
      )}

      <ProgressCard progress={st.progress} />
      <ThresholdCard value={st.min_sim} onSaved={load} />

      <div className="mb-4 grid gap-2 text-xs sm:grid-cols-2">
        {st.roots.map((r) => <RootCard key={r.path} r={r} />)}
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button className="btn-ghost" onClick={scan} disabled={scanning}>
          {scanning ? <Spinner /> : <FolderSearch className="h-4 w-4" />} Найти новые видео
        </button>
        <input className="input w-56 py-2 text-xs" placeholder="Папка для загрузки, напр. PHP/ООП" value={folder} onChange={(e) => setFolder(e.target.value)} />
        <button className="btn-ghost" onClick={() => fileRef.current?.click()} disabled={!!upload}>
          <Upload className="h-4 w-4" /> Загрузить видео
        </button>
        <input ref={fileRef} type="file" multiple accept="video/*,audio/*,.mkv,.avi" className="hidden" onChange={(e) => { uploadFiles(e.target.files); e.target.value = ""; }} />
      </div>
      {upload && (
        <div className="mb-4 text-xs text-zinc-400">
          Загрузка {upload.n}/{upload.of}: {upload.name} — {Math.round(upload.pct * 100)}%
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-white/[0.06]">
            <div className="h-full bg-violet-400 transition-all" style={{ width: `${upload.pct * 100}%` }} />
          </div>
        </div>
      )}

      <div className="mb-3 flex flex-wrap gap-1.5 text-xs">
        {[
          ["all", `Все ${st.videos.length}`],
          ["done", `Готово ${counts.done || 0}`],
          ["queued", `В очереди ${(counts.queued || 0) + (counts.processing || 0)}`],
          ["error", `Ошибки ${counts.error || 0}`],
          ["nobook", "Без учебника"],
        ].map(([id, label]) => (
          <button key={id} onClick={() => setFilter(id)} className={`chip ${filter === id ? "border-violet-400/50 text-white" : ""}`}>{label}</button>
        ))}
        <label className="relative ml-auto flex items-center">
          <Search className="pointer-events-none absolute left-2.5 h-3.5 w-3.5 text-zinc-500" />
          <input
            className="input w-48 py-1.5 pl-8 text-xs"
            placeholder="Поиск по названию или папке"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <span className="self-center text-zinc-500">расшифровано {hours.toFixed(1)} ч</span>
      </div>

      <div ref={listRef} className="max-h-[480px] space-y-1.5 overflow-y-auto pr-1">
        {videos.length === 0 && <div className="py-6 text-center text-sm text-zinc-500">Видео пока нет</div>}
        {visible.map((v) => {
          const s = STATUS[v.status] || STATUS.queued;
          return (
            <div key={v.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2.5">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm text-zinc-100" title={v.title}>{v.title}</div>
                  <div className="truncate text-[11px] text-zinc-500">
                    {v.folder || "—"}{v.duration ? ` · ${fmtTime(v.duration)}` : ""}{v.chunks ? ` · ${v.chunks} фрагм.` : ""}{v.language ? ` · ${v.language}` : ""}
                  </div>
                </div>
                <select
                  className="input w-48 py-1.5 text-xs"
                  value={v.book || ""}
                  onChange={(e) => act(v, "book", { book: e.target.value })}
                  title={v.book_manual ? "Выбрано вручную" : "Определено автоматически"}
                >
                  <option value="">— учебник не выбран —</option>
                  {st.books.map((b) => <option key={b.id} value={b.id}>{b.title}</option>)}
                </select>
                <span className={`flex w-28 items-center gap-1 text-xs ${s.cls}`}>
                  {v.status === "processing" ? <Spinner className="h-3 w-3" /> : v.status === "done" ? <CheckCircle2 className="h-3 w-3" /> : null}
                  {s.label}{v.status === "processing" ? ` ${Math.round(v.progress * 100)}%` : ""}
                </span>
                <div className="flex gap-1">
                  {(v.status === "done" || v.status === "processing" || v.chunks > 0) && (
                    <button className="rounded-lg p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-violet-200" title="Расшифровка" onClick={() => setTranscript(v)}>
                      <FileText className="h-3.5 w-3.5" />
                    </button>
                  )}
                  <button className="rounded-lg p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-violet-200" title="Расшифровать заново" onClick={() => act(v, "reindex")}>
                    <RotateCcw className="h-3.5 w-3.5" />
                  </button>
                  <button className="rounded-lg p-1.5 text-zinc-500 hover:bg-white/[0.06] hover:text-rose-300" title={v.uploaded ? "Удалить" : "Исключить из базы"} onClick={() => act(v, "delete")}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
              {v.status === "processing" && (
                <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div className="h-full bg-gradient-to-r from-violet-500 to-cyan-400" animate={{ width: `${v.progress * 100}%` }} />
                </div>
              )}
              {v.error && <div className={`mt-1 text-[11px] ${v.status === "error" ? "text-rose-300" : "text-amber-300"}`}>{v.error}</div>}
              {!v.book && v.status === "done" && <div className="mt-1 text-[11px] text-amber-300">Выберите учебник — иначе видео не попадёт в статьи.</div>}
              {v.book && bookTitle[v.book] == null && <div className="mt-1 text-[11px] text-amber-300">Учебник «{v.book}» не найден.</div>}
            </div>
          );
        })}
      </div>

      {videos.length > visible.length && (
        <button className="btn-ghost mt-3 w-full text-xs" onClick={() => setShown((s) => s + PAGE)}>
          Показать ещё {Math.min(PAGE, videos.length - visible.length)} — найдено {videos.length}, показано {visible.length}
        </button>
      )}

      <LivePanel log={st.log} busy={!!st.progress?.current} />
      {createPortal(
        <AnimatePresence>{transcript && <TranscriptModal video={transcript} onClose={() => setTranscript(null)} />}</AnimatePresence>,
        document.body,
      )}
    </motion.section>
  );
}

const DEFAULT_SIM = 0.45;

/** Порог сходства «урок ↔ видео»: ниже — больше видео в статьях, выше — только точные совпадения. */
function ThresholdCard({ value, onSaved }) {
  const toast = useToast();
  const saved = Number(value) || DEFAULT_SIM;
  const [v, setV] = useState(saved);
  const [busy, setBusy] = useState(false);
  useEffect(() => setV(saved), [saved]);
  const label = v >= 0.6 ? "только очень точные совпадения" : v >= 0.5 ? "строго" : v >= 0.42 ? "сбалансированно" : v >= 0.35 ? "мягко — возможны лишние видео" : "очень мягко — много лишних";

  async function save(next) {
    setBusy(true);
    try {
      await api("/api/config", { method: "POST", body: { video_min_sim: next == null ? "" : String(next) } });
      toast(next == null ? "Порог сброшен на 0.45" : `Порог сходства: ${next}`, "success");
      onSaved();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <div className="text-sm font-semibold">Насколько видео должно совпадать с уроком</div>
          <div className="text-xs text-zinc-500">
            Косинусное сходство расшифровки с темой урока. Своя тема обычно даёт 0.6–0.8, соседние — до 0.48.
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-xl font-bold tabular-nums text-white">{v.toFixed(2)}</div>
          <div className="text-[11px] text-zinc-400">{label}</div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <span className="text-[11px] text-zinc-500">больше видео</span>
        <input
          type="range"
          min="0.25"
          max="0.8"
          step="0.01"
          value={v}
          onChange={(e) => setV(Number(e.target.value))}
          className="h-1.5 flex-1 cursor-pointer accent-violet-400"
        />
        <span className="text-[11px] text-zinc-500">точнее</span>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button className="btn-primary px-3 py-1.5 text-xs" disabled={busy || Math.abs(v - saved) < 0.001} onClick={() => save(Number(v.toFixed(2)))}>
          {busy ? <Spinner className="h-3.5 w-3.5" /> : null} Применить
        </button>
        {Math.abs(saved - DEFAULT_SIM) > 0.001 && (
          <button className="btn-ghost px-3 py-1.5 text-xs" disabled={busy} onClick={() => save(null)}>Сбросить (0.45)</button>
        )}
        <span className="text-[11px] text-zinc-500">
          Действует сразу при открытии статей; ручной выбор видео в уроке («Видео урока» под статьёй) важнее порога.
        </span>
      </div>
    </div>
  );
}

/** Папка с видео: что сервер в ней видит — и подсказка, если видео не находятся. */
function RootCard({ r }) {
  let problem = "";
  if (!r.uploads) {
    if (r.exists === false || r.is_dir === false)
      problem = `Папки ${r.path} нет внутри контейнера — подключите её в compose: volumes → «- /путь/на/NAS:${r.path}:ro» и перезапустите приложение.`;
    else if (r.readable === false) problem = "Нет прав на чтение папки — проверьте права/ACL датасета на NAS.";
    else if (r.errors?.length) problem = `Ошибки доступа: ${r.errors.join("; ")}`;
    else if (r.media === 0 && r.files === 0) problem = "Папка пустая — возможно, подключена не та папка NAS.";
    else if (r.media === 0)
      problem = `Файлов ${r.files}, но ни одного видео/аудио. Расширения: ${Object.entries(r.other_ext || {}).map(([e, n]) => `${e} ×${n}`).join(", ")}`;
  }
  return (
    <div className={`rounded-lg border px-3 py-2 ${problem ? "border-amber-500/30 bg-amber-500/[0.06]" : "border-white/[0.06] bg-white/[0.02]"}`}>
      <div className="flex justify-between gap-2 text-zinc-500">
        <span>{r.uploads ? "Загруженные через сайт" : "Папка с видео"}</span>
        {r.media != null && r.is_dir && (
          <span>
            видео/аудио <b className="text-zinc-200">{r.media}</b>{r.files > r.media ? ` из ${r.files} файлов` : ""}{r.dirs > 1 ? ` · папок ${r.dirs - 1}` : ""}
          </span>
        )}
      </div>
      <div className={`truncate font-mono ${r.is_dir === false ? "text-zinc-600 line-through" : "text-zinc-200"}`} title={r.path}>{r.path}</div>
      {problem && <div className="mt-1 text-[11px] leading-snug text-amber-200">{problem}</div>}
      {r.media == null && !r.uploads && <div className="mt-1 text-[11px] text-zinc-500">Нажмите «Найти новые видео», чтобы проверить папку.</div>}
    </div>
  );
}

const STAGES = {
  audio: "Извлечение звука (ffmpeg)",
  asr: "Распознавание речи (Whisper)",
  retry: "Whisper не отвечает — ждём повтора",
  index: "Нарезка на фрагменты",
  embed: "Векторизация (Ollama)",
};

function eta(sec) {
  if (sec == null || !isFinite(sec)) return "—";
  if (sec < 60) return "< 1 мин";
  const h = Math.floor(sec / 3600);
  const m = Math.round((sec % 3600) / 60);
  return h ? `${h} ч ${m} мин` : `${m} мин`;
}

/** Что обрабатывается сейчас: этап, кусок, время, прогноз; ниже — очередь. */
function ProgressCard({ progress }) {
  if (!progress) return null;
  const c = progress.current;
  const q = progress.queue;
  if (!c && !q.count) return null;
  const pct = c
    ? c.stage === "audio"
      ? (c.audio_done || 0) / (c.duration || 1) * 0.1
      : c.stage === "asr" || c.stage === "retry"
        ? 0.1 + 0.82 * ((c.done_sec || 0) / (c.duration || 1))
        : c.stage === "index" ? 0.93 : 0.96
    : 0;
  return (
    <div className="mb-4 rounded-xl border border-violet-500/25 bg-violet-500/[0.06] p-4">
      {c && (
        <>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="min-w-0">
              <div className="text-[11px] font-semibold uppercase tracking-widest text-violet-300">{STAGES[c.stage] || c.stage}</div>
              <div className="truncate text-sm text-zinc-100" title={c.title}>{c.title}</div>
            </div>
            <div className="text-2xl font-extrabold tabular-nums text-white">{Math.round(pct * 100)}%</div>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/[0.06]">
            <motion.div className="h-full bg-gradient-to-r from-violet-500 to-cyan-400" animate={{ width: `${pct * 100}%` }} />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-zinc-400">
            {c.duration > 0 && <span>длительность {fmtTime(c.duration)}</span>}
            {c.stage === "audio" && c.audio_done > 0 && <span>звук {fmtTime(c.audio_done)} / {fmtTime(c.duration)}</span>}
            {c.parts > 0 && <span>кусок {Math.max(c.part, 1)}/{c.parts}</span>}
            {c.done_sec > 0 && <span>распознано {fmtTime(c.done_sec)}</span>}
            <span>прошло {eta(c.elapsed)}</span>
            {c.eta != null && <span>осталось ≈ {eta(c.eta)}</span>}
            {c.speed > 0 && <span>скорость ×{c.speed.toFixed(1)} от реального времени</span>}
            {c.language && <span>язык {c.language}</span>}
            {c.stage === "embed" && c.chunks > 0 && <span>фрагментов {c.chunks}</span>}
          </div>
          {c.stage === "retry" && (
            <div className="mt-2 text-[11px] text-amber-300">Повтор через {c.retry_in} с: {c.retry_error}</div>
          )}
        </>
      )}
      {q.count > 0 && (
        <div className={`text-xs text-zinc-400 ${c ? "mt-3 border-t border-white/[0.06] pt-3" : ""}`}>
          В очереди: <b className="text-zinc-200">{q.count}</b> видео
          {q.seconds > 0 && <> · {fmtTime(q.seconds)} записи</>}
          {q.eta != null && <> · примерно {eta(q.eta)}</>}
          {q.unknown > 0 && <span className="text-zinc-500"> (длительность {q.unknown} шт. неизвестна)</span>}
        </div>
      )}
    </div>
  );
}

/** Вкладки: живая расшифровка Whisper и журнал обработки. */
function LivePanel({ log, busy }) {
  const [tab, setTab] = useState("feed");
  const [items, setItems] = useState([]);
  const [follow, setFollow] = useState(true);
  const seq = useRef(0);
  const box = useRef(null);

  useEffect(() => {
    let alive = true;
    let timer;
    const poll = () =>
      api(`/api/videos/feed?since=${seq.current}`)
        .then((r) => {
          if (!alive) return;
          if (r.items.length) {
            seq.current = r.items[r.items.length - 1].seq;
            setItems((xs) => [...xs, ...r.items].slice(-400));
          }
          timer = setTimeout(poll, r.progress?.current ? 2000 : 15000);
        })
        .catch(() => (timer = setTimeout(poll, 15000)));
    poll();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [busy]);

  useEffect(() => {
    if (follow && box.current) box.current.scrollTop = box.current.scrollHeight;
  }, [items, log, tab, follow]);

  if (!items.length && !log.length) return null;
  let lastVideo = null;
  return (
    <div className="mt-4 rounded-xl border border-white/[0.06] bg-ink-900/70">
      <div className="flex items-center gap-1 border-b border-white/[0.06] px-2 pt-2 text-xs">
        {[["feed", `Что распознаёт Whisper${items.length ? ` (${items.length})` : ""}`], ["log", "Журнал"]].map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} className={`rounded-t-lg px-3 py-1.5 ${tab === id ? "bg-white/[0.06] text-white" : "text-zinc-500 hover:text-zinc-200"}`}>
            {label}
          </button>
        ))}
        <label className="ml-auto flex items-center gap-1.5 pb-1 pr-2 text-[11px] text-zinc-500">
          <input type="checkbox" checked={follow} onChange={(e) => setFollow(e.target.checked)} /> прокручивать
        </label>
      </div>
      <div ref={box} className="max-h-72 overflow-y-auto p-3 font-mono text-[11.5px] leading-relaxed">
        {tab === "log" ? (
          log.map((l, i) => <div key={i} className="text-zinc-400">{l}</div>)
        ) : items.length === 0 ? (
          <div className="text-zinc-500">Расшифровка появится здесь по мере работы Whisper (каждые 5 минут записи).</div>
        ) : (
          items.map((it) => {
            const head = it.video !== lastVideo;
            lastVideo = it.video;
            return (
              <div key={it.seq}>
                {head && <div className="mb-1 mt-2 font-sans text-[11px] font-semibold text-violet-300 first:mt-0">{it.title}</div>}
                <div className="flex gap-2">
                  <span className="shrink-0 text-zinc-600">{fmtTime(it.t)}</span>
                  <span className="text-zinc-300">{it.text}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/** Полная расшифровка видео с поиском и переходом к моменту. */
function TranscriptModal({ video, onClose }) {
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const player = useRef(null);
  useEffect(() => {
    api(`/api/videos/${video.id}/transcript`).then(setData).catch(() => setData({ segments: [] }));
  }, [video.id]);
  useEffect(() => {
    const esc = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);
  const segs = (data?.segments || []).filter((sg) => !q || sg.text.toLowerCase().includes(q.toLowerCase()));
  const words = (data?.segments || []).reduce((a, sg) => a + sg.text.split(/\s+/).length, 0);
  const seek = (t) => {
    const v = player.current;
    if (!v) return;
    v.currentTime = t;
    v.play().catch(() => {});
  };
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <motion.div
        initial={{ scale: 0.97, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.97, y: 10 }}
        className="glass flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden bg-ink-900/95"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-white/[0.06] px-5 py-3">
          <div className="min-w-0 flex-1">
            <div className="truncate font-semibold">{video.title}</div>
            <div className="text-xs text-zinc-500">
              {video.folder || "—"} · {data ? `${data.segments.length} фраз, ${words} слов` : "загрузка…"}
              {video.status === "processing" && " · расшифровка ещё идёт"}
            </div>
          </div>
          <button className="rounded-lg p-1.5 text-zinc-400 hover:bg-white/[0.08] hover:text-white" onClick={onClose} aria-label="Закрыть">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="grid min-h-0 flex-1 gap-0 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <div className="border-b border-white/[0.06] p-4 md:border-b-0 md:border-r">
            <video ref={player} className="aspect-video w-full rounded-lg bg-black" controls preload="metadata" src={videoFileUrl(video.id)} />
            <div className="relative mt-3">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
              <input className="input py-2 pl-8 text-xs" placeholder="Найти в расшифровке" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
          </div>
          <div className="min-h-0 overflow-y-auto p-4 text-sm leading-relaxed">
            {!data ? (
              <Spinner />
            ) : segs.length === 0 ? (
              <div className="text-zinc-500">{q ? "Ничего не найдено" : "Расшифровки пока нет"}</div>
            ) : (
              segs.map((sg, i) => (
                <button key={i} onClick={() => seek(sg.start)} className="group flex w-full gap-3 rounded-lg px-2 py-1 text-left hover:bg-white/[0.04]">
                  <span className="shrink-0 font-mono text-xs text-zinc-600 group-hover:text-violet-300">{fmtTime(sg.start)}</span>
                  <span className="text-zinc-300">{sg.text}</span>
                </button>
              ))
            )}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
