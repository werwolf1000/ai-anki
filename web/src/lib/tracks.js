import {
  Brain, ClipboardCheck, Code2, Container, Hexagon, MessageSquareText, Palette, Rabbit, Rocket,
} from "lucide-react";

// Визуальная айдентика профессий
export const TRACK_STYLE = {
  php: { icon: Code2, grad: "from-indigo-500 to-violet-500", soft: "from-indigo-500/25 to-violet-500/5", text: "text-indigo-300" },
  python: { icon: Code2, grad: "from-blue-500 to-amber-400", soft: "from-blue-500/25 to-amber-400/5", text: "text-blue-300" },
  nodejs: { icon: Hexagon, grad: "from-emerald-500 to-lime-500", soft: "from-emerald-500/25 to-lime-500/5", text: "text-emerald-300" },
  go: { icon: Rabbit, grad: "from-cyan-500 to-sky-500", soft: "from-cyan-500/25 to-sky-500/5", text: "text-cyan-300" },
  devops: { icon: Container, grad: "from-orange-500 to-amber-500", soft: "from-orange-500/25 to-amber-500/5", text: "text-orange-300" },
  fde: { icon: Rocket, grad: "from-rose-500 to-orange-500", soft: "from-rose-500/25 to-orange-500/5", text: "text-rose-300" },
  "ai-trainer": { icon: Brain, grad: "from-fuchsia-500 to-pink-500", soft: "from-fuchsia-500/25 to-pink-500/5", text: "text-fuchsia-300" },
  "prompt-engineer": { icon: MessageSquareText, grad: "from-violet-500 to-purple-500", soft: "from-violet-500/25 to-purple-500/5", text: "text-violet-300" },
  "llm-evaluator": { icon: ClipboardCheck, grad: "from-teal-500 to-emerald-500", soft: "from-teal-500/25 to-emerald-500/5", text: "text-teal-300" },
  "ai-artist": { icon: Palette, grad: "from-pink-500 to-amber-400", soft: "from-pink-500/25 to-amber-400/5", text: "text-pink-300" },
};

export const trackStyle = (id) => TRACK_STYLE[id] || TRACK_STYLE.php;

export function verifyUrl(certId) {
  const base = (typeof window !== "undefined" && window.desktop) ? "https://anki.webmastermsk.ru" : window.location.origin;
  return `${base}/verify/${certId}`;
}

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}
