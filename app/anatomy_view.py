from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.anatomy_image import fetch_anatomy_image_bytes, is_remote_image, resolve_anatomy_image_path


class AnatomyImageView(QWidget):
    """Shows anatomy diagram above the question text."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        self._label = QLabel("")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._label.setMinimumHeight(140)
        self._label.setMaximumHeight(280)
        self._label.setScaledContents(False)
        layout.addWidget(self._label)

    def clear(self) -> None:
        self._label.clear()
        self.hide()

    def set_image(self, relative: str, *, alt: str = "") -> None:
        rel = (relative or "").strip()
        if not rel:
            self.clear()
            return
        pix = QPixmap()
        if is_remote_image(rel):
            data = fetch_anatomy_image_bytes(rel)
            if not data or not pix.loadFromData(data):
                self.clear()
                return
        else:
            path = resolve_anatomy_image_path(rel)
            if path is None:
                self.clear()
                return
            pix = QPixmap(str(path))
            if pix.isNull():
                self.clear()
                return
        scaled = pix.scaled(
            max(self._label.width(), 480),
            260,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)
        self._label.setToolTip(alt or "")
        self.show()
