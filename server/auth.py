"""Пользователи и токены доступа (SQLite, только stdlib).

Пароли — scrypt с солью. Токен выдаётся при входе и передаётся в заголовке
`Authorization: Bearer <token>`; в БД хранится только его sha256.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-@]{3,40}$")
MIN_PASSWORD = 6
TOKEN_LIMIT_PER_USER = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt_hex, digest_hex = stored.split("$", 2)
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1, dklen=32
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class User:
    id: int
    username: str
    display_name: str
    is_admin: bool
    created_at: str

    def public(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name or self.username,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
        }


class AuthError(ValueError):
    pass


class UserStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock, self._db:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    display_name TEXT NOT NULL DEFAULT '',
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )"""
            )
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS tokens (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    client TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL
                )"""
            )

    @staticmethod
    def _row_user(row: sqlite3.Row | None) -> User | None:
        if row is None:
            return None
        return User(
            id=int(row["id"]),
            username=row["username"],
            display_name=row["display_name"],
            is_admin=bool(row["is_admin"]),
            created_at=row["created_at"],
        )

    def count(self) -> int:
        with self._lock:
            return int(self._db.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    def get(self, user_id: int) -> User | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row_user(row)

    def register(self, username: str, password: str, display_name: str = "") -> User:
        username = username.strip()
        display_name = display_name.strip()[:60]
        if not USERNAME_RE.match(username):
            raise AuthError("Логин: 3–40 символов, латиница, цифры и . _ - @")
        if len(password) < MIN_PASSWORD:
            raise AuthError(f"Пароль должен быть не короче {MIN_PASSWORD} символов")
        pw_hash = hash_password(password)
        with self._lock, self._db:
            first = int(self._db.execute("SELECT COUNT(*) FROM users").fetchone()[0]) == 0
            try:
                cur = self._db.execute(
                    "INSERT INTO users (username, display_name, password_hash, is_admin, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (username, display_name, pw_hash, 1 if first else 0, _now()),
                )
            except sqlite3.IntegrityError as exc:
                raise AuthError("Такой логин уже занят") from exc
            row = self._db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        user = self._row_user(row)
        assert user is not None
        return user

    def authenticate(self, username: str, password: str) -> User | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM users WHERE username = ?", (username.strip(),)
            ).fetchone()
        if row is None:
            hash_password(password)  # выровнять время ответа
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return self._row_user(row)

    def change_password(self, user_id: int, old: str, new: str) -> None:
        with self._lock:
            row = self._db.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None or not verify_password(old, row["password_hash"]):
            raise AuthError("Текущий пароль указан неверно")
        if len(new) < MIN_PASSWORD:
            raise AuthError(f"Пароль должен быть не короче {MIN_PASSWORD} символов")
        with self._lock, self._db:
            self._db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new), user_id))

    def update_profile(self, user_id: int, display_name: str) -> None:
        with self._lock, self._db:
            self._db.execute(
                "UPDATE users SET display_name = ? WHERE id = ?", (display_name.strip()[:60], user_id)
            )

    def issue_token(self, user_id: int, client: str = "") -> str:
        token = secrets.token_urlsafe(32)
        now = _now()
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO tokens (token_hash, user_id, client, created_at, last_used_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (_token_hash(token), user_id, client[:40], now, now),
            )
            # не копить бесконечно старые сессии
            self._db.execute(
                """DELETE FROM tokens WHERE user_id = ? AND token_hash NOT IN (
                       SELECT token_hash FROM tokens WHERE user_id = ?
                       ORDER BY last_used_at DESC LIMIT ?)""",
                (user_id, user_id, TOKEN_LIMIT_PER_USER),
            )
        return token

    def user_for_token(self, token: str) -> User | None:
        if not token:
            return None
        th = _token_hash(token)
        with self._lock:
            row = self._db.execute(
                "SELECT u.* FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token_hash = ?",
                (th,),
            ).fetchone()
            if row is not None:
                with self._db:
                    self._db.execute(
                        "UPDATE tokens SET last_used_at = ? WHERE token_hash = ?", (_now(), th)
                    )
        return self._row_user(row)

    def revoke(self, token: str) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM tokens WHERE token_hash = ?", (_token_hash(token),))
