import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import {
  ArrowLeft, Award, BookOpenText, Check, ChevronRight, ClipboardList, GraduationCap, Lock, MessagesSquare, Play, Sparkles, Terminal,
} from "lucide-react";
import { api } from "../lib/api";
import { formatDate, trackStyle } from "../lib/tracks";
import { Ring, Spinner, useToast } from "../components/ui";
import StartModal from "../components/StartModal";
import Certificate from "../components/Certificate";

export default function Tracks({ decks, onStart, onRead, onBook, onDeck, onExam, onInterview, openTrack, setOpenTrack }) {
  const [data, setData] = useState(null);
  const [gridRef] = useAutoAnimate({ duration: 250 });

  const load = useCallback(() => api("/api/tracks").then(setData).catch(() => setData({ tracks: [] })), []);
  useEffect(() => {
    load();
  }, [load]);

  if (openTrack) {
    return (
      <TrackDetail
        trackId={openTrack}
        decks={decks}
        onBack={() => {
          setOpenTrack(null);
          load();
        }}
        onStart={onStart}
        onRead={onRead}
        onBook={onBook}
        onDeck={onDeck}
        onExam={onExam}
        onInterview={onInterview}
      />
    );
  }

  const earned = (data?.tracks || []).filter((t) => t.certificate).length;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Профессии</h1>
          <p className="max-w-2xl text-sm text-zinc-400">
            Трек = теория по прикладным предметам + практикум с live-coding. Пройдите AI-собеседование и экзамен — и получите сертификат.
          </p>
        </div>
        {data && (
          <div className="chip px-3 py-1.5 text-sm">
            <Award className="h-4 w-4 text-amber-300" /> Сертификатов: <b className="text-white">{earned}</b> из {data.tracks.length}
          </div>
        )}
      </header>

      {data && <RulesStrip data={data} />}

      {!data ? (
        <div className="flex justify-center py-20"><Spinner className="h-6 w-6" /></div>
      ) : (
        <div ref={gridRef} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {data.tracks.map((t, i) => (
            <TrackCard key={t.id} track={t} index={i} onOpen={() => setOpenTrack(t.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

function RulesStrip({ data }) {
  const steps = [
    { icon: GraduationCap, title: "Обучение", text: `сдайте ≥ ${Math.round((data.coverage || 0.6) * 100)}% карточек трека` },
    { icon: MessagesSquare, title: "AI-собеседование", text: `${(data.interview.theory || 5) + (data.interview.practice || 1)} вопросов, проходной балл ${data.interview.pass_score}` },
    { icon: ClipboardList, title: "Экзамен", text: `${(data.exam.theory || 9) + (data.exam.practice || 3)} заданий за ${data.exam.minutes} мин, балл ≥ ${data.exam.pass_score}` },
    { icon: Award, title: "Сертификат", text: "с публичной проверкой по номеру" },
  ];
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {steps.map((s, i) => (
        <motion.div
          key={s.title}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06 }}
          className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.05] text-zinc-300">
            <s.icon className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-semibold">{i + 1}. {s.title}</div>
            <div className="text-xs text-zinc-500">{s.text}</div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function TrackCard({ track: t, index, onOpen }) {
  const st = trackStyle(t.id);
  const req = t.requirements;
  const doneCount = [req.coverage.done, req.interview.done, req.exam.done].filter(Boolean).length;
  return (
    <motion.button
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, ease: [0.16, 1, 0.3, 1], duration: 0.5 }}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.985 }}
      onClick={onOpen}
      className="glass group relative flex flex-col overflow-hidden p-5 text-left"
    >
      <div className={`pointer-events-none absolute inset-x-0 top-0 h-28 bg-gradient-to-b ${st.soft} opacity-70 transition-opacity group-hover:opacity-100`} />
      {t.certificate && (
        <div className="absolute right-4 top-4 flex items-center gap-1 rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[11px] font-semibold text-amber-200">
          <Award className="h-3 w-3" /> сертификат
        </div>
      )}
      <div className="relative flex items-center gap-3">
        <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${st.grad} shadow-lg`}>
          <st.icon className="h-6 w-6 text-white" />
        </div>
        <div className={`min-w-0 ${t.certificate ? "pr-24" : ""}`}>
          <h3 className="text-lg font-bold leading-tight">{t.title}</h3>
          <div className="text-xs text-zinc-500">{t.book ? `${t.book.lessons} уроков` : `${t.subjects.length} предметов`} · {req.coverage.total} карточек</div>
        </div>
      </div>
      <p className="relative mt-3 line-clamp-2 text-sm text-zinc-400">{t.description}</p>
      <div className="relative mt-4 flex flex-wrap gap-1.5">
        {t.subjects.slice(0, 4).map((s) => (
          <span key={s} className="rounded-md bg-white/[0.04] px-2 py-0.5 text-[11px] text-zinc-400">{s}</span>
        ))}
        {t.subjects.length > 4 && <span className="px-1 text-[11px] text-zinc-500">+{t.subjects.length - 4}</span>}
      </div>
      <div className="relative mt-5 flex items-center gap-4 border-t border-white/[0.06] pt-4">
        <Ring value={req.coverage.value / (req.coverage.required || 0.6)} size={44} stroke={4} gradientId={`tr-${t.id}`}>
          <span className="text-[10px] font-semibold tabular-nums">{Math.round(req.coverage.value * 100)}%</span>
        </Ring>
        <div className="flex flex-1 gap-1.5">
          {[
            ["Учёба", req.coverage.done],
            ["Интервью", req.interview.done],
            ["Экзамен", req.exam.done],
          ].map(([label, ok]) => (
            <div key={label} className={`flex flex-1 items-center justify-center gap-1 rounded-lg py-1.5 text-[11px] font-medium ${ok ? "bg-emerald-500/15 text-emerald-300" : "bg-white/[0.03] text-zinc-500"}`}>
              {ok && <Check className="h-3 w-3" />} {label}
            </div>
          ))}
        </div>
        <span className="text-xs tabular-nums text-zinc-500">{doneCount}/3</span>
      </div>
    </motion.button>
  );
}

function TrackDetail({ trackId, decks, onBack, onStart, onRead, onBook, onDeck, onExam, onInterview }) {
  const toast = useToast();
  const [t, setT] = useState(null);
  const [picked, setPicked] = useState(null);
  const [issuing, setIssuing] = useState(false);
  const [histRef] = useAutoAnimate();

  const load = useCallback(() => api(`/api/tracks/${trackId}`).then(setT).catch((e) => toast(e.message, "error")), [trackId, toast]);
  useEffect(() => {
    load();
  }, [load]);

  if (!t) return <div className="flex justify-center py-20"><Spinner className="h-6 w-6" /></div>;

  const st = trackStyle(t.id);
  const req = t.requirements;
  const deckRow = (id) => (decks || []).find((d) => d.deck_id === id);

  async function issue() {
    setIssuing(true);
    try {
      await api(`/api/tracks/${t.id}/certificate`, { method: "POST" });
      await load();
      toast("Сертификат выдан!", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setIssuing(false);
    }
  }

  const steps = [
    {
      key: "coverage",
      icon: GraduationCap,
      title: "Обучение",
      done: req.coverage.done,
      value: `${req.coverage.passed} из ${req.coverage.total} карточек сдано`,
      need: `нужно ${Math.round(req.coverage.required * 100)}%`,
      progress: Math.min(1, req.coverage.value / req.coverage.required),
      action: (
        <button className="btn-ghost" onClick={() => setPicked(deckRow(t.decks[0]?.deck_id))}>
          <Play className="h-4 w-4" /> Учить
        </button>
      ),
    },
    {
      key: "interview",
      icon: MessagesSquare,
      title: "AI-собеседование",
      done: req.interview.done,
      value: req.interview.best != null ? `лучший результат ${Math.round(req.interview.best)}` : "ещё не проходили",
      need: `проходной ${req.interview.required}`,
      progress: req.interview.best != null ? Math.min(1, req.interview.best / req.interview.required) : 0,
      action: (
        <button className="btn-ghost" onClick={() => onInterview(t)}>
          <MessagesSquare className="h-4 w-4" /> {req.interview.best != null ? "Ещё раз" : "Начать"}
        </button>
      ),
    },
    {
      key: "exam",
      icon: ClipboardList,
      title: "Экзамен",
      done: req.exam.done,
      value: req.exam.best != null ? `лучший результат ${Math.round(req.exam.best)}` : "ещё не сдавали",
      need: `проходной ${req.exam.required} · ${t.exam_config.minutes} мин`,
      progress: req.exam.best != null ? Math.min(1, req.exam.best / req.exam.required) : 0,
      action: (
        <button className="btn-ghost" onClick={() => onExam(t)}>
          <ClipboardList className="h-4 w-4" /> {req.exam.best != null ? "Пересдать" : "Сдать"}
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <button className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white" onClick={onBack}>
        <ArrowLeft className="h-4 w-4" /> Все профессии
      </button>

      <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass relative overflow-hidden p-6 sm:p-8">
        <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${st.soft}`} />
        <div className="relative flex flex-wrap items-start gap-5">
          <motion.div
            initial={{ rotate: -12, scale: 0.8 }}
            animate={{ rotate: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 18 }}
            className={`flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${st.grad} shadow-xl`}
          >
            <st.icon className="h-8 w-8 text-white" />
          </motion.div>
          <div className="min-w-0 flex-1">
            <h1 className="text-3xl font-extrabold tracking-tight">{t.title}</h1>
            <p className="mt-1 max-w-3xl text-sm text-zinc-300">{t.description}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {t.subjects.map((s) => (
                <span key={s} className="rounded-md border border-white/[0.06] bg-black/20 px-2 py-0.5 text-xs text-zinc-300">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </motion.section>

      {t.book && (
        <section className="glass p-5 sm:p-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="flex items-center gap-2 font-semibold"><BookOpenText className="h-5 w-5 text-violet-300" /> Учебник профессии</h2>
              <p className="mt-1 text-sm text-zinc-400">{t.book.chapter_count} глав, {t.book.lessons} уроков. В каждом — статья, вопросы, практика и тест.</p>
            </div>
            <button className="btn-primary" onClick={() => onBook(t.book.id)}>Открыть учебник</button>
          </div>
          <div className="divide-y divide-white/[0.06]">
            {t.book.chapters.map((ch) => (
              <details key={ch.title} className="py-2">
                <summary className="cursor-pointer py-2 text-sm font-semibold text-zinc-200">{ch.title} <span className="ml-2 font-normal text-zinc-500">{ch.lessons.length} уроков</span></summary>
                <div className="space-y-1 pb-2">
                  {ch.lessons.map((ls) => (
                    <div key={ls.title} className="flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 hover:bg-white/[0.03]">
                      <button className="min-w-0 flex-1 text-left text-sm text-zinc-300 hover:text-white" onClick={() => onBook(t.book.id, ls.title)}>{ls.title}</button>
                      <button className="chip text-xs disabled:opacity-40" disabled={!t.book.decks.qa} onClick={() => onDeck(t.book.decks.qa, ls.title)} aria-label={`Вопросы: ${ls.title}`}>{ls.qa} вопросов</button>
                      <button className="chip text-xs disabled:opacity-40" disabled={!t.book.decks.live} onClick={() => onDeck(t.book.decks.live, ls.title)} aria-label={`Практика: ${ls.title}`}>{ls.live} {t.book.is_code ? "live-coding" : "заданий"}</button>
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </section>
      )}

      {/* путь к сертификату */}
      <div className="grid gap-3 lg:grid-cols-3">
        {steps.map((s, i) => (
          <motion.div
            key={s.key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 + i * 0.07 }}
            className={`glass relative overflow-hidden p-5 ${s.done ? "border-emerald-500/25" : ""}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${s.done ? "bg-emerald-500/20 text-emerald-300" : "bg-white/[0.05] text-zinc-300"}`}>
                  {s.done ? <Check className="h-5 w-5" /> : <s.icon className="h-5 w-5" />}
                </div>
                <div>
                  <div className="text-xs text-zinc-500">Шаг {i + 1}</div>
                  <div className="font-semibold">{s.title}</div>
                </div>
              </div>
              {s.action}
            </div>
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
              <motion.div
                className={`h-full rounded-full ${s.done ? "bg-emerald-400" : `bg-gradient-to-r ${st.grad}`}`}
                initial={{ width: 0 }}
                animate={{ width: `${s.progress * 100}%` }}
                transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
            <div className="mt-2 flex justify-between text-xs">
              <span className="text-zinc-300">{s.value}</span>
              <span className="text-zinc-500">{s.need}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* сертификат */}
      <AnimatePresence mode="wait">
        {t.certificate ? (
          <motion.section key="cert" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <h2 className="flex items-center gap-2 font-semibold"><Award className="h-4 w-4 text-amber-300" /> Ваш сертификат</h2>
            <div className="max-w-3xl"><Certificate cert={t.certificate} /></div>
          </motion.section>
        ) : (
          <motion.section key="locked" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass flex flex-wrap items-center gap-4 p-5">
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${t.eligible ? "bg-amber-400/20 text-amber-200" : "bg-white/[0.04] text-zinc-500"}`}>
              {t.eligible ? <Sparkles className="h-6 w-6" /> : <Lock className="h-6 w-6" />}
            </div>
            <div className="flex-1">
              <div className="font-semibold">{t.eligible ? "Все условия выполнены!" : "Сертификат откроется после трёх шагов"}</div>
              <div className="text-sm text-zinc-400">
                {t.eligible ? "Заберите сертификат — его можно распечатать и проверить по номеру." : "Учитываются лучшие результаты собеседования и экзамена."}
              </div>
            </div>
            {t.eligible && (
              <motion.button whileTap={{ scale: 0.97 }} className="btn-primary" onClick={issue} disabled={issuing}>
                {issuing ? <Spinner /> : <Award className="h-4 w-4" />} Получить сертификат
              </motion.button>
            )}
          </motion.section>
        )}
      </AnimatePresence>

      {/* предметы и колоды */}
      <section className="space-y-3">
        <h2 className="font-semibold">Материалы трека</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {t.decks.map((d) => (
            <div key={d.deck_id} className="glass flex items-center gap-4 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.05]">
                {d.kind === "live" ? <Terminal className={`h-5 w-5 ${st.text}`} /> : <GraduationCap className={`h-5 w-5 ${st.text}`} />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate font-semibold">{d.kind === "live" ? (t.book?.is_code ? "Практикум (live-coding)" : "Практические задания") : "Вопросы и ответы"}</div>
                <div className="text-xs text-zinc-500">
                  сдано {d.passed}/{d.total} · новые {d.new}{d.weak ? ` · слабые ${d.weak}` : ""}
                </div>
                <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div className={`h-full bg-gradient-to-r ${st.grad}`} style={{ width: `${(d.passed / Math.max(1, d.total)) * 100}%` }} />
                </div>
              </div>
              <div className="flex gap-1">
                <button className="btn-icon" title="Учебник" onClick={() => onRead(d.deck_id)}>
                  <BookOpenText className="h-4 w-4" />
                </button>
                <button className="btn-ghost px-3 py-2" onClick={() => setPicked(deckRow(d.deck_id))}>
                  <Play className="h-4 w-4" /> Учить
                </button>
              </div>
            </div>
          ))}
        </div>
        {t.related.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm text-zinc-400">
            Дополнительно:
            {t.related.map((r) => (
              <button key={r.deck_id} className="chip hover:border-white/20 hover:text-white" onClick={() => setPicked(deckRow(r.deck_id))}>
                {r.name} <ChevronRight className="h-3 w-3" />
              </button>
            ))}
          </div>
        )}
      </section>

      {/* история попыток */}
      {t.history.length > 0 && (
        <section className="space-y-3">
          <h2 className="font-semibold">История попыток</h2>
          <div ref={histRef} className="glass divide-y divide-white/[0.05]">
            {t.history.map((h) => (
              <div key={h.id} className="flex items-center gap-4 px-5 py-3 text-sm">
                <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${h.kind === "exam" ? "bg-sky-500/15 text-sky-300" : "bg-violet-500/15 text-violet-300"}`}>
                  {h.kind === "exam" ? <ClipboardList className="h-4 w-4" /> : <MessagesSquare className="h-4 w-4" />}
                </span>
                <span className="flex-1">
                  {h.kind === "exam" ? "Экзамен" : "AI-собеседование"}
                  {h.level && <span className="ml-2 chip py-0.5">{h.level}</span>}
                </span>
                <span className="text-zinc-500">{formatDate(h.finished_at)}</span>
                <span className="w-12 text-right font-semibold tabular-nums">{Math.round(h.score)}</span>
                <span className={`w-24 text-right text-xs font-semibold ${h.passed ? "text-emerald-300" : "text-rose-300"}`}>
                  {h.passed ? "пройдено" : "не пройдено"}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      <StartModal
        deck={picked}
        onClose={() => setPicked(null)}
        onRead={(id, topic) => {
          setPicked(null);
          onRead(id, topic);
        }}
        onStart={(s) => {
          setPicked(null);
          setTimeout(() => onStart(s), 180);
        }}
      />
    </div>
  );
}
