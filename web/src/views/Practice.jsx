import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Check, CheckCheck, ChevronRight, Download, FileCode2, FilePlus2, Folder, FolderPlus, History, MessageCircle, Pencil, Play, Save, Send, Square, Terminal, Trash2, X } from "lucide-react";
import { api, getServer, getToken } from "../lib/api";
import { Spinner, useToast } from "../components/ui";

const CodeEditor = lazy(() => import("../components/CodeEditor"));
const language = (path) => ({ py: "python", php: "php", js: "javascript", json: "json", html: "html", css: "css", md: "markdown", csv: "plaintext" }[path.split(".").pop()] || "plaintext");
const running = (run) => ["queued", "running"].includes(run?.result?.status);
const equal = (a, b) => JSON.stringify(a.files) === JSON.stringify(b.files) && JSON.stringify(a.folders) === JSON.stringify(b.folders);
const statusLabel = { queued: "Ожидает запуска", running: "Выполняется", succeeded: "Выполнено", failed: "Ошибка выполнения", cancelled: "Остановлено" };

function download(name, data, type = "application/octet-stream") {
  const url = URL.createObjectURL(new Blob([data], { type }));
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function decode(data) { return Uint8Array.from(atob(data), (c) => c.charCodeAt(0)); }

export default function Practice({ route, navigate, userId, config }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api("/api/practice").then(setData).catch((e) => setError(e.message)); }, [route.project]);
  if (route.project) return <Workspace key={`${userId}:${route.project}`} id={route.project} userId={userId} config={config} onBack={() => navigate({ view: "practice", track: route.track })} />;
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <Spinner className="h-6 w-6" />;
  const projects = data.projects.filter((p) => !route.track || p.track === route.track);
  return <div className="space-y-6">
    <div><h1 className="text-3xl font-bold tracking-tight">Проектная практика</h1><p className="mt-2 max-w-2xl text-zinc-400">Создавайте работающие программы по этапам. Пишите код, запускайте проверки и разбирайте решения с наставником.</p></div>
    <div className="flex flex-wrap gap-2" role="group" aria-label="Язык проектов">
      {[["", "Все проекты"], ["python", "Python"], ["php", "PHP"]].map(([id, title]) => <button key={id} className={route.track === id || (!id && !route.track) ? "btn-primary" : "btn-ghost"} onClick={() => navigate({ view: "practice", track: id })}>{title}</button>)}
    </div>
    {!data.runner_configured && <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 p-4 text-sm text-amber-200">Среда запуска пока не подключена. Можно писать и сохранять код, общаться с наставником и скачивать проект. Для запуска администратору нужно подключить сервис практики.</div>}
    <div className="grid gap-4 lg:grid-cols-2">{projects.map((p) => {
      const progress = data.progress[p.id];
      const done = progress?.completed || 0;
      return <button key={p.id} className="group rounded-2xl border border-white/10 bg-ink-900 p-5 text-left transition-colors hover:border-violet-400/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400" onClick={() => navigate({ view: "practice", project: p.id, track: p.track })}>
        <div className="flex items-center justify-between text-xs text-zinc-400"><span>{p.track === "php" ? "PHP 8" : "Python"} · главы {p.chapters.join(", ")}</span><span>{done}/{p.steps.length} этапов</span></div>
        <h2 className="mt-3 flex items-center gap-2 text-xl font-semibold"><FileCode2 className="h-5 w-5 text-violet-300" />{p.title}</h2>
        <p className="mt-2 min-h-12 text-sm leading-relaxed text-zinc-400">{p.description}</p>
        <div className="mt-5 flex items-center justify-between"><span className="text-sm text-violet-300">{done === p.steps.length ? "Вернуться к проекту" : progress ? "Продолжить" : "Начать проект"}</span><ChevronRight className="h-4 w-4 text-zinc-500 group-hover:text-violet-300" /></div>
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/5"><div className="h-full bg-violet-400" style={{ width: `${100 * done / p.steps.length}%` }} /></div>
      </button>;
    })}</div>
  </div>;
}

function Workspace({ id, userId, config, onBack }) {
  const toast = useToast();
  const [project, setProject] = useState(null), [workspace, setWorkspace] = useState(null);
  const [files, setFiles] = useState({}), [folders, setFolders] = useState([]), [active, setActive] = useState("");
  const [step, setStep] = useState(0), [run, setRun] = useState(null), [configured, setConfigured] = useState(false);
  const [loadError, setLoadError] = useState(""), [saveState, setSaveState] = useState("Сохранено"), [saveError, setSaveError] = useState("");
  const [busy, setBusy] = useState(false), [chatBusy, setChatBusy] = useState(false), [message, setMessage] = useState("");
  const [mode, setMode] = useState("hint"), [chat, setChat] = useState([]), [patch, setPatch] = useState(null);
  const [explanation, setExplanation] = useState(""), [modal, setModal] = useState(null), [name, setName] = useState("");
  const [snapshots, setSnapshots] = useState(null), [tab, setTab] = useState("output"), [oldDraft, setOldDraft] = useState(null);
  const [pollError, setPollError] = useState("");
  const draft = useRef({ files: {}, folders: [] }), saved = useRef(null), saving = useRef(null), alive = useRef(true);
  const backupKey = `anki:practice:${userId}:${id}`;
  draft.current = { files, folders };

  const cacheDraft = useCallback((value, revision) => {
    try { localStorage.setItem(backupKey, JSON.stringify({ ...value, revision })); } catch { /* server save still works */ }
  }, [backupKey]);

  const install = useCallback((ws) => {
    saved.current = ws; draft.current = { files: ws.files, folders: ws.folders };
    setWorkspace(ws); setFiles(ws.files); setFolders(ws.folders); setChat(ws.chat);
    setActive((old) => ws.files[old] !== undefined ? old : Object.keys(ws.files)[0]);
    setSaveState("Сохранено"); setSaveError("");
  }, []);

  useEffect(() => {
    alive.current = true;
    api(`/api/practice/${id}`).then((data) => {
      if (!alive.current) return;
      setProject(data.project); install(data.workspace); setRun(data.run); setConfigured(data.runner_configured);
      setStep(Math.min(Object.keys(data.workspace.completed).length, data.project.steps.length - 1));
      try {
        const backup = JSON.parse(localStorage.getItem(backupKey));
        if (backup && !equal(backup, data.workspace)) {
          if (backup.revision === data.workspace.revision) { setFiles(backup.files); setFolders(backup.folders); toast("Восстановлен несохранённый черновик", "info"); }
          else setOldDraft(backup);
        }
      } catch { /* no draft */ }
    }).catch((e) => setLoadError(e.message));
    return () => { alive.current = false; };
  }, [id, backupKey, install, toast]);

  const save = useCallback(async function flush() {
    if (saving.current) { await saving.current; return flush(); }
    if (!saved.current || equal(draft.current, saved.current)) return saved.current;
    const snapshot = draft.current;
    const request = api(`/api/practice/${id}`, { method: "PUT", body: { ...snapshot, revision: saved.current.revision } });
    saving.current = request;
    if (alive.current) { setSaveState("Сохраняется…"); setSaveError(""); }
    try {
      const result = await request;
      saved.current = result;
      cacheDraft(draft.current, result.revision);
      if (alive.current) { setWorkspace(result); setSaveState(equal(draft.current, result) ? "Сохранено" : "Есть изменения"); }
    } catch (e) {
      if (alive.current) { setSaveState("Не сохранено"); setSaveError(e.message); }
      throw e;
    } finally { saving.current = null; }
    return flush();
  }, [id, cacheDraft]);

  useEffect(() => {
    if (!workspace || equal(draft.current, saved.current)) return;
    cacheDraft(draft.current, saved.current.revision);
    setSaveState("Есть изменения");
    const timer = setTimeout(() => save().catch(() => {}), 900);
    return () => clearTimeout(timer);
  }, [files, folders, workspace, cacheDraft, save]);

  useEffect(() => {
    const warn = (e) => { if (saved.current && !equal(draft.current, saved.current)) { e.preventDefault(); e.returnValue = ""; } };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);

  useEffect(() => {
    if (!running(run)) return;
    let stopped = false;
    const timer = setInterval(() => {
      api(`/api/practice/runs/${run.id}`).then((r) => { if (!stopped) { setRun(r); setPollError(""); } }).catch((e) => { if (!stopped) setPollError(e.message); });
    }, 1200);
    return () => { stopped = true; clearInterval(timer); };
  }, [run?.id, run?.result?.status]);

  const act = async (fn) => { setBusy(true); try { await fn(); } catch (e) { toast(e.message, "error"); } finally { setBusy(false); } };
  const start = (action) => act(async () => {
    const ws = await save();
    setRun(await api(`/api/practice/${id}/runs`, { method: "POST", body: { action, step, revision: ws.revision } }));
    setTab("output"); setPollError("");
  });
  const exportProject = () => act(async () => {
    await save();
    const response = await fetch(getServer() + `/api/practice/${id}/export`, { headers: { Authorization: `Bearer ${getToken()}` } });
    if (!response.ok) throw new Error("Не удалось скачать проект");
    download(id + ".zip", await response.blob(), "application/zip");
  });
  const talk = async (e) => {
    e.preventDefault(); if (!message.trim()) return;
    setChatBusy(true);
    try {
      const ws = await save();
      const data = await api(`/api/practice/${id}/mentor`, { method: "POST", body: { message, mode, step, revision: ws.revision } });
      setChat(data.chat); setMessage("");
    } catch (e) { toast(e.message, "error"); } finally { setChatBusy(false); }
  };
  const complete = () => act(async () => {
    await save();
    const ws = await api(`/api/practice/${id}/complete`, { method: "POST", body: { run_id: run.id, explanation } });
    install(ws); setExplanation("");
    setStep(Math.min(step + 1, project.steps.length - 1));
    toast(Object.keys(ws.completed).length === project.steps.length ? "Проект завершён. Отличная работа!" : "Этап завершён", "success");
  });

  const createPath = (e) => {
    e.preventDefault();
    const path = name.trim();
    if (!path || !/^[A-Za-z0-9_. /-]+$/.test(path) || path.split("/").some((p) => !p || [".", "..", ".git", ".checks"].includes(p))) return toast("Укажите относительный путь, например src/service.py", "error");
    if (files[path] !== undefined || folders.includes(path) || Object.keys(files).some((p) => p.startsWith(path + "/"))) return toast("Такой путь уже существует", "error");
    if (path.split("/").slice(0, -1).some((_, i, parts) => files[parts.slice(0, i + 1).join("/")] !== undefined)) return toast("Родительский путь занят файлом", "error");
    if (modal === "folder") setFolders([...folders, path]);
    else {
      const next = { ...files, [path]: modal === "rename" ? files[active] : path.endsWith(".php") ? "<?php\n" : "" };
      if (modal === "rename") delete next[active];
      setFiles(next); setActive(path);
    }
    setModal(null); setName("");
  };
  const removeFile = () => {
    if (Object.keys(files).length === 1) return toast("В проекте должен остаться хотя бы один файл", "error");
    if (!window.confirm(`Удалить ${active}? Предыдущая версия останется в истории.`)) return;
    const next = { ...files }; delete next[active]; setFiles(next); setActive(Object.keys(next)[0]);
  };
  const applyPatch = () => act(async () => {
    const ws = await save();
    if (ws.revision !== patch.revision) throw new Error("После ответа наставника проект изменился. Попросите проверить актуальный код.");
    const next = { ...draft.current.files, ...Object.fromEntries(patch.patches.map((p) => [p.path, p.content])) };
    draft.current = { ...draft.current, files: next }; setFiles(next);
    await save(); setPatch(null); toast("Предложение применено и сохранено", "success");
  });

  if (loadError) return <div role="alert"><p>{loadError}</p><button className="btn-ghost mt-3" onClick={onBack}>К проектам</button></div>;
  if (!project || !workspace) return <Spinner className="h-6 w-6" />;
  const isDirty = !equal({ files, folders }, saved.current);
  const passed = run?.result?.passed && run.step === step && run.revision === workspace.revision && !isDirty;
  const artifacts = run?.result?.artifacts || [];
  const preview = artifacts.find((a) => a.name === "preview.html");
  const previewHTML = preview ? new TextDecoder().decode(decode(preview.data)) : "";
  const previewDoc = `<!doctype html><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'; base-uri 'none'">${previewHTML}`;

  return <div className="space-y-4">
    <header className="flex flex-wrap items-center justify-between gap-3">
      <div><button className="mb-2 flex items-center gap-1 text-sm text-zinc-400 hover:text-white" onClick={() => act(async () => { await save(); onBack(); })}><ArrowLeft className="h-4 w-4" /> Все проекты</button><h1 className="text-2xl font-bold">{project.title}</h1></div>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`mr-2 text-xs ${saveError ? "text-rose-300" : "text-zinc-500"}`} aria-live="polite">{saveState}</span>
        <button className="btn-ghost" disabled={busy} onClick={() => act(save)} title="Сохранить"><Save className="h-4 w-4" /><span className="sr-only">Сохранить</span></button>
        <button className="btn-ghost" onClick={() => act(async () => { await save(); setSnapshots((await api(`/api/practice/${id}/history`)).snapshots); })}><History className="h-4 w-4" /> Версии</button>
        <button className="btn-ghost" disabled={busy} onClick={exportProject}><Download className="h-4 w-4" /> Проект</button>
      </div>
    </header>
    {saveError && <div role="alert" className="rounded-lg bg-rose-500/10 p-3 text-sm text-rose-200">{saveError} <button className="underline" onClick={() => download(id + "-draft.json", JSON.stringify(draft.current, null, 2), "application/json")}>Скачать черновик</button></div>}
    {oldDraft && <div className="rounded-lg bg-amber-400/10 p-3 text-sm text-amber-200">Найден локальный черновик другой версии. <button className="underline" onClick={() => download(id + "-draft.json", JSON.stringify(oldDraft, null, 2), "application/json")}>Скачать черновик</button><button className="ml-4 underline" onClick={() => setOldDraft(null)}>Скрыть</button></div>}
    {!configured && <p className="rounded-lg border border-amber-400/20 px-4 py-3 text-sm text-amber-200">Запуск ещё не подключён администратором. Файлы и общение с наставником доступны.</p>}
    <nav className="flex flex-wrap gap-2" aria-label="Этапы проекта">{project.steps.map((s, i) => <button key={s.title} disabled={i > Object.keys(workspace.completed).length} className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm disabled:opacity-40 ${step === i ? "border-violet-400/50 bg-violet-400/10 text-violet-200" : "border-white/10 text-zinc-400"}`} onClick={() => setStep(i)}>{workspace.completed[i] ? <Check className="h-4 w-4 text-emerald-400" /> : <span className="text-xs">{i + 1}</span>}{s.title}</button>)}</nav>
    <section className="rounded-xl border border-white/10 bg-ink-900 px-5 py-4"><h2 className="font-semibold">{project.steps[step].title}</h2><p className="mt-2 max-w-4xl text-sm leading-relaxed text-zinc-300">{project.steps[step].task}</p></section>

    <div className="grid items-start gap-3 lg:grid-cols-[190px_minmax(0,1fr)] 2xl:grid-cols-[190px_minmax(0,1fr)_350px]">
      <aside className="min-w-0 rounded-xl border border-white/10 bg-ink-900 p-3">
        <div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-semibold">Файлы</h2><div className="flex gap-2"><button title="Создать файл" aria-label="Создать файл" onClick={() => { setModal("file"); setName(""); }}><FilePlus2 className="h-4 w-4 text-zinc-400" /></button><button title="Создать папку" aria-label="Создать папку" onClick={() => { setModal("folder"); setName(""); }}><FolderPlus className="h-4 w-4 text-zinc-400" /></button></div></div>
        <FileTree files={files} folders={folders} active={active} onSelect={setActive} />
      </aside>
      <div className="min-w-0 space-y-3">
        <section className="overflow-hidden rounded-xl border border-white/10 bg-ink-900">
          <div className="flex items-center justify-between gap-2 border-b border-white/10 px-3 py-2"><span className="truncate font-mono text-xs text-zinc-300">{active}</span><div className="flex shrink-0 gap-3"><button aria-label="Переименовать файл" title="Переименовать файл" onClick={() => { setName(active); setModal("rename"); }}><Pencil className="h-3.5 w-3.5 text-zinc-400" /></button><button aria-label="Удалить файл" title="Удалить файл" onClick={removeFile}><Trash2 className="h-3.5 w-3.5 text-zinc-400" /></button></div></div>
          <Suspense fallback={<div className="p-8"><Spinner /></div>}><CodeEditor key={`${id}/${active}`} value={files[active] || ""} onChange={(content) => setFiles((current) => ({ ...current, [active]: content }))} language={language(active)} theme={config?.code_editor_theme || "dark"} onSubmit={() => start("test")} height={440} /></Suspense>
        </section>
        <section className="overflow-hidden rounded-xl border border-white/10 bg-ink-900">
          <div className="flex flex-wrap items-center gap-2 border-b border-white/10 p-3">
            <button className="btn-primary" disabled={!configured || busy || running(run)} onClick={() => start("run")}><Play className="h-4 w-4" /> Запустить</button>
            <button className="btn-ghost" disabled={!configured || busy || running(run)} onClick={() => start("test")}><CheckCheck className="h-4 w-4" /> Проверить этап</button>
            {running(run) && <button className="btn-ghost" onClick={() => act(async () => setRun(await api(`/api/practice/runs/${run.id}`, { method: "DELETE" })))}><Square className="h-4 w-4" /> Стоп</button>}
            {run && <span className="ml-auto text-xs text-zinc-400" aria-live="polite">{statusLabel[run.result.status]} · версия {run.revision}</span>}
          </div>
          <div className="flex gap-4 border-b border-white/5 px-4 py-2 text-xs"><button className={tab === "output" ? "text-violet-300" : "text-zinc-400"} onClick={() => setTab("output")}>Вывод</button><button disabled={!preview} className={`disabled:opacity-30 ${tab === "preview" ? "text-violet-300" : "text-zinc-400"}`} onClick={() => setTab("preview")}>Предпросмотр</button></div>
          {tab === "preview" && preview ? <><p className="px-4 py-2 text-xs text-zinc-500">HTML-ответ последнего запуска. Формы и скрипты отключены.</p><iframe title="Предпросмотр проекта" sandbox="" srcDoc={previewDoc} className="h-80 w-full bg-white" /></> : <pre className="min-h-32 max-h-80 overflow-auto whitespace-pre-wrap break-words p-4 font-mono text-xs leading-relaxed text-zinc-300">{run?.result?.output || "Запустите программу или проверьте текущий этап. Результат появится здесь."}</pre>}
          {pollError && <p role="alert" className="px-4 pb-3 text-xs text-amber-300">{pollError}</p>}
          {run && (run.revision !== workspace.revision || isDirty) && <p className="px-4 pb-3 text-xs text-amber-300">Код изменён после этого запуска. Для завершения этапа проверьте текущую версию.</p>}
          {artifacts.length > 0 && <div className="flex flex-wrap gap-2 border-t border-white/5 p-3">{artifacts.map((a) => <button className="chip text-xs" key={a.name} onClick={() => download(a.name, decode(a.data))}><Download className="mr-1 inline h-3 w-3" />{a.name}</button>)}</div>}
        </section>
        {passed && !workspace.completed[step] && <section className="rounded-xl border border-emerald-400/20 bg-emerald-400/5 p-4"><h3 className="text-sm font-semibold text-emerald-300">Проверки пройдены</h3><label className="mt-2 block text-sm text-zinc-300" htmlFor="project-explanation">Объясните, как работает ваше решение и какой случай было сложнее обработать.</label><textarea id="project-explanation" className="input mt-2 min-h-24 w-full" value={explanation} onChange={(e) => setExplanation(e.target.value)} /><button disabled={busy || explanation.trim().length < 30} className="btn-primary mt-3" onClick={complete}>Завершить этап</button></section>}
        {Object.keys(workspace.completed).length === project.steps.length && <p className="flex items-center gap-2 text-sm text-emerald-300"><CheckCheck className="h-5 w-5" /> Все этапы пройдены. Проект можно скачать и продолжить самостоятельно.</p>}
      </div>
      <aside className="min-w-0 rounded-xl border border-white/10 bg-ink-900 lg:col-span-2 2xl:col-span-1">
        <div className="border-b border-white/10 p-4"><h2 className="flex items-center gap-2 font-semibold"><MessageCircle className="h-4 w-4 text-violet-300" /> AI-наставник</h2><p className="mt-1 text-xs leading-relaxed text-zinc-500">Помогает разобраться с текущим этапом, вашим кодом и результатами проверок.</p></div>
        <div className="max-h-[560px] min-h-40 space-y-4 overflow-y-auto p-4" aria-live="polite">
          {!chat.length && <p className="text-sm leading-relaxed text-zinc-400">Начните писать решение или спросите, с чего начать. Наставник предложит направление; готовое решение можно запросить отдельно.</p>}
          {chat.map((m, i) => <div key={i} className={m.role === "user" ? "ml-4 rounded-lg bg-white/5 p-3" : "border-l-2 border-violet-400/40 pl-3"}><p className="mb-1 text-xs text-zinc-500">{m.role === "user" ? "Вы" : "Наставник"}</p><p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-zinc-300">{m.message}</p>{m.patches?.length > 0 && <button className="btn-ghost mt-2 text-xs" onClick={() => setPatch(m)}>Посмотреть изменения ({m.patches.length})</button>}</div>)}
          {chatBusy && <div className="flex items-center gap-2 text-sm text-violet-300"><Spinner /> Наставник разбирает проект…</div>}
        </div>
        <form onSubmit={talk} className="space-y-3 border-t border-white/10 p-4"><label className="block text-xs text-zinc-400">Как помочь<select aria-label="Режим наставника" className="input mt-1 w-full" value={mode} onChange={(e) => setMode(e.target.value)}><option value="hint">Подсказать направление</option><option value="explain">Объяснить подход</option><option value="review">Разобрать мой код</option><option value="solution">Показать решение</option></select></label><textarea aria-label="Сообщение наставнику" placeholder="Что не получается или непонятно?" className="input min-h-24 w-full" maxLength={4000} value={message} onChange={(e) => setMessage(e.target.value)} /><button className="btn-primary w-full" disabled={chatBusy || !message.trim()}><Send className="h-4 w-4" /> Отправить</button></form>
      </aside>
    </div>

    {modal && <Modal title={modal === "folder" ? "Новая папка" : modal === "rename" ? "Переименовать файл" : "Новый файл"} onClose={() => setModal(null)}><form onSubmit={createPath}><label className="text-sm text-zinc-300">Путь внутри проекта<input autoFocus className="input mt-2 w-full" value={name} onChange={(e) => setName(e.target.value)} placeholder={modal === "folder" ? "src/services" : project.track === "php" ? "src/Service.php" : "src/service.py"} /></label><button className="btn-primary mt-4" type="submit">{modal === "rename" ? "Переименовать" : "Создать"}</button></form></Modal>}
    {snapshots && <Modal title="Предыдущие версии" onClose={() => setSnapshots(null)}>{!snapshots.length ? <p className="text-sm text-zinc-400">Версии появятся после сохранения изменений.</p> : <div className="space-y-2">{snapshots.map((s) => <button key={s.id} disabled={busy} className="flex w-full justify-between rounded-lg border border-white/10 p-3 text-sm hover:bg-white/5" onClick={() => act(async () => { if (!window.confirm(`Восстановить версию ${s.revision}? Текущая версия сохранится в истории.`)) return; const ws = await save(); install(await api(`/api/practice/${id}/restore`, { method: "POST", body: { snapshot: s.id, revision: ws.revision } })); setSnapshots(null); })}><span>Версия {s.revision}</span><span className="text-zinc-500">{new Date(s.created).toLocaleString()}</span></button>)}</div>}</Modal>}
    {patch && <Modal title="Предложение наставника" onClose={() => setPatch(null)} wide><p className="mb-4 text-sm text-zinc-400">Просмотрите изменения перед применением. Предыдущая версия останется в истории.</p>{patch.patches.map((p) => <div key={p.path} className="mb-4"><h3 className="mb-2 font-mono text-sm">{p.path}</h3><div className="grid gap-2 md:grid-cols-2"><div><p className="text-xs text-zinc-500">Сейчас</p><pre className="max-h-64 overflow-auto rounded-lg bg-black/30 p-3 text-xs">{files[p.path] ?? "Новый файл"}</pre></div><div><p className="text-xs text-zinc-500">Предлагается</p><pre className="max-h-64 overflow-auto rounded-lg bg-emerald-400/5 p-3 text-xs">{p.content}</pre></div></div></div>)}<button disabled={busy || isDirty || patch.revision !== workspace.revision} className="btn-primary" onClick={applyPatch}>Применить изменения</button>{(isDirty || patch.revision !== workspace.revision) && <p className="mt-2 text-sm text-amber-300">Проект изменился. Попросите наставника обновить предложение.</p>}</Modal>}
  </div>;
}

function FileTree({ files, folders, active, onSelect }) {
  const root = Object.create(null);
  for (const path of [...folders.map((f) => f + "/"), ...Object.keys(files)]) {
    let node = root;
    const parts = path.split("/").filter(Boolean);
    parts.forEach((name, i) => { node[name] ||= { path: parts.slice(0, i + 1).join("/"), children: Object.create(null), file: false }; if (i === parts.length - 1 && files[path] !== undefined) node[name].file = true; node = node[name].children; });
  }
  const render = (nodes) => Object.entries(nodes).sort((a, b) => Number(a[1].file) - Number(b[1].file) || a[0].localeCompare(b[0])).map(([name, n]) => n.file ? <button key={n.path} title={n.path} className={`my-0.5 flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs ${active === n.path ? "bg-violet-400/15 text-violet-200" : "text-zinc-400 hover:bg-white/5"}`} onClick={() => onSelect(n.path)}><FileCode2 className="h-3.5 w-3.5 shrink-0" /><span className="truncate">{name}</span></button> : <details open key={n.path}><summary className="cursor-pointer py-1.5 text-xs text-zinc-400"><Folder className="mr-1 inline h-3.5 w-3.5" />{name}</summary><div className="ml-2 border-l border-white/5 pl-1">{render(n.children)}</div></details>);
  return <div>{render(root)}</div>;
}

function Modal({ title, onClose, children, wide = false }) {
  const ref = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    ref.current?.focus();
    const key = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const items = [...ref.current.querySelectorAll('button:not(:disabled), input, textarea, select, [tabindex="0"]')];
        const first = items[0], last = items[items.length - 1];
        if (e.shiftKey && (document.activeElement === first || document.activeElement === ref.current)) { e.preventDefault(); last?.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener("keydown", key);
    return () => { document.removeEventListener("keydown", key); previous?.focus(); };
  }, []);
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onMouseDown={(e) => e.target === e.currentTarget && onClose()}><section ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} className={`max-h-[85vh] w-full overflow-auto rounded-2xl border border-white/10 bg-ink-850 p-6 ${wide ? "max-w-5xl" : "max-w-lg"}`}><div className="mb-4 flex justify-between gap-4"><h2 className="text-lg font-semibold">{title}</h2><button aria-label="Закрыть" onClick={onClose}><X className="h-5 w-5" /></button></div>{children}</section></div>;
}
