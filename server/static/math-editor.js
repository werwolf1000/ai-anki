/* MathLive editor + KaTeX preview for LaTeX answers */
(function () {
  const wrapId = "math-editor-wrap";
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

  async function waitForMathLive() {
    if (window.MathfieldElement) return window.MathfieldElement;
    if (window.MathLive && window.MathLive.MathfieldElement) {
      return window.MathLive.MathfieldElement;
    }
    if (customElements.get("math-field")) {
      return customElements.get("math-field");
    }
    await customElements.whenDefined("math-field");
    return customElements.get("math-field");
  }

  async function ensureReady() {
    if (ready) return ready;
    ready = (async () => {
      loadCss("https://cdn.jsdelivr.net/npm/mathlive/dist/mathlive-static.css");
      loadCss("https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css");
      await loadScript("https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js");
      await loadScript("https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js");
      await loadScript("https://cdn.jsdelivr.net/npm/mathlive/dist/mathlive.min.js");
      await waitForMathLive();
    })();
    return ready;
  }

  function latexOf(el) {
    if (!el) return "";
    if (typeof el.getValue === "function") {
      try {
        return el.getValue("latex") || el.getValue() || el.value || "";
      } catch {
        return el.value || "";
      }
    }
    return el.value || "";
  }

  function setLatex(el, text) {
    if (!el) return;
    const value = text || "";
    if (typeof el.setValue === "function") {
      try {
        el.setValue(value, { format: "latex" });
        return;
      } catch {
        /* fall through */
      }
    }
    el.value = value;
  }

  function renderLatex(el, text) {
    if (!el) return;
    if (!text) {
      el.textContent = "";
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
    const wrap = document.getElementById(wrapId);
    const host = document.getElementById(hostId);
    const preview = document.getElementById(previewId);
    if (!wrap || !host) return;
    wrap.classList.remove("hidden");

    if (!field) {
      host.innerHTML = "";
      const MathfieldElement = await waitForMathLive();
      if (!MathfieldElement) {
        throw new Error("MathLive не загрузился (MathfieldElement недоступен)");
      }

      field = new MathfieldElement({
        smartFence: true,
        smartSuperscript: true,
        virtualKeyboardMode: "manual",
        fontsDirectory: "https://cdn.jsdelivr.net/npm/mathlive/dist/fonts",
      });
      field.style.width = "100%";
      field.style.fontSize = "1.1rem";
      host.appendChild(field);

      field.addEventListener("input", () => {
        renderLatex(preview, latexOf(field));
      });
      field.addEventListener("keydown", (ev) => {
        if (ev.ctrlKey && ev.key === "Enter") {
          ev.preventDefault();
          wrap.dispatchEvent(new CustomEvent("math-submit"));
        }
      });
    }

    setLatex(field, starter || "");
    renderLatex(preview, latexOf(field));
    field.focus();
  }

  function hide() {
    const wrap = document.getElementById(wrapId);
    if (wrap) wrap.classList.add("hidden");
  }

  function getValue() {
    return latexOf(field).trim();
  }

  function clear() {
    setLatex(field, "");
    renderLatex(document.getElementById(previewId), "");
  }

  async function renderQuestion(el, text) {
    await ensureReady();
    renderLatex(el, text || "");
  }

  window.MathEditor = { show, hide, getValue, clear, renderQuestion, ensureReady };
})();
