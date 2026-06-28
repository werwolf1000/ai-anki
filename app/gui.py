from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.deck import Card, ChatMessage, Deck
from app.ollama_client import AnswerEvaluator, OllamaClient
from app.progress import ProgressStore


class EvaluateWorker(QThread):
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, evaluator: AnswerEvaluator, card: Card, answer: str, history: list[ChatMessage], is_follow_up: bool):
        super().__init__()
        self.evaluator = evaluator
        self.card = card
        self.answer = answer
        self.history = history
        self.is_follow_up = is_follow_up

    def run(self) -> None:
        try:
            result = self.evaluator.evaluate(
                self.card,
                self.answer,
                self.history,
                is_follow_up=self.is_follow_up,
            )
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Anki — Ollama")
        self.resize(960, 780)

        self.config_path = Path(__file__).resolve().parent.parent / "config.json"
        self.config = self._load_config()
        self.deck: Deck | None = None
        self.queue: list = []
        self.current_index = 0
        self.current_card: Card | None = None
        self.chat_history: list[ChatMessage] = []
        self.awaiting_follow_up = False
        self.last_review = None
        self.worker: EvaluateWorker | None = None

        self.progress_store = ProgressStore(Path.home() / ".ai-anki" / "progress.json")
        self.progress_store.load()

        self._build_ui()
        self._load_default_deck()

    def _load_config(self) -> dict:
        defaults = {
            "ollama_url": "https://ollama.webmastermsk.ru:330068",
            "model": "qwen3-code:30b",
            "pass_score": 75,
            "timeout": 120,
        }
        if self.config_path.exists():
            defaults.update(json.loads(self.config_path.read_text(encoding="utf-8")))
        return defaults

    def _save_config(self) -> None:
        self.config = {
            "ollama_url": self.url_edit.text().strip(),
            "model": self.model_edit.text().strip(),
            "pass_score": self.pass_score.value(),
            "timeout": self.timeout_spin.value(),
        }
        self.config_path.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        settings = QGroupBox("Ollama")
        form = QFormLayout(settings)
        self.url_edit = QLineEdit(self.config["ollama_url"])
        self.model_edit = QLineEdit(self.config["model"])
        self.pass_score = QSpinBox()
        self.pass_score.setRange(50, 100)
        self.pass_score.setValue(int(self.config.get("pass_score", 75)))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 600)
        self.timeout_spin.setValue(int(self.config.get("timeout", 120)))
        form.addRow("URL", self.url_edit)
        form.addRow("Модель", self.model_edit)
        form.addRow("Порог «усвоено»", self.pass_score)
        form.addRow("Таймаут (с)", self.timeout_spin)
        layout.addWidget(settings)

        deck_row = QHBoxLayout()
        self.deck_label = QLabel("Колода не загружена")
        load_btn = QPushButton("Открыть колоду…")
        load_btn.clicked.connect(self._load_deck_dialog)
        test_btn = QPushButton("Проверить Ollama")
        test_btn.clicked.connect(self._test_ollama)
        deck_row.addWidget(self.deck_label, 1)
        deck_row.addWidget(load_btn)
        deck_row.addWidget(test_btn)
        layout.addLayout(deck_row)

        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)

        q_box = QGroupBox("Вопрос")
        q_layout = QVBoxLayout(q_box)
        self.question_view = QTextEdit()
        self.question_view.setReadOnly(True)
        self.question_view.setMaximumHeight(120)
        font = QFont()
        font.setPointSize(12)
        self.question_view.setFont(font)
        q_layout.addWidget(self.question_view)
        layout.addWidget(q_box)

        a_box = QGroupBox("Ваш ответ (своими словами)")
        a_layout = QVBoxLayout(a_box)
        self.answer_edit = QTextEdit()
        self.answer_edit.setPlaceholderText("Напишите ответ… Enter+Ctrl — отправить")
        self.answer_edit.setMaximumHeight(140)
        a_layout.addWidget(self.answer_edit)
        layout.addWidget(a_box)

        btn_row = QHBoxLayout()
        self.submit_btn = QPushButton("Проверить ответ")
        self.submit_btn.clicked.connect(self._submit_answer)
        self.hint_btn = QPushButton("Подсказка")
        self.hint_btn.clicked.connect(self._show_hint)
        self.hint_btn.setEnabled(False)
        self.next_btn = QPushButton("Следующая карточка →")
        self.next_btn.clicked.connect(self._next_card)
        self.next_btn.setEnabled(False)
        btn_row.addWidget(self.submit_btn)
        btn_row.addWidget(self.hint_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.next_btn)
        layout.addLayout(btn_row)

        f_box = QGroupBox("Обратная связь / диалог")
        f_layout = QVBoxLayout(f_box)
        self.feedback_view = QTextEdit()
        self.feedback_view.setReadOnly(True)
        f_layout.addWidget(self.feedback_view)
        layout.addWidget(f_box, 1)

        self.status_label = QLabel("Загрузите колоду и ответьте на вопрос.")
        layout.addWidget(self.status_label)

    def _load_default_deck(self) -> None:
        sample = Path(__file__).resolve().parent.parent / "decks" / "angular-sample.json"
        anki = Path.home() / "Documents" / "anki-angular.txt"
        if anki.exists():
            self._load_deck_path(anki)
        elif sample.exists():
            self._load_deck_path(sample)

    def _load_deck_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Колода",
            str(Path.home() / "Documents"),
            "Колоды (*.json *.txt);;JSON (*.json);;Anki TXT (*.txt)",
        )
        if path:
            self._load_deck_path(path)

    def _load_deck_path(self, path: str) -> None:
        try:
            p = Path(path)
            if p.suffix.lower() == ".json":
                self.deck = Deck.load_json(p)
            else:
                self.deck = Deck.load_anki_txt(p)
            if not self.deck.cards:
                raise ValueError("Колода пуста")
            self.queue = self.progress_store.next_cards(self.deck)
            self.current_index = 0
            self.deck_label.setText(f"Колода: {self.deck.name} ({len(self.deck.cards)} карточек)")
            self._show_current_card()
            self._update_stats()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _client(self) -> OllamaClient:
        return OllamaClient(
            self.url_edit.text().strip(),
            self.model_edit.text().strip(),
            timeout=self.timeout_spin.value(),
        )

    def _evaluator(self) -> AnswerEvaluator:
        return AnswerEvaluator(self._client())

    def _test_ollama(self) -> None:
        self._save_config()
        self.status_label.setText("Проверка Ollama…")
        try:
            ok = self._client().health()
            if ok:
                QMessageBox.information(self, "OK", "Ollama доступна")
                self.status_label.setText("Ollama доступна")
            else:
                QMessageBox.warning(self, "Ошибка", "Ollama не ответила на /api/tags")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))

    def _show_current_card(self) -> None:
        if not self.queue:
            self.question_view.setPlainText("Нет карточек.")
            return
        self.current_card = self.queue[self.current_index]
        self.chat_history = []
        self.awaiting_follow_up = False
        self.last_review = None
        self.question_view.setPlainText(self.current_card.question)
        self.answer_edit.clear()
        self.feedback_view.clear()
        self.submit_btn.setEnabled(True)
        self.hint_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.status_label.setText(f"Карточка {self.current_index + 1}/{len(self.queue)}")

    def _update_stats(self) -> None:
        if not self.deck:
            return
        mastered = sum(
            1 for c in self.deck.cards if self.progress_store.get(self.deck, c.id).mastered
        )
        self.stats_label.setText(f"Усвоено: {mastered}/{len(self.deck.cards)}")

    def _set_busy(self, busy: bool) -> None:
        self.submit_btn.setEnabled(not busy)
        self.next_btn.setEnabled(not busy and self.last_review is not None)
        if busy:
            self.status_label.setText("Ollama думает…")

    def _submit_answer(self) -> None:
        if not self.current_card:
            return
        answer = self.answer_edit.toPlainText().strip()
        if not answer:
            QMessageBox.warning(self, "Пусто", "Напишите ответ.")
            return
        self._save_config()
        self._set_busy(True)
        self.worker = EvaluateWorker(
            self._evaluator(),
            self.current_card,
            answer,
            self.chat_history.copy(),
            self.awaiting_follow_up,
        )
        self.worker.finished_ok.connect(self._on_review)
        self.worker.failed.connect(self._on_review_failed)
        self.worker.start()

    def _on_review_failed(self, message: str) -> None:
        self._set_busy(False)
        self.feedback_view.append(f"❌ Ошибка: {message}")
        self.status_label.setText("Ошибка запроса к Ollama")

    def _on_review(self, result) -> None:
        self._set_busy(False)
        self.last_review = result

        user_text = self.answer_edit.toPlainText().strip()
        self.chat_history.append(ChatMessage("user", user_text))
        self.chat_history.append(ChatMessage("assistant", result.feedback))

        lines = [
            f"Оценка: {result.score}/100",
            "",
            result.feedback,
        ]
        if result.hint:
            lines.extend(["", f"💡 Подсказка: {result.hint}"])
        if result.follow_up:
            lines.extend(["", f"❓ Уточнение: {result.follow_up}", "(Ответьте на уточнение и нажмите «Проверить ответ»)"])
            self.awaiting_follow_up = True
        else:
            self.awaiting_follow_up = False

        if result.correct and not result.follow_up:
            lines.extend(["", "✅ Карточка усвоена!"])
        elif not result.correct:
            lines.extend(["", "Попробуйте ответить ещё раз или нажмите «Подсказка»."])

        self.feedback_view.setPlainText("\n".join(lines))
        self.hint_btn.setEnabled(bool(result.hint or result.reference_summary))
        self.next_btn.setEnabled(True)

        if self.deck and self.current_card and not self.awaiting_follow_up:
            prog = self.progress_store.get(self.deck, self.current_card.id)
            prog.attempts += 1
            prog.last_score = result.score
            prog.best_score = max(prog.best_score, result.score)
            self.progress_store.update(self.deck, prog, self.pass_score.value())
            self._update_stats()

        self.answer_edit.clear()
        if self.awaiting_follow_up:
            self.answer_edit.setPlaceholderText("Ответ на уточняющий вопрос…")
            self.status_label.setText("Ответьте на уточняющий вопрос")
        else:
            self.answer_edit.setPlaceholderText("Напишите ответ…")
            self.status_label.setText("Готово. Следующая карточка или повторите ответ.")

    def _show_hint(self) -> None:
        if not self.last_review:
            return
        hint = self.last_review.hint or self.last_review.reference_summary
        if hint:
            self.feedback_view.append(f"\n\n💡 Дополнительно: {hint}")
        elif self.current_card:
            ref = self.current_card.reference[:200]
            self.feedback_view.append(f"\n\n📖 Начало эталона: {ref}…")

    def _next_card(self) -> None:
        if not self.queue:
            return
        self.current_index = (self.current_index + 1) % len(self.queue)
        self.queue = self.progress_store.next_cards(self.deck)
        if self.current_index >= len(self.queue):
            self.current_index = 0
        self._show_current_card()
        self._update_stats()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Return:
            self._submit_answer()
            return
        super().keyPressEvent(event)


def run_app() -> None:
    app = QApplication([])
    app.setApplicationName("AI Anki")
    window = MainWindow()
    window.show()
    app.exec()
