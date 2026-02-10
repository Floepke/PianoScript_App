from __future__ import annotations

from dataclasses import fields
from PySide6 import QtCore, QtWidgets

from file_model.info import Info
from file_model.SCORE import SCORE, MetaData


class InfoDialog(QtWidgets.QDialog):
    def __init__(self, score: SCORE, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("File info")
        self.setModal(True)
        self.resize(560, 420)
        self._score = score

        layout = QtWidgets.QVBoxLayout(self)

        meta_group = QtWidgets.QGroupBox("Meta data", self)
        meta_form = QtWidgets.QFormLayout(meta_group)
        meta_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._meta_labels: dict[str, QtWidgets.QLabel] = {}
        for f in fields(MetaData):
            label = QtWidgets.QLabel(self)
            label.setText("")
            key = str(f.name)
            meta_form.addRow(f"{key.replace('_', ' ').capitalize()}:", label)
            self._meta_labels[key] = label
        layout.addWidget(meta_group)

        info_group = QtWidgets.QGroupBox("Info", self)
        info_form = QtWidgets.QFormLayout(info_group)
        info_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._title_edit = QtWidgets.QLineEdit(self)
        self._composer_edit = QtWidgets.QLineEdit(self)
        self._copyright_edit = QtWidgets.QLineEdit(self)
        self._arranger_edit = QtWidgets.QLineEdit(self)
        self._lyricist_edit = QtWidgets.QLineEdit(self)
        self._comment_edit = QtWidgets.QPlainTextEdit(self)
        self._comment_edit.setMinimumHeight(90)
        info_form.addRow("Title:", self._title_edit)
        info_form.addRow("Composer:", self._composer_edit)
        info_form.addRow("Copyright:", self._copyright_edit)
        info_form.addRow("Arranger:", self._arranger_edit)
        info_form.addRow("Lyricist:", self._lyricist_edit)
        info_form.addRow("Comment:", self._comment_edit)
        layout.addWidget(info_group, stretch=1)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_from_score()

    def _load_from_score(self) -> None:
        meta = getattr(self._score, "meta_data", None)
        for key, label in self._meta_labels.items():
            value = ""
            if meta is not None:
                value = str(getattr(meta, key, "") or "")
            label.setText(value or "(not set)")

        info = getattr(self._score, "info", None) or Info()
        self._title_edit.setText(str(getattr(info, "title", "") or ""))
        self._composer_edit.setText(str(getattr(info, "composer", "") or ""))
        self._copyright_edit.setText(str(getattr(info, "copyright", "") or ""))
        self._arranger_edit.setText(str(getattr(info, "arranger", "") or ""))
        self._lyricist_edit.setText(str(getattr(info, "lyricist", "") or ""))
        self._comment_edit.setPlainText(str(getattr(info, "comment", "") or ""))

    def apply_to_score(self) -> None:
        info = getattr(self._score, "info", None)
        if info is None:
            info = Info()
            self._score.info = info
        info.title = str(self._title_edit.text())
        info.composer = str(self._composer_edit.text())
        info.copyright = str(self._copyright_edit.text())
        info.arranger = str(self._arranger_edit.text())
        info.lyricist = str(self._lyricist_edit.text())
        info.comment = str(self._comment_edit.toPlainText())
