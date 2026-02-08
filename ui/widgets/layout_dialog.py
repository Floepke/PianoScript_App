from __future__ import annotations
from dataclasses import fields
from typing import Any, get_args, get_origin, get_type_hints, Literal

from PySide6 import QtCore, QtWidgets

from file_model.layout import Layout


class ScaleSlider(QtWidgets.QWidget):
    def __init__(self, value: float, parent=None) -> None:
        super().__init__(parent)
        self._slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self._slider.setRange(0, 1000)
        self._label = QtWidgets.QLabel(self)
        self._label.setMinimumWidth(50)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._slider, 1)
        layout.addWidget(self._label, 0)
        self.set_value(value)
        self._slider.valueChanged.connect(self._sync_label)

    def set_value(self, value: float) -> None:
        iv = int(max(0.0, min(1.0, float(value))) * 1000.0)
        self._slider.setValue(iv)
        self._sync_label()

    def value(self) -> float:
        return float(self._slider.value()) / 1000.0

    def _sync_label(self) -> None:
        self._label.setText(f"{self.value():.3f}")


class LayoutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, layout: Layout | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Layout")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)
        try:
            screen = QtWidgets.QApplication.primaryScreen()
            if screen is not None:
                max_h = int(screen.availableGeometry().height() / 3 * 2)
                if max_h > 0:
                    self.setMaximumHeight(max_h)
                    self.setFixedHeight(max_h)
        except Exception:
            pass

        self._layout = layout or Layout()
        self._editors: dict[str, QtWidgets.QWidget] = {}

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        content = QtWidgets.QWidget(self)
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        content_layout.addLayout(form)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        lay.addWidget(scroll, 1)

        type_hints = {}
        try:
            type_hints = get_type_hints(Layout)
        except Exception:
            type_hints = {}
        for f in fields(Layout):
            name = f.name
            label = name.replace('_', ' ').capitalize() + ":"
            value = getattr(self._layout, name)
            field_type = type_hints.get(name, f.type)
            editor = self._make_editor(field_type, value, name)
            if editor is None:
                continue
            self._editors[name] = editor
            form.addRow(QtWidgets.QLabel(label, self), editor)

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

    def _make_editor(self, field_type: Any, value: Any, field_name: str) -> QtWidgets.QWidget | None:
        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin is Literal and args:
            combo = QtWidgets.QComboBox(self)
            options = [str(a) for a in args]
            combo.addItems(options)
            try:
                combo.setCurrentText(str(value))
            except Exception:
                pass
            return combo

        if field_type is bool:
            cb = QtWidgets.QCheckBox(self)
            cb.setChecked(bool(value))
            return cb

        if field_type is int:
            sb = QtWidgets.QSpinBox(self)
            sb.setRange(-1000000, 1000000)
            sb.setValue(int(value))
            return sb

        if field_type is float:
            if field_name == 'scale':
                return ScaleSlider(float(value), self)
            dsb = QtWidgets.QDoubleSpinBox(self)
            dsb.setDecimals(3)
            dsb.setRange(-1000000.0, 1000000.0)
            try:
                dsb.setValue(float(value))
            except Exception:
                dsb.setValue(0.0)
            return dsb

        if field_type is str:
            le = QtWidgets.QLineEdit(self)
            le.setText(str(value) if value is not None else "")
            return le

        return None

    def _on_accept_clicked(self) -> None:
        try:
            _ = self.get_values()
        except Exception:
            self.msg_label.setText("Invalid layout values.")
            return
        self.msg_label.setText("")
        self.accept()

    def get_values(self) -> Layout:
        data: dict[str, Any] = {}
        for f in fields(Layout):
            name = f.name
            editor = self._editors.get(name)
            if editor is None:
                continue
            if isinstance(editor, QtWidgets.QCheckBox):
                data[name] = bool(editor.isChecked())
            elif isinstance(editor, QtWidgets.QSpinBox):
                data[name] = int(editor.value())
            elif isinstance(editor, ScaleSlider):
                data[name] = float(editor.value())
            elif isinstance(editor, QtWidgets.QDoubleSpinBox):
                data[name] = float(editor.value())
            elif isinstance(editor, QtWidgets.QComboBox):
                data[name] = str(editor.currentText())
            elif isinstance(editor, QtWidgets.QLineEdit):
                data[name] = str(editor.text())
        return Layout(**data)
