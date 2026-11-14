import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  BookMarked, BookOpenText, Check, ChevronDown, ExternalLink, GraduationCap, Library, MessageCircleQuestion,
  RefreshCw, Search, Send, Sparkles,
} from "lucide-react";
import { api, apiStream } from "../lib/api";
import { kindOf } from "../lib/decks";
import { extractHeadings, RichText } from "../lib/richtext";
import { EmptyState, Spinner, useToast } from "../components/ui";

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
  const topics = (book?.topics || []).filter((t) => t.name.toLowerCase().includes(query.toLowerCase()));
  const readCount = (book?.topics || []).filter((t) => t.read_at).length;

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
            <div className="text-sm font-semibold">Темы</div>
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
            <div ref={topicsRef} className="max-h-[60vh] space-y-1 overflow-y-auto pr-1">
              {topics.map((t) => (
                <button
                  key={t.name}
                  onClick={() => setTopic(t.name)}
                  className={`relative flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-colors ${topic === t.name ? "text-white" : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100"}`}
                >
                  {topic === t.name && (
                    <motion.span layoutId="tb-topic" className="absolute inset-0 rounded-xl border border-violet-500/30 bg-violet-500/15" transition={{ type: "spring", stiffness: 420, damping: 34 }} />
                  )}
                  <span className={`relative flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${t.read_at ? "border-emerald-400/60 bg-emerald-400/20 text-emerald-300" : "border-white/15"}`}>
                    {t.read_at && <Check className="h-3 w-3" />}
                  </span>
                  <span className="relative min-w-0 flex-1 truncate">{t.name}</span>
                  {t.has_article && <Sparkles className="relative h-3.5 w-3.5 shrink-0 text-violet-300/70" title="Статья готова" />}
                  <span className="relative text-[11px] tabular-nums text-zinc-600">{t.cards}</span>
                </button>
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
                title="Выберите тему"
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
      let s = await api("/api/session", { method: "POST", body: { deck_id: deckId, mode: "due", topic } });
      if (s.empty) s = await api("/api/session", { method: "POST", body: { deck_id: deckId, mode: "all", topic } });
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
  const k = kindOf(deck);
  const lang = deck?.language;

  return (
    <div className="grid gap-5 2xl:grid-cols-[minmax(0,1fr)_220px]">
      <div className="min-w-0 space-y-5">
        <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass relative overflow-hidden p-6 sm:p-8">
          <div className={`pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b ${k.grad} opacity-40`} />
          <div className="relative mb-5 flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className={`mb-1 text-xs font-semibold uppercase tracking-widest ${k.text}`}>{deck?.name}</div>
              <h2 className="text-2xl font-extrabold tracking-tight sm:text-3xl">{topic}</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {info && <span className="chip">{info.cards} карточек</span>}
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
                <RichText text={body} sources={sources} codeLanguage={lang} />
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

        {status === "done" && <AskBox deckId={deckId} topic={topic} lang={lang} />}
      </div>

      {/* оглавление */}
      <nav className="hidden 2xl:block">
        {headings.length > 0 && <Toc headings={headings} />}
      </nav>
    </div>
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
