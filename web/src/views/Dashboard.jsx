import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { ArrowRight, CalendarCheck, Flame, GraduationCap, Repeat2, Target } from "lucide-react";
import { api } from "../lib/api";
import { kindOf, plural } from "../lib/decks";
import { CountUp, Ring, Spinner } from "../components/ui";
import StartModal from "../components/StartModal";

function greeting() {
  const h = new Date().getHours();
  if (h < 5) return "Доброй ночи";
  if (h < 12) return "Доброе утро";
  if (h < 18) return "Добрый день";
  return "Добрый вечер";
}

export default function Dashboard({ user, decks, onStart, goDecks }) {
  const [stats, setStats] = useState(null);
  const [picked, setPicked] = useState(null);
  const [listRef] = useAutoAnimate();

  useEffect(() => {
    api("/api/dashboard").then(setStats).catch(() => setStats({ activity: [] }));
  }, []);

  const totals = useMemo(() => {
    const ok = (decks || []).filter((d) => !d.error);
    return {
      total: ok.reduce((a, d) => a + d.total, 0),
      mastered: ok.reduce((a, d) => a + d.mastered, 0),
      today: ok.reduce((a, d) => a + d.passed_today, 0),
      dueReview: ok.reduce((a, d) => a + Math.max(0, d.due - d.new), 0),
      studied: ok.reduce((a, d) => a + d.studied, 0),
    };
  }, [decks]);

  const continueDecks = useMemo(
    () =>
      (decks || [])
        .filter((d) => !d.error && d.studied > 0)
        .sort((a, b) => (b.last_reviewed_at || "").localeCompare(a.last_reviewed_at || ""))
        .slice(0, 6),
    [decks],
  );

  const tiles = [
    { icon: CalendarCheck, label: "Засчитано сегодня", value: totals.today, tone: "text-emerald-300" },
    { icon: Repeat2, label: "Пора повторить", value: totals.dueReview, tone: "text-violet-300" },
    { icon: GraduationCap, label: "Усвоено", value: totals.mastered, sub: `из ${totals.total}`, tone: "text-sky-300" },
    { icon: Flame, label: "Серия", value: stats?.streak ?? 0, sub: plural(stats?.streak ?? 0, "день", "дня", "дней"), tone: "text-rose-300" },
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-400">{greeting()},</p>
          <h1 className="text-3xl font-extrabold tracking-tight">{user.display_name || user.username}</h1>
        </div>
        <button className="btn-primary" onClick={goDecks}>
          К колодам <ArrowRight className="h-4 w-4" />
        </button>
      </header>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {tiles.map((t, i) => (
          <motion.div
            key={t.label}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, ease: [0.16, 1, 0.3, 1], duration: 0.5 }}
            className="glass p-4 sm:p-5"
          >
            <div className="flex items-center gap-2 text-xs font-medium text-zinc-400">
              <t.icon className={`h-4 w-4 ${t.tone}`} />
              {t.label}
            </div>
            <div className="mt-3 flex items-baseline gap-1.5">
              <span className="text-3xl font-bold tabular-nums tracking-tight">
                {decks ? <CountUp value={t.value} /> : "—"}
              </span>
              {t.sub && <span className="text-sm text-zinc-500">{t.sub}</span>}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <motion.section initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass p-5">
          <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
            <div>
              <h2 className="font-semibold">Ответы за 4 недели</h2>
              <p className="text-xs text-zinc-500">Карточки, по которым вы получили итоговую оценку</p>
            </div>
            {stats && (
              <div className="text-right text-xs text-zinc-400">
                <span className="text-base font-semibold text-zinc-100">{stats.week_answers ?? 0}</span> за 7 дней
                {stats.week_avg_score != null && <> · средний балл <span className="text-zinc-100">{stats.week_avg_score}</span></>}
              </div>
            )}
          </div>
          {stats ? <ActivityChart data={stats.activity} /> : <div className="flex h-40 items-center justify-center"><Spinner /></div>}
        </motion.section>

        <motion.section initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.26 }} className="glass flex flex-col items-center justify-center gap-4 p-5 text-center">
          <Ring value={totals.total ? totals.mastered / totals.total : 0} size={148} stroke={11} gradientId="overall">
            <div>
              <div className="text-3xl font-bold tabular-nums">
                {totals.total ? Math.round((totals.mastered / totals.total) * 100) : 0}%
              </div>
              <div className="text-[11px] uppercase tracking-widest text-zinc-500">усвоено</div>
            </div>
          </Ring>
          <div className="text-sm text-zinc-400">
            Изучено <span className="font-semibold text-zinc-100">{totals.studied}</span> из {totals.total} карточек
          </div>
          <div className="flex items-center gap-1.5 text-xs text-zinc-500">
            <Target className="h-3.5 w-3.5" /> Порог зачёта — {stats?.pass_score ?? 75} баллов
          </div>
        </motion.section>
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Продолжить</h2>
          <button className="text-sm text-violet-300 hover:text-violet-200" onClick={goDecks}>Все колоды</button>
        </div>
        {!decks ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : continueDecks.length === 0 ? (
          <div className="glass p-6 text-sm text-zinc-400">
            Вы ещё не начали ни одной колоды. Откройте раздел «Колоды» и выберите тему.
          </div>
        ) : (
          <div ref={listRef} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {continueDecks.map((d) => {
              const k = kindOf(d);
              const dueReview = Math.max(0, d.due - d.new);
              return (
                <motion.button
                  key={d.deck_id}
                  whileHover={{ y: -3 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setPicked(d)}
                  className="glass group flex items-center gap-4 p-4 text-left"
                >
                  <Ring value={d.total ? d.mastered / d.total : 0} size={48} stroke={4} gradientId={`c-${d.deck_id}`}>
                    <k.icon className={`h-4 w-4 ${k.text}`} />
                  </Ring>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-semibold">{d.name}</div>
                    <div className="text-xs text-zinc-400">
                      {dueReview > 0 ? <span className="text-violet-300">{dueReview} к повтору</span> : "Нечего повторять"} · ср. {d.avg_score || "—"}
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-zinc-600 transition-colors group-hover:text-zinc-200" />
                </motion.button>
              );
            })}
          </div>
        )}
      </section>

      <StartModal deck={picked} onClose={() => setPicked(null)} onStart={(s) => { setPicked(null); setTimeout(() => onStart(s), 180); }} />
    </div>
  );
}

/** Столбики: одна серия (ответы в день), подсказка при наведении. */
function ActivityChart({ data }) {
  const [hover, setHover] = useState(null);
  const max = Math.max(1, ...data.map((d) => d.answered));
  const W = 560;
  const H = 150;
  const gap = 4;
  const bw = (W - gap * (data.length - 1)) / data.length;
  const fmt = (iso) => new Date(iso + "T00:00:00").toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
  const ticks = [0, Math.round(max / 2), max].filter((v, i, a) => a.indexOf(v) === i);

  if (!data.length) return <div className="py-10 text-center text-sm text-zinc-500">Нет данных</div>;

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H + 22}`} className="w-full overflow-visible" role="img" aria-label="Количество ответов по дням">
        {ticks.map((t) => {
          const y = H - (t / max) * H;
          return (
            <g key={t}>
              <line x1={0} x2={W} y1={y} y2={y} stroke="rgba(255,255,255,0.06)" />
              <text x={W} y={y - 4} textAnchor="end" className="fill-zinc-500 text-[10px]">{t}</text>
            </g>
          );
        })}
        {data.map((d, i) => {
          const h = d.answered ? Math.max(4, (d.answered / max) * H) : 0;
          const x = i * (bw + gap);
          return (
            <g key={d.date} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <rect x={x - gap / 2} y={0} width={bw + gap} height={H} fill="transparent" />
              {d.answered === 0 && <rect x={x} y={H - 2} width={bw} height={2} rx={1} fill="rgba(255,255,255,0.08)" />}
              <motion.rect
                x={x}
                width={bw}
                rx={4}
                fill={hover === i ? "#c4b5fd" : "#8b5cf6"}
                initial={{ y: H, height: 0 }}
                animate={{ y: H - h, height: h }}
                transition={{ delay: i * 0.015, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              />
            </g>
          );
        })}
        {[0, Math.floor(data.length / 2), data.length - 1].map((i) => (
          <text key={i} x={i * (bw + gap) + bw / 2} y={H + 16} textAnchor="middle" className="fill-zinc-500 text-[10px]">
            {fmt(data[i].date)}
          </text>
        ))}
      </svg>
      {hover != null && (
        <div
          className="pointer-events-none absolute -top-2 z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-lg border border-white/10 bg-ink-900/95 px-3 py-2 text-xs shadow-xl"
          style={{ left: `${((hover * (bw + gap) + bw / 2) / W) * 100}%` }}
        >
          <div className="font-semibold text-zinc-100">{fmt(data[hover].date)}</div>
          <div className="text-zinc-400">
            Ответов: <span className="text-zinc-100">{data[hover].answered}</span>
            {data[hover].answered > 0 && (
              <>
                {" "}· зачтено <span className="text-zinc-100">{data[hover].passed}</span> · ср. балл{" "}
                <span className="text-zinc-100">{data[hover].avg_score}</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
