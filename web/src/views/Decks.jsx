import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { AlertTriangle, Layers, RefreshCw, Search } from "lucide-react";
import { KINDS, kindOf } from "../lib/decks";
import { EmptyState, Ring, Spinner } from "../components/ui";
import StartModal from "../components/StartModal";

const SORTS = [
  { id: "due", label: "К повтору" },
  { id: "name", label: "По имени" },
  { id: "progress", label: "По прогрессу" },
];

export default function Decks({ decks, reload, onStart }) {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("all");
  const [sort, setSort] = useState("due");
  const [picked, setPicked] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [gridRef] = useAutoAnimate({ duration: 260 });

  const kindsPresent = useMemo(() => {
    const set = new Set((decks || []).map((d) => d.kind).filter(Boolean));
    return Object.entries(KINDS).filter(([id]) => set.has(id));
  }, [decks]);

  const shown = useMemo(() => {
    let list = (decks || []).filter((d) => (kind === "all" || d.kind === kind) && d.name.toLowerCase().includes(query.toLowerCase()));
    const pr = (d) => (d.total ? d.mastered / d.total : 0);
    if (sort === "name") list = [...list].sort((a, b) => a.name.localeCompare(b.name, "ru"));
    else if (sort === "progress") list = [...list].sort((a, b) => pr(b) - pr(a));
    else list = [...list].sort((a, b) => (b.due - b.new) - (a.due - a.new) || (b.studied - a.studied));
    return list;
  }, [decks, kind, query, sort]);

  async function refresh() {
    setRefreshing(true);
    try {
      await reload();
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Колоды</h1>
          <p className="text-sm text-zinc-400">{decks ? `${decks.length} колод · выберите колоду и режим` : "Загрузка…"}</p>
        </div>
        <button className="btn-ghost" onClick={refresh} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} /> Обновить
        </button>
      </header>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative lg:w-72">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input className="input pl-9" placeholder="Найти колоду" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <div className="flex flex-wrap gap-1.5">
          <FilterChip active={kind === "all"} onClick={() => setKind("all")}>Все</FilterChip>
          {kindsPresent.map(([id, k]) => (
            <FilterChip key={id} active={kind === id} onClick={() => setKind(id)}>
              <k.icon className={`h-3.5 w-3.5 ${k.text}`} /> {k.label}
            </FilterChip>
          ))}
        </div>
        <div className="flex gap-1 rounded-xl bg-ink-900/70 p-1 lg:ml-auto">
          {SORTS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSort(s.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${sort === s.id ? "bg-white/[0.09] text-white" : "text-zinc-400 hover:text-zinc-200"}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {!decks ? (
        <div className="flex justify-center py-20"><Spinner className="h-6 w-6" /></div>
      ) : shown.length === 0 ? (
        <EmptyState icon={<Layers className="h-6 w-6" />} title="Ничего не найдено" text="Измените фильтр или строку поиска." />
      ) : (
        <div ref={gridRef} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {shown.map((d) => (d.error ? <BrokenDeck key={d.deck_id} deck={d} /> : <DeckCard key={d.deck_id} deck={d} onOpen={() => setPicked(d)} />))}
        </div>
      )}

      <StartModal deck={picked} onClose={() => setPicked(null)} onStart={(s) => { setPicked(null); setTimeout(() => onStart(s), 180); }} />
    </div>
  );
}

function FilterChip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${active ? "border-violet-500/50 bg-violet-500/15 text-white" : "border-white/[0.07] text-zinc-400 hover:border-white/15 hover:text-zinc-200"}`}
    >
      {children}
    </button>
  );
}

function DeckCard({ deck: d, onOpen }) {
  const k = kindOf(d);
  const pct = d.total ? d.mastered / d.total : 0;
  const dueReview = Math.max(0, d.due - d.new);
  return (
    <motion.button
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      onClick={onOpen}
      className="glass group relative flex flex-col overflow-hidden p-5 text-left"
    >
      <div className={`pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b ${k.grad} opacity-60 transition-opacity group-hover:opacity-100`} />
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className={`mb-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest ${k.text}`}>
            <k.icon className="h-3.5 w-3.5" /> {k.label}
          </div>
          <h3 className="truncate text-lg font-bold">{d.name}</h3>
          <div className="text-xs text-zinc-400">
            {d.total} карточек{d.topics_count ? ` · ${d.topics_count} тем` : ""}
          </div>
        </div>
        <Ring value={pct} size={52} stroke={5} gradientId={`d-${d.deck_id}`}>
          <span className="text-xs font-semibold">{Math.round(pct * 100)}%</span>
        </Ring>
      </div>

      <div className="relative mt-5 grid grid-cols-4 gap-2 text-center">
        <Stat label="Повтор" value={dueReview} accent={dueReview > 0} />
        <Stat label="Новые" value={d.new} />
        <Stat label="Слабые" value={d.weak} warn={d.weak > 0} />
        <Stat label="Ср. балл" value={d.studied ? Math.round(d.avg_score) : "—"} />
      </div>

      <div className="relative mt-4 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-violet-500 to-rose-500"
          initial={{ width: 0 }}
          animate={{ width: `${(d.studied / Math.max(1, d.total)) * 100}%` }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
      <div className="relative mt-1.5 flex justify-between text-[11px] text-zinc-500">
        <span>изучено {d.studied}</span>
        {d.passed_today > 0 && <span className="text-emerald-400">+{d.passed_today} сегодня</span>}
      </div>
    </motion.button>
  );
}

function Stat({ label, value, accent, warn }) {
  return (
    <div className="rounded-lg bg-white/[0.03] px-1 py-2">
      <div className={`text-base font-bold tabular-nums ${accent ? "text-violet-300" : warn ? "text-amber-300" : "text-zinc-100"}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</div>
    </div>
  );
}

function BrokenDeck({ deck }) {
  return (
    <div className="glass flex items-start gap-3 border-rose-500/20 p-5">
      <AlertTriangle className="h-5 w-5 shrink-0 text-rose-400" />
      <div>
        <div className="font-semibold">{deck.name}</div>
        <div className="text-xs text-rose-200/80">{deck.error}</div>
      </div>
    </div>
  );
}
