from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QLabel, QPlainTextEdit, QSizePolicy, QVBoxLayout, QWidget

_ASSETS = Path(__file__).resolve().parent / "assets"
_EDITOR_HTML = _ASSETS / "math_editor.html"
_QUESTION_HTML = _ASSETS / "math_question.html"


def _web_engine_types():
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    return QWebEngineView, QWebEngineSettings


def _configure_web_settings(view) -> None:
    _, QWebEngineSettings = _web_engine_types()
    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)


class _EditorBridge(QObject):
    submit_requested = pyqtSignal()
    latex_changed = pyqtSignal(str)
    ready = pyqtSignal()
    keyboard_height_changed = pyqtSignal(int)

    @pyqtSlot()
    def requestSubmit(self) -> None:
        self.submit_requested.emit()

    @pyqtSlot(str)
    def onLatexChanged(self, latex: str) -> None:
        self.latex_changed.emit(latex)

    @pyqtSlot()
    def editorReady(self) -> None:
        self.ready.emit()

    @pyqtSlot(int)
    def onKeyboardHeightChanged(self, height: int) -> None:
        self.keyboard_height_changed.emit(max(0, int(height)))


class _QuestionBridge(QObject):
    ready = pyqtSignal()

    @pyqtSlot()
    def viewReady(self) -> None:
        self.ready.emit()


class MathEditorPanel(QWidget):
    """MathLive + KaTeX preview — same stack as the web version."""

    submit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        QWebEngineView, _ = _web_engine_types()
        self._latex = ""
        self._ready = False
        self._pending_text = ""
        self._page_loaded = False
        self._base_view_height = 200
        self._keyboard_height = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view = QWebEngineView(self)
        self._view.setMinimumHeight(self._base_view_height)
        self._view.setFixedHeight(self._base_view_height)
        self._view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _configure_web_settings(self._view)

        self._bridge = _EditorBridge()
        self._bridge.submit_requested.connect(self.submit_requested.emit)
        self._bridge.latex_changed.connect(self._store_latex)
        self._bridge.ready.connect(self._on_ready)
        self._bridge.keyboard_height_changed.connect(self._on_keyboard_height)

        channel = QWebChannel(self)
        channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(channel)
        self._view.loadFinished.connect(self._on_load_finished)

        layout.addWidget(self._view)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._page_loaded:
            self._page_loaded = True
            self._view.load(QUrl.fromLocalFile(str(_EDITOR_HTML)))

    def _store_latex(self, latex: str) -> None:
        self._latex = latex or ""

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            self._latex = ""

    def _on_ready(self) -> None:
        self._ready = True
        if self._pending_text:
            self.set_text(self._pending_text)
            self._pending_text = ""

    def _on_keyboard_height(self, height: int) -> None:
        self._keyboard_height = max(0, int(height))
        total = self._base_view_height + self._keyboard_height
        self._view.setFixedHeight(total)
        self.setMinimumHeight(total)
        self.updateGeometry()

    def _run_js(self, script: str) -> None:
        if self._ready:
            self._view.page().runJavaScript(script)

    def plain_text(self) -> str:
        return self._latex.strip()

    def set_text(self, text: str) -> None:
        value = text or ""
        if not self._ready:
            self._pending_text = value
            self._latex = value
            return
        payload = json.dumps(value)
        self._run_js(f"window.MathEditor && window.MathEditor.setValue({payload})")
        self._latex = value

    def clear(self) -> None:
        self.set_text("")

    def set_focus(self) -> None:
        self._view.setFocus()
        self._run_js("window.MathEditor && window.MathEditor.focus()")


class MathQuestionView(QWidget):
    """KaTeX rendering for math card questions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        QWebEngineView, _ = _web_engine_types()
        self._ready = False
        self._pending = ""
        self._page_loaded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view = QWebEngineView(self)
        self._view.setMinimumHeight(120)
        self._view.setMaximumHeight(260)
        _configure_web_settings(self._view)

        self._bridge = _QuestionBridge()
        self._bridge.ready.connect(self._on_ready)

        channel = QWebChannel(self)
        channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(channel)

        layout.addWidget(self._view)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._page_loaded:
            self._page_loaded = True
            self._view.load(QUrl.fromLocalFile(str(_QUESTION_HTML)))

    def _on_ready(self) -> None:
        self._ready = True
        if self._pending:
            self.set_question(self._pending)
            self._pending = ""

    def set_question(self, text: str) -> None:
        value = text or ""
        if not self._ready:
            self._pending = value
            return
        payload = json.dumps(value)
        self._view.page().runJavaScript(f"window.setQuestionText({payload})")


class MathEditorPanelFallback(QWidget):
    submit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Установите PyQt6-WebEngine для MathLive-редактора (pip install PyQt6-WebEngine).")
        )
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("LaTeX… Ctrl+Enter — проверить")
        font = QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)
        layout.addWidget(self.editor)
        QShortcut(QKeySequence("Ctrl+Return"), self.editor, self.submit_requested.emit)

    def plain_text(self) -> str:
        return self.editor.toPlainText().strip()

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def clear(self) -> None:
        self.editor.clear()

    def set_focus(self) -> None:
        self.editor.setFocus()


class MathQuestionViewFallback(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._edit = QPlainTextEdit()
        self._edit.setReadOnly(True)
        font = QFont("Monospace")
        font.setPointSize(11)
        self._edit.setFont(font)
        layout.addWidget(self._edit)

    def set_question(self, text: str) -> None:
        self._edit.setPlainText(text)


def create_math_editor_panel(parent: QWidget | None = None) -> QWidget:
    try:
        _web_engine_types()
        return MathEditorPanel(parent)
    except ImportError:
        return MathEditorPanelFallback(parent)


def create_math_question_view(parent: QWidget | None = None) -> QWidget:
    try:
        _web_engine_types()
        return MathQuestionView(parent)
    except ImportError:
        return MathQuestionViewFallback(parent)
