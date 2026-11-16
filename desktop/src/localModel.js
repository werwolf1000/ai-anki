// Мост к локальной модели (Strata, LM Studio, llama.cpp — любой OpenAI-совместимый /v1 на этом компьютере).
// Сервер AI Anki не видит 127.0.0.1 вашего ПК, поэтому приложение само забирает запросы длинным опросом
// (/api/bridge/poll), отправляет их в локальную модель и потоком возвращает ответ (/api/bridge/jobs/<id>).
const fs = require("fs");
const path = require("path");

const DEFAULTS = { enabled: false, url: "http://127.0.0.1:8081/v1", apiKey: "", model: "", noThink: true };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class LocalModelBridge {
  constructor({ userDataDir, version, emit }) {
    this.file = path.join(userDataDir, "local-model.json");
    this.version = version;
    this.emit = emit; // (state) => void — в окно
    this.config = { ...DEFAULTS, ...this.read() };
    this.auth = { server: "", token: "" };
    this.loopId = 0;
    this.detected = { model: "", at: 0 };
    this.state = { status: "off", error: "", model: "", jobs: 0, current: "", lastJobAt: "", lastMs: 0 };
  }

  read() {
    try {
      return JSON.parse(fs.readFileSync(this.file, "utf-8"));
    } catch {
      return {};
    }
  }

  save() {
    try {
      fs.writeFileSync(this.file, JSON.stringify(this.config, null, 1));
    } catch {
      /* не критично */
    }
  }

  publicState() {
    const { apiKey, ...cfg } = this.config;
    return { config: { ...cfg, hasKey: !!apiKey }, state: this.state, connected: !!this.auth.token };
  }

  set(patch) {
    const next = { ...this.config, ...patch };
    if (patch.apiKey === undefined || patch.apiKey === null) next.apiKey = this.config.apiKey; // ключ не стираем пустой формой
    next.url = String(next.url || DEFAULTS.url).trim().replace(/\/+$/, "").replace(/\/chat\/completions$/, "");
    this.config = next;
    this.detected = { model: "", at: 0 };
    this.save();
    this.restart();
    return this.publicState();
  }

  setAuth({ server, token }) {
    const same = server === this.auth.server && token === this.auth.token;
    this.auth = { server: (server || "").replace(/\/+$/, ""), token: token || "" };
    if (!same) this.restart();
  }

  update(patch) {
    this.state = { ...this.state, ...patch };
    this.emit(this.publicState());
  }

  headers() {
    const h = { "Content-Type": "application/json" };
    if (this.config.apiKey) h.Authorization = `Bearer ${this.config.apiKey}`;
    return h;
  }

  /** Модель локального сервера: из настроек или загруженная (/v1/models, status loaded). */
  async model(force = false) {
    if (this.config.model) return this.config.model;
    if (!force && this.detected.model && Date.now() - this.detected.at < 60_000) return this.detected.model;
    const res = await fetch(`${this.config.url}/models`, { headers: this.headers(), signal: AbortSignal.timeout(10_000) });
    if (!res.ok) throw new Error(`${this.config.url}/models: HTTP ${res.status}`);
    const data = await res.json();
    const list = data.data || data.models || [];
    const loaded = list.find((m) => m.status === "loaded" || m.state === "loaded") || list[0];
    const id = loaded?.id || loaded?.name || "";
    if (!id) throw new Error("локальный сервер не вернул ни одной модели");
    this.detected = { model: id, at: Date.now() };
    return id;
  }

  async server(pathname, body) {
    const res = await fetch(`${this.auth.server}${pathname}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.auth.token}` },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(45_000),
    });
    if (res.status === 401) throw Object.assign(new Error("нужно войти в аккаунт"), { auth: true });
    if (!res.ok) throw new Error(`сервер: HTTP ${res.status}`);
    return res.json();
  }

  /** Потоковый запрос к локальной модели: onDelta(текст) для каждого куска content (рассуждения пропускаются). */
  async complete(messages, temperature, onDelta) {
    const model = await this.model();
    const body = { model, messages, temperature, stream: true };
    if (this.config.noThink) body.chat_template_kwargs = { enable_thinking: false };
    let res = await fetch(`${this.config.url}/chat/completions`, {
      method: "POST", headers: this.headers(), body: JSON.stringify(body), signal: AbortSignal.timeout(20 * 60_000),
    });
    if (!res.ok && this.config.noThink && res.status === 400) {
      delete body.chat_template_kwargs; // сервер не знает этот параметр — без него
      res = await fetch(`${this.config.url}/chat/completions`, {
        method: "POST", headers: this.headers(), body: JSON.stringify(body), signal: AbortSignal.timeout(20 * 60_000),
      });
    }
    if (!res.ok) throw new Error(`локальная модель: HTTP ${res.status} ${(await res.text()).slice(0, 200)}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (payload === "[DONE]") return model;
        try {
          const data = JSON.parse(payload);
          if (data.error) throw new Error(data.error.message || String(data.error));
          const piece = data.choices?.[0]?.delta?.content;
          if (piece) onDelta(piece);
        } catch (e) {
          if (e instanceof SyntaxError) continue;
          throw e;
        }
      }
    }
    return model;
  }

  async runJob(job) {
    const t0 = Date.now();
    this.update({ current: `запрос ${job.id.slice(0, 6)}`, status: "busy" });
    let pending = "";
    let lastFlush = Date.now();
    let chain = Promise.resolve();
    const flush = (extra = {}) => {
      const delta = pending;
      pending = "";
      lastFlush = Date.now();
      chain = chain.then(() => this.server(`/api/bridge/jobs/${job.id}`, { delta, ...extra }));
      return chain;
    };
    try {
      await this.complete(job.messages, job.temperature ?? 0.3, (piece) => {
        pending += piece;
        if (Date.now() - lastFlush > 300) flush();
      });
      await flush({ done: true });
      this.update({ jobs: this.state.jobs + 1, lastJobAt: new Date().toISOString(), lastMs: Date.now() - t0, error: "" });
    } catch (e) {
      await chain.catch(() => {});
      await this.server(`/api/bridge/jobs/${job.id}`, { error: String(e.message || e).slice(0, 300) }).catch(() => {});
      this.update({ error: String(e.message || e) });
    } finally {
      this.update({ current: "", status: "online" });
    }
  }

  restart() {
    this.loopId += 1;
    if (this.config.enabled && this.auth.token && this.auth.server) this.loop(this.loopId);
    else this.update({ status: this.config.enabled ? "login" : "off", current: "" });
  }

  async loop(id) {
    this.update({ status: "connecting", error: "" });
    while (id === this.loopId) {
      try {
        let model = "";
        try {
          model = await this.model();
        } catch (e) {
          this.update({ status: "nomodel", error: `локальная модель недоступна: ${e.message}`, model: "" });
          await sleep(10_000);
          continue;
        }
        if (this.state.status !== "busy") this.update({ status: "online", model, error: "" });
        const r = await this.server("/api/bridge/poll", { info: { model, url: this.config.url, app: this.version }, wait: 25 });
        if (id !== this.loopId) return;
        if (r.job) await this.runJob(r.job);
      } catch (e) {
        if (id !== this.loopId) return;
        this.update({ status: e.auth ? "login" : "error", error: String(e.message || e) });
        await sleep(e.auth ? 30_000 : 5_000);
      }
    }
  }

  /** Проверка из настроек: модель отвечает? */
  async test() {
    const t0 = Date.now();
    let text = "";
    const model = await this.complete([{ role: "user", content: "Ответь одним словом по-русски: готово" }], 0, (p) => (text += p));
    return { ok: true, model, text: text.replace(/<think>[\s\S]*?<\/think>/g, "").trim().slice(0, 200), ms: Date.now() - t0 };
  }
}

module.exports = { LocalModelBridge };
