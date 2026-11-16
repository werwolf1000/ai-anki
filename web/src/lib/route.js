// Состояние навигации в адресной строке: ?view=textbook&book=php&lesson=…, ?view=decks&deck=…&topic=…,
// ?view=study&deck=…&mode=…&topic=… — ссылку можно сохранить, обновить страницу или вернуться «Назад».

const KEYS = ["view", "book", "lesson", "deck", "topic", "mode", "track", "from"];

export function readRoute() {
  try {
    const p = new URLSearchParams(window.location.search);
    const r = {};
    for (const k of KEYS) {
      const v = p.get(k);
      if (v) r[k] = v;
    }
    return r;
  } catch {
    return {};
  }
}

export function routeQuery(route) {
  const p = new URLSearchParams();
  for (const k of KEYS) if (route[k] != null && route[k] !== "") p.set(k, route[k]);
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

/** Записать маршрут в адресную строку: push — новая запись истории, replace — уточнение текущей. */
export function writeRoute(route, { replace = false } = {}) {
  try {
    const url = window.location.pathname + routeQuery(route);
    if (url === window.location.pathname + window.location.search) return;
    window.history[replace ? "replaceState" : "pushState"]({ route }, "", url);
  } catch {
    /* file:// или песочница — без истории */
  }
}
