#!/usr/bin/env python3
"""Write simple SVG diagrams for anatomy deck (bundled, offline-friendly)."""
from __future__ import annotations

from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "anatomy-assets"

DIAGRAMS: dict[str, tuple[str, str]] = {
    "terminology-planes.svg": ("Анатомические плоскости", "#3b82f6"),
    "terminology-directions.svg": ("Направления и оси", "#2563eb"),
    "skeleton-overview.svg": ("Скелет человека", "#64748b"),
    "joint-types.svg": ("Типы суставов", "#475569"),
    "bone-structure.svg": ("Строение кости", "#94a3b8"),
    "muscle-structure.svg": ("Строение мышцы", "#dc2626"),
    "muscle-types.svg": ("Типы мышечной ткани", "#ef4444"),
    "heart.svg": ("Сердце и камеры", "#b91c1c"),
    "circulation.svg": ("Малый и большой круг", "#991b1b"),
    "blood-vessels.svg": ("Артерии и вены", "#7f1d1d"),
    "lungs.svg": ("Лёгкие и бронхи", "#0ea5e9"),
    "respiratory-tract.svg": ("Дыхательные пути", "#0284c7"),
    "digestive.svg": ("Пищеварительный тракт", "#d97706"),
    "liver-gall.svg": ("Печень и желчный", "#b45309"),
    "kidney.svg": ("Почка и нефрон", "#0891b2"),
    "urinary.svg": ("Мочевыделительная система", "#0e7490"),
    "neuron.svg": ("Нейрон", "#7c3aed"),
    "cns-overview.svg": ("ЦНС обзор", "#6d28d9"),
    "brain.svg": ("Отделы головного мозга", "#5b21b6"),
    "spine.svg": ("Позвоночник", "#4c1d95"),
    "endocrine.svg": ("Эндокринные железы", "#ca8a04"),
    "eye.svg": ("Строение глаза", "#059669"),
    "ear.svg": ("Строение уха", "#047857"),
    "skin.svg": ("Кожа и слои", "#f59e0b"),
    "lymphatic.svg": ("Лимфатическая система", "#10b981"),
    "reproductive-m.svg": ("Мужская репродукция", "#6366f1"),
    "reproductive-f.svg": ("Женская репродукция", "#818cf8"),
    "brain-cortex.svg": ("Кора больших полушарий", "#9333ea"),
    "spine-regions.svg": ("Отделы позвоночника", "#7e22ce"),
}


def _svg(title: str, color: str, subtitle: str = "") -> str:
    sub = f'<text x="200" y="118" text-anchor="middle" font-size="13" fill="#64748b">{subtitle}</text>' if subtitle else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 220" role="img">
  <rect width="400" height="220" fill="#f8fafc" rx="8"/>
  <rect x="24" y="24" width="352" height="172" fill="#fff" stroke="#cbd5e1" stroke-width="2" rx="6"/>
  <ellipse cx="200" cy="130" rx="90" ry="55" fill="{color}" opacity="0.15"/>
  <ellipse cx="200" cy="130" rx="70" ry="40" fill="none" stroke="{color}" stroke-width="3"/>
  <text x="200" y="88" text-anchor="middle" font-family="system-ui,sans-serif" font-size="16" font-weight="600" fill="#1e293b">{title}</text>
  {sub}
  <text x="200" y="200" text-anchor="middle" font-size="11" fill="#94a3b8">AI Anki · схема для обучения</text>
</svg>
"""


def write_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name, (title, color) in DIAGRAMS.items():
        path = ASSETS / name
        path.write_text(_svg(title, color), encoding="utf-8")
    print(f"Written {len(DIAGRAMS)} SVG assets -> {ASSETS}")


if __name__ == "__main__":
    write_assets()
