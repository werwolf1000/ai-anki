import { BookOpen, Code2, HeartPulse, Sigma, Terminal } from "lucide-react";

export const KINDS = {
  live: { label: "Live-coding", icon: Terminal, grad: "from-emerald-500/25 to-cyan-500/10", text: "text-emerald-300" },
  code: { label: "Код", icon: Code2, grad: "from-violet-500/25 to-indigo-500/10", text: "text-violet-300" },
  math: { label: "Математика", icon: Sigma, grad: "from-amber-500/25 to-orange-500/10", text: "text-amber-300" },
  anatomy: { label: "Анатомия", icon: HeartPulse, grad: "from-rose-500/25 to-pink-500/10", text: "text-rose-300" },
  theory: { label: "Теория", icon: BookOpen, grad: "from-sky-500/25 to-blue-500/10", text: "text-sky-300" },
};

export const kindOf = (deck) => KINDS[deck?.kind] || KINDS.theory;

export const MODES = [
  { id: "due", label: "Повторение", hint: "Новые и те, что пора повторить" },
  { id: "new", label: "Только новые", hint: "Карточки, которые вы ещё не видели" },
  { id: "weak", label: "Слабые", hint: "Ответы ниже порога зачёта" },
  { id: "all", label: "Вся колода", hint: "Все карточки, от слабых к сильным" },
];

export const modeLabel = (id) => MODES.find((m) => m.id === id)?.label || id;

export function plural(n, one, few, many) {
  const a = Math.abs(n) % 100;
  const b = a % 10;
  if (a > 10 && a < 20) return many;
  if (b > 1 && b < 5) return few;
  if (b === 1) return one;
  return many;
}
