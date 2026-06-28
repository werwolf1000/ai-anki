from __future__ import annotations

from pathlib import Path

from app.config_store import clamp_session_limit, load_config, save_config

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.code_editor import CodeEditorPanel
from app.deck import Card, ChatMessage, Deck
from app.ollama_client import AnswerEvaluator, OllamaClient
from app.progress import ProgressStore, StudyMode
from app.registry import DeckEntry, DeckRegistry
from app.welcome import WelcomeScreen


class EvaluateWorker(QThread):
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        evaluator: AnswerEvaluator,
        card: Card,
        answer: str,
        history: list[ChatMessage],
        is_follow_up: bool,
        follow_ups_remaining: int,
        deck_name: str = "",
    ):
        super().__init__()
        self.evaluator = evaluator
        self.card = card
        self.answer = answer
        self.history = history
        self.is_follow_up = is_follow_up
        self.follow_ups_remaining = follow_ups_remaining
        self.deck_name = deck_name

    def run(self) -> None:
        try:
            result = self.evaluator.evaluate(
                self.card,
                self.answer,
                self.history,
                is_follow_up=self.is_follow_up,
                follow_ups_remaining=self.follow_ups_remaining,
                deck_name=self.deck_name,
            )
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class HintWorker(QThread):
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        evaluator: AnswerEvaluator,
        card: Card,
        deck_name: str,
        draft: str,
        *,
        from_review: bool = False,
        review_hint: str = "",
    ):
        super().__init__()
        self.evaluator = evaluator
        self.card = card
        self.deck_name = deck_name
        self.draft = draft
        self.from_review = from_review
        self.review_hint = review_hint

    def run(self) -> None:
        try:
            if self.from_review and self.review_hint:
                self.finished_ok.emit(self.review_hint)
                return
            hint = self.evaluator.request_hint(
                self.card,
                deck_name=self.deck_name,
                user_draft=self.draft,
            )
            self.finished_ok.emit(hint)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class HistoryDialog(QDialog):
    def __init__(self, parent: QWidget, card: Card, records: list) -> None:
        super().__init__(parent)
        self.setWindowTitle("История ответов")
        self.resize(640, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Карточка: {card.question[:120]}…" if len(card.question) > 120 else f"Карточка: {card.question}"))
        view = QTextEdit()
        view.setReadOnly(True)
        if not records:
            view.setPlainText("Пока нет сохранённых ответов.")
        else:
            blocks = []
            for i, rec in enumerate(reversed(records), 1):
                ts = rec.at[:19].replace("T", " ") if rec.at else "?"
                kind = "уточнение" if rec.is_follow_up else "ответ"
                blocks.append(
                    f"── #{len(records) - i + 1} · {ts} · {kind} · {rec.score}/100 ──\n"
                    f"{rec.answer[:800]}\n\n"
                    f"Отзыв: {rec.feedback}\n"
                )
            view.setPlainText("\n".join(blocks))
        layout.addWidget(view)
        close = QPushButton("Закрыть")
        close.clicked.connect(self.accept)
        layout.addWidget(close)


class StudyScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(
        self,
        deck: Deck,
        mode: StudyMode,
        progress_store: ProgressStore,
        config: dict,
        config_path: Path,
    ) -> None:
        super().__init__()
        self.deck = deck
        self.mode = mode
        self.progress_store = progress_store
        self.config = config
        self.config_path = config_path
        self.queue: list[Card] = []
        self.current_index = 0
        self.current_card: Card | None = None
        self.chat_history: list[ChatMessage] = []
        self.awaiting_follow_up = False
        self.follow_up_count = 0
        self.revision_count = 0
        self.last_review = None
        self.worker: EvaluateWorker | None = None
        self.hint_worker: HintWorker | None = None
        self._advance_timer = QTimer(self)
        self._advance_timer.setSingleShot(True)
        self._advance_timer.timeout.connect(self._next_card)
        self._pending_finalize = False
        self._build_ui()
        self._start_session()

    def _pass_score(self) -> int:
        return int(self.config.get("pass_score", 75))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        back_btn = QPushButton("← Колоды")
        back_btn.clicked.connect(self.back_requested.emit)
        self.deck_label = QLabel("")
        self.stats_label = QLabel("")
        history_btn = QPushButton("История карточки")
        history_btn.clicked.connect(self._show_card_history)
        settings_btn = QPushButton("Ollama…")
        settings_btn.clicked.connect(self._show_settings)
        top.addWidget(back_btn)
        top.addWidget(self.deck_label, 1)
        top.addWidget(self.stats_label)
        top.addWidget(history_btn)
        top.addWidget(settings_btn)
        layout.addLayout(top)

        q_box = QGroupBox("Вопрос")
        q_layout = QVBoxLayout(q_box)
        self.question_view = QTextEdit()
        self.question_view.setReadOnly(True)
        self.question_view.setMinimumHeight(120)
        self.question_view.setMaximumHeight(280)
        font = QFont("Monospace")
        font.setPointSize(11)
        self.question_view.setFont(font)
        q_layout.addWidget(self.question_view)
        layout.addWidget(q_box)

        self.answer_box = QGroupBox("Ваш ответ")
        a_layout = QVBoxLayout(self.answer_box)
        self.answer_edit = QTextEdit()
        self.answer_edit.setPlaceholderText("Напишите ответ… Ctrl+Enter — отправить")
        self.answer_edit.setMinimumHeight(100)
        self.answer_edit.setMaximumHeight(220)
        a_layout.addWidget(self.answer_edit)
        QShortcut(QKeySequence("Ctrl+Return"), self.answer_edit, self._submit_answer)

        self.code_panel = CodeEditorPanel()
        self.code_panel.setMinimumHeight(160)
        self.code_panel.setMaximumHeight(360)
        self.code_panel.submit_requested.connect(self._submit_answer)
        self.code_panel.hide()
        a_layout.addWidget(self.code_panel)

        layout.addWidget(self.answer_box)

        btn_row = QHBoxLayout()
        self.submit_btn = QPushButton("Проверить ответ")
        self.submit_btn.clicked.connect(self._submit_answer)
        self.hint_btn = QPushButton("Подсказка")
        self.hint_btn.clicked.connect(self._show_hint)
        self.next_btn = QPushButton("Следующая →")
        self.next_btn.clicked.connect(self._next_card)
        self.next_btn.setEnabled(False)
        btn_row.addWidget(self.submit_btn)
        btn_row.addWidget(self.hint_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.next_btn)
        layout.addLayout(btn_row)

        f_box = QGroupBox("Обратная связь")
        f_layout = QVBoxLayout(f_box)
        self.feedback_view = QTextEdit()
        self.feedback_view.setReadOnly(True)
        f_layout.addWidget(self.feedback_view)
        layout.addWidget(f_box, 1)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def _mode_label(self) -> str:
        return {
            StudyMode.DUE: "повторение",
            StudyMode.NEW: "новые",
            StudyMode.WEAK: "слабые",
            StudyMode.ALL: "вся колода",
        }.get(self.mode, "")

    def _start_session(self) -> None:
        self.progress_store.load()
        self.progress_store.reconcile_deck(self.deck, self._pass_score())
        self.queue = self.progress_store.build_queue(
            self.deck,
            self.mode,
            pass_score=self._pass_score(),
            limit=clamp_session_limit(self.config.get("session_limit", 20)),
        )
        self.current_index = 0
        code_n = sum(1 for c in self.deck.cards if c.is_code)
        extra = f", код: {code_n}" if code_n else ""
        self.deck_label.setText(f"{self.deck.name} · {self._mode_label()}")
        s = self.progress_store.summary(self.deck, self._pass_score())
        self.stats_label.setText(
            f"Сегодня {s.passed_today} · Усвоено {s.mastered}/{s.total}{extra} · "
            f"к повтору {s.due} · сессия {len(self.queue)}"
        )
        if not self.queue:
            self.question_view.setPlainText("Нет карточек для выбранного режима.\nВернитесь и выберите другой режим.")
            self.submit_btn.setEnabled(False)
            self.status_label.setText("Очередь пуста")
            return
        self._show_current_card()

    def _max_follow_ups(self) -> int:
        return int(self.config.get("max_follow_ups", 2))

    def _client(self) -> OllamaClient:
        return OllamaClient(
            self.config["ollama_url"],
            self.config["model"],
            timeout=int(self.config.get("timeout", 120)),
            api_key=self.config.get("api_key", ""),
        )

    def _evaluator(self) -> AnswerEvaluator:
        return AnswerEvaluator(self._client())

    def _show_settings(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Ollama")
        form = QFormLayout(dlg)
        url = QLineEdit(self.config.get("ollama_url", ""))
        model = QLineEdit(self.config.get("model", ""))
        api_key = QLineEdit(self.config.get("api_key", ""))
        api_key.setEchoMode(QLineEdit.EchoMode.Password)
        pass_score = QSpinBox()
        pass_score.setRange(50, 100)
        pass_score.setValue(self._pass_score())
        timeout = QSpinBox()
        timeout.setRange(30, 600)
        timeout.setValue(int(self.config.get("timeout", 120)))
        max_fu = QSpinBox()
        max_fu.setRange(0, 5)
        max_fu.setValue(self._max_follow_ups())
        form.addRow("URL", url)
        form.addRow("Модель", model)
        form.addRow("API-ключ", api_key)
        form.addRow("Порог «усвоено»", pass_score)
        form.addRow("Таймаут (с)", timeout)
        form.addRow("Макс. уточнений", max_fu)
        row = QHBoxLayout()
        test = QPushButton("Проверить")
        save = QPushButton("Сохранить")
        row.addWidget(test)
        row.addWidget(save)
        form.addRow(row)

        def do_save() -> None:
            self.config.update({
                "ollama_url": url.text().strip(),
                "model": model.text().strip(),
                "api_key": api_key.text().strip(),
                "pass_score": pass_score.value(),
                "timeout": timeout.value(),
                "max_follow_ups": max_fu.value(),
            })
            save_config(self.config_path, self.config)
            dlg.accept()

        def do_test() -> None:
            c = OllamaClient(url.text().strip(), model.text().strip(), timeout=timeout.value(), api_key=api_key.text().strip())
            ok, detail = c.health()
            QMessageBox.information(dlg, "Ollama", detail if ok else detail)

        save.clicked.connect(do_save)
        test.clicked.connect(do_test)
        dlg.exec()

    def _show_card_history(self) -> None:
        if not self.current_card:
            return
        records = self.progress_store.card_history(self.deck, self.current_card.id)
        HistoryDialog(self, self.current_card, records).exec()

    def _show_current_card(self) -> None:
        self._cancel_auto_advance()
        if not self.queue:
            return
        self.current_card = self.queue[self.current_index]
        self.chat_history = []
        self.awaiting_follow_up = False
        self.follow_up_count = 0
        self.revision_count = 0
        self.last_review = None
        self._pending_finalize = False
        prog = self.progress_store.get(self.deck, self.current_card.id)
        self.question_view.setPlainText(self.current_card.display_text())
        self._configure_answer_ui(self.current_card)
        self._clear_answer()
        self.feedback_view.clear()
        self.submit_btn.setEnabled(True)
        self.hint_btn.setEnabled(True)
        self.next_btn.setEnabled(False)
        due_hint = ""
        if prog.attempts > 0 and prog.due_at:
            due_hint = f" · повтор через {max(0, round(prog.days_until_due(), 1))} д"
        self.status_label.setText(
            f"{self.current_index + 1}/{len(self.queue)} · "
            f"лучший {prog.best_score} · попыток {prog.attempts}{due_hint}"
        )

    def _configure_answer_ui(self, card: Card) -> None:
        if card.needs_code_editor:
            self.answer_edit.hide()
            self.code_panel.show()
            if card.is_live_code:
                self.answer_box.setTitle("Редактор кода — напишите решение")
            else:
                self.answer_box.setTitle("Редактор кода — исправьте или дополните")
            self.code_panel.set_language_hint(card.language)
            self.code_panel.set_focus()
        else:
            self.code_panel.hide()
            self.answer_edit.show()
            self.answer_box.setTitle("Ваш ответ (своими словами)")
            self.answer_edit.setPlaceholderText("Напишите ответ… Ctrl+Enter — отправить")
            self.answer_edit.setFocus()

    def _answer_text(self) -> str:
        if self.current_card and self.current_card.needs_code_editor:
            return self.code_panel.plain_text().strip()
        return self.answer_edit.toPlainText().strip()

    def _clear_answer(self) -> None:
        if self.current_card and self.current_card.needs_code_editor:
            self.code_panel.clear()
        else:
            self.answer_edit.clear()

    def _cancel_auto_advance(self) -> None:
        if self._advance_timer.isActive():
            self._advance_timer.stop()

    def _schedule_auto_advance(self) -> None:
        delay = int(self.config.get("auto_advance_ms", 10000))
        self._cancel_auto_advance()
        if delay <= 0:
            self.status_label.setText("Нажмите «Следующая →» для продолжения.")
            return
        self.status_label.setText(f"Следующая карточка через {delay // 1000} с…")
        self._advance_timer.start(delay)

    def _set_busy(self, busy: bool) -> None:
        self.submit_btn.setEnabled(not busy)
        self.hint_btn.setEnabled(not busy and self.current_card is not None)
        self.next_btn.setEnabled(not busy and self.last_review is not None)
        if busy:
            self._cancel_auto_advance()
            self.status_label.setText("Ollama думает…")

    def _submit_answer(self) -> None:
        if not self.current_card:
            return
        answer = self._answer_text()
        if not answer:
            label = "Напишите код." if self.current_card.needs_code_editor else "Напишите ответ."
            QMessageBox.warning(self, "Пусто", label)
            return
        max_fu = self._max_follow_ups()
        remaining = max(0, max_fu - self.follow_up_count)
        self._set_busy(True)
        self.worker = EvaluateWorker(
            self._evaluator(),
            self.current_card,
            answer,
            self.chat_history.copy(),
            self.awaiting_follow_up,
            remaining,
            self.deck.name,
        )
        self.worker.finished_ok.connect(self._on_review)
        self.worker.failed.connect(self._on_review_failed)
        self.worker.start()

    def _on_review_failed(self, message: str) -> None:
        self._set_busy(False)
        self.feedback_view.setPlainText(f"❌ Ошибка: {message}")

    def _on_review(self, result) -> None:
        self._set_busy(False)
        self.last_review = result
        was_follow_up_answer = self.awaiting_follow_up
        user_text = self._answer_text()
        self.chat_history.append(ChatMessage("user", user_text))
        self.chat_history.append(ChatMessage("assistant", result.feedback))

        max_fu = self._max_follow_ups()
        lines = [f"Оценка: {result.score}/100", "", result.feedback]

        passed = result.score >= self._pass_score()
        interactions = self.follow_up_count + self.revision_count
        finalize = True

        if result.follow_up and self.follow_up_count < max_fu:
            self.follow_up_count += 1
            lines.extend(["", f"❓ Уточнение ({self.follow_up_count}/{max_fu}): {result.follow_up}"])
            self.awaiting_follow_up = True
            finalize = False
        elif (
            not passed
            and self.current_card
            and self.current_card.needs_code_editor
            and interactions < max_fu
        ):
            self.revision_count += 1
            self.awaiting_follow_up = False
            lines.extend([
                "",
                f"✏️ Исправьте код и отправьте снова "
                f"({self.revision_count}/{max_fu} · осталось {max_fu - self.follow_up_count - self.revision_count})",
            ])
            finalize = False
        else:
            if result.follow_up and self.follow_up_count >= max_fu:
                lines.extend([
                    "",
                    f"ℹ️ Лимит уточнений ({max_fu}) исчерпан — карточка завершена.",
                ])
            elif (
                not passed
                and self.current_card
                and self.current_card.needs_code_editor
                and interactions >= max_fu
            ):
                lines.extend([
                    "",
                    f"ℹ️ Лимит правок ({max_fu}) исчерпан — карточка завершена.",
                ])
            self.awaiting_follow_up = False

        if finalize:
            if passed:
                lines.extend(["", "✅ Засчитано! Следующее повторение по расписанию."])
            else:
                lines.extend(["", "↻ Карточка вернётся в повторение через несколько минут."])

        self.feedback_view.setPlainText("\n".join(lines))
        self.hint_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.submit_btn.setEnabled(not finalize)

        prog = None
        if self.current_card:
            prog = self.progress_store.record_answer(
                self.deck,
                self.current_card.id,
                answer=user_text,
                score=result.score,
                correct=passed,
                feedback=result.feedback,
                pass_score=self._pass_score(),
                is_follow_up=was_follow_up_answer,
                finalize=finalize,
            )
            s = self.progress_store.summary(self.deck, self._pass_score())
            self.stats_label.setText(
                f"Сегодня {s.passed_today} · Усвоено {s.mastered}/{s.total} · "
                f"к повтору {s.due} · сессия {len(self.queue)}"
            )
            if prog and finalize:
                self.status_label.setText(
                    f"Сохранено · оценка {prog.last_score} · "
                    f"лучший {prog.best_score} · попыток {prog.attempts}"
                )

        if finalize:
            self._clear_answer()
        self._pending_finalize = finalize

        if finalize and passed:
            self._schedule_auto_advance()
        elif not finalize:
            self.status_label.setText("Внесите правки и нажмите «Проверить ответ» или «Следующая →».")

    def _append_hint(self, hint: str) -> None:
        if not hint:
            return
        text = self.feedback_view.toPlainText()
        if hint in text:
            return
        if text.strip():
            self.feedback_view.append(f"\n\n💡 {hint}")
        else:
            self.feedback_view.setPlainText(f"💡 {hint}")

    def _show_hint(self) -> None:
        if not self.current_card:
            return
        review_hint = ""
        from_review = False
        if self.last_review:
            review_hint = self.last_review.hint or self.last_review.reference_summary
            from_review = bool(review_hint)
        self._set_busy(True)
        self.hint_worker = HintWorker(
            self._evaluator(),
            self.current_card,
            self.deck.name,
            self._answer_text(),
            from_review=from_review,
            review_hint=review_hint,
        )
        self.hint_worker.finished_ok.connect(self._on_hint)
        self.hint_worker.failed.connect(self._on_hint_failed)
        self.hint_worker.start()

    def _on_hint(self, hint: str) -> None:
        self._set_busy(False)
        self._append_hint(hint)
        if not self.last_review:
            self.status_label.setText("Подсказка получена. Отправьте ответ, когда будете готовы.")

    def _on_hint_failed(self, message: str) -> None:
        self._set_busy(False)
        self.feedback_view.append(f"\n\n❌ Подсказка: {message}")

    def _next_card(self) -> None:
        self._cancel_auto_advance()
        if not self.queue:
            self.back_requested.emit()
            return

        if self._pending_finalize:
            self._pending_finalize = False
            if self.current_index < len(self.queue):
                self.queue.pop(self.current_index)
            self._update_session_stats()
        else:
            self.current_index += 1

        if self.current_index >= len(self.queue):
            self._end_session()
            return
        self._show_current_card()

    def _update_session_stats(self) -> None:
        s = self.progress_store.summary(self.deck, self._pass_score())
        self.stats_label.setText(
            f"Сегодня {s.passed_today} · Усвоено {s.mastered}/{s.total} · "
            f"к повтору {s.due} · сессия {len(self.queue)}"
        )

    def _end_session(self) -> None:
        s = self.progress_store.summary(self.deck, self._pass_score())
        QMessageBox.information(
            self,
            "Сессия завершена",
            f"К повтору в колоде: {s.due}\n\n"
            "Вернитесь на главный экран для новой сессии.",
        )
        self.back_requested.emit()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Anki")
        self.resize(980, 800)

        base = Path(__file__).resolve().parent.parent
        self.config, self.config_path = load_config(base)
        data_dir = Path.home() / ".ai-anki"
        self.progress_store = ProgressStore(data_dir / "progress.json")
        self.progress_store.load()
        self.registry = DeckRegistry(data_dir / "decks.json", base / "decks")
        self.registry.load()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome = WelcomeScreen(
            self.registry,
            self.progress_store,
            self.config,
            self.config_path,
            base / "decks",
        )
        self.welcome.deck_selected.connect(self._open_study)
        self.welcome.config_saved.connect(self._reload_config)
        self.stack.addWidget(self.welcome)

        self.study_screen: StudyScreen | None = None

    def _reload_config(self) -> None:
        base = Path(__file__).resolve().parent.parent
        self.config, self.config_path = load_config(base)

    def _open_study(self, entry: DeckEntry, mode_value: str) -> None:
        try:
            deck = self.registry.load_deck(entry)
            mode = StudyMode(mode_value)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка", str(exc))
            return

        if self.study_screen is not None:
            self.stack.removeWidget(self.study_screen)
            self.study_screen.deleteLater()

        self.config, self.config_path = load_config(Path(__file__).resolve().parent.parent)
        self.progress_store.load()
        self.study_screen = StudyScreen(deck, mode, self.progress_store, self.config, self.config_path)
        self.study_screen.back_requested.connect(self._go_home)
        self.stack.addWidget(self.study_screen)
        self.stack.setCurrentWidget(self.study_screen)

    def _go_home(self) -> None:
        if self.study_screen is not None:
            self.progress_store.save()
            self.stack.removeWidget(self.study_screen)
            self.study_screen.deleteLater()
            self.study_screen = None
        self.config, self.config_path = load_config(Path(__file__).resolve().parent.parent)
        self.welcome.config = self.config
        self.welcome.config_path = self.config_path
        self.welcome.sync_from_config()
        self.welcome.refresh()
        self.stack.setCurrentWidget(self.welcome)


def run_app() -> None:
    app = QApplication([])
    app.setApplicationName("AI Anki")
    window = MainWindow()
    window.show()
    app.exec()
