from __future__ import annotations

import json
import os
from pathlib import Path

SESSION_LIMIT_MAX = 50

DEFAULTS: dict = {
    "ollama_url": "http://ollama.webmastermsk.ru:30068",
    "model": "qwen3-coder:30b",
    "api_key": "",
    "pass_score": 75,
    "timeout": 120,
    "max_follow_ups": 2,
    "session_limit": 20,
    "auto_advance_ms": 10000,
}

# Старое значение по умолчанию (1.5 с → в UI показывалось как «1 с»)
LEGACY_AUTO_ADVANCE_MS = 1500


def data_dir() -> Path:
    if env := os.environ.get("AI_ANKI_DATA_DIR"):
        return Path(env)
    return Path.home() / ".ai-anki"


def user_config_path() -> Path:
    return data_dir() / "config.json"


def load_config(project_dir: Path) -> tuple[dict, Path]:
    """Загрузить настройки: defaults → config.json проекта → ~/.ai-anki/config.json."""
    path = user_config_path()
    config = dict(DEFAULTS)
    project_path = project_dir / "config.json"
    if project_path.exists():
        config.update(json.loads(project_path.read_text(encoding="utf-8")))
    if path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))
    elif project_path.exists():
        save_config(path, config)
    if migrate_config(config):
        save_config(path, config)
    config["session_limit"] = clamp_session_limit(config.get("session_limit", DEFAULTS["session_limit"]))
    config["auto_advance_ms"] = clamp_auto_advance_ms(config.get("auto_advance_ms", DEFAULTS["auto_advance_ms"]))
    return config, path


AUTO_ADVANCE_MAX_SEC = 10


def clamp_auto_advance_ms(value: int | str) -> int:
    try:
        ms = int(value)
    except (TypeError, ValueError):
        ms = int(DEFAULTS["auto_advance_ms"])
    return max(0, min(AUTO_ADVANCE_MAX_SEC * 1000, ms))


def auto_advance_seconds(value: int | str) -> int:
    """Секунды для QSpinBox (из миллисекунд, с учётом clamp)."""
    ms = clamp_auto_advance_ms(value)
    return ms // 1000


def migrate_config(config: dict) -> bool:
    """Обновить устаревшие значения. Возвращает True, если что-то изменилось."""
    changed = False
    if config.get("auto_advance_ms") == LEGACY_AUTO_ADVANCE_MS:
        config["auto_advance_ms"] = DEFAULTS["auto_advance_ms"]
        changed = True
    return changed


def clamp_session_limit(value: int | str) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = int(DEFAULTS["session_limit"])
    return max(1, min(SESSION_LIMIT_MAX, n))


def save_config(path: Path, config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {**DEFAULTS, **config}
    data["session_limit"] = clamp_session_limit(data["session_limit"])
    data["auto_advance_ms"] = clamp_auto_advance_ms(data["auto_advance_ms"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    config.update(data)
