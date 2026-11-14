// Запись с микрофона → /api/asr/transcribe (Whisper на сервере).
import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { Mic, Square } from "lucide-react";
import { api } from "../lib/api";
import { Spinner } from "./ui";

function pickMime() {
  for (const t of ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"]) {
    if (window.MediaRecorder?.isTypeSupported?.(t)) return t;
  }
  return "";
}

export default function VoiceButton({ onText, onStatus, disabled, context = "", compact = false }) {
  const [state, setState] = useState("idle"); // idle | rec | busy
  const rec = useRef(null);
  const stream = useRef(null);
  const chunks = useRef([]);

  useEffect(() => () => stream.current?.getTracks().forEach((t) => t.stop()), []);

  async function start() {
    if (!navigator.mediaDevices?.getUserMedia) {
      onStatus?.("Запись с микрофона не поддерживается", "error");
      return;
    }
    try {
      // моно + шумо/эхоподавление и автоусиление — заметно улучшают распознавание
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
    } catch (e) {
      onStatus?.(`Нет доступа к микрофону: ${e.message}`, "error");
      return;
    }
    const mime = pickMime();
    const opts = { audioBitsPerSecond: 128000, ...(mime ? { mimeType: mime } : {}) };
    const mr = new MediaRecorder(stream.current, opts);
    chunks.current = [];
    mr.ondataavailable = (e) => e.data?.size && chunks.current.push(e.data);
    mr.onstop = async () => {
      stream.current?.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunks.current, { type: mr.mimeType || "audio/webm" });
      if (!blob.size) {
        setState("idle");
        onStatus?.("Запись пуста", "info");
        return;
      }
      setState("busy");
      try {
        const ext = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "mp4" : "webm";
        const form = new FormData();
        form.append("audio", blob, `recording.${ext}`);
        if (context) form.append("context", context.slice(0, 1500));
        const r = await api("/api/asr/transcribe", { method: "POST", form });
        onText(r.text || "", r);
        onStatus?.(r.corrected ? "Текст распознан и исправлен ИИ — проверьте и отправьте" : "Текст распознан — проверьте и отправьте", "success");
      } catch (e) {
        onStatus?.(e.message, "error");
      } finally {
        setState("idle");
      }
    };
    mr.start();
    rec.current = mr;
    setState("rec");
  }

  function stop() {
    if (rec.current?.state !== "inactive") rec.current?.stop();
  }

  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.95 }}
      disabled={disabled || state === "busy"}
      onClick={state === "rec" ? stop : start}
      className={`btn-ghost relative ${state === "rec" ? "border-rose-500/50 text-rose-200" : ""}`}
      title="Ответить голосом"
    >
      {state === "rec" && (
        <motion.span
          className="absolute inset-0 rounded-xl border border-rose-500/60"
          animate={{ scale: [1, 1.08, 1], opacity: [0.8, 0, 0.8] }}
          transition={{ duration: 1.4, repeat: Infinity }}
        />
      )}
      {state === "busy" ? <Spinner /> : state === "rec" ? <Square className="h-4 w-4 fill-current" /> : <Mic className="h-4 w-4" />}
      {!compact && <span className="hidden sm:inline">{state === "rec" ? "Стоп" : state === "busy" ? "Распознаём…" : "Голосом"}</span>}
    </motion.button>
  );
}
