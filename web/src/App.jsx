import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { BookOpenText, Briefcase, LayoutDashboard, Layers, LogOut, Settings as SettingsIcon } from "lucide-react";
import { api, getServer, getToken, setToken, setUnauthorizedHandler } from "./lib/api";
import { desktop, isDesktop } from "./lib/desktop";
import { readRoute, writeRoute } from "./lib/route";
import { Backdrop, Logo, Spinner, ToastProvider, useToast } from "./components/ui";
import TitleBar from "./components/TitleBar";
import AuthScreen from "./views/AuthScreen";
import Dashboard from "./views/Dashboard";
import Decks from "./views/Decks";
import Study from "./views/Study";
import Settings from "./views/Settings";
import Textbook from "./views/Textbook";
import Tracks from "./views/Tracks";
import Exam from "./views/Exam";
import Interview from "./views/Interview";
import Verify from "./views/Verify";

const NAV = [
  { id: "dashboard", label: "Обзор", icon: LayoutDashboard },
  { id: "tracks", label: "Профессии", icon: Briefcase },
  { id: "decks", label: "Колоды", icon: Layers },
  { id: "textbook", label: "Учебник", icon: BookOpenText },
  { id: "settings", label: "Настройки", icon: SettingsIcon },
];

const VERIFY = typeof window !== "undefined" ? window.location.pathname.match(/^\/verify\/([\w-]+)/) : null;

export default function App() {
  return (
    <ToastProvider>
      {VERIFY ? (
        <>
          <Backdrop />
          <Verify certId={VERIFY[1]} />
        </>
      ) : (
        <Root />
      )}
    </ToastProvider>
  );
}

function Root() {
  const [user, setUser] = useState(undefined); // undefined — проверяем токен
  const [route, setRoute] = useState(readRoute); // параметры переходов — в адресной строке
  const [study, setStudy] = useState(null); // ответ /api/session
  const [config, setConfig] = useState(null);
  const [decks, setDecks] = useState(null);
  const [exam, setExam] = useState(null); // ответ /api/tracks/{id}/exam
  const [interview, setInterview] = useState(null);
  const toast = useToast();
  const studyPushed = useRef(false);
  const restoring = useRef(false);
  const exiting = useRef(false); // вышли из занятия — ждём history.back(), сессию не восстанавливать

  const VIEWS = ["dashboard", "tracks", "decks", "textbook", "settings", "study"];
  const view = VIEWS.includes(route.view) ? (route.view === "study" ? "decks" : route.view) : "dashboard";

  /** Перейти: next — полный набор параметров нового экрана. */
  const navigate = useCallback((next, opts = {}) => {
    writeRoute(next, opts);
    setRoute(next);
  }, []);
  const setView = useCallback((id) => navigate({ view: id }), [navigate]);
  const openTrack = route.view === "tracks" ? route.track || null : null;
  const setOpenTrack = useCallback((id) => navigate({ view: "tracks", track: id || "" }), [navigate]);

  // «Назад»/«Вперёд» браузера
  useEffect(() => {
    const onPop = () => {
      exiting.current = false;
      setRoute(readRoute());
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  /** Учебник по колоде: колоды учебников открывают свой учебник (book), остальные — по deck. */
  const openTextbook = useCallback(
    (deckId, topic = "") => {
      const d = (decks || []).find((x) => x.deck_id === deckId);
      navigate(d?.book ? { view: "textbook", book: d.book, lesson: topic } : { view: "textbook", deck: deckId, lesson: topic });
    },
    [decks, navigate],
  );

  const logout = useCallback(async () => {
    try {
      await api("/api/auth/logout", { method: "POST" });
    } catch {
      /* токен мог уже истечь */
    }
    setToken(null);
    setUser(null);
    setStudy(null);
    setDecks(null);
    setConfig(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null);
      setUser(null);
    });
    if (!getToken()) {
      setUser(null);
      return;
    }
    api("/api/auth/me")
      .then((r) => setUser(r.user))
      .catch(() => setUser(null));
  }, []);

  const loadDecks = useCallback(() => api("/api/decks").then((r) => setDecks(r.decks)), []);
  const loadConfig = useCallback(() => api("/api/config").then(setConfig), []);

  // десктоп: мост к локальной модели работает от имени вошедшего пользователя
  useEffect(() => {
    if (!isDesktop || !desktop?.bridge) return;
    desktop.bridge.auth(user ? { server: getServer(), token: getToken() } : { server: "", token: "" });
  }, [user]);

  useEffect(() => {
    if (!user) return;
    loadDecks().catch(() => {});
    loadConfig().catch(() => {});
  }, [user, loadDecks, loadConfig]);

  const startStudy = useCallback(
    (session) => {
      setStudy(session);
      studyPushed.current = true;
      navigate({ view: "study", deck: session.deck_id, mode: session.mode, topic: session.topic || "", from: view });
    },
    [navigate, view],
  );
  const exitStudy = useCallback(() => {
    setStudy(null);
    loadDecks().catch(() => {});
    if (studyPushed.current) {
      studyPushed.current = false;
      exiting.current = true;
      window.history.back(); // вернуться туда, откуда начали (учебник, колоды, обзор…)
    } else {
      navigate({ view: route.from && route.from !== "study" ? route.from : "decks", deck: route.deck, topic: route.topic }, { replace: true });
    }
  }, [loadDecks, navigate, route]);
  // из карточки — в урок учебника
  const readFromStudy = useCallback(
    (deckId, topic) => {
      setStudy(null);
      studyPushed.current = false;
      loadDecks().catch(() => {});
      const d = (decks || []).find((x) => x.deck_id === deckId);
      navigate(d?.book ? { view: "textbook", book: d.book, lesson: topic } : { view: "textbook", deck: deckId, lesson: topic });
    },
    [decks, loadDecks, navigate],
  );

  // обновили страницу посреди занятия — начать сессию заново с теми же параметрами
  useEffect(() => {
    if (!user || route.view !== "study" || study || restoring.current || exiting.current || !route.deck) return;
    restoring.current = true;
    api("/api/session", { method: "POST", body: { deck_id: route.deck, mode: route.mode || "due", ...(route.topic ? { topic: route.topic } : {}) } })
      .then((s) => {
        if (s.empty) {
          toast("В этой теме сейчас нет карточек для повторения", "info");
          navigate({ view: "decks", deck: route.deck, topic: route.topic }, { replace: true });
        } else setStudy(s);
      })
      .catch((e) => {
        toast(e.message, "error");
        navigate({ view: "decks" }, { replace: true });
      })
      .finally(() => {
        restoring.current = false;
      });
  }, [user, route, study, navigate, toast]);

  // «Назад» из занятия кнопкой браузера
  useEffect(() => {
    if (study && route.view !== "study") {
      setStudy(null);
      studyPushed.current = false;
      loadDecks().catch(() => {});
    }
  }, [route.view, study, loadDecks]);

  const startExam = useCallback(
    async (track) => {
      try {
        setExam(await api(`/api/tracks/${track.id}/exam`, { method: "POST" }));
      } catch (e) {
        toast(e.message, "error");
      }
    },
    [toast],
  );
  const startInterview = useCallback(
    async (track) => {
      try {
        setInterview(await api(`/api/tracks/${track.id}/interview`, { method: "POST" }));
      } catch (e) {
        toast(e.message, "error");
      }
    },
    [toast],
  );
  const exitTrackMode = useCallback(() => {
    setExam(null);
    setInterview(null);
    navigate({ view: "tracks", track: route.track || "" });
    loadDecks().catch(() => {});
  }, [loadDecks, navigate, route.track]);

  const subtitle = study ? study.deck_name : exam ? `Экзамен · ${exam.title}` : interview ? `Собеседование · ${interview.title}` : user ? NAV.find((n) => n.id === view)?.label : "";

  return (
    <div className="flex h-full flex-col">
      <TitleBar subtitle={subtitle} />
      <Backdrop />
      <div className="relative min-h-0 flex-1">
        <>
          {user === undefined ? (
            <motion.div key="boot" className="flex h-full items-center justify-center" exit={{ opacity: 0 }}>
              <Spinner className="h-6 w-6 text-violet-300" />
            </motion.div>
          ) : !user ? (
            <motion.div key="auth" className="h-full" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <AuthScreen onAuth={setUser} />
            </motion.div>
          ) : exam ? (
            <motion.div key="exam" className="h-full" initial={{ opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }}>
              <Exam exam={exam} config={config} onExit={exitTrackMode} />
            </motion.div>
          ) : interview ? (
            <motion.div key="interview" className="h-full" initial={{ opacity: 0, scale: 0.985 }} animate={{ opacity: 1, scale: 1 }}>
              <Interview interview={interview} config={config} user={user} onExit={exitTrackMode} />
            </motion.div>
          ) : study ? (
            <motion.div
              key="study"
              className="h-full"
              initial={{ opacity: 0, scale: 0.985 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.985 }}
              transition={{ duration: 0.3 }}
            >
              <Study session={study} config={config} onExit={exitStudy} onRead={readFromStudy} />
            </motion.div>
          ) : route.view === "study" && !exiting.current ? (
            <motion.div key="restore" className="flex h-full items-center justify-center">
              <Spinner className="h-6 w-6 text-violet-300" />
            </motion.div>
          ) : (
            <motion.div key="shell" className="flex h-full" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Sidebar user={user} view={view} setView={setView} onLogout={logout} />
              <main className="min-w-0 flex-1 overflow-y-auto pb-24 md:pb-0">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={view}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                    className={`mx-auto w-full px-4 py-6 sm:px-8 sm:py-8 ${view === "textbook" ? "max-w-[1500px]" : "max-w-6xl"}`}
                  >
                    {view === "dashboard" && <Dashboard user={user} decks={decks} onStart={startStudy} onRead={openTextbook} goDecks={() => setView("decks")} />}
                    {view === "tracks" && (
                      <Tracks
                        decks={decks}
                        onStart={startStudy}
                        onRead={openTextbook}
                        onExam={startExam}
                        onInterview={startInterview}
                        openTrack={openTrack}
                        setOpenTrack={setOpenTrack}
                      />
                    )}
                    {view === "decks" && <Decks decks={decks} reload={loadDecks} onStart={startStudy} onRead={openTextbook} route={route} navigate={navigate} />}
                    {view === "textbook" && (
                      <Textbook user={user} decks={decks} reloadDecks={loadDecks} onStart={startStudy} route={route} navigate={navigate} />
                    )}
                    {view === "settings" && <Settings user={user} setUser={setUser} config={config} setConfig={setConfig} onLogout={logout} />}
                  </motion.div>
                </AnimatePresence>
              </main>
            </motion.div>
          )}
        </>
      </div>
    </div>
  );
}

function Sidebar({ user, view, setView, onLogout }) {
  const initials = (user.display_name || user.username).slice(0, 2).toUpperCase();
  return (
    <>
      {/* десктоп */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-white/[0.05] bg-ink-950/40 p-4 backdrop-blur-xl md:flex">
        {!isDesktop && (
          <div className="mb-8 flex items-center gap-3 px-2 pt-1">
            <Logo />
            <div>
              <div className="font-extrabold tracking-tight">AI Anki</div>
              <div className="text-[11px] text-zinc-500">ИИ-экзаменатор</div>
            </div>
          </div>
        )}
        <nav className={`flex flex-col gap-1 ${isDesktop ? "mt-2" : ""}`}>
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setView(n.id)}
              className={`relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${view === n.id ? "text-white" : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100"}`}
            >
              {view === n.id && (
                <motion.span
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-xl border border-violet-500/20 bg-gradient-to-r from-violet-600/25 to-rose-500/10"
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                />
              )}
              <n.icon className="relative h-[18px] w-[18px]" />
              <span className="relative">{n.label}</span>
            </button>
          ))}
        </nav>
        <div className="mt-auto flex items-center gap-3 rounded-xl border border-white/[0.05] bg-white/[0.02] p-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500/40 to-rose-500/40 text-xs font-bold">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold">{user.display_name || user.username}</div>
            <div className="truncate text-[11px] text-zinc-500">{user.is_admin ? "Администратор" : `@${user.username}`}</div>
          </div>
          <button className="btn-icon" onClick={onLogout} title="Выйти" aria-label="Выйти">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* мобильная нижняя навигация */}
      <nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-5 gap-1 rounded-2xl border border-white/[0.07] bg-ink-900/90 p-1.5 backdrop-blur-xl md:hidden">
        {NAV.map((n) => (
          <button
            key={n.id}
            onClick={() => setView(n.id)}
            className={`relative flex flex-col items-center gap-0.5 rounded-xl py-2 text-[11px] font-medium ${view === n.id ? "text-white" : "text-zinc-500"}`}
          >
            {view === n.id && <motion.span layoutId="nav-active-m" className="absolute inset-0 rounded-xl bg-white/[0.07]" />}
            <n.icon className="relative h-5 w-5" />
            <span className="relative">{n.label}</span>
          </button>
        ))}
      </nav>
    </>
  );
}
