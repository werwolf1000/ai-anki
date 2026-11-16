import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  ArrowLeft, ArrowRight, BookOpenText, CheckCircle2, CornerDownLeft, HelpCircle, ImageOff, Lightbulb, Pencil, RotateCcw, Send, Trophy, XCircle,
} from "lucide-react";
import { api, serverUrl } from "../lib/api";
import { kindOf, modeLabel, plural } from "../lib/decks";
import { CodeBlock, RichText } from "../lib/richtext";
import { CountUp, Ring, Spinner, useToast } from "../components/ui";
import VoiceButton from "../components/VoiceButton";

const CodeEditor = lazy(() => import("../components/CodeEditor"));
const MathEditor = lazy(() => import("../components/MathEditor"));

const STATUS = {
  passed: { label: "Засчитано", icon: CheckCircle2, cls: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30", color: "#34d399" },
  failed: { label: "Не засчитано", icon: XCircle, cls: "text-rose-300 bg-rose-500/10 border-rose-500/30", color: "#fb7185" },
  follow_up: { label: "Уточняющий вопрос", icon: HelpCircle, cls: "text-sky-300 bg-sky-500/10 border-sky-500/30", color: "#38bdf8" },
  revise: { label: "Нужны правки", icon: Pencil, cls: "text-amber-300 bg-amber-500/10 border-amber-500/30", color: "#fbbf24" },
};

function initialAnswer(card) {
  if (!card) return "";
  if (card.needs_math) return card.math_starter || "";
  if (card.needs_code && !card.is_live_code && card.code) return card.code;
  return "";
}

export default function Study({ session, config, onExit, onRead }) {
  const toast = useToast();
  const [sid, setSid] = useState(session.session_id);
  const [deckName, setDeckName] = useState(session.deck_name);
  const [card, setCard] = useState(session.card);
  const [stats, setStats] = useState(session.stats);
  const [answer, setAnswer] = useState(initialAnswer(session.card));
  const [reviews, setReviews] = useState([]);
  const [hints, setHints] = useState([]);
  const [busy, setBusy] = useState(null); // submit | hint | next
  const [canSubmit, setCanSubmit] = useState(true);
  const [answeredOnce, setAnsweredOnce] = useState(false);
  const [auto, setAuto] = useState(null); // { ms, key }
  const [done, setDone] = useState(false);
  const [cardKey, setCardKey] = useState(0);
  const [voice, setVoice] = useState(null); // { raw, text } — последнее распознавание с ИИ-правками
  const [feedRef] = useAutoAnimate({ duration: 240 });
  const autoTimer = useRef(null);
  const textRef = useRef(null);
  const editorTheme = config?.code_editor_theme || "dark";

  const resetForCard = useCallback((c) => {
    setCard(c);
    setAnswer(initialAnswer(c));
    setReviews([]);
    setHints([]);
    setCanSubmit(true);
    setAnsweredOnce(false);
    setVoice(null);
    setCardKey((k) => k + 1);
  }, []);

  const clearAuto = () => {
    clearTimeout(autoTimer.current);
    setAuto(null);
  };
  useEffect(() => () => clearTimeout(autoTimer.current), []);

  const next = useCallback(async () => {
    clearAuto();
    setBusy("next");
    try {
      const r = await api(`/api/session/${sid}/next`, { method: "POST" });
      setStats(r.stats);
      if (r.done) setDone(true);
      else resetForCard(r.card);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(null);
    }
  }, [sid, resetForCard, toast]);

  const submit = useCallback(async () => {
    if (!canSubmit || busy) return;
    const text = answer.trim();
    if (!text) {
      toast("Сначала напишите ответ", "info");
      return;
    }
    setBusy("submit");
    try {
      const r = await api(`/api/session/${sid}/answer`, { method: "POST", body: { answer: text } });
      setReviews((xs) => [...xs, { ...r.review, answer: text, id: Date.now() }]);
      setStats(r.stats);
      setCanSubmit(r.can_submit);
      setAnsweredOnce(true);
      if (r.clear_answer) setAnswer("");
      if (r.auto_advance_ms > 0) {
        setAuto({ ms: r.auto_advance_ms, key: Date.now() });
        autoTimer.current = setTimeout(next, r.auto_advance_ms);
      }
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(null);
    }
  }, [answer, busy, canSubmit, next, sid, toast]);

  async function hint() {
    setBusy("hint");
    try {
      const r = await api(`/api/session/${sid}/hint`, { method: "POST", body: { draft: answer } });
      setHints((xs) => (xs.includes(r.hint) ? xs : [...xs, r.hint]));
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(null);
    }
  }

  async function restart() {
    setBusy("next");
    try {
      const body = { deck_id: session.deck_id, mode: session.mode };
      if (session.topic) body.topic = session.topic;
      const s = await api("/api/session", { method: "POST", body });
      if (s.empty) {
        toast("Больше нет карточек в этом режиме", "info");
        return;
      }
      setSid(s.session_id);
      setDeckName(s.deck_name);
      setStats(s.stats);
      setDone(false);
      resetForCard(s.card);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(null);
    }
  }

  // Ctrl+Enter — отправить (текстовые карточки), Ctrl+→ — следующая
  useEffect(() => {
    const onKey = (e) => {
      if (e.ctrlKey && e.key === "ArrowRight" && answeredOnce && !busy) {
        e.preventDefault();
        next();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [answeredOnce, busy, next]);

  const position = stats.initial ? Math.min(stats.initial, stats.initial - stats.remaining + 1) : stats.index;
  const progress = stats.initial ? (stats.initial - stats.remaining) / stats.initial : 0;
  const lastReview = reviews[reviews.length - 1];

  return (
    <div className="flex h-full flex-col">
      {/* верхняя панель */}
      <div className="shrink-0 border-b border-white/[0.05] bg-ink-950/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
          <button className="btn-ghost px-3" onClick={onExit}>
            <ArrowLeft className="h-4 w-4" /> <span className="hidden sm:inline">Выйти</span>
          </button>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">{deckName}</div>
            <div className="text-xs text-zinc-500">
              {modeLabel(session.mode)} · карточка {done ? stats.initial : position} из {stats.initial || stats.queue}
            </div>
          </div>
          {onRead && card?.topic && (
            <button
              className="btn-ghost px-3 text-xs"
              onClick={() => onRead(session.deck_id, card.lesson || card.topic)}
              title={`Открыть урок «${card.topic}» в учебнике`}
            >
              <BookOpenText className="h-4 w-4" /> <span className="hidden lg:inline">Урок</span>
            </button>
          )}
          <div className="hidden items-center gap-4 text-xs text-zinc-400 md:flex">
            <span>Ответов <b className="text-zinc-100">{stats.answered}</b></span>
            <span>Зачтено <b className="text-emerald-300">{stats.passed}</b></span>
            <span>Ср. балл <b className="text-zinc-100">{stats.avg_score ?? "—"}</b></span>
            <span>Усвоено <b className="text-zinc-100">{stats.mastered}/{stats.total}</b></span>
          </div>
        </div>
        <div className="h-0.5 bg-white/[0.04]">
          <motion.div className="h-full bg-gradient-to-r from-violet-500 to-rose-500" animate={{ width: `${(done ? 1 : progress) * 100}%` }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }} />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          {done ? (
            <Finished key="done" stats={stats} onRestart={restart} onExit={onExit} busy={busy === "next"} />
          ) : (
            <motion.div
              key={cardKey}
              initial={{ opacity: 0, x: 40, rotate: 0.6 }}
              animate={{ opacity: 1, x: 0, rotate: 0 }}
              exit={{ opacity: 0, x: -40, rotate: -0.6 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              className={`mx-auto grid max-w-7xl gap-5 px-4 py-6 sm:px-6 ${card?.needs_code || card?.is_anatomy ? "lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]" : "lg:grid-cols-2"}`}
            >
              <QuestionCard card={card} />

              <div className="space-y-5">
                {/* ответ */}
                <section className="glass p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-zinc-300">
                      {card.needs_math ? "Ваше решение (LaTeX)" : card.needs_code ? (card.is_live_code ? "Напишите решение" : "Исправьте или допишите код") : card.is_anatomy ? "Ваш ответ — ориентируйтесь на схему" : "Ваш ответ своими словами"}
                    </h3>
                    {card.attempts > 0 && (
                      <span className="chip">лучший {card.best_score} · попыток {card.attempts}</span>
                    )}
                  </div>

                  {card.needs_code ? (
                    <Suspense fallback={<EditorFallback />}>
                      <CodeEditor key={cardKey} value={answer} onChange={setAnswer} language={card.language} theme={editorTheme} onSubmit={submit} height={card.is_live_code ? 380 : 300} />
                    </Suspense>
                  ) : card.needs_math ? (
                    <Suspense fallback={<EditorFallback />}>
                      <MathEditor value={answer} onChange={setAnswer} onSubmit={submit} resetKey={cardKey} />
                    </Suspense>
                  ) : (
                    <textarea
                      ref={textRef}
                      autoFocus
                      className="input min-h-[150px] resize-y text-[15px] leading-relaxed"
                      placeholder={lastReview?.status === "follow_up" ? "Ответьте на уточняющий вопрос…" : "Сформулируйте ответ…"}
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.ctrlKey && e.key === "Enter") {
                          e.preventDefault();
                          submit();
                        }
                      }}
                    />
                  )}

                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <motion.button whileTap={{ scale: 0.97 }} className="btn-primary" onClick={submit} disabled={!canSubmit || !!busy}>
                      {busy === "submit" ? <Spinner /> : <Send className="h-4 w-4" />}
                      {busy === "submit" ? "Модель думает…" : lastReview?.status === "revise" ? "Отправить снова" : "Проверить"}
                    </motion.button>
                    {!card.needs_code && !card.needs_math && config?.asr_enabled && (
                      <VoiceButton
                        disabled={!canSubmit || !!busy}
                        context={card.prompt || card.question}
                        onText={(t, r) => {
                          setAnswer(t);
                          setVoice(r?.corrected ? { raw: r.raw, text: t } : null);
                        }}
                        onStatus={(m, k) => toast(m, k)}
                      />
                    )}
                    <button className="btn-ghost" onClick={hint} disabled={!!busy}>
                      {busy === "hint" ? <Spinner /> : <Lightbulb className="h-4 w-4" />} Подсказка
                    </button>
                    <button className={answeredOnce ? "btn-ghost ml-auto border-violet-500/40 text-white" : "btn-ghost ml-auto"} onClick={next} disabled={busy === "next"}>
                      {answeredOnce ? "Следующая" : "Пропустить"} <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                  {voice && answer === voice.text && (
                    <div className="mt-3 rounded-lg border border-violet-500/20 bg-violet-500/[0.06] px-3 py-2 text-xs text-zinc-400">
                      <span className="text-violet-200">Исправлено ИИ.</span> Распознано было: «{voice.raw}»{" "}
                      <button className="font-semibold text-violet-300 hover:text-violet-200" onClick={() => setAnswer(voice.raw)}>
                        вернуть
                      </button>
                    </div>
                  )}
                  <div className="mt-3 flex items-center gap-1.5 text-[11px] text-zinc-500">
                    <CornerDownLeft className="h-3 w-3" /> Ctrl+Enter — проверить{answeredOnce ? " · Ctrl+→ — следующая" : ""}
                  </div>
                </section>

                {/* автопереход */}
                <AnimatePresence>
                  {auto && (
                    <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="glass flex items-center gap-3 overflow-hidden px-4 py-3 text-sm">
                      <span className="text-zinc-300">Следующая карточка через {Math.round(auto.ms / 1000)} с</span>
                      <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                        <motion.div key={auto.key} className="h-full bg-emerald-400" initial={{ width: "100%" }} animate={{ width: "0%" }} transition={{ duration: auto.ms / 1000, ease: "linear" }} />
                      </div>
                      <button className="text-xs font-semibold text-violet-300 hover:text-violet-200" onClick={clearAuto}>Остаться</button>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* обратная связь */}
                <div ref={feedRef} className="space-y-4">
                  {reviews.map((r, i) => (
                    <ReviewCard key={r.id} review={r} latest={i === reviews.length - 1} card={card} />
                  ))}
                  {hints.map((h) => (
                    <div key={h} className="glass flex gap-3 border-amber-500/20 p-4">
                      <Lightbulb className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
                      <RichText text={h} codeLanguage={card.language} math={card.needs_math} className="text-sm text-zinc-200" />
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function EditorFallback() {
  return (
    <div className="flex h-[300px] items-center justify-center rounded-xl border border-white/[0.08] bg-[#0a0a14] text-sm text-zinc-500">
      <Spinner className="mr-2 h-4 w-4" /> Загрузка редактора…
    </div>
  );
}

function QuestionCard({ card }) {
  const [imgError, setImgError] = useState(false);
  const typeLabel = card.is_live_code ? "Live-coding" : card.needs_code ? "Код" : card.needs_math ? "Формула" : card.is_anatomy ? "Анатомия" : "Вопрос";
  const k = kindOf({ kind: card.is_live_code ? "live" : card.needs_code ? "code" : card.needs_math ? "math" : card.is_anatomy ? "anatomy" : "theory" });
  return (
    <section className="glass relative h-fit overflow-hidden p-6 lg:sticky lg:top-6">
      <div className={`pointer-events-none absolute inset-x-0 top-0 h-48 bg-gradient-to-b ${k.grad} opacity-40`} />
      <div className="relative mb-4 flex flex-wrap items-center gap-2">
        <span className={`chip ${k.text}`}>
          <k.icon className="h-3.5 w-3.5" /> {typeLabel}
        </span>
        {card.topic && <span className="chip">{card.topic}</span>}
        {card.language && (card.needs_code || card.code) && <span className="chip font-mono uppercase">{card.language}</span>}
      </div>
      <div className="question-text relative text-[16px] leading-relaxed text-zinc-300">
        <RichText text={card.prompt || card.question} math={card.needs_math} codeLanguage={card.language} />
      </div>
      {card.code && (
        <div className="relative mt-4">
          <CodeBlock code={card.code} language={card.language} />
        </div>
      )}
      {card.task && !card.needs_math && (
        <div className="relative mt-4 rounded-xl border border-violet-500/20 bg-violet-500/[0.07] px-4 py-3 text-sm">
          <span className="font-semibold text-violet-200">Задание: </span>
          <span className="text-zinc-200">{card.task}</span>
        </div>
      )}
      {card.image && (
        <div className="relative mt-5 overflow-hidden rounded-xl border border-white/[0.06] bg-white">
          {imgError ? (
            <div className="flex h-40 flex-col items-center justify-center gap-2 bg-ink-900 text-sm text-zinc-500">
              <ImageOff className="h-6 w-6" /> Изображение недоступно
            </div>
          ) : (
            <motion.img
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              src={serverUrl(card.image)}
              alt={card.image_alt || card.topic || "Схема"}
              onError={() => setImgError(true)}
              className="max-h-[420px] w-full object-contain"
              loading="lazy"
            />
          )}
          {card.image_alt && <div className="bg-ink-900 px-3 py-2 text-xs text-zinc-400">{card.image_alt}</div>}
        </div>
      )}
    </section>
  );
}

function ReviewCard({ review: r, latest, card }) {
  const st = STATUS[r.status] || STATUS.failed;
  return (
    <motion.section
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: latest ? 1 : 0.6, y: 0, scale: 1 }}
      className="glass p-5"
    >
      <div className="flex items-center gap-4">
        <Ring value={r.score / 100} size={64} stroke={6} color={st.color} gradientId={`r-${r.id}`}>
          <span className="text-lg font-bold tabular-nums"><CountUp value={r.score} duration={0.8} /></span>
        </Ring>
        <div className="min-w-0 flex-1">
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${st.cls}`}>
            <st.icon className="h-3.5 w-3.5" /> {st.label}
          </span>
          {!latest && <div className="mt-1 truncate text-xs text-zinc-500">Ваш ответ: {r.answer}</div>}
        </div>
      </div>
      <RichText text={r.feedback} codeLanguage={card.language} math={card.needs_math} className="mt-4 text-sm text-zinc-200" />
      {r.follow_up && (
        <div className="mt-4 rounded-xl border border-sky-500/25 bg-sky-500/[0.08] p-4">
          <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-sky-300">
            <HelpCircle className="h-3.5 w-3.5" /> Уточнение {r.follow_up_index}/{r.max_follow_ups}
          </div>
          <RichText text={r.follow_up} codeLanguage={card.language} className="text-sm text-zinc-100" />
        </div>
      )}
      {r.note && <div className="mt-3 text-xs text-zinc-400">{r.note}</div>}
      {r.reference_summary && (
        <details className="group mt-4 rounded-xl border border-white/[0.06] bg-white/[0.02]">
          <summary className="cursor-pointer select-none px-4 py-2.5 text-xs font-semibold text-zinc-400 hover:text-zinc-200">Эталонный ответ (кратко)</summary>
          <RichText text={r.reference_summary} codeLanguage={card.language} math={card.needs_math} className="px-4 pb-4 text-sm text-zinc-300" />
        </details>
      )}
    </motion.section>
  );
}

function Finished({ stats, onRestart, onExit, busy }) {
  const rate = stats.answered ? stats.passed / stats.answered : 0;
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
      className="mx-auto flex max-w-lg flex-col items-center px-4 py-16 text-center"
    >
      <div className="relative mb-6">
        {[...Array(10)].map((_, i) => (
          <motion.span
            key={i}
            className="absolute left-1/2 top-1/2 h-2 w-2 rounded-full"
            style={{ background: i % 2 ? "#8b5cf6" : "#f43f5e" }}
            initial={{ x: 0, y: 0, opacity: 1 }}
            animate={{ x: Math.cos((i / 10) * Math.PI * 2) * 110, y: Math.sin((i / 10) * Math.PI * 2) * 110, opacity: 0 }}
            transition={{ duration: 1.2, delay: 0.2, ease: "easeOut" }}
          />
        ))}
        <Ring value={rate} size={150} stroke={10} gradientId="finish">
          <Trophy className="h-12 w-12 text-amber-300" />
        </Ring>
      </div>
      <h2 className="text-3xl font-extrabold">Сессия завершена</h2>
      <p className="mt-2 text-zinc-400">
        {stats.answered
          ? `${stats.passed} из ${stats.answered} ${plural(stats.answered, "карточки", "карточек", "карточек")} засчитано`
          : "Вы просмотрели карточки без ответов"}
      </p>
      <div className="mt-8 grid w-full grid-cols-3 gap-3">
        {[
          ["Ответов", stats.answered],
          ["Ср. балл", stats.avg_score ?? "—"],
          ["Сегодня", stats.passed_today],
        ].map(([l, v]) => (
          <div key={l} className="glass p-4">
            <div className="text-2xl font-bold">{v}</div>
            <div className="text-xs text-zinc-500">{l}</div>
          </div>
        ))}
      </div>
      <div className="mt-8 flex gap-3">
        <button className="btn-ghost" onClick={onExit}><ArrowLeft className="h-4 w-4" /> К колодам</button>
        <button className="btn-primary" onClick={onRestart} disabled={busy}>
          {busy ? <Spinner /> : <RotateCcw className="h-4 w-4" />} Ещё сессия
        </button>
      </div>
    </motion.div>
  );
}
