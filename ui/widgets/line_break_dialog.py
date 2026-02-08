from __future__ import annotations
from typing import Optional, Tuple
from PySide6 import QtCore, QtWidgets

from file_model.events.line_break import LineBreak


class LineBreakDialog(QtWidgets.QDialog):
    def __init__(self,
                 parent=None,
                 margin_mm: Optional[list[float]] = None,
                 stave_range: Optional[list[int] | bool] = None,
                 page_break: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle("Line Break")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)

        self.margin_left = QtWidgets.QLineEdit(self)
        self.margin_right = QtWidgets.QLineEdit(self)
        form.addRow(QtWidgets.QLabel("Margin left:", self), self.margin_left)
        form.addRow(QtWidgets.QLabel("Margin right:", self), self.margin_right)

        self.range_low = QtWidgets.QLineEdit(self)
        self.range_high = QtWidgets.QLineEdit(self)
        form.addRow(QtWidgets.QLabel("Range from key:", self), self.range_low)
        form.addRow(QtWidgets.QLabel("Range to key:", self), self.range_high)

        lay.addLayout(form)

        self.auto_range_cb = QtWidgets.QCheckBox("Auto range", self)
        self.auto_range_cb.toggled.connect(self._sync_range_enabled)

        # Page break toggle
        self.page_break_cb = QtWidgets.QCheckBox("Page break", self)
        self.page_break_cb.toggled.connect(self._sync_page_break_indicator)

        options_row = QtWidgets.QHBoxLayout()
        options_row.setContentsMargins(0, 0, 0, 0)
        options_row.setSpacing(6)
        options_col = QtWidgets.QVBoxLayout()
        options_col.setContentsMargins(0, 0, 0, 0)
        options_col.setSpacing(4)
        options_col.addWidget(self.auto_range_cb)
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
        self.break_marker.setFixedWidth(22)
        self.break_marker.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.break_marker.setStyleSheet("QLabel { background: #000000; color: #ffffff; border-radius: 3px; }")
        options_row.addWidget(self.break_marker)
        lay.addLayout(options_row)

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
        default_range = list(defaults.stave_range) if isinstance(defaults.stave_range, list) else [0, 0]
        m = margin_mm if margin_mm is not None else list(defaults.margin_mm)
        is_auto = bool(stave_range is True)
        r = [] if is_auto else (stave_range if isinstance(stave_range, list) else list(default_range))
        self.margin_left.setText(str(m[0] if len(m) > 0 else defaults.margin_mm[0]))
        self.margin_right.setText(str(m[1] if len(m) > 1 else defaults.margin_mm[1]))
        self.range_low.setText(str(r[0] if len(r) > 0 else default_range[0]))
        self.range_high.setText(str(r[1] if len(r) > 1 else default_range[1]))
        self.auto_range_cb.setChecked(is_auto)
        self._sync_range_enabled()
        self.page_break_cb.setChecked(bool(page_break))
        self._sync_page_break_indicator()

        QtCore.QTimer.singleShot(0, self._focus_first)

    def _focus_first(self) -> None:
        try:
            self.margin_left.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
            self.margin_left.selectAll()
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
        self.range_low.setEnabled(enabled)
        self.range_high.setEnabled(enabled)
        self.range_low.setReadOnly(not enabled)
        self.range_high.setReadOnly(not enabled)
        if enabled:
            self.range_low.setStyleSheet("")
            self.range_high.setStyleSheet("")
        else:
            self.range_low.setStyleSheet("QLineEdit { color: #888888; }")
            self.range_high.setStyleSheet("QLineEdit { color: #888888; }")

    def _sync_page_break_indicator(self) -> None:
        self.break_marker.setText("P" if self.page_break_cb.isChecked() else "L")

    def _on_accept_clicked(self) -> None:
        ml = self._parse_float(self.margin_left.text())
        mr = self._parse_float(self.margin_right.text())
        if self.auto_range_cb.isChecked():
            rl = 0
            rh = 0
        else:
            rl = self._parse_int(self.range_low.text())
            rh = self._parse_int(self.range_high.text())

        if ml is None or mr is None:
            self.msg_label.setText("Margins must be numbers (mm).")
            return
        if rl is None or rh is None:
            self.msg_label.setText("Stave range must be integers (0 for auto).")
            return
        self.msg_label.setText("")
        self.accept()

    def get_values(self) -> Tuple[list[float], list[int] | bool, bool]:
        ml = float(self.margin_left.text().strip() or 0.0)
        mr = float(self.margin_right.text().strip() or 0.0)
        if self.auto_range_cb.isChecked():
            return [ml, mr], True, bool(self.page_break_cb.isChecked())
        rl = int(self.range_low.text().strip() or 0)
        rh = int(self.range_high.text().strip() or 0)
        return [ml, mr], [rl, rh], bool(self.page_break_cb.isChecked())
