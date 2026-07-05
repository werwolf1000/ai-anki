from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

MATH_SNIPPETS: dict[str, str] = {
    "Дробь": r"\frac{a}{b}",
    "Корень": r"\sqrt{x}",
    "Степень": r"x^{n}",
    "Интеграл": r"\int_{a}^{b} f(x)\,dx",
    "Сумма": r"\sum_{i=1}^{n} a_i",
    "Предел": r"\lim_{x \to 0} f(x)",
    "Произв.": r"\frac{d}{dx} f(x)",
    "Матр. 2×2": r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
    "Матр. 3×3": r"\begin{pmatrix} a & b & c \\ d & e & f \\ g & h & i \end{pmatrix}",
    "det": r"\det(A)",
    "Вектор": r"\vec{v} = \begin{pmatrix} x \\ y \\ z \end{pmatrix}",
    "Система": r"\begin{cases} x + y = 1 \\ 2x - y = 0 \end{cases}",
}


class MathEditorPanel(QWidget):
    submit_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        for label, snippet in MATH_SNIPPETS.items():
            btn = QPushButton(label)
            btn.setProperty("snippet", snippet)
            btn.clicked.connect(self._insert_snippet)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "LaTeX: \\frac{a}{b}, \\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}, "
            "Ctrl+Enter — проверить"
        )
        font = QFont("Monospace")
        font.setPointSize(11)
        self.editor.setFont(font)
        self.editor.setMinimumHeight(120)
        layout.addWidget(self.editor)

    def _insert_snippet(self) -> None:
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        snippet = btn.property("snippet")
        if not snippet:
            return
        cursor = self.editor.textCursor()
        cursor.insertText(str(snippet))
        self.editor.setFocus()

    def plain_text(self) -> str:
        return self.editor.toPlainText()

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def clear(self) -> None:
        self.editor.clear()

    def set_focus(self) -> None:
        self.editor.setFocus()
