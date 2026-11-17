import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  BookMarked, BookOpenText, Check, ChevronDown, ExternalLink, GraduationCap, Library, MessageCircleQuestion,
  ArrowDown, ArrowUp, Code2, Layers, Pencil, PlayCircle, Plus, RefreshCw, Search, Send, Sparkles, Trash2, X,
} from "lucide-react";
import { api, apiStream } from "../lib/api";
import { kindOf } from "../lib/decks";
import { extractHeadings, RichText } from "../lib/richtext";
import { EmptyState, Spinner, useToast } from "../components/ui";
import { fmtTime, videoFileUrl } from "../components/VideoLibrary";
import LessonQuiz from "../components/LessonQuiz";

export default function Textbook({ user, decks, reloadDecks, onStart, route = {}, navigate }) {
  const toast = useToast();
  const usable = useMemo(() => (decks || []).filter((d) => !d.error), [decks]);
  const [book, setBook] = useState(null); // /api/textbook/{deck}
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(false);
  const [topicsRef] = useAutoAnimate({ duration: 200 });

  // учебники: по одному на программу (колода «вопросы» учебника) + колоды без программы
  const options = useMemo(() => {
    const out = [];
    const seen = new Set();
    for (const d of usable) {
      if (d.book) {
        if (seen.has(d.book)) continue;
        seen.add(d.book);
        const pick =
          usable.find((x) => x.book === d.book && x.book_deck && x.kind !== "live") || usable.find((x) => x.book === d.book && x.kind !== "live") || d;
        out.push({ key: `b:${d.book}`, book: d.book, title: d.book_title || pick.name, deck: pick });
      } else if (d.kind !== "live") {
        out.push({ key: `d:${d.deck_id}`, book: "", title: d.name, deck: d });
      }
    }
    return out.sort((a, b) => a.title.localeCompare(b.title, "ru"));
  }, [usable]);

  const current = route.book
    ? options.find((o) => o.book === route.book)
    : route.deck
      ? options.find((o) => o.deck.deck_id === route.deck) ||
        (() => {
          const d = usable.find((x) => x.deck_id === route.deck);
          return d ? { key: `d:${d.deck_id}`, book: d.book || "", title: d.name, deck: d } : null;
        })()
      : null;
  const deckId = current?.deck.deck_id || null;
  const topic = route.lesson || "";
  const place = useCallback(
    (o) => (o?.book ? { view: "textbook", book: o.book } : { view: "textbook", deck: o?.deck.deck_id }),
    [],
  );
  const setTopic = useCallback((t, opts) => navigate({ ...place(current), ...(t ? { lesson: t } : {}) }, opts), [navigate, place, current]);

  // учебник по умолчанию — PHP (или первый)
  useEffect(() => {
    if (current || !options.length) return;
    const def = options.find((o) => o.book === "php") || options[0];
    navigate({ ...place(def), ...(route.lesson ? { lesson: route.lesson } : {}) }, { replace: true });
  }, [current, options, navigate, place, route.lesson]);

  const loadBook = useCallback(() => {
    if (!deckId) return Promise.resolve();
    return api(`/api/textbook/${deckId}`)
      .then(setBook)
      .catch((e) => toast(e.message, "error"));
  }, [deckId, toast]);

  useEffect(() => {
    setBook(null);
    setEditing(false);
    loadBook();
  }, [loadBook]);

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

  // переход из карточки/старой колоды: тема колоды → урок программы
  useEffect(() => {
    if (!book || !topic || book.topics.some((t) => t.name === topic)) return;
    const hit = book.topics.find((t) => t.card_topic === topic) || book.topics.find((t) => t.name.toLowerCase().includes(topic.toLowerCase()));
    setTopic(hit ? hit.name : "", { replace: true });
  }, [book, topic, setTopic]);

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

  const openDeck = (kind, lesson = topic) => {
    const id = book?.decks?.[kind];
    if (id) navigate({ view: "decks", deck: id, ...(lesson ? { topic: lesson } : {}) });
  };
  const totals = (book?.topics || []).reduce((a, t) => ({ qa: a.qa + (t.cards || 0), live: a.live + (t.live || 0) }), { qa: 0, live: 0 });

  return (
    <div className="space-y-6">
      {book?.book?.track && <button className="text-sm text-violet-300 hover:text-white" onClick={() => navigate({ view: "tracks", track: book.book.track })}>Вернуться к профессии</button>}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-extrabold tracking-tight">Учебник</h1>
          <p className="text-sm text-zinc-400">Прочитайте урок перед карточками — у каждого урока свои вопросы{book?.book?.has_practice ? " и практические задания" : ""}.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {book?.decks?.qa && (
            <button className="btn-ghost" onClick={() => openDeck("qa", "")} title="Колода вопросов этого учебника">
              <Layers className="h-4 w-4" /> Вопросы <span className="text-zinc-500">{totals.qa}</span>
            </button>
          )}
          {book?.decks?.live && (
            <button className="btn-ghost" onClick={() => openDeck("live", "")} title="Колода практических заданий этого учебника">
              <Code2 className="h-4 w-4" /> {book?.book?.is_code ? "Live-coding" : "Практика"} <span className="text-zinc-500">{totals.live}</span>
            </button>
          )}
          <BookPicker options={options} value={current?.key} onChange={(o) => navigate(place(o))} />
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-[310px_minmax(0,1fr)]">
        {/* программа */}
        <aside className="glass h-fit p-4 lg:sticky lg:top-6">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="min-w-0 truncate text-sm font-semibold">{book?.book ? `Программа: ${book.book.title}` : "Темы"}</div>
            {user.is_admin && book?.book ? (
              <button
                className={`shrink-0 rounded-lg px-2 py-1 text-[11px] ${editing ? "bg-violet-500/20 text-violet-100" : "text-zinc-400 hover:bg-white/[0.06] hover:text-white"}`}
                onClick={() => setEditing((e) => !e)}
                title="Добавить, переименовать, удалить главы и уроки"
              >
                <Pencil className="mr-1 inline h-3 w-3" />
                {editing ? "Готово" : "Править"}
              </button>
            ) : (
              book && <div className="text-xs text-zinc-500">прочитано {readCount}/{book.topics.length}</div>
            )}
          </div>
          {editing && book?.book ? (
            <SyllabusEditor
              bookId={book.book.id}
              current={topic}
              onChanged={(renamed) => {
                loadBook();
                reloadDecks?.().catch?.(() => {});
                if (renamed && renamed.from === topic) setTopic(renamed.to || "", { replace: true });
              }}
            />
          ) : (
            <>
              {book && book.topics.length > 0 && (
                <div className="mb-3 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400" animate={{ width: `${(readCount / book.topics.length) * 100}%` }} />
                </div>
              )}
              <div className="relative mb-3">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
                <input className="input py-2 pl-8 text-xs" placeholder="Найти урок" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
              {!book ? (
                <div className="flex justify-center py-8"><Spinner /></div>
              ) : (
                <div ref={topicsRef} className="max-h-[62vh] space-y-1 overflow-y-auto pr-1">
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
                      {isOpen(ch.title) &&
                        ch.items.map((t) => (
                          <button
                            key={t.name}
                            onClick={() => setTopic(t.name)}
                            title={`${t.name}\n${t.cards || 0} вопросов${book.book?.has_practice ? `, ${t.live || 0} практических заданий` : ""}`}
                            className={`relative flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition-colors ${topic === t.name ? "text-white" : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100"}`}
                          >
                            {topic === t.name && (
                              <span className="absolute inset-0 rounded-xl border border-violet-500/30 bg-violet-500/15" />
                            )}
                            <span className={`relative flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${t.read_at ? "border-emerald-400/60 bg-emerald-400/20 text-emerald-300" : "border-white/15"}`}>
                              {t.read_at && <Check className="h-3 w-3" />}
                            </span>
                            <span className="relative min-w-0 flex-1 truncate">{t.name}</span>
                            {t.has_article && <Sparkles className="relative h-3.5 w-3.5 shrink-0 text-violet-300/70" />}
                            <span className={`relative text-[11px] tabular-nums ${t.cards ? "text-zinc-600" : "text-amber-400/70"}`}>
                              {t.cards || 0}
                              {book.book?.has_practice ? `·${t.live || 0}` : ""}
                            </span>
                          </button>
                        ))}
                    </div>
                  ))}
                </div>
              )}
            </>
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
              {user.is_admin && book.book && <CardsPanel bookId={book.book.id} isCode={book.book.has_practice} targets={book.book.targets} topics={book.topics} onDone={() => { loadBook(); reloadDecks?.().catch?.(() => {}); }} />}
              {user.is_admin && book.topics.some((t) => !t.has_article) && (
                <button className="btn-ghost mt-2 w-full justify-center py-1.5 text-xs" onClick={generateDeck}>
                  <Sparkles className="h-3.5 w-3.5" /> Написать статьи для всех уроков ({book.topics.filter((t) => !t.has_article).length})
                </button>
              )}
            </div>
          )}
        </aside>

        {/* статья */}
        <div className="min-w-0">
          {topic && (!deckId || !book) ? (
            <div className="glass flex justify-center py-16"><Spinner /></div>
          ) : !topic ? (
            <div className="glass">
              <EmptyState
                icon={<BookOpenText className="h-6 w-6" />}
                title={book?.book ? "Выберите урок" : "Выберите тему"}
                text="Статья будет сгенерирована по документации и материалам урока, сохранится и откроется мгновенно в следующий раз."
              />
            </div>
          ) : (
            <Article
              key={`${deckId}|${topic}`}
              user={user}
              deck={deck}
              deckId={deckId}
              topic={topic}
              bookInfo={book?.book}
              bookDecks={book?.decks || {}}
              info={book?.topics.find((t) => t.name === topic)}
              onRead={(read_at) => updateTopic(topic, { read_at })}
              onWritten={() => updateTopic(topic, { has_article: true })}
              onStart={onStart}
              onOpenDeck={openDeck}
              onCardsChanged={() => { loadBook(); reloadDecks?.().catch?.(() => {}); }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function BookPicker({ options, value, onChange }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const current = options.find((o) => o.key === value);
  const k = kindOf(current?.deck);
  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [open]);
  const shown = options.filter((o) => o.title.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="relative" onClick={(e) => e.stopPropagation()}>
      <button className="btn-ghost min-w-[240px] justify-between" onClick={() => setOpen((o) => !o)}>
        <span className="flex items-center gap-2 truncate">
          <k.icon className={`h-4 w-4 ${k.text}`} /> {current?.title || "Учебник"}
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
            className="glass absolute right-0 z-30 mt-2 max-h-[60vh] w-80 overflow-y-auto bg-ink-850/95 p-1.5"
          >
            <input className="input mb-1.5 py-1.5 text-xs" placeholder="Найти учебник" value={q} onChange={(e) => setQ(e.target.value)} autoFocus />
            {shown.map((o) => {
              const dk = kindOf(o.deck);
              return (
                <button
                  key={o.key}
                  onClick={() => { onChange(o); setOpen(false); }}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm ${o.key === value ? "bg-white/[0.08] text-white" : "text-zinc-300 hover:bg-white/[0.05]"}`}
                >
                  <dk.icon className={`h-4 w-4 ${dk.text}`} />
                  <span className="flex-1 truncate">{o.title}</span>
                  {!o.book && <span className="text-[10px] text-zinc-500">колода</span>}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Админ: правка программы — главы и уроки (добавить, переименовать, переставить, удалить). */
function SyllabusEditor({ bookId, current, onChanged }) {
  const toast = useToast();
  const [b, setB] = useState(null);
  const [busy, setBusy] = useState(false);
  const [edit, setEdit] = useState(null); // {type, chapter, lesson, value}
  const [listRef] = useAutoAnimate({ duration: 160 });

  useEffect(() => {
    api(`/api/books/${bookId}`).then(setB).catch((e) => toast(e.message, "error"));
  }, [bookId, toast]);

  async function run(body, renamed) {
    setBusy(true);
    try {
      const r = await api(`/api/books/${bookId}/edit`, { method: "POST", body });
      setB(r);
      setEdit(null);
      onChanged(renamed);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  function submit() {
    const v = (edit?.value || "").trim();
    if (!v) return setEdit(null);
    if (edit.type === "chapter.rename") run({ op: "chapter.rename", chapter: edit.chapter, title: v });
    else if (edit.type === "chapter.add") run({ op: "chapter.add", title: v });
    else if (edit.type === "lesson.rename") run({ op: "lesson.rename", lesson: edit.lesson, title: v }, { from: edit.lesson, to: v });
    else if (edit.type === "lesson.add") run({ op: "lesson.add", chapter: edit.chapter, title: v });
  }

  const input = (
    <input
      autoFocus
      className="input py-1 text-xs"
      value={edit?.value || ""}
      onChange={(e) => setEdit((x) => ({ ...x, value: e.target.value }))}
      onKeyDown={(e) => {
        if (e.key === "Enter") submit();
        if (e.key === "Escape") setEdit(null);
      }}
      onBlur={submit}
      placeholder="Название"
    />
  );

  if (!b) return <div className="flex justify-center py-8"><Spinner /></div>;
  const iconBtn = "rounded p-1 text-zinc-500 hover:bg-white/[0.08] hover:text-white disabled:opacity-30";
  return (
    <div className="space-y-2 text-xs">
      <div className="rounded-lg border border-violet-500/20 bg-violet-500/[0.06] p-2 text-[11px] leading-snug text-zinc-400">
        Двойной клик или ✎ — переименовать. Переименование урока переносит его карточки, статью, видео и отметки;
        удаление урока удаляет его карточки и статью.
      </div>
      <div ref={listRef} className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
        {b.chapters.map((ch, ci) => (
          <div key={ch.title} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-1.5">
            <div className="group flex items-center gap-1">
              {edit?.type === "chapter.rename" && edit.chapter === ch.title ? (
                input
              ) : (
                <span
                  className="min-w-0 flex-1 truncate px-1 font-semibold text-zinc-200"
                  onDoubleClick={() => setEdit({ type: "chapter.rename", chapter: ch.title, value: ch.title })}
                  title={ch.title}
                >
                  {ch.title}
                </span>
              )}
              <button className={iconBtn} disabled={busy || ci === 0} title="Выше" onClick={() => run({ op: "chapter.move", chapter: ch.title, delta: -1 })}><ArrowUp className="h-3 w-3" /></button>
              <button className={iconBtn} disabled={busy || ci === b.chapters.length - 1} title="Ниже" onClick={() => run({ op: "chapter.move", chapter: ch.title, delta: 1 })}><ArrowDown className="h-3 w-3" /></button>
              <button className={iconBtn} disabled={busy} title="Переименовать главу" onClick={() => setEdit({ type: "chapter.rename", chapter: ch.title, value: ch.title })}><Pencil className="h-3 w-3" /></button>
              <button
                className={`${iconBtn} hover:text-rose-300`}
                disabled={busy}
                title="Удалить главу"
                onClick={() => {
                  const n = ch.lessons.reduce((a, l) => a + l.qa + l.live, 0);
                  if (confirm(`Удалить главу «${ch.title}» и все её уроки (${ch.lessons.length}) вместе с ${n} карточками и статьями?`))
                    run({ op: "chapter.delete", chapter: ch.title }, ch.lessons.some((l) => l.title === current) ? { from: current, to: "" } : null);
                }}
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
            <div className="mt-1 space-y-0.5">
              {ch.lessons.map((l, li) => (
                <div key={l.title} className={`group flex items-center gap-1 rounded px-1 py-0.5 ${l.title === current ? "bg-violet-500/10" : "hover:bg-white/[0.03]"}`}>
                  {edit?.type === "lesson.rename" && edit.lesson === l.title ? (
                    input
                  ) : (
                    <span className="min-w-0 flex-1 truncate text-zinc-300" onDoubleClick={() => setEdit({ type: "lesson.rename", lesson: l.title, value: l.title })} title={l.title}>
                      {l.title}
                    </span>
                  )}
                  <span className={`shrink-0 tabular-nums text-[10px] ${l.qa ? "text-zinc-600" : "text-amber-400/80"}`}>{l.qa}{b.has_practice ? `·${l.live}` : ""}</span>
                  <span className="flex shrink-0 opacity-0 transition-opacity group-hover:opacity-100">
                    <button className={iconBtn} disabled={busy || (ci === 0 && li === 0)} title="Выше" onClick={() => run({ op: "lesson.move", lesson: l.title, delta: -1 })}><ArrowUp className="h-3 w-3" /></button>
                    <button className={iconBtn} disabled={busy || (ci === b.chapters.length - 1 && li === ch.lessons.length - 1)} title="Ниже" onClick={() => run({ op: "lesson.move", lesson: l.title, delta: 1 })}><ArrowDown className="h-3 w-3" /></button>
                    <button className={iconBtn} disabled={busy} title="Переименовать" onClick={() => setEdit({ type: "lesson.rename", lesson: l.title, value: l.title })}><Pencil className="h-3 w-3" /></button>
                    <button
                      className={`${iconBtn} hover:text-rose-300`}
                      disabled={busy}
                      title="Удалить урок"
                      onClick={() => {
                        if (confirm(`Удалить урок «${l.title}»? Будут удалены ${l.qa + l.live} карточек урока и его статья.`))
                          run({ op: "lesson.delete", lesson: l.title }, l.title === current ? { from: current, to: "" } : null);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </span>
                </div>
              ))}
              {edit?.type === "lesson.add" && edit.chapter === ch.title ? (
                <div className="px-1">{input}</div>
              ) : (
                <button className="w-full rounded px-1 py-1 text-left text-[11px] text-zinc-500 hover:bg-white/[0.04] hover:text-violet-200" disabled={busy} onClick={() => setEdit({ type: "lesson.add", chapter: ch.title, value: "" })}>
                  <Plus className="mr-1 inline h-3 w-3" /> Урок
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      {edit?.type === "chapter.add" ? (
        input
      ) : (
        <button className="btn-ghost w-full justify-center py-1.5 text-xs" disabled={busy} onClick={() => setEdit({ type: "chapter.add", value: "" })}>
          <Plus className="h-3.5 w-3.5" /> Глава
        </button>
      )}
    </div>
  );
}

/** Админ: карточки учебника — сколько есть, где не хватает, догенерация выбранной моделью. */
function CardsPanel({ bookId, isCode, targets = { qa: 8, live: 3 }, topics, onDone }) {
  const toast = useToast();
  const [job, setJob] = useState(null);
  const thin = topics.filter((t) => (t.cards || 0) < targets.qa || (isCode && (t.live || 0) < targets.live)).length;
  const wasRunning = useRef(false);

  useEffect(() => {
    let timer;
    let alive = true;
    const tick = () =>
      api("/api/books-job")
        .then((j) => {
          if (!alive) return;
          setJob(j);
          if (wasRunning.current && !j.running) onDone();
          wasRunning.current = j.running;
          timer = setTimeout(tick, j.running ? 3000 : 20000);
        })
        .catch(() => {});
    tick();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  async function start() {
    try {
      const r = await api("/api/books/generate", { method: "POST", body: { book: bookId } });
      toast(r.queued ? `Уроков в очереди: ${r.queued}` : "Во всех уроках карточек достаточно", r.queued ? "success" : "info");
      setJob(await api("/api/books-job"));
      wasRunning.current = true;
    } catch (e) {
      toast(e.message, "error");
    }
  }

  return (
    <div className="mt-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
      <div className="flex items-center justify-between gap-2">
        <span>Уроков с нехваткой карточек: <b className={thin ? "text-amber-300" : "text-emerald-300"}>{thin}</b></span>
        {job?.running ? (
          <button className="rounded px-2 py-1 text-[11px] text-rose-200 hover:bg-white/[0.06]" onClick={() => api("/api/books/generate/stop", { method: "POST" })}>Стоп</button>
        ) : (
          <button className="rounded px-2 py-1 text-[11px] text-violet-200 hover:bg-white/[0.06] disabled:opacity-40" disabled={!thin} onClick={start}>
            <Sparkles className="mr-1 inline h-3 w-3" /> Догенерировать
          </button>
        )}
      </div>
      <div className="mt-1 text-[10px] text-zinc-600">минимум на урок: {targets.qa} вопросов{isCode ? ` и ${targets.live} практических заданий` : ""}</div>
      {job?.running && (
        <div className="mt-1.5 text-violet-200">
          {job.done}/{job.total} · {job.current}
          <div className="text-zinc-500">+{job.added_qa} вопросов{isCode ? `, +${job.added_live} практических заданий` : ""}</div>
          <div className="text-zinc-500">Осталось добавить: {job.remaining_qa} вопросов, {job.remaining_live} заданий</div>
        </div>
      )}
      {!job?.running && job?.log?.length > 0 && <div className="mt-1.5 text-zinc-500">{job.log[job.log.length - 1]}</div>}
    </div>
  );
}

function Article({ user, deck, deckId, topic, info, bookInfo, bookDecks = {}, onRead, onWritten, onStart, onOpenDeck, onCardsChanged }) {
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

  // колоды учебника: тема = урок; иначе — тема колоды, ближайшая к уроку
  async function practice(kind = "qa") {
    const target = bookDecks[kind] || (kind === "qa" ? deckId : null);
    if (!target) return;
    const cardTopic = bookDecks[kind] ? topic : info?.card_topic || undefined;
    setStarting(kind);
    try {
      let s = await api("/api/session", { method: "POST", body: { deck_id: target, mode: "due", topic: cardTopic } });
      if (s.empty) s = await api("/api/session", { method: "POST", body: { deck_id: target, mode: "all", topic: cardTopic } });
      if (s.empty) toast(kind === "live" ? "В уроке пока нет практических заданий" : "В уроке пока нет карточек", "info");
      else onStart(s);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setStarting(false);
    }
  }

  async function generateCards() {
    try {
      const r = await api("/api/books/generate", { method: "POST", body: { book: bookInfo.id, lesson: topic } });
      toast(r.queued ? "Карточки урока генерируются в фоне — появятся через минуту-другую" : "Карточек урока уже достаточно", r.queued ? "success" : "info");
      if (r.queued) {
        const wait = async () => {
          const j = await api("/api/books-job").catch(() => null);
          if (j?.running) setTimeout(wait, 3000);
          else onCardsChanged?.();
        };
        setTimeout(wait, 3000);
      }
    } catch (e) {
      toast(e.message, "error");
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
                {info && (
                  <button className="chip hover:text-white" onClick={() => onOpenDeck?.("qa", topic)} disabled={!bookDecks.qa} title="Открыть колоду на этом уроке">
                    <Layers className="h-3 w-3" /> {info.cards || 0} вопросов
                  </button>
                )}
                {bookInfo?.has_practice && info && (
                  <button className="chip hover:text-white" onClick={() => onOpenDeck?.("live", topic)} disabled={!bookDecks.live} title="Открыть практические задания этого урока">
                    <Code2 className="h-3 w-3" /> {info.live || 0} заданий
                  </button>
                )}
                {sources.length > 0 && <span className="chip"><Library className="h-3 w-3" /> {sources.length} фрагм. документации</span>}
                {meta.retrieval === "hybrid" && <span className="chip text-violet-200">поиск: смысловой + BM25</span>}
                {readAt && <span className="chip border-emerald-500/30 text-emerald-300"><Check className="h-3 w-3" /> прочитано</span>}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className={`btn-ghost ${readAt ? "border-emerald-500/30 text-emerald-200" : ""}`} onClick={() => toggleRead()}>
                <BookMarked className="h-4 w-4" /> {readAt ? "Прочитано" : "Отметить прочитанным"}
              </button>
              {bookInfo?.has_practice && bookDecks.live && (
                <button className="btn-ghost" onClick={() => practice("live")} disabled={!!starting || !info?.live}>
                  {starting === "live" ? <Spinner /> : <Code2 className="h-4 w-4" />} {bookInfo.is_code ? "Live-coding" : "Практика"}
                </button>
              )}
              <motion.button whileTap={{ scale: 0.97 }} className="btn-primary" onClick={() => practice("qa")} disabled={!!starting || (bookDecks.qa && !info?.cards)}>
                {starting === "qa" ? <Spinner /> : <GraduationCap className="h-4 w-4" />} Проверить себя
              </motion.button>
              {user.is_admin && bookInfo && info && (info.cards < (bookInfo.targets?.qa ?? 8) || (bookInfo.has_practice && info.live < (bookInfo.targets?.live ?? 3))) && (
                <button className="btn-ghost" onClick={generateCards} title="Догенерировать карточки этого урока выбранной моделью учебника">
                  <Sparkles className="h-4 w-4" /> Карточки
                </button>
              )}
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

        {status === "done" && user.is_admin && <LessonVideos deckId={deckId} topic={topic} sources={sources} onChanged={() => generate(false)} />}
        {bookInfo && <LessonQuiz book={bookInfo.id} lesson={topic} />}
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

function parseTime(text) {
  const parts = String(text || "").trim().split(":").map((x) => Number(x));
  if (!parts.length || parts.some((x) => !isFinite(x))) return null;
  return parts.reduce((acc, x) => acc * 60 + x, 0);
}

/** Админ: какие видео показываются в уроке — убрать лишние, закрепить нужные с нужного момента. */
function LessonVideos({ deckId, topic, sources, onChanged }) {
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [d, setD] = useState(null);
  const [busy, setBusy] = useState("");
  const [q, setQ] = useState("");
  const [pick, setPick] = useState(null); // видео, для которого выбираем момент
  const [listRef] = useAutoAnimate({ duration: 180 });

  const load = useCallback(() => {
    api(`/api/textbook/${deckId}/lesson-videos?topic=${encodeURIComponent(topic)}`).then(setD).catch((e) => toast(e.message, "error"));
  }, [deckId, topic, toast]);
  useEffect(() => {
    if (open) load();
  }, [open, load]);

  async function act(video, action, start = 0) {
    setBusy(`${video}:${action}`);
    try {
      await api(`/api/textbook/${deckId}/lesson-videos`, { method: "POST", body: { topic, video, action, start } });
      setPick(null);
      load();
      onChanged();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy("");
    }
  }

  const shown = sources.filter((s) => s.video);
  const lib = (d?.library || []).filter((v) => {
    const t = `${v.folder} ${v.title}`.toLowerCase();
    return !q || q.toLowerCase().split(/\s+/).every((w) => t.includes(w));
  });

  return (
    <section className="glass p-4 text-sm">
      <button className="flex w-full items-center gap-2 font-semibold text-zinc-200" onClick={() => setOpen((o) => !o)}>
        <PlayCircle className="h-4 w-4 text-rose-300" /> Видео урока
        <span className="text-xs font-normal text-zinc-500">· {shown.length ? `показано ${shown.length}` : "нет"} · правка для администратора</span>
        <ChevronDown className={`ml-auto h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="mt-4 space-y-5">
          {/* что показано сейчас */}
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-zinc-500">Сейчас в уроке</div>
            {shown.length === 0 && <div className="text-xs text-zinc-500">Видео нет — прикрепите из подсказок или видеотеки ниже.</div>}
            <div ref={listRef} className="space-y-1.5">
              {shown.map((s) => (
                <div key={`${s.n}-${s.video}`} className="flex items-center gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                  <span className="cite cite-video">{s.n}</span>
                  <span className="min-w-0 flex-1 truncate text-zinc-200" title={s.title}>{s.title.replace(/^Видео:\s*/, "")}</span>
                  <span className={`chip ${s.pinned ? "border-emerald-500/40 text-emerald-200" : s.attached ? "" : "border-violet-500/30 text-violet-200"}`}>
                    {s.pinned ? "закреплено" : s.attached ? "подобрано" : "в тексте"}
                  </span>
                  {s.pinned && (
                    <button className="btn-ghost px-2 py-1 text-xs" disabled={!!busy} onClick={() => act(s.video, "reset")}>Открепить</button>
                  )}
                  <button className="btn-ghost px-2 py-1 text-xs text-rose-200" disabled={!!busy} onClick={() => act(s.video, "block")}>
                    {busy === `${s.video}:block` ? <Spinner className="h-3 w-3" /> : <X className="h-3 w-3" />} Убрать
                  </button>
                </div>
              ))}
            </div>
            {d?.blocks?.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-zinc-500">
                Скрыто:
                {d.blocks.map((b) => (
                  <button key={b.video} className="chip hover:text-white" title="Вернуть" onClick={() => act(b.video, "reset")}>
                    {b.folder ? `${b.folder} / ` : ""}{b.title} ↺
                  </button>
                ))}
              </div>
            )}
          </div>

          {!d ? (
            <Spinner />
          ) : (
            <>
              {/* подсказки по сходству */}
              <div>
                <div className="mb-2 flex items-baseline justify-between gap-2">
                  <div className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Похожие видео учебника</div>
                  <div className="text-[11px] text-zinc-500">
                    порог {d.threshold}
                    {!d.embedding && <span className="text-amber-300"> · эмбеддинги недоступны, подбор по словам</span>}
                  </div>
                </div>
                {d.suggestions.length === 0 && <div className="text-xs text-zinc-500">Нет расшифрованных видео этого учебника.</div>}
                <div className="space-y-1.5">
                  {d.suggestions.map((c) => (
                    <div key={c.video} className={`rounded-lg border px-3 py-2 ${c.passed ? "border-white/[0.08]" : "border-white/[0.04] opacity-75"}`}>
                      <div className="flex items-center gap-2">
                        <span className={`w-12 shrink-0 font-mono text-xs ${c.passed ? "text-emerald-300" : "text-zinc-500"}`} title={c.passed ? "проходит порог" : "ниже порога"}>
                          {c.how === "words" ? "слова" : c.score.toFixed(2)}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-zinc-200">{c.folder ? `${c.folder} / ` : ""}{c.title}</span>
                        <span className="text-xs text-zinc-500">{c.section}</span>
                        {c.pinned ? (
                          <span className="chip border-emerald-500/40 text-emerald-200">закреплено</span>
                        ) : (
                          <button className="btn-ghost px-2 py-1 text-xs" disabled={!!busy} onClick={() => act(c.video, "pin", c.start)}>Прикрепить</button>
                        )}
                        <button className="btn-ghost px-2 py-1 text-xs" onClick={() => setPick(pick?.id === c.video ? null : { id: c.video, title: c.title })}>Момент…</button>
                      </div>
                      <div className="mt-1 line-clamp-2 pl-14 text-xs text-zinc-500">{c.text}</div>
                      {pick?.id === c.video && <MomentPicker video={pick} onPick={(t) => act(c.video, "pin", t)} />}
                    </div>
                  ))}
                </div>
              </div>

              {/* вся видеотека */}
              <div>
                <div className="mb-2 text-xs font-semibold uppercase tracking-widest text-zinc-500">Добавить из видеотеки</div>
                <div className="relative mb-2">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
                  <input className="input py-2 pl-8 text-xs" placeholder={`Поиск по ${d.library.length} видео: папка или название`} value={q} onChange={(e) => setQ(e.target.value)} />
                </div>
                <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
                  {lib.slice(0, 80).map((v) => (
                    <div key={v.id}>
                      <button
                        className={`flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-xs hover:bg-white/[0.04] ${pick?.id === v.id ? "bg-white/[0.05]" : ""}`}
                        onClick={() => setPick(pick?.id === v.id ? null : { id: v.id, title: v.title })}
                      >
                        <span className="min-w-0 flex-1 truncate text-zinc-300">{v.folder ? `${v.folder} / ` : ""}{v.title}</span>
                        <span className="text-zinc-600">{v.book || "без учебника"}</span>
                        <span className="w-12 text-right font-mono text-zinc-600">{fmtTime(v.duration)}</span>
                      </button>
                      {pick?.id === v.id && <MomentPicker video={pick} onPick={(t) => act(v.id, "pin", t)} />}
                    </div>
                  ))}
                  {lib.length === 0 && <div className="text-xs text-zinc-500">Ничего не найдено</div>}
                </div>
              </div>
            </>
          )}
          <p className="text-[11px] leading-relaxed text-zinc-500">
            Изменения видны сразу: закреплённые видео показываются в блоке «Видео по теме», убранные исчезают (их сноски в
            тексте станут серыми). Чтобы модель процитировала закреплённое видео в тексте — «Сгенерировать заново».
          </p>
        </div>
      )}
    </section>
  );
}

/** Выбор момента видео: по расшифровке (поиск, клик по фразе) или вручную мм:сс. */
function MomentPicker({ video, onPick }) {
  const [segs, setSegs] = useState(null);
  const [q, setQ] = useState("");
  const [manual, setManual] = useState("0:00");
  useEffect(() => {
    api(`/api/videos/${video.id}/transcript`).then((r) => setSegs(r.segments || [])).catch(() => setSegs([]));
  }, [video.id]);
  const list = (segs || []).filter((s) => !q || s.text.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="my-2 ml-3 rounded-lg border border-white/[0.06] bg-ink-900/60 p-3 text-xs">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <input className="input w-56 py-1.5 text-xs" placeholder="Найти фразу в расшифровке" value={q} onChange={(e) => setQ(e.target.value)} />
        <span className="text-zinc-500">или с момента</span>
        <input className="input w-20 py-1.5 text-center font-mono text-xs" value={manual} onChange={(e) => setManual(e.target.value)} />
        <button
          className="btn-primary px-3 py-1.5 text-xs"
          onClick={() => {
            const t = parseTime(manual);
            if (t != null) onPick(t);
          }}
        >
          Закрепить
        </button>
      </div>
      {!segs ? (
        <Spinner className="h-4 w-4" />
      ) : (
        <div className="max-h-48 overflow-y-auto">
          {list.slice(0, 200).map((s, i) => (
            <button key={i} className="group flex w-full gap-2 rounded px-2 py-1 text-left hover:bg-white/[0.05]" onClick={() => onPick(s.start)} title="Закрепить с этого момента">
              <span className="shrink-0 font-mono text-zinc-600 group-hover:text-emerald-300">{fmtTime(s.start)}</span>
              <span className="text-zinc-300">{s.text}</span>
            </button>
          ))}
          {list.length === 0 && <div className="text-zinc-500">Ничего не найдено</div>}
        </div>
      )}
    </div>
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
          {src.pinned && <span className="mr-1.5 text-emerald-300" title="Закреплено администратором">📌</span>}
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
