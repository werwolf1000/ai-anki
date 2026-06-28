from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config_store import SESSION_LIMIT_MAX, clamp_session_limit, save_config
from app.ollama_client import OllamaClient
from app.progress import ProgressStore, StudyMode
from app.registry import DeckEntry, DeckRegistry


class WelcomeScreen(QWidget):
    deck_selected = pyqtSignal(object, str)  # DeckEntry, StudyMode value
    config_saved = pyqtSignal()

    def __init__(
        self,
        registry: DeckRegistry,
        progress: ProgressStore,
        config: dict,
        config_path: Path,
        decks_dir: Path,
    ) -> None:
        super().__init__()
        self.registry = registry
        self.progress = progress
        self.config = config
        self.config_path = config_path
        self.decks_dir = decks_dir
        self._selected_entry: DeckEntry | None = None
        self._build_ui()
        self.sync_from_config()
        self.refresh()

    def sync_from_config(self) -> None:
        self.pass_score = int(self.config.get("pass_score", 75))
        self.session_limit.setValue(clamp_session_limit(self.config.get("session_limit", 20)))
        self.pass_score_spin.setValue(self.pass_score)
        self.max_follow_ups.setValue(int(self.config.get("max_follow_ups", 2)))
        self.auto_advance.setValue(max(0, int(self.config.get("auto_advance_ms", 1500)) // 1000))
        self.ollama_url.setText(self.config.get("ollama_url", ""))
        self.ollama_model.setText(self.config.get("model", ""))
        self.ollama_timeout.setValue(int(self.config.get("timeout", 120)))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("AI Anki")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        subtitle = QLabel("Выберите колоду и режим занятия. Прогресс и история ответов сохраняются локально.")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.summary_label = QLabel("")
        layout.addWidget(self.summary_label)

        settings_box = QGroupBox("Настройки")
        settings_layout = QHBoxLayout(settings_box)

        left_form = QFormLayout()
        self.session_limit = QSpinBox()
        self.session_limit.setRange(1, SESSION_LIMIT_MAX)
        self.session_limit.setToolTip(f"Сколько карточек максимум за одну сессию (до {SESSION_LIMIT_MAX})")
        left_form.addRow("Карточек за сессию", self.session_limit)

        self.pass_score_spin = QSpinBox()
        self.pass_score_spin.setRange(50, 100)
        self.pass_score_spin.setToolTip("Минимальная оценка для зачёта карточки")
        left_form.addRow("Порог зачёта", self.pass_score_spin)

        self.max_follow_ups = QSpinBox()
        self.max_follow_ups.setRange(0, 5)
        self.max_follow_ups.setToolTip("Сколько уточняющих вопросов от модели на карточку")
        left_form.addRow("Макс. уточнений", self.max_follow_ups)

        self.auto_advance = QSpinBox()
        self.auto_advance.setRange(0, 10)
        self.auto_advance.setSuffix(" с")
        self.auto_advance.setToolTip("Пауза перед автопереходом к следующей карточке (0 — выключено)")
        left_form.addRow("Автопереход", self.auto_advance)

        right_form = QFormLayout()
        self.ollama_url = QLineEdit()
        self.ollama_url.setPlaceholderText("http://host:port")
        right_form.addRow("Ollama URL", self.ollama_url)

        self.ollama_model = QLineEdit()
        right_form.addRow("Модель", self.ollama_model)

        self.ollama_timeout = QSpinBox()
        self.ollama_timeout.setRange(30, 600)
        self.ollama_timeout.setSuffix(" с")
        right_form.addRow("Таймаут", self.ollama_timeout)

        settings_layout.addLayout(left_form, 1)
        settings_layout.addLayout(right_form, 1)

        settings_btns = QVBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save_settings)
        test_btn = QPushButton("Проверить Ollama")
        test_btn.clicked.connect(self._test_ollama)
        settings_btns.addWidget(save_btn)
        settings_btns.addWidget(test_btn)
        settings_btns.addStretch()
        settings_layout.addLayout(settings_btns)

        layout.addWidget(settings_box)

        box = QGroupBox("Колоды")
        box_layout = QVBoxLayout(box)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Колода", "Всего", "Усвоено", "Сегодня", "К повтору", "Новые", "Слабые", "Ср. балл"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(lambda: self._start(StudyMode.DUE))
        box_layout.addWidget(self.table)

        layout.addWidget(box, 1)

        mode_row = QHBoxLayout()
        self.btn_due = QPushButton("Повторить (к сроку)")
        self.btn_due.setToolTip("Новые карточки и те, у которых наступило время повторения")
        self.btn_due.clicked.connect(lambda: self._start(StudyMode.DUE))
        self.btn_new = QPushButton("Только новые")
        self.btn_new.clicked.connect(lambda: self._start(StudyMode.NEW))
        self.btn_weak = QPushButton("Слабые места")
        self.btn_weak.clicked.connect(lambda: self._start(StudyMode.WEAK))
        self.btn_all = QPushButton("Вся колода")
        self.btn_all.clicked.connect(lambda: self._start(StudyMode.ALL))
        for btn in (self.btn_due, self.btn_new, self.btn_weak, self.btn_all):
            btn.setEnabled(False)
            mode_row.addWidget(btn)
        layout.addLayout(mode_row)

        bottom = QHBoxLayout()
        add_btn = QPushButton("Добавить колоду…")
        add_btn.clicked.connect(self._add_deck)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)
        bottom.addWidget(add_btn)
        bottom.addWidget(refresh_btn)
        bottom.addStretch()
        layout.addLayout(bottom)

    def _save_settings(self) -> None:
        self.config.update({
            "session_limit": self.session_limit.value(),
            "pass_score": self.pass_score_spin.value(),
            "max_follow_ups": self.max_follow_ups.value(),
            "auto_advance_ms": self.auto_advance.value() * 1000,
            "ollama_url": self.ollama_url.text().strip(),
            "model": self.ollama_model.text().strip(),
            "timeout": self.ollama_timeout.value(),
        })
        save_config(self.config_path, self.config)
        self.pass_score = int(self.config["pass_score"])
        self.config_saved.emit()
        self.refresh()
        QMessageBox.information(self, "Настройки", "Сохранено.")

    def _test_ollama(self) -> None:
        url = self.ollama_url.text().strip()
        model = self.ollama_model.text().strip()
        if not url or not model:
            QMessageBox.warning(self, "Ollama", "Укажите URL и модель.")
            return
        client = OllamaClient(
            url,
            model,
            timeout=self.ollama_timeout.value(),
            api_key=self.config.get("api_key", ""),
        )
        ok, detail = client.health()
        if ok:
            QMessageBox.information(self, "Ollama", detail)
        else:
            QMessageBox.warning(self, "Ollama", detail)

    def refresh(self) -> None:
        self.registry.load()
        self.progress.load()
        entries = self.registry.entries
        self.table.setRowCount(len(entries))

        total_cards = total_due = total_mastered = total_today = 0
        for row, entry in enumerate(entries):
            try:
                deck = self.registry.load_deck(entry)
                self.progress.reconcile_deck(deck, self.pass_score)
                s = self.progress.summary(deck, self.pass_score)
            except Exception as exc:  # noqa: BLE001
                deck = None
                s = None
                err = str(exc)
            name_item = QTableWidgetItem(entry.name)
            name_item.setData(Qt.ItemDataRole.UserRole, entry.deck_id)
            if s is None:
                name_item.setToolTip(err)
            self.table.setItem(row, 0, name_item)

            if s:
                total_cards += s.total
                total_due += s.due
                total_mastered += s.mastered
                total_today += s.passed_today
                vals = [
                    str(s.total),
                    f"{s.mastered} ({self._pct(s.mastered, s.total)}%)",
                    str(s.passed_today),
                    str(s.due),
                    str(s.new),
                    str(s.weak),
                    str(s.avg_score) if s.studied else "—",
                ]
                for col, text in enumerate(vals, start=1):
                    item = QTableWidgetItem(text)
                    if col == 3 and s.passed_today > 0:
                        item.setForeground(QColor("#2e7d32"))
                    if col == 4 and s.due > 0:
                        item.setForeground(QColor("#b8860b"))
                    if col == 6 and s.weak > 0:
                        item.setForeground(QColor("#c0392b"))
                    self.table.setItem(row, col, item)
            else:
                for col in range(1, 8):
                    self.table.setItem(row, col, QTableWidgetItem("—"))

        self.summary_label.setText(
            f"Колод: {len(entries)} · карточек: {total_cards} · "
            f"усвоено: {total_mastered} · сегодня пройдено: {total_today} · к повтору: {total_due}"
        )
        if entries:
            self.table.selectRow(0)

    @staticmethod
    def _pct(part: int, whole: int) -> int:
        if whole <= 0:
            return 0
        return round(part * 100 / whole)

    def _on_select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_entry = None
            for btn in (self.btn_due, self.btn_new, self.btn_weak, self.btn_all):
                btn.setEnabled(False)
            return
        deck_id = self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        self._selected_entry = self.registry.get(deck_id)
        for btn in (self.btn_due, self.btn_new, self.btn_weak, self.btn_all):
            btn.setEnabled(self._selected_entry is not None)

    def _start(self, mode: StudyMode) -> None:
        if not self._selected_entry:
            rows = self.table.selectionModel().selectedRows()
            if rows:
                deck_id = self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
                self._selected_entry = self.registry.get(deck_id)
        if not self._selected_entry:
            QMessageBox.information(self, "Колода", "Выберите колоду в таблице.")
            return
        self.deck_selected.emit(self._selected_entry, mode.value)

    def _add_deck(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Добавить колоду",
            str(self.decks_dir),
            "Колоды (*.json *.txt);;JSON (*.json);;Anki TXT (*.txt)",
        )
        if not path:
            return
        try:
            self.registry.register_file(path)
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))
