import { useEffect, useState } from "react";
import { Copy, Minus, Square, X } from "lucide-react";
import { isDesktop, windowControls } from "../lib/desktop";
import { Logo } from "./ui";

/** Заголовок frameless-окна Electron: перетаскивание + кнопки окна. */
export default function TitleBar({ subtitle }) {
  const [maximized, setMaximized] = useState(false);
  useEffect(() => {
    if (!isDesktop) return;
    windowControls.isMaximized().then(setMaximized);
    return windowControls.onMaximizeChange(setMaximized);
  }, []);
  if (!isDesktop) return null;
  return (
    <div
      className="drag relative z-40 flex h-10 shrink-0 items-center justify-between border-b border-white/[0.05] bg-ink-950/70 pl-3 backdrop-blur-xl"
      onDoubleClick={windowControls.toggleMaximize}
    >
      <div className="flex items-center gap-2.5 text-xs">
        <Logo size={20} />
        <span className="font-semibold tracking-wide text-zinc-200">AI Anki</span>
        {subtitle && <span className="text-zinc-500">· {subtitle}</span>}
      </div>
      <div className="no-drag flex h-full">
        <button className="flex h-full w-12 items-center justify-center text-zinc-400 transition-colors hover:bg-white/[0.06] hover:text-white" onClick={windowControls.minimize} aria-label="Свернуть">
          <Minus className="h-4 w-4" />
        </button>
        <button className="flex h-full w-12 items-center justify-center text-zinc-400 transition-colors hover:bg-white/[0.06] hover:text-white" onClick={windowControls.toggleMaximize} aria-label="Развернуть">
          {maximized ? <Copy className="h-3.5 w-3.5 -scale-x-100" /> : <Square className="h-3.5 w-3.5" />}
        </button>
        <button className="flex h-full w-12 items-center justify-center text-zinc-400 transition-colors hover:bg-rose-600 hover:text-white" onClick={windowControls.close} aria-label="Закрыть">
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
