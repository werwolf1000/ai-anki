"""Видеотека учебника: видеоуроки → звук → Whisper → фрагменты с таймкодами в базе знаний.

Видео лежат в каталогах из AI_ANKI_VIDEO_DIRS (через «,» или «;», например смонтированная папка NAS)
и в <data>/videos (загрузки через веб). Новые файлы находятся сканированием — по кнопке и автоматически
раз в AI_ANKI_VIDEO_SCAN_MINUTES минут (0 — выключить).

Каждое видео — отдельный источник базы знаний `vid:<id>`; к учебнику (программе) его привязывает поле
book: по папке/названию, иначе по словам расшифровки. Статьи цитируют фрагменты и встраивают плеер.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from server.knowledge import Chunk, KnowledgeStore
from server.syllabus import all_syllabi, stems

MEDIA_EXT = {".mp4", ".m4v", ".mkv", ".webm", ".mov", ".avi", ".wmv", ".flv", ".mpg", ".mpeg", ".ts",
             ".mp3", ".m4a", ".wav", ".ogg", ".opus", ".flac", ".aac"}
SEGMENT_SECONDS = 300  # звук режется на куски по 5 минут: прогресс, лента расшифровки, продолжение после сбоя
CHUNK_CHARS = 1100
CHUNK_VERSION = 2  # 2: в заголовке фрагмента — папка курса
EMBED_BATCH = 16


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ffmpeg_exe() -> str | None:
    exe = os.environ.get("AI_ANKI_FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    try:  # для разработки: pip install imageio-ffmpeg
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return None


def probe_duration(path: str) -> float:
    """Длительность медиафайла по заголовку (ffmpeg -i), 0 — не удалось."""
    exe = ffmpeg_exe()
    if not exe:
        return 0.0
    try:
        proc = subprocess.run([exe, "-hide_banner", "-nostdin", "-i", path], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def fmt_time(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def nice_title(stem: str) -> str:
    t = re.sub(r"[_\.]+", " ", stem)
    return " ".join(t.split()) or stem


# ── привязка к учебнику ─────────────────────────────────────────────


def guess_book(folder: str, title: str, text: str = "") -> str:
    """Программа учебника для видео: сначала по папке и названию, потом по словам расшифровки."""
    books = all_syllabi()
    for hay in (folder.lower(), f"{folder} {title}".lower()):
        for part in [hay, *re.split(r"[/\\]", hay)]:
            part = part.strip()
            if not part:
                continue
            for sy in books:
                if re.search(sy.match, part, re.I) or sy.title.lower() in part or part == sy.id:
                    return sy.id
    if not text:
        return ""
    words = Counter(w for w in (m[:6] for m in re.findall(r"[a-zа-яё0-9_]{3,}", text.lower())))
    best, best_score = "", 0.0
    for sy in books:
        vocab = set()
        for ch in sy.chapters:
            vocab |= stems(ch.title)
            for ls in ch.lessons:
                vocab |= stems(ls)
        if not vocab:
            continue
        score = sum(min(words[s], 5) for s in vocab) / math.sqrt(len(vocab))
        if score > best_score:
            best, best_score = sy.id, score
    return best if best_score >= 3.0 else ""


def chunk_title(folder: str, title: str) -> str:
    folder = folder.replace("/", " / ").strip()
    return f"{folder} / {title}" if folder else title


def segments_to_chunks(video_id: str, title: str, segments: list[dict]) -> list[Chunk]:
    chunks: list[Chunk] = []
    buf: list[str] = []
    start = end = 0.0
    size = 0

    def flush() -> None:
        nonlocal buf, size
        text = " ".join(buf).strip()
        if len(text) >= 40:
            chunks.append(Chunk(
                page=f"vid:{video_id}", url=f"/api/videos/{video_id}/file#t={int(start)}", title=title,
                section=f"{fmt_time(start)}–{fmt_time(end)}", text=text, ord=len(chunks),
            ))
        buf, size = [], 0

    for seg in segments:
        if not buf:
            start = seg["start"]
        buf.append(seg["text"])
        size += len(seg["text"]) + 1
        end = seg["end"] or seg["start"]
        if size >= CHUNK_CHARS:
            flush()
    flush()
    return chunks


# ── хранилище ───────────────────────────────────────────────────────


class VideoLibrary:
    def __init__(self, data_dir: Path, knowledge: KnowledgeStore, services) -> None:
        self.services = services
        self.knowledge = knowledge
        self.upload_dir = data_dir / "videos"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.get("AI_ANKI_VIDEO_DIRS", "")
        self.roots = [Path(p.strip()) for p in re.split(r"[;,]", env) if p.strip()] + [self.upload_dir]
        self._db = sqlite3.connect(str(data_dir / "videos.db"), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock, self._db:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY, path TEXT UNIQUE NOT NULL, root TEXT NOT NULL, folder TEXT NOT NULL,
                    title TEXT NOT NULL, size INTEGER, mtime REAL, duration REAL DEFAULT 0,
                    book TEXT DEFAULT '', book_manual INTEGER DEFAULT 0, status TEXT NOT NULL,
                    error TEXT DEFAULT '', progress REAL DEFAULT 0, language TEXT DEFAULT '',
                    segments TEXT DEFAULT '', chunks INTEGER DEFAULT 0, added_at TEXT, indexed_at TEXT
                )"""
            )
            cols = {r[1] for r in self._db.execute("PRAGMA table_info(videos)")}
            if "chunk_version" not in cols:
                self._db.execute("ALTER TABLE videos ADD COLUMN chunk_version INTEGER DEFAULT 1")
            if "retries" not in cols:
                self._db.execute("ALTER TABLE videos ADD COLUMN retries INTEGER DEFAULT 0")
            if "parts_done" not in cols:
                self._db.execute("ALTER TABLE videos ADD COLUMN parts_done INTEGER DEFAULT 0")
            if "asr_seconds" not in cols:
                self._db.execute("ALTER TABLE videos ADD COLUMN asr_seconds REAL DEFAULT 0")
            # прерванная перезапуском обработка — в очередь заново
            self._db.execute("UPDATE videos SET status='queued', progress=0 WHERE status='processing'")
        self.current = ""
        self.state: dict = {}  # что делает обработчик прямо сейчас (для прогресса в интерфейсе)
        self.feed: deque = deque(maxlen=400)  # последние распознанные Whisper фразы
        self._feed_seq = 0
        self.log: list[str] = []
        self._wake = threading.Event()
        threading.Thread(target=self._worker, daemon=True, name="video-worker").start()
        minutes = float(os.environ.get("AI_ANKI_VIDEO_SCAN_MINUTES", "30") or 0)
        if minutes > 0:
            threading.Thread(target=self._autoscan, args=(minutes,), daemon=True, name="video-scan").start()

    def say(self, msg: str) -> None:
        self.log.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")
        del self.log[:-80]

    def _stage(self, stage: str, **kw) -> None:
        self.state.update(stage=stage, **kw)

    def _speed(self) -> float:
        """Скорость Whisper (секунд звука за секунду работы) по уже обработанным видео."""
        with self._lock:
            r = self._db.execute(
                "SELECT SUM(duration), SUM(asr_seconds) FROM videos WHERE status='done' AND asr_seconds > 0"
            ).fetchone()
        return (r[0] / r[1]) if r and r[0] and r[1] else 0.0

    def progress(self) -> dict:
        """Текущее видео, очередь и прогноз — для панели видеотеки."""
        with self._lock:
            q = self._db.execute("SELECT COUNT(*), SUM(duration), SUM(duration = 0) FROM videos WHERE status='queued'").fetchone()
        st = dict(self.state)
        speed = st.get("speed") or self._speed()
        if st:
            st["elapsed"] = time.time() - st.get("started", time.time())
            left = max(0.0, (st.get("duration") or 0) - (st.get("done_sec") or 0))
            st["eta"] = left / speed if speed and st.get("stage") in ("asr", "audio") else None
        queued_sec = float(q[1] or 0)
        return {
            "current": st or None,
            "queue": {
                "count": int(q[0] or 0),
                "seconds": queued_sec,
                "unknown": int(q[2] or 0),
                "eta": queued_sec / speed if speed else None,
            },
            "speed": speed,
        }

    def feed_since(self, seq: int = 0, limit: int = 150) -> list[dict]:
        return [f for f in self.feed if f["seq"] > seq][-limit:]

    def _feed(self, vid: str, title: str, segs: list[dict]) -> None:
        for sg in segs:
            self._feed_seq += 1
            self.feed.append({"seq": self._feed_seq, "video": vid, "title": title, "t": sg["start"], "text": sg["text"]})

    # — сканирование —

    def scan(self) -> dict:
        added = changed = missing = 0
        seen: set[str] = set()
        with self._lock:
            known = {r["path"]: r for r in self._db.execute("SELECT id, path, size, mtime, status FROM videos")}
        for root in self.roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if path.suffix.lower() not in MEDIA_EXT or not path.is_file() or any(p.startswith(".") for p in path.parts):
                    continue
                key = str(path.resolve())
                seen.add(key)
                st = path.stat()
                row = known.get(key)
                folder = str(path.parent.relative_to(root)).replace("\\", "/")
                folder = "" if folder == "." else folder
                with self._lock, self._db:
                    if row is None:
                        vid = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
                        title = nice_title(path.stem)
                        self._db.execute(
                            "INSERT OR IGNORE INTO videos (id, path, root, folder, title, size, mtime, duration, book, status, added_at)"
                            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?)",
                            (vid, key, str(root), folder, title, st.st_size, st.st_mtime, probe_duration(key),
                             guess_book(folder, title), _now()),
                        )
                        added += 1
                    elif row["status"] == "missing" or (row["status"] != "skipped" and (row["size"] != st.st_size or abs((row["mtime"] or 0) - st.st_mtime) > 1)):
                        self._db.execute(
                            "UPDATE videos SET size=?, mtime=?, duration=?, status='queued', progress=0, error='',"
                            " parts_done=0, segments='', asr_seconds=0 WHERE id=?",
                            (st.st_size, st.st_mtime, probe_duration(key), row["id"]),
                        )
                        changed += 1
        for key, row in known.items():
            if key not in seen and row["status"] != "missing" and any(key.startswith(str(r.resolve())) for r in self.roots if r.is_dir()):
                self.knowledge.delete_source(f"vid:{row['id']}")
                with self._lock, self._db:
                    self._db.execute("UPDATE videos SET status='missing', chunks=0 WHERE id=?", (row["id"],))
                missing += 1
        if added or changed:
            self.say(f"Найдено новых видео: {added}, изменённых: {changed}")
            self._wake.set()
        return {"added": added, "changed": changed, "missing": missing}

    def _autoscan(self, minutes: float) -> None:
        time.sleep(20)
        while True:
            try:
                self.scan()
            except Exception as exc:  # noqa: BLE001
                self.say(f"Ошибка сканирования: {exc}")
            time.sleep(minutes * 60)

    # — обработка —

    def _next(self) -> sqlite3.Row | None:
        with self._lock:
            return self._db.execute(
                "SELECT * FROM videos WHERE status='queued' ORDER BY added_at, path LIMIT 1"
            ).fetchone()

    def _set(self, vid: str, **fields) -> None:
        cols = ", ".join(f"{k}=?" for k in fields)
        with self._lock, self._db:
            self._db.execute(f"UPDATE videos SET {cols} WHERE id=?", (*fields.values(), vid))

    def _maintain(self) -> None:
        """Без перерасшифровки: пересобрать фрагменты старого формата и достроить векторы,
        которые не получились (например, Ollama была занята). Видео, упавшие из-за временной
        недоступности Whisper/ffmpeg-сети, — снова в очередь (до 5 раз)."""
        with self._lock, self._db:
            n = self._db.execute(
                "UPDATE videos SET status='queued', progress=0, retries=retries+1"
                " WHERE status='error' AND retries < 5 AND (error LIKE 'Whisper%' OR error LIKE 'ASR%')"
            ).rowcount
        if n:
            self.say(f"Повторная расшифровка после ошибок Whisper: {n}")
            return
        with self._lock:
            rows = self._db.execute(
                "SELECT id, folder, title, segments, chunk_version FROM videos WHERE status='done' AND segments != ''"
            ).fetchall()
        for r in rows:
            src = f"vid:{r['id']}"
            if (r["chunk_version"] or 1) < CHUNK_VERSION:
                chunks = segments_to_chunks(r["id"], chunk_title(r["folder"], r["title"]), json.loads(r["segments"]))
                self.knowledge.replace_source(src, 1, chunks)
                self._set(r["id"], chunks=len(chunks), chunk_version=CHUNK_VERSION)
            if self.knowledge.missing_embeddings(src, 1):
                try:
                    self._embed(src)
                    self._set(r["id"], error="")
                    self.say(f"Векторы построены: {r['title']}")
                except Exception as exc:  # noqa: BLE001
                    self._set(r["id"], error=f"векторы не построены: {exc}"[:500])
                    return  # Ollama недоступна — попробуем в следующий раз
            if self._next() is not None:
                return

    def _worker(self) -> None:
        last_maint = 0.0
        while True:
            row = self._next()
            if row is None:
                if time.time() - last_maint > 600:
                    last_maint = time.time()
                    try:
                        self._maintain()
                    except Exception as exc:  # noqa: BLE001
                        self.say(f"Обслуживание видеотеки: {exc}")
                self._wake.wait(timeout=60)
                self._wake.clear()
                continue
            self.current = row["id"]
            try:
                self._process(row)
            except Exception as exc:  # noqa: BLE001
                self._set(row["id"], status="error", error=str(exc)[:500])
                self.say(f"Ошибка «{row['title']}»: {exc}")
                time.sleep(5)
            finally:
                self.current = ""
                self.state = {}

    def _process(self, row: sqlite3.Row) -> None:
        from app.asr_client import transcribe_segments

        vid, title = row["id"], row["title"]
        cfg = self.services.config
        if not str(cfg.get("asr_url", "")).strip():
            raise RuntimeError("не задан адрес Whisper (Настройки → Распознавание речи)")
        ffmpeg = ffmpeg_exe()
        if not ffmpeg:
            raise RuntimeError("не найден ffmpeg")
        name = f"{row['folder'] + ' / ' if row['folder'] else ''}{title}"
        duration = row["duration"] or probe_duration(row["path"])
        # продолжение после сбоя: уже расшифрованные куски не отправляются в Whisper повторно
        resume = int(row["parts_done"] or 0)
        segments: list[dict] = json.loads(row["segments"] or "[]") if resume else []
        asr_seconds = float(row["asr_seconds"] or 0) if resume else 0.0
        self.state = {"id": vid, "title": name, "stage": "audio", "duration": duration, "done_sec": 0.0,
                      "part": 0, "parts": 0, "started": time.time(), "speed": 0.0}
        self._set(vid, status="processing", progress=0.01, error="", duration=duration)
        self.say(f"Обработка: {name} ({fmt_time(duration)})" + (f", продолжение с куска {resume + 1}" if resume else ""))
        book_title = next((s.title for s in all_syllabi() if s.id == row["book"]), "")
        prompt = ". ".join(x for x in (book_title, row["folder"].replace("/", ". "), title) if x) + "."
        language = row["language"] or ""
        with tempfile.TemporaryDirectory(prefix="aianki-video-") as tmp:
            # 1. звук: 16 кГц моно, куски по SEGMENT_SECONDS; прогресс ffmpeg — из -progress
            cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", row["path"], "-vn", "-ac", "1",
                   "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "48k", "-f", "segment", "-segment_time",
                   str(SEGMENT_SECONDS), "-reset_timestamps", "1", "-progress", "pipe:1", "-nostats",
                   str(Path(tmp) / "part%04d.mp3")]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    encoding="utf-8", errors="replace")
            for line in proc.stdout:  # type: ignore[union-attr]
                if line.startswith("out_time_us=") and duration:
                    try:
                        done = int(line.split("=", 1)[1]) / 1e6
                    except ValueError:
                        continue
                    self.state["audio_done"] = min(done, duration)
                    self._set(vid, progress=round(0.01 + 0.09 * min(done / duration, 1), 3))
            err_text = proc.stderr.read() if proc.stderr else ""  # type: ignore[union-attr]
            proc.wait()
            parts = sorted(Path(tmp).glob("part*.mp3"))
            if proc.returncode != 0 or not parts:
                tail = err_text.strip().splitlines()[-1:] or ["?"]
                raise RuntimeError(f"ffmpeg не извлёк звук: {tail[0][:200]}")
            if not duration:
                duration = len(parts) * SEGMENT_SECONDS
            if resume > len(parts):
                resume, segments, asr_seconds = 0, [], 0.0
            self._stage("asr", parts=len(parts), part=resume, done_sec=min(resume * SEGMENT_SECONDS, duration), duration=duration)
            self.say(f"Звук извлечён: {len(parts)} кусков по {SEGMENT_SECONDS // 60} мин")

            # 2. Whisper по кускам
            for i, part in enumerate(parts):
                if i < resume:
                    continue
                offset = i * SEGMENT_SECONDS
                self._stage("asr", part=i + 1)
                last: Exception | None = None
                t0 = time.time()
                for attempt in range(5):  # Whisper бывает недоступен минуту-другую (загрузка модели)
                    try:
                        segs, lang = transcribe_segments(
                            cfg.get("asr_url", ""), part.read_bytes(), part.name,
                            language=str(cfg.get("video_language", "") or ""),
                            login=str(cfg.get("asr_user", "")), password=str(cfg.get("asr_password", "")),
                            initial_prompt=prompt,
                        )
                        break
                    except Exception as exc:  # noqa: BLE001
                        last = exc
                        wait = min(20 * 2**attempt, 180)
                        self._stage("retry", retry_in=wait, retry_error=str(exc)[:120])
                        self.say(f"Whisper не ответил ({str(exc)[:80]}), кусок {i + 1}/{len(parts)}, повтор через {wait} с")
                        time.sleep(wait)
                        self._stage("asr")
                        t0 = time.time()
                else:
                    raise RuntimeError(f"Whisper: {last}")
                took = time.time() - t0
                asr_seconds += took
                language = language or lang
                shifted = [{"start": x["start"] + offset, "end": x["end"] + offset, "text": x["text"]} for x in segs]
                segments.extend(shifted)
                self._feed(vid, name, shifted)
                piece = min(SEGMENT_SECONDS, max(0.0, duration - offset))
                done_sec = min(offset + piece, duration)
                speed = done_sec / asr_seconds if asr_seconds else 0.0
                self._stage("asr", done_sec=done_sec, speed=speed, language=language)
                words = sum(len(x["text"].split()) for x in segs)
                self.say(f"Кусок {i + 1}/{len(parts)} ({fmt_time(offset)}–{fmt_time(offset + piece)}): {len(segs)} фраз, "
                         f"{words} слов за {took:.0f} с" + (f", язык {lang}" if lang else ""))
                # сохраняем после каждого куска: расшифровку видно сразу, после сбоя — продолжение
                self._set(vid, progress=round(0.1 + 0.82 * (i + 1) / len(parts), 3), parts_done=i + 1,
                          segments=json.dumps(segments, ensure_ascii=False), asr_seconds=asr_seconds, language=language)

        if not segments:
            raise RuntimeError("в записи не распознано речи")
        # 3. фрагменты и векторы
        self._stage("index")
        text = " ".join(x["text"] for x in segments)
        book = row["book"] if row["book_manual"] or row["book"] else guess_book(row["folder"], title, text)
        chunks = segments_to_chunks(vid, chunk_title(row["folder"], title), segments)
        self.knowledge.replace_source(f"vid:{vid}", 1, chunks)
        self._set(vid, book=book, chunks=len(chunks), progress=0.94, chunk_version=CHUNK_VERSION)
        self.say(f"Фрагментов для поиска: {len(chunks)}, векторизация…")
        self._stage("embed", chunks=len(chunks))
        err = ""
        try:
            self._embed(f"vid:{vid}")
        except Exception as exc:  # noqa: BLE001 — без векторов работает поиск по словам
            err = f"векторы не построены: {exc}"
        self._set(vid, status="done", progress=1.0, error=err, indexed_at=_now(), retries=0, parts_done=0)
        self.say(f"Готово: {name} — {fmt_time(duration)}, {len(segments)} фраз, фрагментов {len(chunks)}"
                 + (f", учебник: {book}" if book else ", учебник не определён") + (f" ({err})" if err else ""))

    def _embed(self, source_id: str) -> None:
        ollama = self.services.rag_client()
        model = self.services.embed_model()
        while True:
            batch = self.knowledge.missing_embeddings(source_id, EMBED_BATCH)
            if not batch:
                return
            vecs = ollama.embed(model, [t for _, t in batch])
            self.knowledge.save_embeddings([(cid, vecs[i]) for i, (cid, _) in enumerate(batch)])

    # — чтение —

    def get(self, vid: str) -> sqlite3.Row | None:
        with self._lock:
            return self._db.execute("SELECT * FROM videos WHERE id=?", (vid,)).fetchone()

    def book_summary(self, book: str) -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT id, folder, title, status, chunks, error FROM videos WHERE book=? ORDER BY folder, title", (book,)
            ).fetchall()
        return [dict(r) for r in rows]

    def sources_for_book(self, book: str) -> list[str]:
        if not book:
            return []
        with self._lock:
            rows = self._db.execute("SELECT id FROM videos WHERE book=? AND status='done' AND chunks>0", (book,)).fetchall()
        return [f"vid:{r['id']}" for r in rows]

    def public(self) -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT id, path, root, folder, title, size, duration, book, book_manual, status, error, progress,"
                " language, chunks, added_at, indexed_at FROM videos ORDER BY folder, title"
            ).fetchall()
        up = str(self.upload_dir.resolve())
        return [dict(r) | {"uploaded": r["path"].startswith(up), "path": None} for r in rows]

    # — изменения —

    def update(self, vid: str, *, book: str | None = None, title: str | None = None) -> None:
        if book is not None:
            self._set(vid, book=book, book_manual=1)
        if title is not None and title.strip():
            self._set(vid, title=title.strip())

    def requeue(self, vid: str) -> None:
        """Расшифровать заново с нуля."""
        self._set(vid, status="queued", progress=0, error="", retries=0, parts_done=0, segments="", asr_seconds=0, language="")
        self._wake.set()

    def remove(self, vid: str) -> None:
        row = self.get(vid)
        if row is None:
            return
        self.knowledge.delete_source(f"vid:{vid}")
        up = str(self.upload_dir.resolve())
        if row["path"].startswith(up):
            try:
                Path(row["path"]).unlink()
            except OSError:
                pass
            with self._lock, self._db:
                self._db.execute("DELETE FROM videos WHERE id=?", (vid,))
        else:  # чужую папку не трогаем — просто не индексируем
            self._set(vid, status="skipped", chunks=0, segments="")


# ── API ─────────────────────────────────────────────────────────────


class VideoPatch(BaseModel):
    book: str | None = None
    title: str | None = None


def build_router(services, current_ctx: Callable, user_for_token: Callable[[str], object]) -> APIRouter:
    r = APIRouter()
    lib: VideoLibrary = services.videos

    def admin(ctx=Depends(current_ctx)):
        if not ctx.user.is_admin:
            raise HTTPException(403, "Только для администратора")
        return ctx

    @r.get("/api/videos")
    def list_videos(ctx=Depends(admin)) -> dict:
        return {
            "roots": [{"path": str(p), "exists": p.is_dir(), "uploads": p == lib.upload_dir} for p in lib.roots],
            "ffmpeg": bool(ffmpeg_exe()),
            "asr": bool(str(services.config.get("asr_url", "")).strip()),
            "current": lib.current,
            "progress": lib.progress(),
            "log": lib.log[-30:],
            "books": [{"id": s.id, "title": s.title} for s in all_syllabi()],
            "videos": lib.public(),
        }

    @r.get("/api/videos/feed")
    def feed(since: int = 0, ctx=Depends(admin)) -> dict:
        return {"items": lib.feed_since(since), "progress": lib.progress(), "log": lib.log[-30:]}

    @r.post("/api/videos/scan")
    def scan(ctx=Depends(admin)) -> dict:
        return lib.scan()

    @r.post("/api/videos/upload")
    def upload(file: UploadFile = File(...), folder: str = Form(""), ctx=Depends(admin)) -> dict:
        name = Path(file.filename or "video").name
        if Path(name).suffix.lower() not in MEDIA_EXT:
            raise HTTPException(400, "Неподдерживаемый формат файла")
        parts = [re.sub(r'[<>:"|?*\\]+', "_", p).strip(" .") for p in folder.replace("\\", "/").split("/")]
        target_dir = lib.upload_dir.joinpath(*[p for p in parts if p and p != ".."])
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / name
        with target.open("wb") as out:
            shutil.copyfileobj(file.file, out, length=4 * 1024 * 1024)
        return {"ok": True, **lib.scan()}

    @r.patch("/api/videos/{vid}")
    def patch(vid: str, body: VideoPatch, ctx=Depends(admin)) -> dict:
        if lib.get(vid) is None:
            raise HTTPException(404, "Видео не найдено")
        lib.update(vid, book=body.book, title=body.title)
        return {"ok": True}

    @r.post("/api/videos/{vid}/reindex")
    def reindex(vid: str, ctx=Depends(admin)) -> dict:
        if lib.get(vid) is None:
            raise HTTPException(404, "Видео не найдено")
        lib.requeue(vid)
        return {"ok": True}

    @r.delete("/api/videos/{vid}")
    def delete(vid: str, ctx=Depends(admin)) -> dict:
        lib.remove(vid)
        return {"ok": True}

    @r.get("/api/videos/{vid}/transcript")
    def transcript(vid: str, ctx=Depends(current_ctx)) -> dict:
        row = lib.get(vid)
        if row is None:
            raise HTTPException(404, "Видео не найдено")
        return {"id": vid, "title": row["title"], "segments": json.loads(row["segments"] or "[]")}

    @r.get("/api/videos/{vid}/file")
    def video_file(vid: str, token: str = Query("")):
        # <video src> не умеет заголовки — токен передаётся параметром
        if user_for_token(token) is None:
            raise HTTPException(401, "Требуется вход в аккаунт")
        row = lib.get(vid)
        if row is None or not Path(row["path"]).is_file():
            raise HTTPException(404, "Видео не найдено")
        return FileResponse(row["path"], filename=Path(row["path"]).name, content_disposition_type="inline")

    return r
