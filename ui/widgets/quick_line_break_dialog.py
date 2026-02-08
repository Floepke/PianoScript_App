from __future__ import annotations
from typing import List, Optional

from PySide6 import QtCore, QtWidgets


class QuickLineBreaksDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, initial_text: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Set Quick Line Breaks Tool")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        desc = (
            "Enter one or more integers separated by spaces. Each number is the number of measures\n"
            "per line. Example: '4 6 4' makes 4 measures in line 1, 6 in line 2, 4 in line 3,\n"
            "then repeats the last number for the remaining lines until the end of the score."
        )
        self.desc_label = QtWidgets.QLabel(desc, self)
        self.desc_label.setWordWrap(True)
        lay.addWidget(self.desc_label)

        self.input_edit = QtWidgets.QLineEdit(self)
        self.input_edit.setPlaceholderText("e.g. 4 6 4")
        self.input_edit.setText(initial_text or "")
        lay.addWidget(self.input_edit)

        self.msg_label = QtWidgets.QLabel("", self)
        pal = self.msg_label.palette()
        pal.setColor(self.msg_label.foregroundRole(), QtCore.Qt.GlobalColor.red)
        self.msg_label.setPalette(pal)
        lay.addWidget(self.msg_label)

        self.btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self,
        )
        self.btns.accepted.connect(self._on_accept_clicked)
        self.btns.rejected.connect(self.reject)
        lay.addWidget(self.btns)

        QtCore.QTimer.singleShot(0, self._focus_first)

    def _focus_first(self) -> None:
        try:
            self.input_edit.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
            self.input_edit.selectAll()
        except Exception:
            pass

    def _parse_values(self, text: str) -> Optional[List[int]]:
        try:
            parts = [p for p in text.strip().split() if p.strip()]
            if not parts:
                return None
            values = [int(p) for p in parts]
            if any(v <= 0 for v in values):
                return None
            return values
        except Exception:
            return None

    def _on_accept_clicked(self) -> None:
        values = self._parse_values(self.input_edit.text())
        if values is None:
            self.msg_label.setText("Enter one or more positive integers separated by spaces.")
            return
        self.msg_label.setText("")
        self.accept()

    def get_values(self) -> List[int]:
        values = self._parse_values(self.input_edit.text())
        return values or []
