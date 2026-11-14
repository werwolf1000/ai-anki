// Редактор формул MathLive + предпросмотр KaTeX.
import { useEffect, useRef } from "react";
import { MathfieldElement } from "mathlive";
import { RichText } from "../lib/richtext";

MathfieldElement.fontsDirectory = "https://cdn.jsdelivr.net/npm/mathlive@0.101.2/fonts/";
MathfieldElement.soundsDirectory = null;

export default function MathEditor({ value, onChange, onSubmit, resetKey }) {
  const ref = useRef(null);
  const submitRef = useRef(onSubmit);
  submitRef.current = onSubmit;
  const changeRef = useRef(onChange);
  changeRef.current = onChange;

  useEffect(() => {
    const mf = ref.current;
    if (!mf) return;
    mf.smartFence = true;
    mf.smartSuperscript = true;
    mf.mathVirtualKeyboardPolicy = "manual";
    const onInput = () => changeRef.current(mf.getValue("latex"));
    const onKey = (e) => {
      if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        submitRef.current?.();
      }
    };
    mf.addEventListener("input", onInput);
    mf.addEventListener("keydown", onKey);
    return () => {
      mf.removeEventListener("input", onInput);
      mf.removeEventListener("keydown", onKey);
    };
  }, []);

  // внешняя установка значения (новая карточка / очистка)
  useEffect(() => {
    const mf = ref.current;
    if (mf && mf.getValue("latex") !== value) mf.setValue(value || "", { silenceNotifications: true });
    mf?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey]);

  return (
    <div className="space-y-3">
      <math-field ref={ref} aria-label="Редактор формул" />
      <div className="flex items-center justify-between text-xs text-zinc-500">
        <span>Предпросмотр</span>
        <button type="button" className="text-violet-300 hover:text-violet-200" onClick={() => ref.current?.executeCommand("toggleVirtualKeyboard")}>
          Экранная клавиатура
        </button>
      </div>
      <div className="min-h-[3rem] rounded-xl border border-dashed border-white/[0.08] px-4 py-3 text-zinc-200">
        {value ? <RichText text={`$$${value}$$`} math /> : <span className="text-sm text-zinc-600">Формула появится здесь</span>}
      </div>
    </div>
  );
}
