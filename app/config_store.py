from __future__ import annotations

import json
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
    "auto_advance_ms": 1500,
}


def user_config_path() -> Path:
    return Path.home() / ".ai-anki" / "config.json"


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
    config["session_limit"] = clamp_session_limit(config.get("session_limit", DEFAULTS["session_limit"]))
    return config, path


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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
