// API-клиент. В браузере сервер — тот же origin; в Electron — адрес из настроек входа.
import { isDesktop } from "./desktop";

export const DEFAULT_SERVER = "https://anki.webmastermsk.ru";
const TOKEN_KEY = "anki:token";
const SERVER_KEY = "anki:server";

function storageGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function storageSet(key, value) {
  try {
    if (value == null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    /* приватный режим */
  }
}

export function getServer() {
  if (!isDesktop) return "";
  return (storageGet(SERVER_KEY) || DEFAULT_SERVER).replace(/\/+$/, "");
}
export function setServer(url) {
  storageSet(SERVER_KEY, (url || DEFAULT_SERVER).trim().replace(/\/+$/, ""));
}

export function getToken() {
  return storageGet(TOKEN_KEY);
}
export function setToken(token) {
  storageSet(TOKEN_KEY, token);
}

/** Абсолютный URL ресурса сервера (картинки карточек и т.п.). */
export function serverUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//.test(path)) return path;
  return getServer() + path;
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

export async function api(path, { method = "GET", body, form, signal } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(getServer() + path, { method, headers, body: payload, signal });
  } catch (e) {
    if (e.name === "AbortError") throw e;
    throw new ApiError("Сервер недоступен. Проверьте подключение.", 0);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((d) => d.msg).join("; ")
      : data.detail;
    if (res.status === 401 && token) onUnauthorized();
    throw new ApiError(detail || res.statusText || "Ошибка запроса", res.status);
  }
  return data;
}

/** POST с потоковым ответом NDJSON: onEvent вызывается на каждую строку. */
export async function apiStream(path, body, onEvent, { signal } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(getServer() + path, { method: "POST", headers, body: JSON.stringify(body), signal });
  } catch (e) {
    if (e.name === "AbortError") throw e;
    throw new ApiError("Сервер недоступен. Проверьте подключение.", 0);
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 && token) onUnauthorized();
    throw new ApiError(data.detail || res.statusText, res.status);
  }
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
      if (line) onEvent(JSON.parse(line));
    }
  }
  if (buf.trim()) onEvent(JSON.parse(buf));
}
