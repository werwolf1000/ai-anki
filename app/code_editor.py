from __future__ import annotations

from PyQt6.Qsci import (
    QsciAPIs,
    QsciLexerCPP,
    QsciLexerHTML,
    QsciLexerJavaScript,
    QsciLexerPython,
    QsciScintilla,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeySequence
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.code_completions import completion_items, normalize_editor_language
from app.config_store import normalize_code_editor_theme

_EDITOR_THEMES: dict[str, dict[str, str]] = {
    "light": {
        "paper": "#ffffff",
        "foreground": "#1a1a1a",
        "margin_fg": "#888888",
        "margin_bg": "#f0f0f0",
        "caret": "#111111",
        "selection": "#cce5ff",
        "hint": "#666666",
    },
    "dark": {
        "paper": "#1e1e1e",
        "foreground": "#d4d4d4",
        "margin_fg": "#858585",
        "margin_bg": "#252526",
        "caret": "#aeafad",
        "selection": "#264f78",
        "hint": "#aaaaaa",
    },
}


class CodeEditor(QsciScintilla):
    submit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._apis: QsciAPIs | None = None
        self._lexer = None
        self._language = "typescript"
        self._theme = "light"
        self._configure_base()
        self.set_language("typescript")

    def _configure_base(self) -> None:
        font = QFont("Monospace", 11)
        if not font.exactMatch():
            font = QFont("DejaVu Sans Mono", 11)
        self.setFont(font)
        self.setTabWidth(4)
        self.setIndentationWidth(4)
        self.setAutoIndent(True)
        self.setIndentationsUseTabs(False)
        self.setTabIndents(True)
        self.setBackspaceUnindents(True)
        self.setIndentationGuides(True)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setWhitespaceVisibility(QsciScintilla.WhitespaceVisibility.WsInvisible)
        self.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        self.setFolding(QsciScintilla.FoldStyle.NoFoldStyle)

        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")

        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)
        self._apply_theme()

    def _apply_theme(self) -> None:
        colors = _EDITOR_THEMES[self._theme]
        self.setPaper(QColor(colors["paper"]))
        self.setColor(QColor(colors["foreground"]))
        self.setMarginsForegroundColor(QColor(colors["margin_fg"]))
        self.setMarginsBackgroundColor(QColor(colors["margin_bg"]))
        self.setCaretForegroundColor(QColor(colors["caret"]))
        self.setSelectionBackgroundColor(QColor(colors["selection"]))
        if self._lexer is not None:
            self._lexer.setDefaultPaper(QColor(colors["paper"]))
            self._lexer.setDefaultColor(QColor(colors["foreground"]))
            self._lexer.setPaper(QColor(colors["paper"]))

    def set_theme(self, theme: str) -> None:
        self._theme = normalize_code_editor_theme(theme)
        self._apply_theme()

    def _make_lexer(self, language: str, font: QFont):
        lang = normalize_editor_language(language)
        if lang == "python":
            lexer = QsciLexerPython()
        elif lang in ("typescript", "javascript"):
            lexer = QsciLexerJavaScript()
        elif lang == "php":
            lexer = QsciLexerHTML()
        elif lang != "plaintext":
            lexer = QsciLexerCPP()
        else:
            return None

        lexer.setDefaultFont(font)
        lexer.setFont(font)
        return lexer

    def _apply_apis(self, lexer) -> None:
        apis = QsciAPIs(lexer)
        for item in completion_items(self._language):
            apis.add(item)
        apis.prepare()
        self._apis = apis

    def set_language(self, language: str) -> None:
        self._language = normalize_editor_language(language)
        font = self.font()
        lexer = self._make_lexer(self._language, font)
        self._lexer = lexer
        self._apis = None
        if lexer is None:
            self.setLexer(None)
            return
        self.setLexer(lexer)
        self._apply_apis(lexer)
        self._apply_theme()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.matches(QKeySequence.StandardKey.InsertParagraphSeparator):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self.submit_requested.emit()
                return
        if event.key() == Qt.Key.Key_Space and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.autoCompleteFromAll()
            return
        super().keyPressEvent(event)


class CodeEditorPanel(QWidget):
    """Syntax-highlighted code editor with autocomplete for code answers."""

    submit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        self.editor = CodeEditor()
        self.editor.submit_requested.connect(self.submit_requested.emit)
        layout.addWidget(self.editor)

    def set_theme(self, theme: str) -> None:
        self._theme = normalize_code_editor_theme(theme)
        self.editor.set_theme(self._theme)
        colors = _EDITOR_THEMES[self._theme]
        self.hint_label.setStyleSheet(f"color: {colors['hint']};")

    def set_placeholder(self, text: str) -> None:
        self.hint_label.setText(text)

    def set_language_hint(self, language: str) -> None:
        lang = normalize_editor_language(language)
        label = {
            "typescript": "TypeScript",
            "javascript": "JavaScript",
            "python": "Python",
            "php": "PHP",
        }.get(lang, lang)
        self.editor.set_language(language)
        self.set_placeholder(
            f"Напишите код ({label})…  Ctrl+Space — автодополнение · Ctrl+Enter — проверить"
        )

    def plain_text(self) -> str:
        return self.editor.text()

    def set_plain_text(self, text: str) -> None:
        self.editor.setText(text)

    def clear(self) -> None:
        self.editor.clear()

    def set_focus(self) -> None:
        self.editor.setFocus()
