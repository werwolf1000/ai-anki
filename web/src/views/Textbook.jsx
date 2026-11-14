import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  BookMarked, BookOpenText, Check, ChevronDown, ExternalLink, GraduationCap, Library, MessageCircleQuestion,
  PlayCircle, RefreshCw, Search, Send, Sparkles, X,
} from "lucide-react";
import { api, apiStream } from "../lib/api";
import { kindOf } from "../lib/decks";
import { extractHeadings, RichText } from "../lib/richtext";
import { EmptyState, Spinner, useToast } from "../components/ui";
import { fmtTime, videoFileUrl } from "../components/VideoLibrary";

export default function Textbook({ user, decks, initial, onStart }) {
  const toast = useToast();
  const usable = useMemo(() => (decks || []).filter((d) => !d.error), [decks]);
  const [deckId, setDeckId] = useState(initial?.deckId || null);
  const [book, setBook] = useState(null); // /api/textbook/{deck}
  const [topic, setTopic] = useState(initial?.topic || "");
  const [query, setQuery] = useState("");
  const [topicsRef] = useAutoAnimate({ duration: 200 });

  useEffect(() => {
    if (!deckId && usable.length) {
      const php = usable.find((d) => /^php/i.test(d.name) && d.kind !== "live") || usable.find((d) => d.language === "php" && d.kind !== "live");
      setDeckId((php || usable[0]).deck_id);
    }
  }, [deckId, usable]);

  const loadBook = useCallback(() => {
    if (!deckId) return;
    api(`/api/textbook/${deckId}`)
      .then(setBook)
      .catch((e) => toast(e.message, "error"));
  }, [deckId, toast]);

  useEffect(() => {
    setBook(null);
    loadBook();
  }, [loadBook]);

  useEffect(() => {
    if (initial?.deckId) {
      setDeckId(initial.deckId);
      setTopic(initial.topic || "");
    }
  }, [initial]);

  const deck = usable.find((d) => d.deck_id === deckId);
  const q = query.trim().toLowerCase();
  const topics = (book?.topics || []).filter((t) => !q || t.name.toLowerCase().includes(q) || (t.chapter || "").toLowerCase().includes(q));
  const readCount = (book?.topics || []).filter((t) => t.read_at).length;
  const chapters = useMemo(() => {
    const out = [];
    for (const t of topics) {
      let ch = out[out.length - 1];
      if (!ch || ch.title !== t.chapter) {
        ch = { title: t.chapter, items: [] };
        out.push(ch);
      }
      ch.items.push(t);
    }
    return out;
  }, [topics]);
  const [openChapters, setOpenChapters] = useState({});
  const currentChapter = book?.topics.find((t) => t.name === topic)?.chapter;
  const isOpen = (title) => !!q || chapters.length === 1 || (openChapters[title] ?? title === (currentChapter ?? chapters[0]?.title));
  const toggleChapter = (title) => setOpenChapters((o) => ({ ...o, [title]: !isOpen(title) }));

  // переход из карточки: тема колоды → первый урок программы с этой темой
  useEffect(() => {
    if (!book || !topic || book.topics.some((t) => t.name === topic)) return;
    const hit = book.topics.find((t) => t.card_topic === topic) || book.topics.find((t) => t.name.toLowerCase().includes(topic.toLowerCase()));
    setTopic(hit ? hit.name : "");
  }, [book, topic]);

  async function generateDeck() {
    try {
      const r = await api("/api/textbook/generate-all", { method: "POST", body: { deck_id: deckId } });
      toast(`В очереди тем: ${r.queued}. Статьи пишутся в фоне, прогресс — в Настройках.`, "success");
    } catch (e) {
      toast(e.message, "error");
    }
  }

  const updateTopic = (name, patch) =>
    setBook((b) => b && { ...b, topics: b.topics.map((t) => (t.name === name ? { ...t, ...patch } : t)) });

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-extrabold tracking-tight">
            Учебник
          </h1>
          <p className="text-sm text-zinc-400">Прочитайте тему перед карточками — статьи собраны из официальной документации и материалов колоды.</p>
        </div>
        <DeckPicker decks={usable} value={deckId} onChange={(id) => { setDeckId(id); setTopic(""); }} />
      </header>

      <div className="grid gap-5 lg:grid-cols-[290px_minmax(0,1fr)]">
        {/* темы */}
        <aside className="glass h-fit p-4 lg:sticky lg:top-6">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm font-semibold">{book?.book ? `Программа: ${book.book.title}` : "Темы"}</div>
            {book && <div className="text-xs text-zinc-500">прочитано {readCount}/{book.topics.length}</div>}
          </div>
          {book && book.topics.length > 0 && (
            <div className="mb-3 h-1 overflow-hidden rounded-full bg-white/[0.06]">
              <motion.div className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400" animate={{ width: `${(readCount / book.topics.length) * 100}%` }} />
            </div>
          )}
          <div className="relative mb-3">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
            <input className="input py-2 pl-8 text-xs" placeholder="Найти тему" value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>
          {!book ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <div ref={topicsRef} className="max-h-[65vh] space-y-1 overflow-y-auto pr-1">
              {chapters.map((ch) => (
                <div key={ch.title || "_"}>
                  {ch.title && (
                    <button
                      onClick={() => toggleChapter(ch.title)}
                      className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400 hover:text-zinc-100"
                    >
                      <ChevronDown className={`h-3.5 w-3.5 shrink-0 transition-transform ${isOpen(ch.title) ? "" : "-rotate-90"}`} />
                      <span className="min-w-0 flex-1 truncate normal-case tracking-normal">{ch.title}</span>
                      <span className="text-[10px] font-normal tabular-nums text-zinc-600">
                        {ch.items.filter((t) => t.read_at).length}/{ch.items.length}
                      </span>
                    </button>
                  )}
                  {isOpen(ch.title) && ch.items.map((t) => (
                <button
                  key={t.name}
                  onClick={() => setTopic(t.name)}
                  title={t.name}
                  className={`relative flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition-colors ${topic === t.name ? "text-white" : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100"}`}
                >
                  {topic === t.name && (
                    <motion.span layoutId="tb-topic" className="absolute inset-0 rounded-xl border border-violet-500/30 bg-violet-500/15" transition={{ type: "spring", stiffness: 420, damping: 34 }} />
                  )}
                  <span className={`relative flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${t.read_at ? "border-emerald-400/60 bg-emerald-400/20 text-emerald-300" : "border-white/15"}`}>
                    {t.read_at && <Check className="h-3 w-3" />}
                  </span>
                  <span className="relative min-w-0 flex-1 truncate">{t.name}</span>
                  {t.has_article && <Sparkles className="relative h-3.5 w-3.5 shrink-0 text-violet-300/70" title="Статья готова" />}
                  <span className="relative text-[11px] tabular-nums text-zinc-600">{t.cards || ""}</span>
                </button>
              ))}
                </div>
              ))}
            </div>
          )}
          {book && (
            <div className="mt-4 border-t border-white/[0.06] pt-3 text-[11px] leading-relaxed text-zinc-500">
              {book.sources.length ? (
                <>
                  <Library className="mr-1 inline h-3 w-3" /> {book.sources.length > 1 ? "Источники" : "Источник"}:{" "}
                  {book.sources.map((s, i) => (
                    <span key={s.id}>
                      {i > 0 && ", "}
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-zinc-300 hover:text-white">{s.title}</a>
                    </span>
                  ))}
                </>
              ) : (
                <>База знаний для этой колоды ещё не загружена — статьи строятся по материалам карточек.</>
              )}
              {book.videos > 0 && (
                <div className="mt-1.5"><PlayCircle className="mr-1 inline h-3 w-3" /> Видеоуроков в базе: {book.videos}</div>
              )}
              {user.is_admin && book.topics.some((t) => !t.has_article) && (
                <button className="btn-ghost mt-3 w-full justify-center py-1.5 text-xs" onClick={generateDeck}>
                  <Sparkles className="h-3.5 w-3.5" /> Написать статьи для всех тем ({book.topics.filter((t) => !t.has_article).length})
                </button>
              )}
            </div>
          )}
        </aside>

        {/* статья */}
        <div className="min-w-0">
          {!topic ? (
            <div className="glass">
              <EmptyState
                icon={<BookOpenText className="h-6 w-6" />}
                title={book?.book ? "Выберите урок" : "Выберите тему"}
                text="Статья будет сгенерирована по документации и карточкам темы, сохранится и откроется мгновенно в следующий раз."
              />
            </div>
          ) : (
            <Article
              key={`${deckId}|${topic}`}
              user={user}
              deck={deck}
              deckId={deckId}
              topic={topic}
              info={book?.topics.find((t) => t.name === topic)}
              onRead={(read_at) => updateTopic(topic, { read_at })}
              onWritten={() => updateTopic(topic, { has_article: true })}
              onStart={onStart}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function DeckPicker({ decks, value, onChange }) {
  const [open, setOpen] = useState(false);
  const current = decks.find((d) => d.deck_id === value);
  const k = kindOf(current);
  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [open]);
  return (
    <div className="relative" onClick={(e) => e.stopPropagation()}>
      <button className="btn-ghost min-w-[240px] justify-between" onClick={() => setOpen((o) => !o)}>
        <span className="flex items-center gap-2 truncate">
          <k.icon className={`h-4 w-4 ${k.text}`} /> {current?.name || "Колода"}
        </span>
        <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="glass absolute right-0 z-30 mt-2 max-h-[60vh] w-72 overflow-y-auto bg-ink-850/95 p-1.5"
          >
            {decks.map((d) => {
              const dk = kindOf(d);
              return (
                <button
                  key={d.deck_id}
                  onClick={() => { onChange(d.deck_id); setOpen(false); }}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm ${d.deck_id === value ? "bg-white/[0.08] text-white" : "text-zinc-300 hover:bg-white/[0.05]"}`}
                >
                  <dk.icon className={`h-4 w-4 ${dk.text}`} />
                  <span className="flex-1 truncate">{d.name}</span>
                  {d.language === "php" && <span className="rounded bg-violet-500/20 px-1.5 text-[10px] font-semibold text-violet-200">docs</span>}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Article({ user, deck, deckId, topic, info, onRead, onWritten, onStart }) {
  const toast = useToast();
  const [content, setContent] = useState("");
  const [sources, setSources] = useState([]);
  const [meta, setMeta] = useState({});
  const [status, setStatus] = useState("loading"); // loading | searching | writing | done | error
  const [error, setError] = useState("");
  const [readAt, setReadAt] = useState(info?.read_at || null);
  const [starting, setStarting] = useState(false);
  const abortRef = useRef(null);
  const endRef = useRef(null);

  const generate = useCallback(
    async (regenerate = false) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setContent("");
      setError("");
      setStatus("searching");
      try {
        await apiStream(
          `/api/textbook/${deckId}/article/stream`,
          { topic, regenerate },
          (ev) => {
            if (ev.type === "sources") {
              setSources(ev.sources || []);
              setMeta({ cached: ev.cached, model: ev.model, retrieval: ev.retrieval });
              setStatus("writing");
            } else if (ev.type === "delta") setContent((c) => c + ev.text);
            else if (ev.type === "error") {
              setError(ev.message);
              setStatus("error");
            } else if (ev.type === "done") {
              setStatus("done");
              if (!ev.cached) onWritten();
            }
          },
          { signal: ctrl.signal },
        );
      } catch (e) {
        if (e.name !== "AbortError") {
          setError(e.message);
          setStatus("error");
        }
      }
    },
    [deckId, topic, onWritten],
  );

  useEffect(() => {
    generate(false);
    return () => abortRef.current?.abort();
  }, [generate]);

  async function toggleRead(read = !readAt) {
    try {
      const r = await api(`/api/textbook/${deckId}/read`, { method: "POST", body: { topic, read } });
      setReadAt(r.read_at || null);
      onRead(r.read_at || null);
    } catch (e) {
      toast(e.message, "error");
    }
  }

  // дочитали до конца — отмечаем автоматически
  useEffect(() => {
    if (status !== "done" || readAt || !endRef.current) return;
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        toggleRead(true);
        toast("Тема отмечена как прочитанная", "success");
        io.disconnect();
      }
    }, { threshold: 1 });
    io.observe(endRef.current);
    return () => io.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, readAt]);

  async function practice() {
    setStarting(true);
    try {
      const cardTopic = info?.card_topic || undefined;
      let s = await api("/api/session", { method: "POST", body: { deck_id: deckId, mode: "due", topic: cardTopic } });
      if (s.empty) s = await api("/api/session", { method: "POST", body: { deck_id: deckId, mode: "all", topic: cardTopic } });
      if (s.empty) toast("В теме нет карточек", "info");
      else onStart(s);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setStarting(false);
    }
  }

  // модель иногда начинает с заголовка-названия темы — он уже есть в шапке
  const body = useMemo(() => {
    const m = content.match(/^\s*#{1,3}\s*\**(.+?)\**\s*(\n|$)/);
    return m && m[1].trim().toLowerCase() === topic.trim().toLowerCase() ? content.slice(m[0].length) : content;
  }, [content, topic]);
  const headings = useMemo(() => (status === "done" ? extractHeadings(body) : []), [body, status]);
  // [[video:n]] на отдельной строке — плеер видеофрагмента n
  const pieces = useMemo(() => {
    const out = [];
    let last = 0;
    const re = /^[ \t]*\[\[video:(\d+)\]\][ \t]*$/gm;
    for (const m of body.matchAll(re)) {
      if (m.index > last) out.push({ text: body.slice(last, m.index) });
      const src = sources.find((s) => s.n === Number(m[1]) && s.video);
      if (src) out.push({ video: src });
      last = m.index + m[0].length;
    }
    out.push({ text: body.slice(last) });
    return out.filter((p) => p.video || p.text.trim());
  }, [body, sources]);
  const restVideos = useMemo(() => {
    const embedded = new Set(pieces.filter((p) => p.video).map((p) => p.video.video));
    const seen = new Set();
    return sources.filter((s) => s.video && !embedded.has(s.video) && !seen.has(s.video) && seen.add(s.video));
  }, [pieces, sources]);
  const k = kindOf(deck);
  const lang = deck?.language;

  return (
    <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_220px]">
      <div className="min-w-0 space-y-5">
        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass relative overflow-hidden p-6 sm:p-8">
          <div className={`pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b ${k.grad} opacity-40`} />
          <div className="relative mb-5 flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className={`mb-1 text-xs font-semibold uppercase tracking-widest ${k.text}`}>
                {info?.chapter ? `${deck?.name} · ${info.chapter}` : deck?.name}
              </div>
              <h2 className="text-2xl font-extrabold tracking-tight sm:text-3xl">{topic}</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {info?.cards > 0 && <span className="chip">{info.cards} карточек</span>}
                {sources.length > 0 && <span className="chip"><Library className="h-3 w-3" /> {sources.length} фрагм. документации</span>}
                {meta.retrieval === "hybrid" && <span className="chip text-violet-200">поиск: смысловой + BM25</span>}
                {readAt && <span className="chip border-emerald-500/30 text-emerald-300"><Check className="h-3 w-3" /> прочитано</span>}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className={`btn-ghost ${readAt ? "border-emerald-500/30 text-emerald-200" : ""}`} onClick={() => toggleRead()}>
                <BookMarked className="h-4 w-4" /> {readAt ? "Прочитано" : "Отметить прочитанным"}
              </button>
              <motion.button whileTap={{ scale: 0.97 }} className="btn-primary" onClick={practice} disabled={starting}>
                {starting ? <Spinner /> : <GraduationCap className="h-4 w-4" />} Проверить себя
              </motion.button>
            </div>
          </div>

          <div className="relative">
            {(status === "searching" || status === "loading") && <Preparing stage="search" />}
            {status === "writing" && !content && <Preparing stage="write" />}
            {status === "error" && (
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200">
                {error}
                <button className="ml-3 font-semibold underline" onClick={() => generate(false)}>Повторить</button>
              </div>
            )}
            {content && (
              <div className={`article-body ${status === "writing" ? "stream-caret" : ""}`}>
                {pieces.map((p, i) =>
                  p.video ? (
                    <VideoEmbed key={i} src={p.video} />
                  ) : (
                    <RichText key={i} text={p.text} sources={sources} codeLanguage={lang} />
                  ),
                )}
              </div>
            )}
            {status === "done" && restVideos.length > 0 && (
              <div className="mt-8">
                <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-zinc-500">
                  <PlayCircle className="h-3.5 w-3.5" /> Видео по теме
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  {restVideos.map((s) => <VideoEmbed key={s.n} src={s} compact />)}
                </div>
              </div>
            )}
          </div>

          {status === "done" && sources.length > 0 && (
            <div className="relative mt-8 border-t border-white/[0.06] pt-5">
              <div className="mb-3 text-xs font-semibold uppercase tracking-widest text-zinc-500">Источники</div>
              <ol className="space-y-1.5 text-sm">
                {sources.map((s) => (
                  <li key={s.n} className="flex gap-2">
                    <span className="cite translate-y-0.5">{s.n}</span>
                    <a href={s.url} target="_blank" rel="noreferrer" className="group inline-flex min-w-0 items-center gap-1 text-zinc-300 hover:text-white">
                      <span className="truncate">{s.title}</span>
                      <ExternalLink className="h-3 w-3 shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
                    </a>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {status === "done" && (
            <div ref={endRef} className="relative mt-6 flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-500">
              <span>
                {meta.cached ? "Сохранённая статья" : "Статья сгенерирована"}
                {meta.model ? ` · ${meta.model}` : ""}
              </span>
              {user.is_admin && (
                <button className="inline-flex items-center gap-1.5 text-zinc-400 hover:text-white" onClick={() => generate(true)}>
                  <RefreshCw className="h-3.5 w-3.5" /> Сгенерировать заново
                </button>
              )}
            </div>
          )}
        </motion.section>

        {status === "done" && user.is_admin && <VideoDebug deckId={deckId} topic={topic} />}
        {status === "done" && <AskBox deckId={deckId} topic={topic} lang={lang} />}
      </div>
      <FloatingPlayer />

      {/* оглавление */}
      <nav className="hidden 2xl:block">
        {headings.length > 0 && <Toc headings={headings} />}
      </nav>
    </div>
  );
}

const VSTATUS = { queued: "в очереди", processing: "расшифровка", done: "готово", error: "ошибка", missing: "файл пропал", skipped: "исключено" };

/** Админ: какие видео учебника рассматривались для урока и с каким сходством. */
function VideoDebug({ deckId, topic }) {
  const [open, setOpen] = useState(false);
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    if (!open) return;
    setD(null);
    setErr("");
    api(`/api/textbook/${deckId}/videos-debug?topic=${encodeURIComponent(topic)}`).then(setD).catch((e) => setErr(e.message));
  }, [open, deckId, topic]);
  return (
    <section className="glass p-4 text-xs text-zinc-400">
      <button className="flex items-center gap-2 font-semibold text-zinc-300" onClick={() => setOpen((o) => !o)}>
        <PlayCircle className="h-3.5 w-3.5" /> Подбор видео для урока (диагностика)
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && !d && !err && <div className="mt-3"><Spinner /></div>}
      {err && <div className="mt-3 text-rose-300">{err}</div>}
      {d && (
        <div className="mt-3 space-y-3">
          {!d.book ? (
            <div>У колоды нет программы учебника — видео не подбираются.</div>
          ) : (
            <>
              <div>
                Учебник <b className="text-zinc-200">{d.book}</b> · порог сходства <b className="text-zinc-200">{d.threshold}</b> ·
                {" "}эмбеддинги {d.embedding ? "работают" : <span className="text-rose-300">недоступны — подбор только по словам</span>}
                <div className="mt-1 font-mono text-[11px] text-zinc-500">запрос: {d.query}</div>
              </div>
              <div>
                <div className="mb-1 font-semibold text-zinc-300">Видео этого учебника: {d.videos.length}</div>
                {d.videos.length === 0 && <div className="text-amber-300">Ни одно видео не привязано к учебнику — выберите учебник в Настройках → «Видеотека учебника».</div>}
                {d.videos.slice(0, 30).map((v) => (
                  <div key={v.id} className="flex gap-2">
                    <span className="min-w-0 flex-1 truncate">{v.folder ? `${v.folder} / ` : ""}{v.title}</span>
                    <span className={v.status === "done" ? "text-emerald-300" : "text-amber-300"}>{VSTATUS[v.status] || v.status}</span>
                    <span className={v.chunks && v.embedded < v.chunks ? "text-amber-300" : ""}>векторов {v.embedded}/{v.chunks}</span>
                  </div>
                ))}
              </div>
              <div>
                <div className="mb-1 font-semibold text-zinc-300">Лучшие фрагменты</div>
                {d.candidates.length === 0 && <div>Нет ни одного кандидата.</div>}
                {d.candidates.map((c, i) => (
                  <div key={i} className="mb-1.5">
                    <span className={`mr-2 font-mono ${c.passed ? "text-emerald-300" : "text-zinc-500"}`}>{c.how === "words" ? "слова" : c.score.toFixed(3)}</span>
                    <span className="text-zinc-200">{c.title}</span> <span className="text-zinc-500">{c.section}</span>
                    <div className="truncate text-zinc-500">{c.text}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}

function VideoEmbed({ src, compact = false }) {
  const ref = useRef(null);
  const [failed, setFailed] = useState(false);
  const label = (src.title || "").replace(/^Видео:\s*/, "");
  return (
    <figure className={`overflow-hidden rounded-2xl border border-white/[0.08] bg-black/40 ${compact ? "" : "my-6"}`}>
      {failed ? (
        <div className="flex aspect-video items-center justify-center p-6 text-center text-sm text-zinc-400">
          Браузер не может воспроизвести этот формат видео (например, MKV/AVI). Расшифровка фрагмента учтена в статье.
        </div>
      ) : (
        <video
          ref={ref}
          className="aspect-video w-full bg-black"
          controls
          preload="metadata"
          src={`${videoFileUrl(src.video)}#t=${src.start || 0}`}
          onError={() => setFailed(true)}
        />
      )}
      <figcaption className="flex items-center justify-between gap-3 px-4 py-2.5 text-xs text-zinc-400">
        <span className="min-w-0 truncate" title={label}>
          <span className="cite mr-1.5">{src.n}</span>
          {label}
        </span>
        <button
          className="shrink-0 rounded-md px-2 py-1 text-violet-200 hover:bg-white/[0.06]"
          onClick={() => {
            const v = ref.current;
            if (!v) return;
            v.currentTime = src.start || 0;
            v.play().catch(() => {});
          }}
        >
          ▶ с {fmtTime(src.start)}
        </button>
      </figcaption>
    </figure>
  );
}

/** Плеер, который открывают сноски на видео (в статье и в ответах «Спросить учебник»). */
function FloatingPlayer() {
  const [src, setSrc] = useState(null);
  useEffect(() => {
    const open = (e) => setSrc({ ...e.detail, key: Date.now() });
    window.addEventListener("textbook:video", open);
    return () => window.removeEventListener("textbook:video", open);
  }, []);
  return (
    <AnimatePresence>
      {src && (
        <motion.div
          key="fp"
          initial={{ opacity: 0, y: 30, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 30, scale: 0.96 }}
          className="fixed bottom-4 right-4 z-50 w-[min(440px,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-white/10 bg-ink-900 shadow-2xl"
        >
          <video
            key={src.key}
            className="aspect-video w-full bg-black"
            controls
            autoPlay
            src={`${videoFileUrl(src.video)}#t=${src.start || 0}`}
          />
          <div className="flex items-center gap-2 px-3 py-2 text-xs text-zinc-400">
            <span className="min-w-0 flex-1 truncate">{(src.title || "").replace(/^Видео:\s*/, "")}</span>
            <button className="rounded-md p-1 hover:bg-white/[0.08] hover:text-white" onClick={() => setSrc(null)} aria-label="Закрыть">
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Preparing({ stage }) {
  const steps = [
    { id: "search", label: "Ищу фрагменты в документации" },
    { id: "write", label: "Пишу статью по найденным материалам" },
  ];
  const active = steps.findIndex((s) => s.id === stage);
  return (
    <div className="space-y-4 py-2">
      {steps.map((s, i) => (
        <div key={s.id} className={`flex items-center gap-3 text-sm ${i <= active ? "text-zinc-200" : "text-zinc-600"}`}>
          {i < active ? <Check className="h-4 w-4 text-emerald-400" /> : i === active ? <Spinner className="h-4 w-4 text-violet-300" /> : <span className="h-4 w-4 rounded-full border border-white/15" />}
          {s.label}
        </div>
      ))}
      <div className="space-y-2.5 pt-2">
        {[92, 100, 76, 88, 60].map((w, i) => (
          <motion.div
            key={i}
            className="h-3 rounded-full bg-white/[0.06]"
            style={{ width: `${w}%` }}
            animate={{ opacity: [0.4, 0.9, 0.4] }}
            transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.12 }}
          />
        ))}
      </div>
    </div>
  );
}

function Toc({ headings }) {
  const [active, setActive] = useState(headings[0]?.id);
  useEffect(() => {
    const els = headings.map((h) => document.getElementById(h.id)).filter(Boolean);
    const io = new IntersectionObserver(
      (entries) => {
        const vis = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (vis[0]) setActive(vis[0].target.id);
      },
      { rootMargin: "0px 0px -70% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [headings]);
  return (
    <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="sticky top-6">
      <div className="mb-3 text-xs font-semibold uppercase tracking-widest text-zinc-500">Содержание</div>
      <ul className="space-y-1 border-l border-white/[0.07]">
        {headings.map((h) => (
          <li key={h.id}>
            <a
              href={`#${h.id}`}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById(h.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
              className={`-ml-px block border-l py-1 text-[13px] transition-colors ${h.level >= 3 ? "pl-6" : "pl-3"} ${active === h.id ? "border-violet-400 text-white" : "border-transparent text-zinc-500 hover:text-zinc-200"}`}
            >
              {h.text}
            </a>
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

function AskBox({ deckId, topic, lang }) {
  const toast = useToast();
  const [question, setQuestion] = useState("");
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const [listRef] = useAutoAnimate({ duration: 220 });

  async function ask(e) {
    e?.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    const id = Date.now();
    setItems((xs) => [{ id, q, a: "", sources: [], done: false }, ...xs]);
    setQuestion("");
    setBusy(true);
    const patch = (fn) => setItems((xs) => xs.map((x) => (x.id === id ? fn(x) : x)));
    try {
      await apiStream(`/api/textbook/${deckId}/ask`, { topic, question: q }, (ev) => {
        if (ev.type === "sources") patch((x) => ({ ...x, sources: ev.sources }));
        else if (ev.type === "delta") patch((x) => ({ ...x, a: x.a + ev.text }));
        else if (ev.type === "error") patch((x) => ({ ...x, a: `❌ ${ev.message}`, done: true }));
        else if (ev.type === "done") patch((x) => ({ ...x, done: true }));
      });
    } catch (err) {
      toast(err.message, "error");
      patch((x) => ({ ...x, done: true }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass p-5 sm:p-6">
      <h3 className="mb-1 flex items-center gap-2 font-semibold">
        <MessageCircleQuestion className="h-4 w-4 text-violet-300" /> Спросить учебник
      </h3>
      <p className="mb-4 text-xs text-zinc-500">Ответ ищется в той же базе знаний — с ссылками на документацию.</p>
      <form onSubmit={ask} className="flex gap-2">
        <input className="input" placeholder={`Например: чем отличается … в теме «${topic}»?`} value={question} onChange={(e) => setQuestion(e.target.value)} />
        <motion.button whileTap={{ scale: 0.95 }} className="btn-primary shrink-0 px-3.5" disabled={busy || !question.trim()} aria-label="Спросить">
          {busy ? <Spinner /> : <Send className="h-4 w-4" />}
        </motion.button>
      </form>
      <div ref={listRef} className="mt-4 space-y-3">
        {items.map((it) => (
          <div key={it.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <div className="mb-2 text-sm font-semibold text-white">{it.q}</div>
            {it.a ? (
              <div className={`text-sm text-zinc-300 ${it.done ? "" : "stream-caret"}`}>
                <RichText text={it.a} sources={it.sources} codeLanguage={lang} />
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-zinc-500"><Spinner className="h-3.5 w-3.5" /> Ищу ответ…</div>
            )}
          </div>
        ))}
      </div>
    </motion.section>
  );
}
