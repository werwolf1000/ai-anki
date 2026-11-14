import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { AlertTriangle, ArrowLeft, ArrowRight, Award, Check, ChevronDown, Clock, Flag, Save, XCircle } from "lucide-react";
import { api } from "../lib/api";
import { CodeBlock, RichText } from "../lib/richtext";
import { trackStyle } from "../lib/tracks";
import { CountUp, Modal, Ring, Spinner, useToast } from "../components/ui";
import Certificate from "../components/Certificate";

const CodeEditor = lazy(() => import("../components/CodeEditor"));

function useCountdown(seconds) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => {
    const end = Date.now() + seconds * 1000;
    const id = setInterval(() => setLeft(Math.max(0, Math.round((end - Date.now()) / 1000))), 500);
    return () => clearInterval(id);
  }, [seconds]);
  return left;
}

export default function Exam({ exam, config, onExit }) {
  const toast = useToast();
  const st = trackStyle(exam.track_id);
  const [index, setIndex] = useState(0);
  const [drafts, setDrafts] = useState(() => exam.questions.map(() => ""));
  const [saved, setSaved] = useState(() => exam.questions.map(() => ""));
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [result, setResult] = useState(null);
  const left = useCountdown(exam.seconds_left);
  const q = exam.questions[index];
  const answered = saved.filter(Boolean).length;

  const finish = useCallback(async () => {
    setConfirm(false);
    setFinishing(true);
    try {
      const r = await api(`/api/exams/${exam.exam_id}/finish`, { method: "POST" });
      setResult(r);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setFinishing(false);
    }
  }, [exam.exam_id, toast]);

  // время вышло — завершаем автоматически
  useEffect(() => {
    if (left === 0 && !result && !finishing) {
      toast("Время вышло — экзамен завершён", "info");
      finish();
    }
  }, [left, result, finishing, finish, toast]);

  async function save(goNext = true) {
    const text = drafts[index].trim();
    if (!text) {
      toast("Ответ пустой", "info");
      return;
    }
    setBusy(true);
    try {
      await api(`/api/exams/${exam.exam_id}/answer`, { method: "POST", body: { index, answer: text } });
      setSaved((s) => s.map((v, i) => (i === index ? text : v)));
      if (goNext) {
        const nextUnanswered = exam.questions.findIndex((_, i) => i > index && !saved[i]);
        if (nextUnanswered >= 0) setIndex(nextUnanswered);
        else if (index < exam.questions.length - 1) setIndex(index + 1);
      }
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  const setDraft = (v) => setDrafts((d) => d.map((x, i) => (i === index ? v : x)));
  const mm = String(Math.floor(left / 60)).padStart(2, "0");
  const ss = String(left % 60).padStart(2, "0");
  const urgent = left < 300;

  if (result) return <ExamResult result={result} exam={exam} onExit={onExit} />;

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-white/[0.05] bg-ink-950/60 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
          <button className="btn-ghost px-3" onClick={() => setConfirm(true)}>
            <Flag className="h-4 w-4" /> <span className="hidden sm:inline">Завершить</span>
          </button>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">Экзамен · {exam.title}</div>
            <div className="text-xs text-zinc-500">Отвечено {answered} из {exam.questions.length} · проходной балл {exam.pass_score}</div>
          </div>
          <motion.div
            animate={urgent ? { scale: [1, 1.06, 1] } : {}}
            transition={{ duration: 1, repeat: urgent ? Infinity : 0 }}
            className={`flex items-center gap-2 rounded-xl border px-3 py-2 font-mono text-lg font-semibold tabular-nums ${urgent ? "border-rose-500/40 bg-rose-500/10 text-rose-200" : "border-white/[0.08] bg-white/[0.03]"}`}
          >
            <Clock className="h-4 w-4" /> {mm}:{ss}
          </motion.div>
        </div>
        <div className="mx-auto flex max-w-7xl gap-1.5 overflow-x-auto px-4 pb-3 sm:px-6">
          {exam.questions.map((qq, i) => (
            <button
              key={i}
              onClick={() => setIndex(i)}
              className={`relative flex h-9 min-w-[2.25rem] items-center justify-center rounded-lg border text-sm font-semibold transition-colors ${
                i === index ? "border-violet-400 text-white" : saved[i] ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200" : "border-white/[0.07] text-zinc-500 hover:text-zinc-200"
              }`}
              title={qq.kind === "practice" ? "Практика" : qq.topic}
            >
              {i === index && <motion.span layoutId="exam-q" className="absolute inset-0 rounded-lg bg-violet-500/20" />}
              <span className="relative">{qq.kind === "practice" ? "⌘" : i + 1}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.25 }}
            className={`mx-auto grid max-w-7xl gap-5 px-4 py-6 sm:px-6 ${q.needs_code ? "lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]" : "lg:grid-cols-2"}`}
          >
            <section className="glass relative h-fit overflow-hidden p-6">
              <div className={`pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b ${st.soft} opacity-60`} />
              <div className="relative mb-4 flex flex-wrap gap-2">
                <span className="chip">Вопрос {index + 1} из {exam.questions.length}</span>
                <span className={`chip ${q.kind === "practice" ? "text-emerald-300" : ""}`}>{q.kind === "practice" ? "Практика" : "Теория"}</span>
                {q.topic && <span className="chip">{q.topic}</span>}
                {q.language && q.needs_code && <span className="chip font-mono uppercase">{q.language}</span>}
              </div>
              <div className="question-text relative text-[16px] leading-relaxed text-zinc-300">
                <RichText text={q.question} codeLanguage={q.language} />
              </div>
              {q.code && <div className="relative mt-4"><CodeBlock code={q.code} language={q.language} /></div>}
            </section>

            <section className="glass h-fit p-5">
              <div className="mb-3 flex items-center justify-between text-sm">
                <span className="font-semibold text-zinc-300">Ваш ответ</span>
                {saved[index] && (
                  <span className="flex items-center gap-1 text-xs text-emerald-300">
                    <Check className="h-3.5 w-3.5" /> сохранён{drafts[index].trim() !== saved[index] ? " (есть правки)" : ""}
                  </span>
                )}
              </div>
              {q.needs_code ? (
                <Suspense fallback={<div className="flex h-[360px] items-center justify-center"><Spinner /></div>}>
                  <CodeEditor key={index} value={drafts[index]} onChange={setDraft} language={q.language} theme={config?.code_editor_theme || "dark"} onSubmit={() => save(true)} height={380} />
                </Suspense>
              ) : (
                <textarea
                  key={index}
                  autoFocus
                  className="input min-h-[220px] resize-y text-[15px] leading-relaxed"
                  placeholder="Ответьте своими словами. Подсказок на экзамене нет."
                  value={drafts[index]}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.ctrlKey && e.key === "Enter") {
                      e.preventDefault();
                      save(true);
                    }
                  }}
                />
              )}
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <button className="btn-ghost px-3" disabled={index === 0} onClick={() => setIndex(index - 1)}>
                  <ArrowLeft className="h-4 w-4" />
                </button>
                <motion.button whileTap={{ scale: 0.97 }} className="btn-primary" onClick={() => save(true)} disabled={busy || !drafts[index].trim()}>
                  {busy ? <Spinner /> : <Save className="h-4 w-4" />} Сохранить и дальше
                </motion.button>
                <button className="btn-ghost px-3" disabled={index === exam.questions.length - 1} onClick={() => setIndex(index + 1)}>
                  <ArrowRight className="h-4 w-4" />
                </button>
                {answered === exam.questions.length && (
                  <button className="btn-ghost ml-auto border-emerald-500/40 text-emerald-200" onClick={() => setConfirm(true)}>
                    <Flag className="h-4 w-4" /> Сдать экзамен
                  </button>
                )}
              </div>
              <p className="mt-3 text-[11px] text-zinc-500">Ответы проверяются в фоне; результат — после завершения. Ctrl+Enter — сохранить.</p>
            </section>
          </motion.div>
        </AnimatePresence>
      </div>

      <Modal open={confirm} onClose={() => setConfirm(false)} width="max-w-md">
        <div className="p-6">
          <h3 className="text-lg font-bold">Завершить экзамен?</h3>
          <p className="mt-2 text-sm text-zinc-400">
            Отвечено {answered} из {exam.questions.length}. Вопросы без ответа получат 0 баллов.
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <button className="btn-ghost" onClick={() => setConfirm(false)}>Продолжить</button>
            <button className="btn-primary" onClick={finish}>Завершить</button>
          </div>
        </div>
      </Modal>

      <AnimatePresence>
        {finishing && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-ink-950/85 backdrop-blur">
            <Spinner className="h-8 w-8 text-violet-300" />
            <div className="text-lg font-semibold">Подводим итоги…</div>
            <div className="text-sm text-zinc-400">Модель завершает проверку ответов, это может занять до минуты</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ExamResult({ result, exam, onExit }) {
  const [open, setOpen] = useState(null);
  const [listRef] = useAutoAnimate();
  const items = result.details.items;
  const topics = useMemo(() => Object.entries(result.details.topics).sort((a, b) => a[1] - b[1]), [result]);
  const color = result.passed ? "#34d399" : "#fb7185";
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
        <motion.section initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="glass flex flex-wrap items-center gap-6 p-6 sm:p-8">
          <Ring value={result.score / 100} size={140} stroke={11} color={color} gradientId="exam-res">
            <div className="text-center">
              <div className="text-4xl font-extrabold tabular-nums"><CountUp value={result.score} decimals={0} /></div>
              <div className="text-[11px] uppercase tracking-widest text-zinc-500">из 100</div>
            </div>
          </Ring>
          <div className="min-w-0 flex-1">
            <div className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-semibold ${result.passed ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200" : "border-rose-500/30 bg-rose-500/10 text-rose-200"}`}>
              {result.passed ? <Check className="h-4 w-4" /> : <XCircle className="h-4 w-4" />} {result.passed ? "Экзамен сдан" : "Экзамен не сдан"}
            </div>
            <h1 className="mt-2 text-2xl font-extrabold">{exam.title}</h1>
            <p className="text-sm text-zinc-400">
              Проходной балл {result.details.pass_score} · отвечено {result.details.answered} из {items.length} · {Math.round(result.details.duration_sec / 60)} мин
            </p>
            <div className="mt-4 flex gap-2">
              <button className="btn-ghost" onClick={onExit}><ArrowLeft className="h-4 w-4" /> К профессии</button>
            </div>
          </div>
        </motion.section>

        {result.certificate && (
          <section className="space-y-3">
            <h2 className="flex items-center gap-2 font-semibold"><Award className="h-4 w-4 text-amber-300" /> Поздравляем — сертификат получен!</h2>
            <div className="max-w-3xl"><Certificate cert={result.certificate} /></div>
          </section>
        )}

        <section className="glass p-5">
          <h2 className="mb-4 font-semibold">Результаты по темам</h2>
          <div className="space-y-2.5">
            {topics.map(([name, score], i) => (
              <div key={name} className="grid grid-cols-[minmax(0,180px)_1fr_40px] items-center gap-3 text-sm">
                <span className="truncate text-zinc-300">{name}</span>
                <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div
                    className={`h-full rounded-full ${score >= result.details.pass_score ? "bg-emerald-400" : score >= 50 ? "bg-amber-400" : "bg-rose-400"}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${score}%` }}
                    transition={{ delay: i * 0.05, duration: 0.8 }}
                  />
                </div>
                <span className="text-right tabular-nums text-zinc-200">{Math.round(score)}</span>
              </div>
            ))}
          </div>
          {topics.some(([, s]) => s < result.details.pass_score) && (
            <div className="mt-4 flex items-center gap-2 text-xs text-amber-200/80">
              <AlertTriangle className="h-3.5 w-3.5" /> Повторите темы ниже проходного балла в учебнике и колоде трека.
            </div>
          )}
        </section>

        <section className="space-y-3">
          <h2 className="font-semibold">Разбор ответов</h2>
          <div ref={listRef} className="space-y-2">
            {items.map((it, i) => (
              <div key={i} className="glass overflow-hidden">
                <button className="flex w-full items-center gap-3 px-5 py-3 text-left" onClick={() => setOpen(open === i ? null : i)}>
                  <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-bold tabular-nums ${it.score >= result.details.pass_score ? "bg-emerald-500/15 text-emerald-300" : it.score >= 50 ? "bg-amber-500/15 text-amber-300" : "bg-rose-500/15 text-rose-300"}`}>
                    {it.score}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-sm">{it.question.split("\n")[0]}</span>
                  <span className="hidden text-xs text-zinc-500 sm:inline">{it.kind === "practice" ? "практика" : it.topic}</span>
                  <ChevronDown className={`h-4 w-4 text-zinc-500 transition-transform ${open === i ? "rotate-180" : ""}`} />
                </button>
                <AnimatePresence initial={false}>
                  {open === i && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <div className="space-y-3 border-t border-white/[0.05] px-5 py-4 text-sm">
                        <RichText text={it.question} codeLanguage={it.language} className="text-zinc-300" />
                        <div>
                          <div className="label">Ваш ответ</div>
                          {it.answer ? (
                            it.needs_code ? <CodeBlock code={it.answer} language={it.language} /> : <div className="whitespace-pre-wrap text-zinc-200">{it.answer}</div>
                          ) : (
                            <span className="text-zinc-500">нет ответа</span>
                          )}
                        </div>
                        {it.feedback && (
                          <div>
                            <div className="label">Комментарий экзаменатора</div>
                            <RichText text={it.feedback} codeLanguage={it.language} className="text-zinc-300" />
                          </div>
                        )}
                        {it.reference_summary && (
                          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                            <div className="label">Эталон кратко</div>
                            <RichText text={it.reference_summary} codeLanguage={it.language} className="text-zinc-300" />
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
