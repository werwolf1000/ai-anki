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


class CodeEditor(QsciScintilla):
    submit_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._apis: QsciAPIs | None = None
        self._lexer = None
        self._language = "typescript"
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
        self.setMarginsForegroundColor(QColor("#888888"))
        self.setMarginsBackgroundColor(QColor("#f0f0f0"))

        self.setCaretForegroundColor(QColor("#111111"))
        self.setSelectionBackgroundColor(QColor("#cce5ff"))

        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

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
        self.setPaper(QColor("#ffffff"))

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
        self.hint_label.setStyleSheet("color: #666666;")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        self.editor = CodeEditor()
        self.editor.submit_requested.connect(self.submit_requested.emit)
        layout.addWidget(self.editor)

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
