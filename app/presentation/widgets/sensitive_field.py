"""Masked sensitive text widget with reveal toggle."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
)


class SensitiveFieldWidget(QWidget):
    """Input/display widget for sensitive identifiers (PAN) with mask/unmask toggle."""

    def __init__(self, placeholder: str = "Enter sensitive value", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setEchoMode(QLineEdit.Password)

        self.btn_toggle = QToolButton()
        self.btn_toggle.setText("👁")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setToolTip("Show / Hide sensitive value")
        self.btn_toggle.toggled.connect(self._on_toggled)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.btn_toggle)

    def _on_toggled(self, checked: bool) -> None:
        if checked:
            self.line_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.line_edit.setEchoMode(QLineEdit.Password)

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, text: str) -> None:
        self.line_edit.setText(text)
