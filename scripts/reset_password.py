"""Сброс пароля пользователя веб-версии.

    docker exec -it ai-anki python scripts/reset_password.py <логин> <новый_пароль>
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config_store import data_dir  # noqa: E402
from server.auth import hash_password  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]
    if len(password) < 6:
        sys.exit("Пароль должен быть не короче 6 символов")
    db = sqlite3.connect(str(data_dir() / "users.db"))
    with db:
        cur = db.execute(
            "UPDATE users SET password_hash = ? WHERE username = ? COLLATE NOCASE",
            (hash_password(password), username),
        )
        if cur.rowcount:
            uid = db.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()[0]
            db.execute("DELETE FROM tokens WHERE user_id = ?", (uid,))
    print("Пароль изменён" if cur.rowcount else f"Пользователь {username!r} не найден")


if __name__ == "__main__":
    main()
