// AI Anki Desktop — frameless-окно Electron поверх того же React-интерфейса, что и веб.
// Данные (аккаунт, прогресс, настройки) хранятся на сервере и синхронизируются через API.
const { app, BrowserWindow, ipcMain, net, protocol, session, shell } = require("electron");
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { LocalModelBridge } = require("./localModel");

const RENDERER_DIR = path.join(__dirname, "..", "renderer");
const devUrl = process.argv.find((a) => a.startsWith("--dev-url="))?.slice("--dev-url=".length);

// app:// — стандартная безопасная схема: работают fetch, module workers (Monaco) и localStorage
protocol.registerSchemesAsPrivileged([
  { scheme: "app", privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } },
]);

if (!app.requestSingleInstanceLock()) {
  app.quit();
}

/** @type {BrowserWindow | null} */
let win = null;

// ── размеры окна между запусками ───────────────────────────────────
const stateFile = () => path.join(app.getPath("userData"), "window-state.json");
function loadState() {
  try {
    return JSON.parse(fs.readFileSync(stateFile(), "utf-8"));
  } catch {
    return { width: 1320, height: 860 };
  }
}
function saveState() {
  if (!win || win.isDestroyed()) return;
  const b = win.getNormalBounds();
  try {
    fs.writeFileSync(stateFile(), JSON.stringify({ ...b, maximized: win.isMaximized() }));
  } catch {
    /* не критично */
  }
}

function registerAppProtocol() {
  protocol.handle("app", (request) => {
    const url = new URL(request.url);
    let rel = decodeURIComponent(url.pathname).replace(/^\/+/, "") || "index.html";
    let file = path.normalize(path.join(RENDERER_DIR, rel));
    if (!file.startsWith(RENDERER_DIR) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      file = path.join(RENDERER_DIR, "index.html");
    }
    return net.fetch(pathToFileURL(file).toString());
  });
}

function createWindow() {
  const st = loadState();
  win = new BrowserWindow({
    width: st.width,
    height: st.height,
    x: st.x,
    y: st.y,
    minWidth: 900,
    minHeight: 620,
    frame: false,
    backgroundColor: "#07070d",
    show: false,
    title: "AI Anki",
    icon: path.join(__dirname, "..", "assets", process.platform === "win32" ? "icon.ico" : "icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      spellcheck: false,
      backgroundThrottling: false, // таймер экзамена и анимации не замирают в фоне
    },
  });
  if (st.maximized) win.maximize();

  win.once("ready-to-show", () => win.show());
  win.on("maximize", () => win.webContents.send("win:maximized", true));
  win.on("unmaximize", () => win.webContents.send("win:maximized", false));
  win.on("close", saveState);

  // внешние ссылки — в системный браузер
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("app://") && !(devUrl && url.startsWith(devUrl))) {
      e.preventDefault();
      if (/^https?:/.test(url)) shell.openExternal(url);
    }
  });

  win.loadURL(devUrl || "app://anki/index.html");
}

app.on("second-instance", () => {
  if (!win) return;
  if (win.isMinimized()) win.restore();
  win.focus();
});

/** @type {LocalModelBridge | null} */
let bridge = null;

app.whenReady().then(() => {
  registerAppProtocol();
  bridge = new LocalModelBridge({
    userDataDir: app.getPath("userData"),
    version: app.getVersion(),
    emit: (st) => win && !win.isDestroyed() && win.webContents.send("bridge:state", st),
  });
  // микрофон для голосовых ответов
  session.defaultSession.setPermissionRequestHandler((_wc, permission, cb) => {
    cb(["media", "clipboard-read", "clipboard-sanitized-write"].includes(permission));
  });
  session.defaultSession.setPermissionCheckHandler((_wc, permission) => ["media", "clipboard-read"].includes(permission));
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// ── управление окном из renderer ───────────────────────────────────
ipcMain.on("win:minimize", () => win?.minimize());
ipcMain.on("win:toggle-maximize", () => {
  if (!win) return;
  if (win.isMaximized()) win.unmaximize();
  else win.maximize();
});
ipcMain.on("win:close", () => win?.close());
ipcMain.handle("win:is-maximized", () => !!win?.isMaximized());
ipcMain.handle("app:version", () => app.getVersion());

// ── локальная модель (мост сервер ⇄ модель на этом компьютере) ──────
ipcMain.handle("bridge:get", () => bridge?.publicState());
ipcMain.handle("bridge:set", (_e, patch) => bridge?.set(patch || {}));
ipcMain.handle("bridge:auth", (_e, auth) => bridge?.setAuth(auth || {}));
ipcMain.handle("bridge:test", async () => {
  try {
    return await bridge.test();
  } catch (e) {
    return { ok: false, error: String(e.message || e) };
  }
});
