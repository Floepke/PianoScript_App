from __future__ import annotations
from typing import Callable, Optional, Tuple, Literal
from PySide6 import QtCore, QtGui, QtWidgets

from utils.CONSTANT import BE_KEYS, CF_KEYS

from file_model.events.line_break import LineBreak


class FlexibleDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        try:
            self.setLocale(QtCore.QLocale.c())
        except Exception:
            pass

    def _normalize_text(self, text: str) -> str:
        return text.replace(',', '.')

    def validate(self, text: str, pos: int) -> QtGui.QValidator.State:
        normalized = self._normalize_text(text)
        return super().validate(normalized, pos)

    def valueFromText(self, text: str) -> float:
        normalized = self._normalize_text(text)
        return super().valueFromText(normalized)

    def fixup(self, text: str) -> str:
        return self._normalize_text(text)

    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        if ev.text() == ',':
            ev = QtGui.QKeyEvent(ev.type(), ev.key(), ev.modifiers(), '.')
        super().keyPressEvent(ev)


class LineBreakDialog(QtWidgets.QDialog):
    valuesChanged = QtCore.Signal()
    def __init__(self,
                 parent=None,
                 line_breaks: Optional[list[LineBreak]] = None,
                 selected_line_break: Optional[LineBreak] = None,
                 apply_quick_cb: Optional[Callable[..., None]] = None,
                 reload_cb: Optional[Callable[[], list[LineBreak]]] = None,
                 margin_mm: Optional[list[float]] = None,
                 stave_range: Optional[list[int] | Literal['auto'] | bool] = None,
                 page_break: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle("Line Break")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)
        try:
            self.resize(900, 600)
        except Exception:
            pass

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        self._line_breaks: list[LineBreak] = list(line_breaks or [])
        self._selected_line_break: Optional[LineBreak] = selected_line_break
        self._apply_quick_cb = apply_quick_cb
        self._reload_cb = reload_cb
        self._original_state: dict[int, tuple[list[float], list[int] | Literal['auto'], bool]] = {}

        list_label = QtWidgets.QLabel("Line breaks:", self)
        self.break_table = QtWidgets.QTableWidget(self)
        self.break_table.setColumnCount(4)
        self.break_table.setHorizontalHeaderLabels([
            " Type ",
            " Left margin " ,
            " Right margin ",
            " Key range ",
        ])
        self.break_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.break_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.break_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.break_table.verticalHeader().setVisible(False)
        self.break_table.horizontalHeader().setStretchLastSection(True)
        self.break_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.break_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.break_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.break_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        lay.addWidget(list_label)
        lay.addWidget(self.break_table)

        quick_row = QtWidgets.QHBoxLayout()
        quick_row.setContentsMargins(0, 0, 0, 0)
        quick_row.setSpacing(6)
        self.apply_quick_btn = QtWidgets.QPushButton("Line Break Grouping Tool", self)
        self.apply_quick_btn.clicked.connect(self._on_apply_quick_clicked)
        quick_row.addWidget(self.apply_quick_btn)
        quick_row.addStretch(1)
        lay.addLayout(quick_row)

        bulk_row = QtWidgets.QHBoxLayout()
        bulk_row.setContentsMargins(0, 0, 0, 0)
        bulk_row.setSpacing(6)
        self.edit_all_left_btn = QtWidgets.QPushButton("Edit All Left Margins", self)
        self.edit_all_right_btn = QtWidgets.QPushButton("Edit All Right Margins", self)
        self.edit_all_left_btn.clicked.connect(lambda: self._edit_all_margins(side="left"))
        self.edit_all_right_btn.clicked.connect(lambda: self._edit_all_margins(side="right"))
        bulk_row.addWidget(self.edit_all_left_btn)
        bulk_row.addWidget(self.edit_all_right_btn)
        bulk_row.addStretch(1)
        lay.addLayout(bulk_row)

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

        self.valuesChanged.connect(self._validate_form)

        # Initialize
        self._populate_break_list()
        if self._selected_line_break is None and self._line_breaks:
            self._selected_line_break = self._line_breaks[0]
        self._select_line_break(self._selected_line_break)
        self._capture_original_state()
        self._validate_form()

        self.break_table.currentCellChanged.connect(lambda _r, _c, _pr, _pc: self._on_break_selected())

        QtCore.QTimer.singleShot(0, self._focus_first)

    def _focus_first(self) -> None:
        try:
            self.break_table.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
        except Exception:
            pass

    def _create_type_badge(self, is_page: bool) -> QtWidgets.QToolButton:
        btn = QtWidgets.QToolButton(self)
        btn.setText("P" if is_page else "L")
        btn.setAutoRaise(True)
        btn.setFixedSize(22, 22)
        try:
            from fonts import register_font_from_bytes
            marker_family = register_font_from_bytes('C059') or 'C059'
        except Exception:
            marker_family = 'C059'
        marker_font = btn.font()
        marker_font.setFamily(marker_family)
        marker_font.setPointSize(18)
        marker_font.setBold(True)
        btn.setFont(marker_font)
        btn.setStyleSheet("QToolButton { background: #000000; color: #ffffff; border-radius: 0px; }")
        btn.setToolTip("Page" if is_page else "Line")
        return btn

    def _create_margin_spin(self, value: float) -> FlexibleDoubleSpinBox:
        spin = FlexibleDoubleSpinBox(self)
        spin.setRange(0.0, 200.0)
        spin.setDecimals(2)
        spin.setSingleStep(0.5)
        spin.setValue(float(value))
        spin.setKeyboardTracking(True)
        spin.setMinimumWidth(80)
        return spin

    def _create_range_widget(self, lb: LineBreak) -> QtWidgets.QWidget:
        defaults = LineBreak()
        lb_range = getattr(lb, 'stave_range', defaults.stave_range)
        is_auto = bool(lb_range == 'auto' or lb_range is True or lb_range is None)
        fallback = 'auto' if defaults.stave_range == 'auto' else list(defaults.stave_range or [1, 88])
        if is_auto:
            rng = [1, 88]
        else:
            base_range = lb_range if lb_range is not None else ([1, 88] if fallback == 'auto' else fallback)
            rng = list(base_range)

        def _note_name(key_num: int) -> str:
            midi_note = int(key_num) + 20  # Piano key 1 corresponds to MIDI 21 (A0)
            names = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
            name = names[midi_note % 12]
            octave = (midi_note // 12) - 1
            return f"{name}{octave}"

        def _closest(keys: list[int], target: int) -> int:
            return min(keys, key=lambda k: abs(int(k) - int(target))) if keys else target

        wrapper = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        auto_cb = QtWidgets.QCheckBox(wrapper)
        auto_cb.setChecked(is_auto)
        auto_cb.setText("Automatic key range")

        cf_keys = sorted(CF_KEYS)
        be_keys = sorted(BE_KEYS)

        def _build_combo(prefix: str, keys: list[int]) -> QtWidgets.QComboBox:
            combo = QtWidgets.QComboBox(wrapper)
            combo.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
            for key in keys:
                combo.addItem(f"{prefix} key {key} ({_note_name(key)})", key)
            return combo

        from_combo = _build_combo("from", cf_keys)
        to_combo = _build_combo("to", be_keys)

        def _set_combo_value(combo: QtWidgets.QComboBox, value: int, keys: list[int]) -> None:
            target = _closest(keys, value)
            idx = combo.findData(target)
            combo.setCurrentIndex(idx if idx >= 0 else 0)

        low_val = int(rng[0]) if len(rng) > 0 else 1
        high_val = int(rng[1]) if len(rng) > 1 else 88
        _set_combo_value(from_combo, low_val, cf_keys)
        _set_combo_value(to_combo, high_val, be_keys)

        layout.addWidget(auto_cb)
        layout.addWidget(from_combo)
        layout.addWidget(to_combo)
        layout.addStretch(1)

        def _refresh_combo_style() -> None:
            disabled_style = "QComboBox { color: #7a7a7a; }"
            from_combo.setStyleSheet("" if from_combo.isEnabled() else disabled_style)
            to_combo.setStyleSheet("" if to_combo.isEnabled() else disabled_style)

        def _apply_range_state() -> None:
            is_auto_mode = bool(auto_cb.isChecked())
            from_combo.setEnabled(not is_auto_mode)
            to_combo.setEnabled(not is_auto_mode)
            _refresh_combo_style()
            if is_auto_mode:
                lb.stave_range = 'auto'
            else:
                lb.stave_range = [int(from_combo.currentData()), int(to_combo.currentData())]
            self.valuesChanged.emit()

        def _range_changed(_v: int) -> None:
            if not auto_cb.isChecked():
                lb.stave_range = [int(from_combo.currentData()), int(to_combo.currentData())]
                self.valuesChanged.emit()

        auto_cb.toggled.connect(lambda _v: _apply_range_state())
        from_combo.currentIndexChanged.connect(_range_changed)
        to_combo.currentIndexChanged.connect(_range_changed)

        _apply_range_state()
        _refresh_combo_style()

        return wrapper

    def _populate_break_list(self) -> None:
        self.break_table.blockSignals(True)
        self.break_table.setRowCount(0)
        for lb in self._line_breaks:
            row = self.break_table.rowCount()
            self.break_table.insertRow(row)
            self._set_break_row(row, lb)
        self.break_table.blockSignals(False)

    def _set_break_row(self, row: int, lb: LineBreak) -> None:
        type_item = QtWidgets.QTableWidgetItem("")
        type_item.setData(QtCore.Qt.ItemDataRole.UserRole, lb)
        self.break_table.setItem(row, 0, type_item)

        defaults = LineBreak()
        margin_mm = list(getattr(lb, 'margin_mm', defaults.margin_mm) or defaults.margin_mm)
        left_margin = float(margin_mm[0] if len(margin_mm) > 0 else defaults.margin_mm[0])
        right_margin = float(margin_mm[1] if len(margin_mm) > 1 else defaults.margin_mm[1])

        type_btn = self._create_type_badge(bool(getattr(lb, 'page_break', False)))
        left_spin = self._create_margin_spin(left_margin)
        right_spin = self._create_margin_spin(right_margin)
        range_widget = self._create_range_widget(lb)

        def _toggle_type() -> None:
            lb.page_break = not bool(getattr(lb, 'page_break', False))
            type_btn.setText("P" if lb.page_break else "L")
            type_btn.setToolTip("Page" if lb.page_break else "Line")
            self.valuesChanged.emit()

        def _left_changed(val: float) -> None:
            cur = list(getattr(lb, 'margin_mm', defaults.margin_mm) or defaults.margin_mm)
            if len(cur) < 2:
                cur = [float(cur[0]) if cur else 0.0, 0.0]
            cur[0] = float(val)
            lb.margin_mm = list(cur)
            self.valuesChanged.emit()

        def _right_changed(val: float) -> None:
            cur = list(getattr(lb, 'margin_mm', defaults.margin_mm) or defaults.margin_mm)
            if len(cur) < 2:
                cur = [float(cur[0]) if cur else 0.0, 0.0]
            cur[1] = float(val)
            lb.margin_mm = list(cur)
            self.valuesChanged.emit()

        type_btn.clicked.connect(_toggle_type)
        left_spin.valueChanged.connect(_left_changed)
        right_spin.valueChanged.connect(_right_changed)

        self.break_table.setCellWidget(row, 0, type_btn)
        self.break_table.setCellWidget(row, 1, left_spin)
        self.break_table.setCellWidget(row, 2, right_spin)
        self.break_table.setCellWidget(row, 3, range_widget)

    def _select_line_break(self, lb: Optional[LineBreak]) -> None:
        if lb is None:
            self.break_table.clearSelection()
            return
        for row in range(self.break_table.rowCount()):
            item = self.break_table.item(row, 0)
            if item is not None and item.data(QtCore.Qt.ItemDataRole.UserRole) is lb:
                self.break_table.setCurrentCell(row, 0)
                return

    def _current_line_break(self) -> Optional[LineBreak]:
        row = self.break_table.currentRow()
        if row < 0:
            return None
        item = self.break_table.item(row, 0)
        if item is None:
            return None
        return item.data(QtCore.Qt.ItemDataRole.UserRole)

    def _on_break_selected(self) -> None:
        lb = self._current_line_break()
        if lb is None:
            return
        self._selected_line_break = lb

    def _reload_line_breaks(self) -> None:
        if self._reload_cb is not None:
            self._line_breaks = list(self._reload_cb() or [])
        self._populate_break_list()
        if self._line_breaks:
            self._selected_line_break = self._line_breaks[0]
        else:
            self._selected_line_break = None
        self._select_line_break(self._selected_line_break)
        self._capture_original_state()
        self._validate_form()

    def _on_apply_quick_clicked(self) -> None:
        if self._apply_quick_cb is None:
            return

        def _refresh() -> None:
            self._reload_line_breaks()

        try:
            self._apply_quick_cb(_refresh)
        except TypeError:
            self._apply_quick_cb()
            _refresh()

    def _edit_all_margins(self, side: str) -> None:
        if side not in ("left", "right"):
            return
        title = "Edit All Left Margins" if side == "left" else "Edit All Right Margins"
        label = "Left margin (mm):" if side == "left" else "Right margin (mm):"
        val = self._prompt_margin_value(title, label, 5.0)
        if val is None:
            return
        defaults = LineBreak()
        for lb in self._line_breaks:
            margin_mm = list(getattr(lb, 'margin_mm', defaults.margin_mm) or defaults.margin_mm)
            if len(margin_mm) < 2:
                margin_mm = [float(margin_mm[0]) if margin_mm else 0.0, 0.0]
            if side == "left":
                margin_mm[0] = float(val)
            else:
                margin_mm[1] = float(val)
            lb.margin_mm = list(margin_mm)
        self._populate_break_list()
        self.valuesChanged.emit()

    def _prompt_margin_value(self, title: str, label: str, initial_value: float) -> Optional[float]:
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setModal(True)
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        text = QtWidgets.QLabel(label, dlg)
        layout.addWidget(text)

        spin = FlexibleDoubleSpinBox(dlg)
        spin.setRange(0.0, 200.0)
        spin.setDecimals(2)
        spin.setSingleStep(0.5)
        spin.setValue(float(initial_value))
        spin.setKeyboardTracking(True)
        layout.addWidget(spin)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=dlg,
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return None
        return float(spin.value())

    def _capture_original_state(self) -> None:
        self._original_state = {}
        for lb in self._line_breaks:
            margin_mm, stave_range, page_break = self._values_from_line_break(lb)
            self._original_state[id(lb)] = (margin_mm, stave_range, page_break)

    def _validate_form(self) -> bool:
        msg = ""
        defaults = LineBreak()
        for lb in self._line_breaks:
            lb_range = getattr(lb, 'stave_range', defaults.stave_range)
            if lb_range == 'auto' or lb_range is True:
                continue
            try:
                low, high = int(lb_range[0]), int(lb_range[1])
            except Exception:
                msg = "Key range must contain two numbers."
                break
            if not (1 <= low <= 88 and 1 <= high <= 88):
                msg = "Key range must stay between key 1 and key 88."
                break
            if low >= high:
                msg = "Key range must have 'from key' lower than 'to key'."
                break

        self.msg_label.setText(msg)
        ok_btn = self.btns.button(QtWidgets.QDialogButtonBox.Ok)
        if ok_btn is not None:
            ok_btn.setEnabled(not bool(msg))
        return not bool(msg)

    def _values_from_line_break(self, lb: LineBreak) -> Tuple[list[float], list[int] | Literal['auto'], bool]:
        defaults = LineBreak()
        margin_mm = list(getattr(lb, 'margin_mm', defaults.margin_mm) or defaults.margin_mm)
        lb_range = getattr(lb, 'stave_range', defaults.stave_range)
        if lb_range == 'auto' or lb_range is True:
            dialog_range: list[int] | Literal['auto'] = 'auto'
        else:
            fallback = 'auto' if defaults.stave_range == 'auto' else list(defaults.stave_range or [0, 0])
            dialog_range = list(lb_range or fallback)
        return margin_mm, dialog_range, bool(getattr(lb, 'page_break', False))

    def restore_original_state(self) -> None:
        for lb in self._line_breaks:
            key = id(lb)
            if key not in self._original_state:
                continue
            margin_mm, stave_range, page_break = self._original_state[key]
            lb.margin_mm = list(margin_mm)
            lb.stave_range = 'auto' if stave_range == 'auto' else list(stave_range)
            lb.page_break = bool(page_break)
        self.valuesChanged.emit()

    def _on_accept_clicked(self) -> None:
        if not self._validate_form():
            return
        self.msg_label.setText("")
        self.accept()
