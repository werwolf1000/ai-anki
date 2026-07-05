/* MathLive editor + KaTeX preview for LaTeX answers */
(function () {
  const hostId = "math-editor-host";
  const previewId = "math-preview";
  let field = null;
  let ready = null;

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }
      const s = document.createElement("script");
      s.src = src;
      s.defer = true;
      s.onload = () => resolve();
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function loadCss(href) {
    if (document.querySelector(`link[href="${href}"]`)) return;
    const l = document.createElement("link");
    l.rel = "stylesheet";
    l.href = href;
    document.head.appendChild(l);
  }

  async function ensureReady() {
    if (ready) return ready;
    ready = (async () => {
      loadCss("https://cdn.jsdelivr.net/npm/mathlive/dist/mathlive-static.css");
      loadCss("https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css");
      await loadScript("https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js");
      await loadScript("https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js");
      await loadScript("https://cdn.jsdelivr.net/npm/mathlive/dist/mathlive.min.js");
    })();
    return ready;
  }

  function renderLatex(el, text) {
    if (!el || !text) {
      if (el) el.textContent = "";
      return;
    }
    el.textContent = text;
    if (window.renderMathInElement) {
      renderMathInElement(el, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true },
        ],
        throwOnError: false,
      });
    }
  }

  async function show(starter) {
    await ensureReady();
    const host = document.getElementById(hostId);
    const preview = document.getElementById(previewId);
    if (!host) return;
    host.classList.remove("hidden");
    if (preview) preview.classList.remove("hidden");

    if (!field) {
      host.innerHTML = "";
      field = MathLive.makeMathField(host, {
        smartFence: true,
        smartSuperscript: true,
        virtualKeyboardMode: "manual",
        fontsDirectory: "https://cdn.jsdelivr.net/npm/mathlive/dist/fonts",
      });
      field.addEventListener("input", () => {
        renderLatex(preview, field.getValue("latex"));
      });
      field.addEventListener("keydown", (ev) => {
        if (ev.ctrlKey && ev.key === "Enter") {
          ev.preventDefault();
          host.dispatchEvent(new CustomEvent("math-submit"));
        }
      });
    }

    field.setValue(starter || "", { format: "latex" });
    renderLatex(preview, field.getValue("latex"));
    field.focus();
  }

  function hide() {
    const host = document.getElementById(hostId);
    const preview = document.getElementById(previewId);
    if (host) host.classList.add("hidden");
    if (preview) preview.classList.add("hidden");
  }

  function getValue() {
    return field ? field.getValue("latex") : "";
  }

  function clear() {
    if (field) field.setValue("", { format: "latex" });
    const preview = document.getElementById(previewId);
    renderLatex(preview, "");
  }

  function renderQuestion(el, text) {
    if (!el) return;
    renderLatex(el, text);
  }

  window.MathEditor = { show, hide, getValue, clear, renderQuestion, ensureReady };
})();
