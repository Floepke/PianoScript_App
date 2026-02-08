from __future__ import annotations
from dataclasses import fields
from typing import Any, get_args, get_origin, get_type_hints, Literal

from PySide6 import QtCore, QtGui, QtWidgets

from file_model.layout import LAYOUT_FLOAT_CONFIG

from file_model.layout import Layout


class ClickSlider(QtWidgets.QSlider):
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.orientation() == QtCore.Qt.Orientation.Horizontal:
                pos = ev.position().x()
                span = max(1.0, float(self.width()))
                val = self.minimum() + (self.maximum() - self.minimum()) * (pos / span)
            else:
                pos = ev.position().y()
                span = max(1.0, float(self.height()))
                val = self.maximum() - (self.maximum() - self.minimum()) * (pos / span)
            self.setSliderPosition(int(round(val)))
            self.setSliderDown(True)
            self.sliderMoved.emit(self.sliderPosition())
            ev.accept()
            return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self.isSliderDown():
            if self.orientation() == QtCore.Qt.Orientation.Horizontal:
                pos = ev.position().x()
                span = max(1.0, float(self.width()))
                val = self.minimum() + (self.maximum() - self.minimum()) * (pos / span)
            else:
                pos = ev.position().y()
                span = max(1.0, float(self.height()))
                val = self.maximum() - (self.maximum() - self.minimum()) * (pos / span)
            self.setSliderPosition(int(round(val)))
            self.sliderMoved.emit(self.sliderPosition())
            ev.accept()
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self.isSliderDown():
            self.setSliderDown(False)
        super().mouseReleaseEvent(ev)


class FloatSliderEdit(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(float)

    def __init__(self, value: float, min_value: float, max_value: float, step: float, parent=None) -> None:
        super().__init__(parent)
        self._min = float(min_value)
        self._max = float(max_value)
        self._step = float(step)
        self._slider = ClickSlider(QtCore.Qt.Orientation.Horizontal, self)
        self._edit = QtWidgets.QLineEdit(self)
        self._edit.setMinimumWidth(70)
        self._edit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._edit.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"[0-9.]+"), self))
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._slider, 1)
        layout.addWidget(self._edit, 0)
        self._apply_range()
        self.set_value(value)
        self._slider.valueChanged.connect(self._on_slider_changed)
        self._edit.editingFinished.connect(self._on_edit_finished)

    def _apply_range(self) -> None:
        steps = max(1, int(round((self._max - self._min) / max(1e-6, self._step))))
        self._slider.setRange(0, steps)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(max(1, int(round(steps / 10.0))))

    def _clamp(self, val: float) -> float:
        return max(self._min, min(self._max, val))

    def _snap(self, val: float) -> float:
        if self._step <= 0:
            return val
        snapped = round(val / self._step) * self._step
        return round(snapped, 2)

    def _slider_to_value(self, sv: int) -> float:
        return self._min + float(sv) * self._step

    def _value_to_slider(self, val: float) -> int:
        return int(round((val - self._min) / self._step))

    def set_value(self, value: float) -> None:
        val = self._snap(self._clamp(float(value)))
        self._slider.blockSignals(True)
        self._slider.setValue(self._value_to_slider(val))
        self._slider.blockSignals(False)
        self._edit.setText(f"{val:.2f}")

    def value(self) -> float:
        val = self._slider_to_value(self._slider.value())
        return self._snap(self._clamp(val))

    def _on_slider_changed(self, _v: int) -> None:
        val = self.value()
        self._edit.setText(f"{val:.2f}")
        self.valueChanged.emit(val)

    def _on_edit_finished(self) -> None:
        text = self._edit.text().strip()
        try:
            val = float(text)
        except Exception:
            val = self.value()
        val = self._snap(self._clamp(val))
        self.set_value(val)
        self.valueChanged.emit(val)

    def wheelEvent(self, ev: QtGui.QWheelEvent) -> None:
        delta = ev.angleDelta().y()
        if delta == 0:
            return
        step = self._step if self._step > 0 else 1.0
        cur = self.value()
        direction = 1.0 if delta > 0 else -1.0
        self.set_value(cur + (direction * step))
        self.valueChanged.emit(self.value())
        ev.accept()


class ColorPickerEdit(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(str)

    def __init__(self, value: str, parent=None) -> None:
        super().__init__(parent)
        self._edit = QtWidgets.QLineEdit(self)
        self._button = QtWidgets.QPushButton("Pick", self)
        self._button.setFixedWidth(48)
        self._edit.setMinimumWidth(90)
        self._edit.setValidator(
            QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"#?[0-9a-fA-F]+"), self)
        )
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._edit, 1)
        layout.addWidget(self._button, 0)
        self.set_value(str(value))
        self._button.clicked.connect(self._open_dialog)
        self._edit.editingFinished.connect(self._on_edit_finished)

    def set_value(self, value: str) -> None:
        txt = str(value or '').strip()
        if txt and not txt.startswith('#'):
            txt = f"#{txt}"
        self._edit.setText(txt)

    def value(self) -> str:
        txt = self._edit.text().strip()
        if txt and not txt.startswith('#'):
            txt = f"#{txt}"
        return txt

    def _open_dialog(self) -> None:
        col = QtGui.QColor(self.value())
        if not col.isValid():
            col = QtGui.QColor(0, 0, 0)
        picked = QtWidgets.QColorDialog.getColor(col, self)
        if not picked.isValid():
            return
        self.set_value(picked.name())
        self.valueChanged.emit(self.value())

    def _on_edit_finished(self) -> None:
        txt = self.value()
        self.set_value(txt)
        self.valueChanged.emit(txt)


class LayoutDialog(QtWidgets.QDialog):
    values_changed = QtCore.Signal()

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
        try:
            self.setMinimumWidth(900)
            self.resize(900, self.height())
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
        self._type_hints = type_hints
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
            self._wire_editor_change(editor)

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
            if field_name in LAYOUT_FLOAT_CONFIG:
                cfg = LAYOUT_FLOAT_CONFIG[field_name]
                return FloatSliderEdit(float(value), cfg['min'], cfg['max'], cfg['step'], self)
            is_mm = field_name.endswith('_mm')
            is_pt = field_name.endswith('_pt')
            if is_mm:
                return FloatSliderEdit(float(value), 0.0, 1000.0, 0.5, self)
            if is_pt:
                return FloatSliderEdit(float(value), 1.0, 200.0, 0.5, self)
            return FloatSliderEdit(float(value), -1000.0, 1000.0, 0.01, self)

        if field_type is str and (field_name.startswith('color_') or field_name.endswith('_color')):
            return ColorPickerEdit(str(value or ''), self)

        if field_type is str:
            le = QtWidgets.QLineEdit(self)
            le.setText(str(value) if value is not None else "")
            return le

        if origin is list and args and args[0] is float:
            le = QtWidgets.QLineEdit(self)
            le.setText(self._format_float_list(value))
            le.setValidator(
                QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"[0-9. ]*"), self)
            )
            return le

        return None

    def _wire_editor_change(self, editor: QtWidgets.QWidget) -> None:
        try:
            if isinstance(editor, QtWidgets.QCheckBox):
                editor.stateChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, QtWidgets.QSpinBox):
                editor.valueChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, FloatSliderEdit):
                editor.valueChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, QtWidgets.QComboBox):
                editor.currentTextChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, QtWidgets.QLineEdit):
                editor.textChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, ColorPickerEdit):
                editor.valueChanged.connect(lambda _v: self.values_changed.emit())
        except Exception:
            pass

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
            field_type = self._type_hints.get(name, f.type)
            origin = get_origin(field_type)
            args = get_args(field_type)
            if isinstance(editor, QtWidgets.QCheckBox):
                data[name] = bool(editor.isChecked())
            elif isinstance(editor, QtWidgets.QSpinBox):
                data[name] = int(editor.value())
            elif isinstance(editor, FloatSliderEdit):
                data[name] = float(editor.value())
            elif isinstance(editor, ColorPickerEdit):
                data[name] = str(editor.value())
            elif origin is list and args and args[0] is float and isinstance(editor, QtWidgets.QLineEdit):
                data[name] = self._parse_float_list(editor.text())
            elif isinstance(editor, QtWidgets.QComboBox):
                data[name] = str(editor.currentText())
            elif isinstance(editor, QtWidgets.QLineEdit):
                data[name] = str(editor.text())
        return Layout(**data)

    def _format_float_list(self, value: Any) -> str:
        if not isinstance(value, list):
            return ""
        parts: list[str] = []
        for v in value:
            try:
                parts.append(f"{float(v):.2f}".rstrip('0').rstrip('.'))
            except Exception:
                continue
        return " ".join(parts)

    def _parse_float_list(self, text: str) -> list[float]:
        if not text:
            return []
        parts = text.replace(',', ' ').split()
        values: list[float] = []
        for part in parts:
            try:
                values.append(float(part))
            except Exception:
                continue
        return values
