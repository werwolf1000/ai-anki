import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { ArrowLeft, Award, Bot, Check, CornerDownLeft, Lightbulb, Send, Target, TrendingUp, User, XCircle } from "lucide-react";
import { api } from "../lib/api";
import { RichText } from "../lib/richtext";
import { trackStyle } from "../lib/tracks";
import { CountUp, Ring, Spinner, useToast } from "../components/ui";
import Certificate from "../components/Certificate";
import VoiceButton from "../components/VoiceButton";

const CodeEditor = lazy(() => import("../components/CodeEditor"));

export default function Interview({ interview, config, user, onExit }) {
  const toast = useToast();
  const st = trackStyle(interview.track_id);
  const [messages, setMessages] = useState(() => interview.messages.map((m, i) => ({ ...m, id: i })));
  const [meta, setMeta] = useState({ index: interview.index, total: interview.total, input: interview.input, language: interview.language, topic: interview.topic });
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null); // { report, certificate }
  const [listRef] = useAutoAnimate({ duration: 220 });
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  async function send() {
    const text = answer.trim();
    if (!text || busy) return;
    setMessages((m) => [...m, { role: "candidate", text, id: Date.now() }]);
    setAnswer("");
    setBusy(true);
    try {
      const r = await api(`/api/interviews/${interview.interview_id}/answer`, { method: "POST", body: { answer: text } });
      setMessages((m) => [...m, ...r.messages.map((x, i) => ({ ...x, id: Date.now() + i + 1 }))]);
      setMeta({ index: r.index, total: r.total, input: r.input, language: r.language, topic: r.topic });
      if (r.done) setDone({ report: r.report, certificate: r.certificate });
    } catch (e) {
      toast(e.message, "error");
      setMessages((m) => m.slice(0, -1));
      setAnswer(text);
    } finally {
      setBusy(false);
    }
  }

  const progress = done ? 1 : (meta.index - 1) / Math.max(1, meta.total);

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-white/[0.05] bg-ink-950/60 backdrop-blur-xl">
        <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-3 sm:px-6">
          <button className="btn-ghost px-3" onClick={onExit}>
            <ArrowLeft className="h-4 w-4" /> <span className="hidden sm:inline">Выйти</span>
          </button>
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${st.grad}`}>
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">AI-собеседование · {interview.title}</div>
            <div className="text-xs text-zinc-500">
              {done ? "Завершено" : `Вопрос ${meta.index} из ${meta.total}${meta.topic ? ` · ${meta.topic}` : ""}`}
            </div>
          </div>
        </div>
        <div className="h-0.5 bg-white/[0.04]">
          <motion.div className={`h-full bg-gradient-to-r ${st.grad}`} animate={{ width: `${progress * 100}%` }} />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div ref={listRef} className="mx-auto max-w-4xl space-y-4 px-4 py-6 sm:px-6">
          {messages.map((m) => (
            <Bubble key={m.id} m={m} st={st} user={user} lang={meta.language} />
          ))}
          {busy && (
            <div className="flex items-end gap-3">
              <Avatar st={st} />
              <div className="rounded-2xl rounded-bl-md border border-white/[0.06] bg-ink-800/80 px-4 py-3">
                <div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <motion.span key={i} className="h-2 w-2 rounded-full bg-zinc-400" animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }} transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }} />
                  ))}
                </div>
              </div>
            </div>
          )}
          {done && <Report report={done.report} certificate={done.certificate} onExit={onExit} />}
          <div ref={endRef} />
        </div>
      </div>

      {!done && (
        <div className="shrink-0 border-t border-white/[0.05] bg-ink-950/60 backdrop-blur-xl">
          <div className="mx-auto max-w-4xl px-4 py-3 sm:px-6">
            {meta.input === "code" ? (
              <Suspense fallback={<div className="flex h-[260px] items-center justify-center"><Spinner /></div>}>
                <CodeEditor key={meta.index} value={answer} onChange={setAnswer} language={meta.language} theme={config?.code_editor_theme || "dark"} onSubmit={send} height={260} />
              </Suspense>
            ) : (
              <textarea
                autoFocus
                rows={3}
                className="input resize-none text-[15px]"
                placeholder="Ваш ответ интервьюеру…"
                value={answer}
                disabled={busy}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || !e.shiftKey) && !e.nativeEvent.isComposing) {
                    e.preventDefault();
                    send();
                  }
                }}
              />
            )}
            <div className="mt-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[11px] text-zinc-500">
                <CornerDownLeft className="h-3 w-3" /> {meta.input === "code" ? "Ctrl+Enter — отправить" : "Enter — отправить, Shift+Enter — новая строка"}
              </span>
              <div className="flex gap-2">
                {meta.input !== "code" && config?.asr_enabled && (
                  <VoiceButton
                    disabled={busy}
                    context={[...messages].reverse().find((m) => m.role === "interviewer")?.text || ""}
                    onText={(t) => setAnswer((a) => (a.trim() ? `${a.trim()} ${t}` : t))}
                    onStatus={(m, k) => toast(m, k)}
                  />
                )}
                <motion.button whileTap={{ scale: 0.96 }} className="btn-primary" onClick={send} disabled={busy || !answer.trim()}>
                  {busy ? <Spinner /> : <Send className="h-4 w-4" />} Ответить
                </motion.button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Avatar({ st }) {
  return (
    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${st.grad}`}>
      <Bot className="h-4 w-4 text-white" />
    </div>
  );
}

function Bubble({ m, st, user, lang }) {
  const mine = m.role === "candidate";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 380, damping: 30 }}
      className={`flex items-end gap-3 ${mine ? "flex-row-reverse" : ""}`}
    >
      {mine ? (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/[0.08] text-xs font-bold">
          {(user.display_name || user.username).slice(0, 1).toUpperCase() || <User className="h-4 w-4" />}
        </div>
      ) : (
        <Avatar st={st} />
      )}
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
          mine
            ? "rounded-br-md bg-gradient-to-br from-violet-600/80 to-rose-500/70 text-white"
            : `rounded-bl-md border bg-ink-800/80 text-zinc-200 ${m.follow_up ? "border-sky-500/30" : "border-white/[0.06]"}`
        }`}
      >
        {m.follow_up && <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-sky-300">Уточняющий вопрос</div>}
        {mine ? <div className="whitespace-pre-wrap font-[inherit]">{m.text}</div> : <RichText text={m.text} codeLanguage={lang} />}
      </div>
    </motion.div>
  );
}

function Report({ report, certificate, onExit }) {
  const color = report.passed ? "#34d399" : "#fb7185";
  const blocks = [
    { icon: TrendingUp, title: "Сильные стороны", items: report.strengths, cls: "text-emerald-300" },
    { icon: Target, title: "Пробелы", items: report.gaps, cls: "text-amber-300" },
    { icon: Lightbulb, title: "Рекомендации", items: report.recommendations, cls: "text-violet-300" },
  ];
  return (
    <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="space-y-4 pt-4">
      <div className="glass flex flex-wrap items-center gap-6 p-6">
        <Ring value={report.score / 100} size={120} stroke={10} color={color} gradientId="iv-res">
          <div className="text-center">
            <div className="text-3xl font-extrabold tabular-nums"><CountUp value={report.score} /></div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-500">баллов</div>
          </div>
        </Ring>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-semibold ${report.passed ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200" : "border-rose-500/30 bg-rose-500/10 text-rose-200"}`}>
              {report.passed ? <Check className="h-4 w-4" /> : <XCircle className="h-4 w-4" />} {report.passed ? "Собеседование пройдено" : "Не пройдено"}
            </span>
            <span className="chip text-sm">Уровень: <b className="text-white">{report.level}</b></span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-zinc-300">{report.summary}</p>
          <div className="mt-1 text-xs text-zinc-500">Проходной балл {report.pass_score}</div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {blocks.map((b) => (
          <div key={b.title} className="glass p-4">
            <div className={`mb-2 flex items-center gap-2 text-sm font-semibold ${b.cls}`}><b.icon className="h-4 w-4" /> {b.title}</div>
            <ul className="space-y-1.5 text-sm text-zinc-300">
              {(b.items.length ? b.items : ["—"]).map((x, i) => <li key={i}>• {x}</li>)}
            </ul>
          </div>
        ))}
      </div>

      <div className="glass divide-y divide-white/[0.05]">
        {report.questions.map((q, i) => (
          <div key={i} className="flex items-start gap-3 px-5 py-3 text-sm">
            <span className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${q.score >= report.pass_score ? "bg-emerald-500/15 text-emerald-300" : q.score >= 50 ? "bg-amber-500/15 text-amber-300" : "bg-rose-500/15 text-rose-300"}`}>{q.score ?? 0}</span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-zinc-200">{q.question.split("\n")[0]}</div>
              <div className="line-clamp-2 text-xs text-zinc-500">{q.feedback}</div>
            </div>
          </div>
        ))}
      </div>

      <AnimatePresence>
        {certificate && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <h2 className="flex items-center gap-2 font-semibold"><Award className="h-4 w-4 text-amber-300" /> Сертификат получен!</h2>
            <Certificate cert={certificate} />
          </motion.div>
        )}
      </AnimatePresence>

      <button className="btn-ghost" onClick={onExit}><ArrowLeft className="h-4 w-4" /> К профессии</button>
    </motion.section>
  );
}
