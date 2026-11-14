// Рендер текста карточек и ответов модели: абзацы, списки, `код`, ```блоки```, $формулы$.
import { Fragment, useMemo } from "react";
import katex from "katex";
import hljs from "highlight.js/lib/core";
import php from "highlight.js/lib/languages/php";
import python from "highlight.js/lib/languages/python";
import typescript from "highlight.js/lib/languages/typescript";
import javascript from "highlight.js/lib/languages/javascript";
import go from "highlight.js/lib/languages/go";
import xml from "highlight.js/lib/languages/xml";
import bash from "highlight.js/lib/languages/bash";
import sql from "highlight.js/lib/languages/sql";
import json from "highlight.js/lib/languages/json";
import css from "highlight.js/lib/languages/css";

hljs.registerLanguage("php", php);
hljs.registerLanguage("python", python);
hljs.registerLanguage("typescript", typescript);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("go", go);
hljs.registerLanguage("xml", xml);
hljs.registerLanguage("bash", bash);
hljs.registerLanguage("sql", sql);
hljs.registerLanguage("json", json);
hljs.registerLanguage("css", css);

const LANG_ALIAS = { ts: "typescript", js: "javascript", py: "python", html: "xml", sh: "bash", shell: "bash", golang: "go" };

export function normalizeLang(lang) {
  const l = (lang || "").toLowerCase();
  return LANG_ALIAS[l] || l;
}

export function CodeBlock({ code, language, className = "" }) {
  const html = useMemo(() => {
    const lang = normalizeLang(language);
    try {
      if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value;
      return hljs.highlightAuto(code, ["php", "python", "typescript", "go", "bash", "sql"]).value;
    } catch {
      return escapeHtml(code);
    }
  }, [code, language]);
  return (
    <pre className={`code-block ${className}`}>
      {language && <span className="code-lang">{normalizeLang(language)}</span>}
      <code className="hljs" dangerouslySetInnerHTML={{ __html: html }} />
    </pre>
  );
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function MathTex({ tex, display }) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(tex, { displayMode: display, throwOnError: false });
    } catch {
      return escapeHtml(tex);
    }
  }, [tex, display]);
  return <span className={display ? "block my-2 overflow-x-auto" : ""} dangerouslySetInnerHTML={{ __html: html }} />;
}

// Инлайн: `код`, $$..$$, $..$ (только если включены формулы), **жирный**
function Inline({ text, math }) {
  const parts = [];
  const re = math
    ? /(`[^`\n]+`|\$\$[^$]+\$\$|\$[^$\n]+\$|\\\([^)]*\\\)|\*\*[^*\n]+\*\*)/g
    : /(`[^`\n]+`|\*\*[^*\n]+\*\*)/g;
  let last = 0;
  let m;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(<Fragment key={i++}>{text.slice(last, m.index)}</Fragment>);
    const tok = m[0];
    if (tok.startsWith("`")) parts.push(<code key={i++} className="inline-code">{tok.slice(1, -1)}</code>);
    else if (tok.startsWith("**")) parts.push(<strong key={i++} className="font-semibold text-white">{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("$$")) parts.push(<MathTex key={i++} tex={tok.slice(2, -2)} display />);
    else if (tok.startsWith("\\(")) parts.push(<MathTex key={i++} tex={tok.slice(2, -2)} />);
    else parts.push(<MathTex key={i++} tex={tok.slice(1, -1)} />);
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(<Fragment key={i++}>{text.slice(last)}</Fragment>);
  return <>{parts}</>;
}

/** Разбор текста на блоки: код, списки, абзацы. */
function parseBlocks(text) {
  const blocks = [];
  const lines = (text || "").replace(/\r\n/g, "\n").split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const fence = line.match(/^\s*```\s*([\w+-]*)\s*$/);
    if (fence) {
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) buf.push(lines[i++]);
      i++;
      blocks.push({ type: "code", lang: fence[1], text: buf.join("\n") });
      continue;
    }
    if (/^── Код ──$/.test(line.trim())) {
      // формат display_text() десктопной версии
      const buf = [];
      i++;
      while (i < lines.length && !/^Задание:/.test(lines[i])) buf.push(lines[i++]);
      blocks.push({ type: "code", lang: "", text: buf.join("\n").trim() });
      continue;
    }
    if (/^\s*[-•*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-•*]\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*[-•*]\s+/, ""));
      blocks.push({ type: "list", items });
      continue;
    }
    if (/^\s*\d+[.)]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*\d+[.)]\s+/, ""));
      blocks.push({ type: "olist", items });
      continue;
    }
    if (!line.trim()) {
      i++;
      continue;
    }
    const buf = [line];
    i++;
    while (i < lines.length && lines[i].trim() && !/^\s*(```|[-•*]\s+|\d+[.)]\s+)/.test(lines[i])) buf.push(lines[i++]);
    // блок формулы $$...$$ на отдельных строках
    blocks.push({ type: "p", text: buf.join("\n") });
  }
  return blocks;
}

export function RichText({ text, math = false, codeLanguage, className = "" }) {
  const blocks = useMemo(() => parseBlocks(text), [text]);
  return (
    <div className={`rich-text ${className}`}>
      {blocks.map((b, idx) => {
        if (b.type === "code") return <CodeBlock key={idx} code={b.text} language={b.lang || codeLanguage} />;
        if (b.type === "list")
          return (
            <ul key={idx} className="rt-list">
              {b.items.map((it, j) => (
                <li key={j}>
                  <Inline text={it} math={math} />
                </li>
              ))}
            </ul>
          );
        if (b.type === "olist")
          return (
            <ol key={idx} className="rt-olist">
              {b.items.map((it, j) => (
                <li key={j}>
                  <Inline text={it} math={math} />
                </li>
              ))}
            </ol>
          );
        return (
          <p key={idx} className="whitespace-pre-line">
            <Inline text={b.text} math={math} />
          </p>
        );
      })}
    </div>
  );
}
