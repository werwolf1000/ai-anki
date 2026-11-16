"""База знаний (RAG) для интерактивного учебника.

Источники — официальная документация (см. server/kb_sources.py): PHP Manual (рус.),
MDN JavaScript (рус.), Python, Node.js, TypeScript, Angular, Laravel, Go.
Страницы разбираются в Markdown, режутся на фрагменты, индексируются в SQLite:
  - FTS5 (BM25) — точные термины: array_map, readonly, match…
  - векторы Ollama (qwen3-embedding, 1024 измерения) — смысловой поиск по-русски.
Результаты объединяются через Reciprocal Rank Fusion.

Статьи учебника генерирует Ollama по фрагментам документации и карточкам темы;
готовые статьи кешируются в той же базе (общие для всех пользователей).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import numpy as np
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from app.ollama_client import normalize_ollama_url

EMBED_DIM = 1024
EMBED_BATCH = 32
CHUNK_CHARS = 1400
USER_AGENT = "ai-anki-knowledge/2.0 (+https://anki.webmastermsk.ru)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── источники ───────────────────────────────────────────────────────


PHP_BOOKS = [
    "array", "strings", "json", "pdo", "datetime", "mbstring", "pcre", "filesystem", "spl", "var",
    "funchand", "classobj", "errorfunc", "math", "ctype", "password", "session", "url", "outcontrol",
    "reflection", "info", "random", "filter",
]
PHP_PREFIXES = ("language.", "control-structures.", "functions.", "features.", "langref", "oop5", "types.", "reserved.")
PHP_MIGRATIONS = re.compile(r"^migration(7\d|8\d)(\.|$)")

# ── HTML → Markdown ─────────────────────────────────────────────────

_BLOCK = {
    "p", "div", "ul", "ol", "table", "tr", "dl", "dt", "dd", "blockquote", "section", "tbody", "thead",
}
_SKIP_CLASSES = {"headerlink", "navbar", "manualnavbar", "change-language", "edit-bug", "navbar__inner", "up", "contribute"}


def _render(node, out: list[str], lang: str | None = None) -> None:
    if isinstance(node, NavigableString):
        out.append(str(node))
        return
    if not isinstance(node, Tag):
        return
    name = node.name
    classes = set(node.get("class") or [])
    if name in ("script", "style", "button", "svg", "nav", "form") or classes & _SKIP_CLASSES:
        return
    if name == "pre":
        code = node.get_text().strip("\n")
        fence = ("php" if "<?php" in code or "$" in code else "") if lang is None else lang
        out.append(f"\n\n```{fence}\n{code.rstrip()}\n```\n\n")
        return
    if name in ("h1", "h2", "h3", "h4", "h5"):
        level = min(4, max(2, int(name[1])))  # h1 страницы → ##, разделы → ###
        text = " ".join(node.get_text(" ").split())
        if text:
            out.append(f"\n\n{'#' * level} {text}\n\n")
        return
    if name == "br":
        out.append("\n")
        return
    if name == "li":
        out.append("\n\n- ")
        for c in node.children:
            _render(c, out, lang)
        out.append("\n\n")
        return
    if name in ("td", "th"):
        for c in node.children:
            _render(c, out, lang)
        out.append(" | ")
        return
    if name == "code" or "function" in classes or "methodname" in classes:
        text = " ".join(node.get_text(" ").split())
        if text:
            out.append(f"`{text}`")
        return
    block = name in _BLOCK
    if block:
        out.append("\n\n")
    for c in node.children:
        _render(c, out, lang)
    if block:
        out.append("\n\n")


def _tidy(md: str) -> str:
    parts = re.split(r"(```[\s\S]*?```)", md)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append("\n\n" + part.strip() + "\n\n")
            continue
        part = re.sub(r"[ \t\r\f\v]+", " ", part)
        paras = []
        for para in re.split(r"\n\s*\n", part):
            lines = [ln.strip() for ln in para.split("\n") if ln.strip()]
            if not lines:
                continue
            text = " ".join(lines)
            text = re.sub(r"\s+([,.;:!?)])", r"\1", text)
            text = re.sub(r"`\s*`", "", text)
            if text.strip(" |"):
                paras.append(text.strip())
        out.append("\n\n".join(paras))
    md = "\n\n".join(p.strip() for p in out if p.strip())
    return re.sub(r"\n{3,}", "\n\n", md).strip()


@dataclass
class Page:
    name: str
    title: str
    url: str
    markdown: str


def parse_php_page(name: str, html: str, base_url: str) -> Page | None:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find(id="layout-content") or soup.body
    if root is None:
        return None
    h1 = root.find(["h1", "h2"])
    purpose = root.find(class_="refpurpose")
    title = (soup.title.get_text(strip=True) if soup.title else name)
    if h1 is not None:
        head = " ".join(h1.get_text(" ").split())
        if purpose is not None:
            p = " ".join(purpose.get_text(" ").split())
            title = p if p.startswith(head) else f"{head} — {title}"
        else:
            title = head
    out: list[str] = []
    _render(root, out)
    md = _tidy("".join(out))
    if len(md) < 80:
        return None
    url = base_url + name.replace(".html", ".php")
    return Page(name=name, title=title, url=url, markdown=md)


@dataclass
class Chunk:
    page: str
    url: str
    title: str
    section: str
    text: str
    ord: int

    @property
    def embed_text(self) -> str:
        head = self.title if not self.section or self.section == self.title else f"{self.title} › {self.section}"
        return f"{head}\n\n{self.text}"

    @property
    def hash(self) -> str:
        return hashlib.sha1(self.embed_text.encode("utf-8")).hexdigest()


def chunk_page(page: Page, limit: int = CHUNK_CHARS) -> list[Chunk]:
    blocks = _split_blocks(page.markdown)
    chunks: list[Chunk] = []
    section = page.title
    buf: list[str] = []
    size = 0

    def flush() -> None:
        nonlocal buf, size
        text = "\n\n".join(buf).strip()
        if len(text) >= 60:
            chunks.append(Chunk(page.name, page.url, page.title, section, text, len(chunks)))
        buf, size = [], 0

    for block in blocks:
        heading = re.match(r"^#{2,4} (.+)$", block)
        if heading:
            if size > limit * 0.4:
                flush()
            section = heading.group(1).strip()
            buf.append(block)
            size += len(block)
            continue
        if len(block) > limit * 2:  # длинный пример кода — отдельным фрагментом, с обрезкой
            flush()
            buf.append(block[: limit * 2] + ("\n```" if block.startswith("```") else ""))
            size = limit
            flush()
            continue
        if size + len(block) > limit and buf:
            flush()
        buf.append(block)
        size += len(block)
    flush()
    return chunks


def _split_blocks(md: str) -> list[str]:
    blocks: list[str] = []
    for i, part in enumerate(re.split(r"(```[\s\S]*?```)", md)):
        if i % 2 == 1:
            blocks.append(part.strip())
        else:
            blocks.extend(b.strip() for b in part.split("\n\n") if b.strip())
    return blocks


def select_php_pages(files: dict[str, str]) -> list[str]:
    """Отобрать страницы мануала, относящиеся к колодам.

    Берём справочник языка, миграции PHP 7/8 и из каждой книги-расширения — только
    функции и классы из её оглавления (плюс методы этих классов). По ссылкам
    «Смотрите также» не ходим, чтобы не утечь в посторонние расширения.
    """
    chosen: set[str] = set()
    for name in files:
        if name.startswith(PHP_PREFIXES) or PHP_MIGRATIONS.match(name):
            chosen.add(name)
    link_re = re.compile(r'href="([a-z0-9_.\-]+\.html)(?:#[^"]*)?"', re.I)
    classes: set[str] = set()
    for book in PHP_BOOKS:
        seed = f"book.{book}.html"
        if seed not in files:
            continue
        queue = deque([(seed, 0)])
        seen = {seed}
        while queue:
            name, depth = queue.popleft()
            chosen.add(name)
            html = files[name]
            body = html[html.find('id="layout-content"') :]  # без навигации «назад/вперёд/вверх»
            for target in link_re.findall(body):
                if target in seen or target not in files:
                    continue
                seen.add(target)
                if target.startswith("function."):
                    chosen.add(target)
                elif target.startswith("class."):
                    chosen.add(target)
                    classes.add(target[len("class.") : -len(".html")])
                elif depth < 2 and not target.startswith(("book.", "refs.", "index", "funcref", "extensions", "install", "langref", "language.", "about.")):
                    queue.append((target, depth + 1))
    prefixes = tuple(f"{c}." for c in classes)
    chosen.update(n for n in files if n.startswith(prefixes))
    return sorted(chosen)


# ── хранилище ───────────────────────────────────────────────────────


class KnowledgeStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._matrix: dict[str, tuple[int, np.ndarray, np.ndarray]] = {}
        self._version = 0
        with self._lock, self._db:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY, pages INTEGER, chunks INTEGER, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL, page TEXT NOT NULL, url TEXT NOT NULL,
                    title TEXT NOT NULL, section TEXT NOT NULL, text TEXT NOT NULL,
                    ord INTEGER NOT NULL, hash TEXT NOT NULL, emb BLOB
                );
                CREATE INDEX IF NOT EXISTS chunks_source ON chunks(source);
                CREATE INDEX IF NOT EXISTS chunks_hash ON chunks(hash);
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    title, section, text, content='chunks', content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );
                CREATE TABLE IF NOT EXISTS articles (
                    deck_id TEXT NOT NULL, topic TEXT NOT NULL,
                    content TEXT NOT NULL, sources TEXT NOT NULL,
                    model TEXT NOT NULL, created_at TEXT NOT NULL,
                    PRIMARY KEY (deck_id, topic)
                );
                """
            )

    # — запись —

    def replace_source(self, source_id: str, pages: int, chunks: list[Chunk]) -> int:
        """Заменить фрагменты источника; эмбеддинги неизменённых фрагментов сохраняются."""
        with self._lock, self._db:
            old = {
                r["hash"]: r["emb"]
                for r in self._db.execute("SELECT hash, emb FROM chunks WHERE source = ? AND emb IS NOT NULL", (source_id,))
            }
            ids = [r[0] for r in self._db.execute("SELECT id FROM chunks WHERE source = ?", (source_id,))]
            for i in range(0, len(ids), 500):
                part = ids[i : i + 500]
                q = ",".join("?" * len(part))
                self._db.execute(
                    f"INSERT INTO chunks_fts(chunks_fts, rowid, title, section, text) "
                    f"SELECT 'delete', id, title, section, text FROM chunks WHERE id IN ({q})",
                    part,
                )
            self._db.execute("DELETE FROM chunks WHERE source = ?", (source_id,))
            reused = 0
            for c in chunks:
                h = c.hash
                emb = old.get(h)
                reused += emb is not None
                cur = self._db.execute(
                    "INSERT INTO chunks (source, page, url, title, section, text, ord, hash, emb)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (source_id, c.page, c.url, c.title, c.section, c.text, c.ord, h, emb),
                )
                self._db.execute(
                    "INSERT INTO chunks_fts(rowid, title, section, text) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, c.title, c.section, c.text),
                )
            self._db.execute(
                "INSERT INTO sources (id, pages, chunks, updated_at) VALUES (?, ?, ?, ?)"
                " ON CONFLICT(id) DO UPDATE SET pages=excluded.pages, chunks=excluded.chunks, updated_at=excluded.updated_at",
                (source_id, pages, len(chunks), _now()),
            )
            self._version += 1
            return reused

    def delete_source(self, source_id: str) -> None:
        self.replace_source(source_id, 0, [])
        with self._lock, self._db:
            self._db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            self._version += 1

    def missing_embeddings(self, source_id: str, limit: int) -> list[tuple[int, str]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT id, title, section, text FROM chunks WHERE source = ? AND emb IS NULL ORDER BY id LIMIT ?",
                (source_id, limit),
            ).fetchall()
        out = []
        for r in rows:
            c = Chunk(page="", url="", title=r["title"], section=r["section"], text=r["text"], ord=0)
            out.append((int(r["id"]), c.embed_text))
        return out

    def save_embeddings(self, items: list[tuple[int, np.ndarray]]) -> None:
        with self._lock, self._db:
            self._db.executemany(
                "UPDATE chunks SET emb = ? WHERE id = ?",
                [(v.astype(np.float32).tobytes(), cid) for cid, v in items],
            )
            self._version += 1

    # — чтение —

    def stats(self) -> dict[str, dict]:
        with self._lock:
            rows = self._db.execute(
                """SELECT s.id, s.pages, s.chunks, s.updated_at,
                          (SELECT COUNT(*) FROM chunks c WHERE c.source = s.id AND c.emb IS NOT NULL) AS embedded
                   FROM sources s"""
            ).fetchall()
        return {r["id"]: dict(r) for r in rows}

    def _vectors(self, source_id: str) -> tuple[np.ndarray, np.ndarray] | None:
        cached = self._matrix.get(source_id)
        if cached and cached[0] == self._version:
            return cached[1], cached[2]
        with self._lock:
            rows = self._db.execute(
                "SELECT id, emb FROM chunks WHERE source = ? AND emb IS NOT NULL", (source_id,)
            ).fetchall()
        if not rows:
            return None
        ids = np.array([r["id"] for r in rows], dtype=np.int64)
        mat = np.frombuffer(b"".join(r["emb"] for r in rows), dtype=np.float32).reshape(len(rows), -1)
        self._matrix[source_id] = (self._version, ids, mat)
        return ids, mat

    def fts_search(self, query: str, sources: list[str], limit: int = 40) -> list[int]:
        terms = [t for t in re.findall(r"[\w$]+", query.lower()) if len(t) >= 3][:24]
        if not terms or not sources:
            return []
        match = " OR ".join(f'"{t}"' for t in dict.fromkeys(terms))
        q = ",".join("?" * len(sources))
        with self._lock:
            try:
                rows = self._db.execute(
                    f"""SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id = f.rowid
                        WHERE chunks_fts MATCH ? AND c.source IN ({q})
                        ORDER BY bm25(chunks_fts, 4.0, 2.0, 1.0) LIMIT ?""",
                    (match, *sources, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
        return [int(r[0]) for r in rows]

    def vector_search(self, qvec: np.ndarray, sources: list[str], limit: int = 40) -> list[int]:
        return [cid for _, cid in self.vector_scores(qvec, sources, limit)]

    def vector_scores(self, qvec: np.ndarray, sources: list[str], limit: int = 40) -> list[tuple[float, int]]:
        """Косинусная близость (векторы нормированы) — (сходство, id) по убыванию."""
        scored: list[tuple[float, int]] = []
        for sid in sources:
            loaded = self._vectors(sid)
            if loaded is None:
                continue
            ids, mat = loaded
            if mat.shape[1] != qvec.shape[0]:
                continue
            sims = mat @ qvec
            top = np.argsort(-sims)[:limit]
            scored.extend((float(sims[i]), int(ids[i])) for i in top)
        scored.sort(reverse=True)
        return scored[:limit]

    def source_chunks(self, source_id: str) -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT id, source, page, url, title, section, text FROM chunks WHERE source = ? ORDER BY ord", (source_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_chunks(self, ids: list[int]) -> list[dict]:
        if not ids:
            return []
        q = ",".join("?" * len(ids))
        with self._lock:
            rows = self._db.execute(
                f"SELECT id, source, page, url, title, section, text FROM chunks WHERE id IN ({q})", ids
            ).fetchall()
        by_id = {r["id"]: dict(r) for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    # — статьи —

    def get_article(self, deck_id: str, topic: str) -> dict | None:
        with self._lock:
            r = self._db.execute(
                "SELECT * FROM articles WHERE deck_id = ? AND topic = ?", (deck_id, topic)
            ).fetchone()
        if r is None:
            return None
        d = dict(r)
        d["sources"] = json.loads(d["sources"])
        return d

    def save_article(self, deck_id: str, topic: str, content: str, sources: list[dict], model: str) -> None:
        with self._lock, self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO articles (deck_id, topic, content, sources, model, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (deck_id, topic, content, json.dumps(sources, ensure_ascii=False), model, _now()),
            )

    def articles_for_deck(self, deck_id: str) -> set[str]:
        with self._lock:
            return {r[0] for r in self._db.execute("SELECT topic FROM articles WHERE deck_id = ?", (deck_id,))}


# ── Ollama: эмбеддинги и потоковая генерация ────────────────────────


class OllamaRag:
    def __init__(self, url: str, api_key: str = "", timeout: int = 300) -> None:
        self.url = normalize_ollama_url(url)
        self.headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
        if api_key.strip():
            self.headers["Authorization"] = f"Bearer {api_key.strip()}"
        self.timeout = timeout

    def embed(self, model: str, texts: list[str]) -> np.ndarray:
        r = requests.post(
            f"{self.url}/api/embed",
            json={"model": model, "input": texts, "dimensions": EMBED_DIM, "truncate": True},
            headers=self.headers,
            timeout=self.timeout,
        )
        r.raise_for_status()
        vecs = np.array(r.json()["embeddings"], dtype=np.float32)
        if vecs.shape[1] > EMBED_DIM:  # MRL: усечь и перенормировать
            vecs = vecs[:, :EMBED_DIM]
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.maximum(norms, 1e-9)

    def stream_chat(self, model: str, messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
        with requests.post(
            f"{self.url}/api/chat",
            json={"model": model, "messages": messages, "stream": True, "options": {"temperature": temperature, "num_ctx": 16384}},
            headers=self.headers,
            timeout=self.timeout,
            stream=True,
        ) as r:
            if r.status_code == 401:
                raise PermissionError("401 — нужен API-ключ Ollama")
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise RuntimeError(data["error"])
                piece = data.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if data.get("done"):
                    break


class ThinkFilter:
    """Вырезает блоки <think>…</think> из потока (для «думающих» моделей)."""

    def __init__(self) -> None:
        self.buf = ""
        self.inside = False

    def feed(self, piece: str) -> str:
        self.buf += piece
        out = ""
        while self.buf:
            if self.inside:
                end = self.buf.find("</think>")
                if end < 0:
                    self.buf = self.buf[-8:]
                    return out
                self.buf = self.buf[end + 8 :]
                self.inside = False
            else:
                start = self.buf.find("<think>")
                if start < 0:
                    keep = 7 if "<" in self.buf[-7:] else 0
                    out += self.buf[: len(self.buf) - keep]
                    self.buf = self.buf[len(self.buf) - keep :]
                    return out
                out += self.buf[:start]
                self.buf = self.buf[start + 7 :]
                self.inside = True
        return out

    def flush(self) -> str:
        rest = "" if self.inside else self.buf
        self.buf = ""
        return rest


# ── индексация (фоновая задача) ─────────────────────────────────────


@dataclass
class IndexJob:
    running: bool = False
    stage: str = ""
    done: int = 0
    total: int = 0
    error: str = ""
    source: str = ""
    started_at: str = ""
    finished_at: str = ""
    log: list[str] = field(default_factory=list)

    def public(self) -> dict:
        return {k: getattr(self, k) for k in ("running", "stage", "source", "done", "total", "error", "started_at", "finished_at")} | {
            "log": self.log[-8:]
        }


class KnowledgeIndexer:
    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store
        self.job = IndexJob()
        self._lock = threading.Lock()

    def _say(self, stage: str, msg: str = "") -> None:
        self.job.stage = stage
        if msg:
            self.job.log.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")

    def start(
        self, source_ids: list[str], ollama: OllamaRag, embed_model: str, *, download: bool = True, context: dict | None = None
    ) -> bool:
        with self._lock:
            if self.job.running:
                return False
            self.job = IndexJob(running=True, started_at=_now())
        threading.Thread(
            target=self._run, args=(list(source_ids), ollama, embed_model, download, context or {}), daemon=True, name="knowledge-index"
        ).start()
        return True

    def _run(self, source_ids: list[str], ollama: OllamaRag, embed_model: str, download: bool, context: dict) -> None:
        from server.kb_sources import SOURCES, load_pages

        failed: list[str] = []
        try:
            # сначала скачать и разобрать всё (полнотекстовый поиск работает сразу), потом векторизовать
            if download:
                for sid in source_ids:
                    src = SOURCES[sid]
                    self.job.source = sid
                    self.job.done = self.job.total = 0
                    self._say("download", f"[{sid}] загрузка: {src.title}")
                    try:
                        def tick(i: int, n: int) -> None:
                            self.job.stage, self.job.done, self.job.total = "parse", i, n

                        pages = load_pages(src, lambda m, s=sid: self._say(self.job.stage, f"[{s}] {m}"), tick, context)
                        chunks: list[Chunk] = []
                        for page in pages:
                            chunks.extend(chunk_page(page))
                        if not chunks:
                            raise RuntimeError("не найдено ни одной страницы")
                        reused = self.store.replace_source(sid, len(pages), chunks)
                        self._say("parse", f"[{sid}] страниц: {len(pages)}, фрагментов: {len(chunks)} (векторы переиспользованы: {reused})")
                    except Exception as exc:  # noqa: BLE001 — один источник не должен ронять остальные
                        failed.append(sid)
                        self._say("error", f"[{sid}] ошибка: {exc}")
            for sid in source_ids:
                if sid in failed:
                    continue
                self.job.source = sid
                self._embed_all(sid, ollama, embed_model)
            if failed:
                self.job.error = "Не загружены: " + ", ".join(failed)
            self._say("done", "Готово")
        except Exception as exc:  # noqa: BLE001
            self.job.error = str(exc)
            self._say("error", f"Ошибка: {exc}")
        finally:
            self.job.running = False
            self.job.source = ""
            self.job.finished_at = _now()

    def _embed_all(self, source_id: str, ollama: OllamaRag, embed_model: str) -> None:
        stats = self.store.stats().get(source_id, {})
        total = int(stats.get("chunks") or 0)
        done = int(stats.get("embedded") or 0)
        self.job.total, self.job.done = total, done
        self._say("embed", f"[{source_id}] векторизация: {done}/{total} ({embed_model})")
        t0 = time.time()
        while True:
            batch = self.store.missing_embeddings(source_id, EMBED_BATCH)
            if not batch:
                break
            vecs = ollama.embed(embed_model, [t for _, t in batch])
            self.store.save_embeddings([(cid, vecs[i]) for i, (cid, _) in enumerate(batch)])
            self.job.done += len(batch)
            rate = (self.job.done - done) / max(1e-6, time.time() - t0)
            self.job.stage = "embed"
            if rate > 0:
                left = (self.job.total - self.job.done) / rate
                self.job.log[-1:] = [f"{datetime.now().strftime('%H:%M:%S')} [{source_id}] векторизация: {self.job.done}/{self.job.total}, осталось ~{int(left // 60)} мин"]


# ── поиск и генерация ───────────────────────────────────────────────


def hybrid_search(
    store: KnowledgeStore,
    query: str,
    sources: list[str],
    *,
    qvec: np.ndarray | None,
    k: int = 8,
    per_page: int = 2,
) -> list[dict]:
    lexical = store.fts_search(query, sources)
    semantic = store.vector_search(qvec, sources) if qvec is not None else []
    scores: dict[int, float] = {}
    for ranking, weight in ((lexical, 1.0), (semantic, 1.2)):
        for rank, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + weight / (60 + rank)
    ordered = sorted(scores, key=lambda c: -scores[c])
    picked: list[dict] = []
    per: dict[str, int] = {}
    for row in store.get_chunks(ordered[: k * 4]):
        if per.get(row["page"], 0) >= per_page:
            continue
        per[row["page"]] = per.get(row["page"], 0) + 1
        picked.append(row)
        if len(picked) >= k:
            break
    return picked


ARTICLE_SYSTEM = """Ты — автор интерактивного учебника для подготовки к собеседованиям и экзаменам.
Пиши на русском языке, понятно и по делу, в формате Markdown.

Правила:
1. Опирайся на ИСТОЧНИКИ (официальная документация) и КАРТОЧКИ темы.
   Источники могут быть на английском — всё равно пиши по-русски; имена функций, классов и код не переводи.
2. ОБЯЗАТЕЛЬНО ставь сноски: после каждого утверждения, взятого из источника, пиши его номер в квадратных
   скобках, например «…выбрасывает ValueError [4].» или «[1][3]». В статье должно быть не меньше 5 сносок,
   если источники переданы. Не придумывай номера, которых нет в списке ИСТОЧНИКОВ.
3. Не выдумывай функции, параметры и версии, которых нет в источниках или карточках.
4. Код — в блоках ```{lang} с указанием языка; примеры короткие и рабочие.
5. НЕ начинай с заголовка с названием темы — оно уже показано. Структура (заголовки ##):
   ## Коротко — 2–3 предложения: что это и зачем.
   ## Ключевые понятия — список с пояснениями.
   ## Как это работает — объяснение с примерами кода (можно подзаголовки ###).
   ## Типичные ошибки и подводные камни
   ## Проверьте себя — 3–5 вопросов в стиле карточек (без ответов).
6. Объём — 500–1000 слов. Без вступлений вроде «Конечно!» и без заключительных фраз.
7. Источники с пометкой ВИДЕО — расшифровки видеоуроков (устная речь, возможны ошибки распознавания терминов).
   Цитируй их так же, сносками [n]. Если видеофрагмент хорошо показывает тему раздела, вставь после абзаца
   отдельной строкой маркер [[video:n]] (n — номер этого видеоисточника) — там появится плеер. Не больше двух
   маркеров на статью и только для источников с пометкой ВИДЕО."""

ASK_SYSTEM = """Ты — помощник в интерактивном учебнике. Отвечай на русском, кратко (до 200 слов), в Markdown.
Опирайся на приведённые ИСТОЧНИКИ и отмечай факты ссылками [n]. Если в источниках нет ответа — скажи об этом
и ответь по общим знаниям, явно пометив это. Код — в блоках ``` с языком."""


def format_context(chunks: list[dict], cards: list[dict], *, card_limit: int = 24) -> tuple[str, list[dict]]:
    sources = []
    parts = []
    for i, c in enumerate(chunks, 1):
        label = c["title"] if c["section"] in ("", c["title"]) else f"{c['title']} › {c['section']}"
        src = {"n": i, "title": label, "url": c["url"], "source": c["source"]}
        if c["source"].startswith("vid:"):
            m = re.search(r"#t=(\d+)", c["url"])
            src |= {"video": c["source"][4:], "start": int(m[1]) if m else 0, "title": f"Видео: {label}"}
            parts.append(f"[{i}] ВИДЕО «{c['title']}», {c['section']} (расшифровка)\n{c['text'][:1800]}")
        else:
            parts.append(f"[{i}] {label}\n{c['text'][:1800]}")
        sources.append(src)
    card_lines = []
    for c in cards[:card_limit]:
        q = c["question"].strip().replace("\n", " ")[:300]
        ref = c["reference"].strip()[:500]
        card_lines.append(f"- В: {q}\n  О: {ref}")
    ctx = ""
    if parts:
        ctx += "ИСТОЧНИКИ:\n\n" + "\n\n".join(parts) + "\n\n"
    if card_lines:
        ctx += "КАРТОЧКИ ТЕМЫ (вопрос → эталонный ответ):\n" + "\n".join(card_lines)
    return ctx, sources
