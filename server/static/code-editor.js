(() => {
  const CDN_VS = "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs";
  const LOCAL_VS = "/static/vendor/monaco";

  let editor = null;
  let initPromise = null;

  function mapLanguage(lang) {
    const l = (lang || "typescript").toLowerCase();
    const m = {
      typescript: "typescript",
      ts: "typescript",
      javascript: "javascript",
      js: "javascript",
      python: "python",
      py: "python",
      php: "php",
      html: "html",
      css: "css",
      json: "json",
      sql: "sql",
      shell: "shell",
      bash: "shell",
    };
    return m[l] || "plaintext";
  }

  function configureMonacoEnv(base) {
    window.MonacoEnvironment = {
      getWorkerUrl(_moduleId, label) {
        if (label === "json") return `${base}/language/json/jsonWorker.js`;
        if (label === "css" || label === "scss" || label === "less") {
          return `${base}/language/css/cssWorker.js`;
        }
        if (label === "html" || label === "handlebars" || label === "razor") {
          return `${base}/language/html/htmlWorker.js`;
        }
        if (label === "typescript" || label === "javascript") {
          return `${base}/language/typescript/tsWorker.js`;
        }
        return `${base}/editor/editor.worker.js`;
      },
    };
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.appendChild(s);
    });
  }

  async function resolveVsBase() {
    try {
      const r = await fetch(`${LOCAL_VS}/loader.js`, { method: "HEAD" });
      if (r.ok) return LOCAL_VS;
    } catch (_) {
      /* CDN fallback */
    }
    return CDN_VS;
  }

  async function ensureEditor() {
    if (editor) return editor;
    if (initPromise) return initPromise;

    initPromise = (async () => {
      const vsBase = await resolveVsBase();
      configureMonacoEnv(vsBase);
      await loadScript(`${vsBase}/loader.js`);
      await new Promise((resolve, reject) => {
        window.require.config({ paths: { vs: vsBase } });
        window.require(["vs/editor/editor.main"], resolve, reject);
      });

      const host = document.getElementById("code-editor-host");
      editor = monaco.editor.create(host, {
        value: "",
        language: "typescript",
        theme: "vs",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        lineNumbers: "on",
        tabSize: 2,
        insertSpaces: true,
        wordWrap: "off",
        scrollBeyondLastLine: false,
        padding: { top: 8, bottom: 8 },
        suggestOnTriggerCharacters: true,
        quickSuggestions: { other: true, comments: false, strings: false },
        tabCompletion: "on",
        wordBasedSuggestions: "matchingDocuments",
        renderLineHighlight: "all",
        scrollbar: { verticalScrollbarSize: 10, horizontalScrollbarSize: 10 },
      });

      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
        host.dispatchEvent(new CustomEvent("code-submit", { bubbles: true }));
      });

      return editor;
    })();

    return initPromise;
  }

  window.CodeEditor = {
    async show(language) {
      const host = document.getElementById("code-editor-host");
      host.classList.remove("hidden");
      await ensureEditor();
      const model = editor.getModel();
      monaco.editor.setModelLanguage(model, mapLanguage(language));
      editor.layout();
      editor.focus();
    },

    hide() {
      document.getElementById("code-editor-host").classList.add("hidden");
    },

    getValue() {
      return editor ? editor.getValue() : "";
    },

    clear() {
      if (editor) editor.setValue("");
    },

    layout() {
      if (editor) editor.layout();
    },
  };
})();
