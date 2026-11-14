import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { AlertTriangle, CheckCircle2, Clapperboard, FolderSearch, RotateCcw, Trash2, Upload } from "lucide-react";
import { api, getToken, serverUrl } from "../lib/api";
import { Spinner, useToast } from "./ui";

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
  const fileRef = useRef(null);
  const [listRef] = useAutoAnimate({ duration: 200 });

  const load = () => api("/api/videos").then(setSt).catch((e) => toast(e.message, "error"));
  useEffect(() => {
    let timer;
    let alive = true;
    const tick = () =>
      api("/api/videos")
        .then((r) => {
          if (!alive) return;
          setSt(r);
          const busy = r.videos.some((v) => v.status === "processing" || v.status === "queued");
          timer = setTimeout(tick, busy ? 4000 : 30000);
        })
        .catch(() => {});
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
      toast(`Новых: ${r.added}, изменённых: ${r.changed}${r.missing ? `, пропало: ${r.missing}` : ""}`, "success");
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
    if (filter === "all") return all;
    if (filter === "nobook") return all.filter((v) => !v.book && v.status !== "skipped");
    return all.filter((v) => v.status === filter);
  }, [st, filter]);

  if (!st) return null;
  const counts = st.videos.reduce((a, v) => ({ ...a, [v.status]: (a[v.status] || 0) + 1 }), {});
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

      <div className="mb-4 grid gap-2 text-xs sm:grid-cols-2">
        {st.roots.map((r) => (
          <div key={r.path} className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
            <div className="text-zinc-500">{r.uploads ? "Загруженные через сайт" : "Папка с видео"}</div>
            <div className={`truncate font-mono ${r.exists ? "text-zinc-200" : "text-zinc-600 line-through"}`} title={r.path}>{r.path}</div>
          </div>
        ))}
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
        <span className="ml-auto self-center text-zinc-500">расшифровано {hours.toFixed(1)} ч</span>
      </div>

      <div ref={listRef} className="max-h-[480px] space-y-1.5 overflow-y-auto pr-1">
        {videos.length === 0 && <div className="py-6 text-center text-sm text-zinc-500">Видео пока нет</div>}
        {videos.map((v) => {
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

      {st.log.length > 0 && (
        <div className="mt-3 rounded-xl border border-white/[0.06] bg-ink-900/70 p-3 font-mono text-[11px] leading-relaxed text-zinc-400">
          {st.log.map((l, i) => <div key={i}>{l}</div>)}
        </div>
      )}
    </motion.section>
  );
}
