import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { useAutoAnimate } from "@formkit/auto-animate/react";
import { BookOpenText, Play, Search } from "lucide-react";
import { api } from "../lib/api";
import { kindOf, MODES } from "../lib/decks";
import { Modal, Ring, Spinner, useToast } from "./ui";

export default function StartModal({ deck, onClose, onStart, onRead }) {
  const toast = useToast();
  const [mode, setMode] = useState("due");
  const [topics, setTopics] = useState(null);
  const [topic, setTopic] = useState("");
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [listRef] = useAutoAnimate({ duration: 180 });

  useEffect(() => {
    setMode("due");
    setTopic("");
    setQuery("");
    setTopics(null);
    if (deck?.has_topics) {
      api(`/api/deck/${deck.deck_id}/topics`)
        .then((r) => setTopics(r.topics))
        .catch(() => setTopics([]));
    }
  }, [deck]);

  async function start() {
    setBusy(true);
    try {
      const body = { deck_id: deck.deck_id, mode };
      if (topic) body.topic = topic;
      const s = await api("/api/session", { method: "POST", body });
      if (s.empty) {
        toast("В этом режиме нет карточек — попробуйте другой", "info");
        return;
      }
      onStart(s);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  if (!deck) return <Modal open={false} />;
  const k = kindOf(deck);
  const counts = { due: deck.due, new: deck.new, weak: deck.weak, all: deck.total };
  const shownTopics = (topics || []).filter((t) => t.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <Modal open={!!deck} onClose={onClose} width="max-w-2xl">
      <div className={`relative overflow-hidden rounded-t-2xl bg-gradient-to-br ${k.grad} p-6 pb-5`}>
        <div className="flex items-center gap-4">
          <Ring value={deck.total ? deck.mastered / deck.total : 0} size={64} stroke={6} gradientId={`m-${deck.deck_id}`}>
            <k.icon className={`h-6 w-6 ${k.text}`} />
          </Ring>
          <div className="min-w-0 pr-8">
            <div className={`text-xs font-semibold uppercase tracking-widest ${k.text}`}>{k.label}</div>
            <h2 className="truncate text-2xl font-bold">{deck.name}</h2>
            <div className="mt-1 text-sm text-zinc-300">
              {deck.total} карточек · усвоено {deck.mastered} · сегодня {deck.passed_today}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6 p-6">
        <div>
          <div className="label">Режим</div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                title={m.hint}
                className={`relative rounded-xl border px-3 py-3 text-left transition-colors ${mode === m.id ? "border-violet-500/50 text-white" : "border-white/[0.07] text-zinc-400 hover:border-white/15 hover:text-zinc-200"}`}
              >
                {mode === m.id && (
                  <motion.span layoutId="mode-active" className="absolute inset-0 rounded-xl bg-violet-500/15" transition={{ type: "spring", stiffness: 420, damping: 34 }} />
                )}
                <div className="relative text-sm font-semibold">{m.label}</div>
                <div className="relative mt-0.5 text-lg font-bold tabular-nums">{counts[m.id] ?? 0}</div>
              </button>
            ))}
          </div>
        </div>

        {deck.has_topics && (
          <div>
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="label mb-0">Тема</div>
              <div className="relative w-48">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-500" />
                <input className="input py-1.5 pl-8 text-xs" placeholder="Поиск темы" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
            </div>
            {topics === null ? (
              <div className="flex justify-center py-6"><Spinner /></div>
            ) : (
              <div ref={listRef} className="grid max-h-64 grid-cols-1 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
                <TopicButton active={!topic} onClick={() => setTopic("")} name="Все темы" sub={`${topics.length} тем`} />
                {shownTopics.map((t) => (
                  <TopicButton
                    key={t.name}
                    active={topic === t.name}
                    onClick={() => setTopic(t.name)}
                    name={t.name}
                    sub={`${t.total} · повтор ${t.due} · новые ${t.new}${t.weak ? ` · слабые ${t.weak}` : ""}`}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          {onRead && (
            <button className="btn-ghost sm:mr-auto" onClick={() => onRead(deck.deck_id, topic)} title="Прочитать теорию перед карточками">
              <BookOpenText className="h-4 w-4" /> {topic ? "Прочитать тему" : "Учебник"}
            </button>
          )}
          <button className="btn-ghost" onClick={onClose}>Отмена</button>
          <motion.button whileTap={{ scale: 0.97 }} className="btn-primary px-6" onClick={start} disabled={busy}>
            {busy ? <Spinner /> : <Play className="h-4 w-4" />} Начать
          </motion.button>
        </div>
      </div>
    </Modal>
  );
}

function TopicButton({ active, onClick, name, sub }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-xl border px-3 py-2.5 text-left transition-colors ${active ? "border-violet-500/50 bg-violet-500/15" : "border-white/[0.06] bg-white/[0.02] hover:border-white/15"}`}
    >
      <div className="truncate text-sm font-medium">{name}</div>
      <div className="truncate text-[11px] text-zinc-500">{sub}</div>
    </button>
  );
}
