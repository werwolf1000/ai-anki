// Monaco из npm (без CDN) — работает и в браузере, и в Electron офлайн.
import { useEffect, useRef } from "react";
import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import editorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import tsWorker from "monaco-editor/esm/vs/language/typescript/ts.worker?worker";
import jsonWorker from "monaco-editor/esm/vs/language/json/json.worker?worker";
import cssWorker from "monaco-editor/esm/vs/language/css/css.worker?worker";
import htmlWorker from "monaco-editor/esm/vs/language/html/html.worker?worker";
import { ANGULAR_LIBS } from "./angularTypes";

self.MonacoEnvironment = {
  getWorker(_id, label) {
    if (label === "typescript" || label === "javascript") return new tsWorker();
    if (label === "json") return new jsonWorker();
    if (label === "css" || label === "scss" || label === "less") return new cssWorker();
    if (label === "html" || label === "handlebars" || label === "razor") return new htmlWorker();
    return new editorWorker();
  },
};
loader.config({ monaco });

let configured = false;
function configure(m) {
  if (configured) return;
  configured = true;
  const ts = m.languages.typescript;
  const opts = {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.NodeJs,
    allowNonTsExtensions: true,
    experimentalDecorators: true,
    allowJs: true,
    noEmit: true,
    strict: false,
  };
  for (const d of [ts.typescriptDefaults, ts.javascriptDefaults]) {
    d.setCompilerOptions(opts);
    d.setDiagnosticsOptions({ noSemanticValidation: true, noSyntaxValidation: true });
    d.setEagerModelSync(true);
    for (const lib of ANGULAR_LIBS) d.addExtraLib(lib.content, lib.path);
  }
  m.editor.defineTheme("anki-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "6b6b85", fontStyle: "italic" },
      { token: "keyword", foreground: "c4a5ff" },
      { token: "string", foreground: "86efac" },
      { token: "number", foreground: "fdba74" },
      { token: "type", foreground: "fcd34d" },
    ],
    colors: {
      "editor.background": "#0a0a14",
      "editor.lineHighlightBackground": "#ffffff08",
      "editorLineNumber.foreground": "#3f3f58",
      "editorLineNumber.activeForeground": "#a1a1c2",
      "editor.selectionBackground": "#8b5cf640",
      "editorCursor.foreground": "#a78bfa",
      "editorWidget.background": "#141421",
      "editorSuggestWidget.background": "#141421",
      "editorSuggestWidget.border": "#26263a",
      "editorSuggestWidget.selectedBackground": "#8b5cf633",
    },
  });
}

const LANGS = { ts: "typescript", js: "javascript", py: "python", golang: "go", bash: "shell" };
export const monacoLanguage = (lang) => {
  const l = (lang || "typescript").toLowerCase();
  return LANGS[l] || l;
};

export default function CodeEditor({ value, onChange, language, theme = "dark", onSubmit, height = 340 }) {
  const submitRef = useRef(onSubmit);
  submitRef.current = onSubmit;
  const editorRef = useRef(null);

  useEffect(() => {
    editorRef.current?.focus();
  }, [language]);

  return (
    <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-[#0a0a14] focus-within:border-violet-500/60">
      <Editor
        height={height}
        language={monacoLanguage(language)}
        value={value}
        onChange={(v) => onChange(v ?? "")}
        theme={theme === "light" ? "vs" : "anki-dark"}
        beforeMount={configure}
        onMount={(editor, m) => {
          editorRef.current = editor;
          editor.addCommand(m.KeyMod.CtrlCmd | m.KeyCode.Enter, () => submitRef.current?.());
          editor.focus();
        }}
        loading={<div className="text-sm text-zinc-500">Загрузка редактора…</div>}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: '"JetBrains Mono", "Cascadia Code", Consolas, monospace',
          fontLigatures: true,
          tabSize: 4,
          scrollBeyondLastLine: false,
          padding: { top: 14, bottom: 14 },
          renderLineHighlight: "all",
          renderValidationDecorations: "off",
          smoothScrolling: true,
          cursorBlinking: "smooth",
          cursorSmoothCaretAnimation: "on",
          automaticLayout: true,
          wordBasedSuggestions: "currentDocument",
          quickSuggestions: { other: true, comments: false, strings: true },
          scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
        }}
      />
    </div>
  );
}
