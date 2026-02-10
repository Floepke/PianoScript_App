from __future__ import annotations
from typing import Optional, Tuple, Literal
from PySide6 import QtCore, QtGui, QtWidgets

from ui.widgets.style_dialog import ClickSlider


class LimitedSliderEdit(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(float)

    def __init__(self, value: float, min_value: float, max_value: float, step: float, parent=None) -> None:
        super().__init__(parent)
        self._min = float(min_value)
        self._max = float(max_value)
        self._step = float(step)
        self._value = float(value)
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

    def _slider_to_value(self, sv: int) -> float:
        return self._min + float(sv) * self._step

    def _value_to_slider(self, val: float) -> int:
        return int(round((val - self._min) / self._step))

    def set_value(self, value: float) -> None:
        val = max(self._min, float(value))
        self._value = val
        slider_val = min(self._max, val)
        self._slider.blockSignals(True)
        self._slider.setValue(self._value_to_slider(slider_val))
        self._slider.blockSignals(False)
        self._edit.setText(f"{val:.2f}")

    def value(self) -> float:
        return float(self._value)

    def _on_slider_changed(self, _v: int) -> None:
        val = self._slider_to_value(self._slider.value())
        self._value = val
        self._edit.setText(f"{val:.2f}")
        self.valueChanged.emit(val)

    def _on_edit_finished(self) -> None:
        text = self._edit.text().strip()
        try:
            val = float(text)
        except Exception:
            val = self._value
        val = max(self._min, val)
        self.set_value(val)
        self.valueChanged.emit(val)

from file_model.events.line_break import LineBreak


class LineBreakDialog(QtWidgets.QDialog):
    valuesChanged = QtCore.Signal()
    def __init__(self,
                 parent=None,
                 margin_mm: Optional[list[float]] = None,
                 stave_range: Optional[list[int] | Literal['auto'] | bool] = None,
                 page_break: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle("Line Break")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Page break toggle
        self.page_break_cb = QtWidgets.QCheckBox("Is Page Break", self)
        self.page_break_cb.toggled.connect(self._sync_page_break_indicator)
        self.page_break_cb.toggled.connect(lambda _v: self.valuesChanged.emit())

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)

        self.margin_left = LimitedSliderEdit(0.0, 0.0, 50.0, 0.1, self)
        self.margin_right = LimitedSliderEdit(0.0, 0.0, 50.0, 0.1, self)
        form.addRow(QtWidgets.QLabel("Stave Margin Left:", self), self.margin_left)
        form.addRow(QtWidgets.QLabel("Stave Margin Right:", self), self.margin_right)

        self.auto_range_cb = QtWidgets.QCheckBox("Auto Calculate Stave Width", self)
        self.auto_range_cb.toggled.connect(self._sync_range_enabled)
        self.auto_range_cb.toggled.connect(lambda _v: self.valuesChanged.emit())

        form.addRow(self.auto_range_cb)

        self.range_low_label = QtWidgets.QLabel("Stave range from key:", self)
        self.range_high_label = QtWidgets.QLabel("Stave range to key:", self)
        self.range_low = QtWidgets.QSpinBox(self)
        self.range_high = QtWidgets.QSpinBox(self)
        self.range_low.setRange(1, 88)
        self.range_high.setRange(1, 88)
        self.range_low.valueChanged.connect(lambda _v: self.valuesChanged.emit())
        self.range_high.valueChanged.connect(lambda _v: self.valuesChanged.emit())
        form.addRow(self.range_low_label, self.range_low)
        form.addRow(self.range_high_label, self.range_high)

        options_row = QtWidgets.QHBoxLayout()
        options_row.setContentsMargins(0, 0, 0, 0)
        options_row.setSpacing(6)
        options_col = QtWidgets.QVBoxLayout()
        options_col.setContentsMargins(0, 0, 0, 0)
        options_col.setSpacing(4)
        options_col.addWidget(self.page_break_cb)
        options_row.addLayout(options_col)
        options_row.addStretch(1)
        self.break_marker = QtWidgets.QLabel("L", self)
        try:
            from fonts import register_font_from_bytes
            marker_family = register_font_from_bytes('C059') or 'C059'
        except Exception:
            marker_family = 'C059'
        marker_font = self.break_marker.font()
        marker_font.setFamily(marker_family)
        marker_font.setPointSize(18)
        marker_font.setBold(True)
        self.break_marker.setFont(marker_font)
        self.break_marker.setFixedSize(22, 22)
        self.break_marker.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.break_marker.setStyleSheet("QLabel { background: #000000; color: #ffffff; border-radius: 0px; }")
        options_row.addWidget(self.break_marker)
        lay.addLayout(options_row)

        lay.addLayout(form)

        # Validation message
        self.msg_label = QtWidgets.QLabel("", self)
        pal = self.msg_label.palette()
        pal.setColor(self.msg_label.foregroundRole(), QtCore.Qt.GlobalColor.red)
        self.msg_label.setPalette(pal)
        lay.addWidget(self.msg_label)

        # Buttons
        self.btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self)
        self.btns.accepted.connect(self._on_accept_clicked)
        self.btns.rejected.connect(self.reject)
        lay.addWidget(self.btns)

        # Initialize
        defaults = LineBreak()
        default_range = list(defaults.stave_range) if isinstance(defaults.stave_range, list) else [40, 44]
        m = margin_mm if margin_mm is not None else list(defaults.margin_mm)
        is_auto = bool(stave_range == 'auto' or stave_range is True)
        r = [] if is_auto else (stave_range if isinstance(stave_range, list) else list(default_range))
        self.margin_left.set_value(float(m[0] if len(m) > 0 else defaults.margin_mm[0]))
        self.margin_right.set_value(float(m[1] if len(m) > 1 else defaults.margin_mm[1]))
        self.range_low.setValue(int(r[0] if len(r) > 0 else default_range[0]))
        self.range_high.setValue(int(r[1] if len(r) > 1 else default_range[1]))
        self.auto_range_cb.setChecked(is_auto)
        self._sync_range_enabled()
        self.page_break_cb.setChecked(bool(page_break))
        self._sync_page_break_indicator()

        self.margin_left.valueChanged.connect(lambda _v: self.valuesChanged.emit())
        self.margin_right.valueChanged.connect(lambda _v: self.valuesChanged.emit())

        QtCore.QTimer.singleShot(0, self._focus_first)

    def _focus_first(self) -> None:
        try:
            if hasattr(self.margin_left, "_edit"):
                self.margin_left._edit.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
                self.margin_left._edit.selectAll()
            else:
                self.margin_left.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
        except Exception:
            pass

    def _parse_float(self, text: str) -> Optional[float]:
        try:
            return float(text.strip())
        except Exception:
            return None

    def _parse_int(self, text: str) -> Optional[int]:
        try:
            return int(text.strip())
        except Exception:
            return None

    def _sync_range_enabled(self) -> None:
        enabled = not self.auto_range_cb.isChecked()
        self.range_low.setVisible(enabled)
        self.range_high.setVisible(enabled)
        self.range_low_label.setVisible(enabled)
        self.range_high_label.setVisible(enabled)

    def _sync_page_break_indicator(self) -> None:
        self.break_marker.setText("P" if self.page_break_cb.isChecked() else "L")

    def _on_accept_clicked(self) -> None:
        ml = float(self.margin_left.value())
        mr = float(self.margin_right.value())
        if self.auto_range_cb.isChecked():
            rl = 0
            rh = 0
        else:
            rl = int(self.range_low.value())
            rh = int(self.range_high.value())

        self.msg_label.setText("")
        self.accept()

    def get_values(self) -> Tuple[list[float], list[int] | Literal['auto'], bool]:
        ml = float(self.margin_left.value())
        mr = float(self.margin_right.value())
        if self.auto_range_cb.isChecked():
            return [ml, mr], 'auto', bool(self.page_break_cb.isChecked())
        rl = int(self.range_low.value())
        rh = int(self.range_high.value())
        return [ml, mr], [rl, rh], bool(self.page_break_cb.isChecked())
