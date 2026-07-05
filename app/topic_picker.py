from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.live_coding import topic_summaries
from app.progress import ProgressStore, StudyMode
from app.registry import DeckEntry, DeckRegistry


class TopicPickerDialog(QDialog):
    def __init__(
        self,
        entry: DeckEntry,
        registry: DeckRegistry,
        progress: ProgressStore,
        mode: StudyMode,
        *,
        pass_score: int = 75,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Выбор темы")
        self.resize(520, 420)
        self._selected_topic = ""

        deck = registry.load_deck(entry)
        summaries = topic_summaries(deck, progress, pass_score=pass_score)
        mode_label = {
            StudyMode.DUE: "повторение",
            StudyMode.NEW: "новые",
            StudyMode.WEAK: "слабые",
            StudyMode.ALL: "вся колода",
        }[mode]

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>{entry.name}</b> · режим: {mode_label}"))
        layout.addWidget(QLabel("Выберите тему — в сессию попадут только карточки этой темы:"))

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._accept_current)
        for row in summaries:
            label = (
                f"{row['name']}  —  всего {row['total']}, "
                f"к повтору {row['due']}, новые {row['new']}, слабые {row['weak']}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, row["name"])
            self.list.addItem(item)
        layout.addWidget(self.list, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_current)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.list.count():
            self.list.setCurrentRow(0)

    def _accept_current(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        self._selected_topic = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @property
    def selected_topic(self) -> str:
        return self._selected_topic
