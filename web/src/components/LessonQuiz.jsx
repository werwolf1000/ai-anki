import { useState } from "react";
import { ClipboardList } from "lucide-react";
import { api } from "../lib/api";
import { Spinner } from "./ui";

export default function LessonQuiz({ book, lesson }) {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function generate() {
    setBusy("generate"); setError("");
    try {
      const data = await api(`/api/books/${book}/quiz`, { method: "POST", body: { lesson } });
      setQuiz(data); setAnswers({}); setResult(null);
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  async function check() {
    setBusy("check"); setError("");
    try {
      setResult(await api(`/api/lesson-quizzes/${quiz.id}/check`, {
        method: "POST", body: { answers: quiz.questions.map((_, i) => answers[i]) },
      }));
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }
  return (
    <section className="glass space-y-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 font-semibold"><ClipboardList className="h-4 w-4 text-violet-300" /> Тест по уроку</h3>
          <p className="mt-1 text-sm text-zinc-400">Проверьте понимание темы. Результат не влияет на сертификат.</p>
        </div>
        <button className="btn-ghost" onClick={generate} disabled={!!busy}>{busy === "generate" && <Spinner />}{quiz ? "Новый тест" : "Создать тест"}</button>
      </div>
      {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
      {quiz && <div className="space-y-5">
        {quiz.questions.map((q, i) => (
          <fieldset key={`${quiz.id}-${i}`} disabled={!!busy || !!result} className="space-y-2">
            <legend className="mb-2 text-sm font-semibold">{i + 1}. {q.question}</legend>
            {q.options.map((option, j) => (
              <label key={j} className="flex cursor-pointer items-start gap-3 rounded-lg border border-white/10 px-3 py-2 text-sm text-zinc-300 focus-within:border-violet-400">
                <input type="radio" name={`${quiz.id}-${i}`} checked={answers[i] === j} onChange={() => setAnswers((a) => ({ ...a, [i]: j }))} className="mt-1 accent-violet-500" />
                <span>{option}</span>
              </label>
            ))}
            {result && <p className={`text-sm ${result.results[i].passed ? "text-emerald-300" : "text-amber-300"}`}>
              {result.results[i].passed ? "Верно. " : `Правильный ответ: ${q.options[result.results[i].correct]}. `}{result.results[i].explanation}
            </p>}
          </fieldset>
        ))}
        {result ? <p role="status" className="font-semibold">Правильных ответов: {result.score} из {result.total}</p> :
          <button className="btn-primary" onClick={check} disabled={!!busy || Object.keys(answers).length !== quiz.questions.length}>{busy === "check" && <Spinner />}Проверить ответы</button>}
      </div>}
    </section>
  );
}
