"""Limits shared by the application and the isolated practice worker."""
from __future__ import annotations

import hashlib
import json
import re

MAX_FILES = 64
MAX_BYTES = 512_000
RUNTIMES = {"python", "python-data", "python-ml", "php"}


def validate_path(path: str) -> str:
    if not isinstance(path, str) or len(path) > 180 or not re.fullmatch(r"[A-Za-z0-9_. /-]+", path):
        raise ValueError("Путь: латинские буквы, цифры, пробелы, _, -, . и /; до 180 символов")
    parts = path.split("/")
    if len(parts) > 8 or any(p in {"", ".", "..", ".git", ".checks"} or p != p.strip() for p in parts):
        raise ValueError("Недопустимый путь файла или папки")
    return path


def validate_files(files: dict[str, str], folders: list[str] | None = None) -> None:
    folders = folders or []
    if not isinstance(files, dict) or not 1 <= len(files) <= MAX_FILES or len(folders) > MAX_FILES:
        raise ValueError(f"В проекте должно быть от 1 до {MAX_FILES} файлов")
    size = 0
    for path, content in files.items():
        validate_path(path)
        if not isinstance(content, str) or "\x00" in content:
            raise ValueError("Поддерживаются текстовые файлы без нулевых байтов")
        size += len(content.encode("utf-8"))
    if size > MAX_BYTES:
        raise ValueError("Проект превышает 512 КБ")
    for path in [*files, *folders]:
        validate_path(path)
        if path in folders and path in files:
            raise ValueError("Папка и файл не могут иметь одинаковый путь")
        parts = path.split("/")
        if any("/".join(parts[:i]) in files for i in range(1, len(parts))):
            raise ValueError("Файл не может быть родительской папкой")


def file_digest(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
