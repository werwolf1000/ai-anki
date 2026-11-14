import { useState } from "react";
import { motion } from "motion/react";
import { Award, Check, Copy, ExternalLink, Printer, ShieldCheck } from "lucide-react";
import { formatDate, trackStyle, verifyUrl } from "../lib/tracks";
import { Logo } from "./ui";

/** Сертификат о прохождении трека. Печатается отдельно от интерфейса (см. .print-cert в CSS). */
export default function Certificate({ cert, actions = true }) {
  const [copied, setCopied] = useState(false);
  const st = trackStyle(cert.track_id);
  const url = verifyUrl(cert.id);

  function copy() {
    navigator.clipboard?.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    });
  }

  return (
    <div className="space-y-3">
      <motion.div
        initial={{ opacity: 0, y: 16, rotateX: 8 }}
        animate={{ opacity: 1, y: 0, rotateX: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="print-cert relative overflow-hidden rounded-2xl border border-amber-200/20 bg-[#0d0c14] p-[3px] shadow-[0_30px_80px_-30px_rgba(251,191,36,0.35)]"
      >
        <div className="relative overflow-hidden rounded-[14px] border border-amber-200/10 bg-gradient-to-br from-[#14121f] via-[#0f0e18] to-[#171225] px-6 py-8 sm:px-12 sm:py-10">
          {/* декор */}
          <div className={`pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-gradient-to-br ${st.grad} opacity-20 blur-3xl`} />
          <div className="pointer-events-none absolute -bottom-28 -left-20 h-72 w-72 rounded-full bg-amber-400/10 blur-3xl" />
          <motion.div
            className="pointer-events-none absolute inset-0 bg-[linear-gradient(110deg,transparent_35%,rgba(255,255,255,0.06)_50%,transparent_65%)]"
            initial={{ x: "-100%" }}
            animate={{ x: "100%" }}
            transition={{ duration: 2.2, delay: 0.4, ease: "easeInOut" }}
          />

          <div className="relative flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <Logo size={36} />
              <div>
                <div className="text-sm font-bold tracking-wide text-zinc-100">AI Anki</div>
                <div className="text-[10px] uppercase tracking-[0.25em] text-amber-200/60">Academy</div>
              </div>
            </div>
            <div className="text-right text-[10px] uppercase tracking-[0.2em] text-zinc-500">
              № {cert.id}
            </div>
          </div>

          <div className="relative mt-8 text-center">
            <div className="text-[11px] font-semibold uppercase tracking-[0.35em] text-amber-200/70">Сертификат</div>
            <div className="mt-1 text-xs text-zinc-400">подтверждает, что</div>
            <div className="mt-3 bg-gradient-to-r from-amber-100 via-amber-300 to-amber-100 bg-clip-text font-serif text-3xl font-bold text-transparent sm:text-4xl">
              {cert.holder}
            </div>
            <div className="mx-auto mt-4 max-w-md text-sm leading-relaxed text-zinc-300">
              успешно прошёл(-а) обучение, AI-собеседование и итоговый экзамен по профессии
            </div>
            <div className={`mt-3 inline-flex items-center gap-2 rounded-full bg-gradient-to-r ${st.grad} px-5 py-2 text-base font-bold text-white shadow-lg`}>
              <st.icon className="h-4 w-4" /> {cert.track_title}
            </div>
          </div>

          <div className="relative mx-auto mt-8 grid max-w-lg grid-cols-3 gap-3 text-center">
            {[
              ["Экзамен", `${Math.round(cert.exam_score)}`],
              ["Собеседование", `${Math.round(cert.interview_score)}`],
              ["Освоено", `${Math.round(cert.coverage * 100)}%`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-white/[0.06] bg-white/[0.03] px-2 py-3">
                <div className="text-xl font-bold tabular-nums text-zinc-50">{value}</div>
                <div className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</div>
              </div>
            ))}
          </div>

          <div className="relative mt-8 flex items-end justify-between gap-4 text-xs text-zinc-500">
            <div>
              <div className="text-zinc-300">{formatDate(cert.issued_at)}</div>
              <div>дата выдачи</div>
            </div>
            <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-amber-300/40 bg-amber-300/5 text-amber-200">
              <Award className="h-8 w-8" />
            </div>
            <div className="text-right">
              <div className="flex items-center justify-end gap-1 text-zinc-300"><ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> проверяемый</div>
              <div className="max-w-[180px] truncate">{url.replace(/^https?:\/\//, "")}</div>
            </div>
          </div>
        </div>
      </motion.div>

      {actions && (
        <div className="no-print flex flex-wrap gap-2">
          <button className="btn-ghost" onClick={() => window.print()}>
            <Printer className="h-4 w-4" /> Печать / PDF
          </button>
          <button className="btn-ghost" onClick={copy}>
            {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />} Ссылка для проверки
          </button>
          <a className="btn-ghost" href={url} target="_blank" rel="noreferrer">
            <ExternalLink className="h-4 w-4" /> Открыть
          </a>
        </div>
      )}
    </div>
  );
}
