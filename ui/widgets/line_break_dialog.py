from __future__ import annotations
from typing import Callable, Optional, Tuple, Literal
from PySide6 import QtCore, QtGui, QtWidgets

from file_model.events.line_break import LineBreak


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
        self.apply_quick_btn = QtWidgets.QPushButton("Apply Measure Grouping for each Line", self)
        self.apply_quick_btn.clicked.connect(self._on_apply_quick_clicked)
        quick_row.addWidget(self.apply_quick_btn)
        quick_row.addStretch(1)
        lay.addLayout(quick_row)

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
        self._populate_break_list()
        if self._selected_line_break is None and self._line_breaks:
            self._selected_line_break = self._line_breaks[0]
        self._select_line_break(self._selected_line_break)
        self._capture_original_state()

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

    def _create_margin_spin(self, value: float) -> QtWidgets.QDoubleSpinBox:
        spin = QtWidgets.QDoubleSpinBox(self)
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
        is_auto = bool(lb_range == 'auto' or lb_range is True)
        fallback = 'auto' if defaults.stave_range == 'auto' else list(defaults.stave_range or [0, 0])
        rng = list(lb_range or fallback) if not is_auto else [1, 88]

        wrapper = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        auto_label = QtWidgets.QLabel("(automatic range)", wrapper)
        auto_label.setVisible(is_auto)

        manual_cb = QtWidgets.QCheckBox("Manual", wrapper)
        manual_cb.setChecked(not is_auto)

        low_spin = QtWidgets.QSpinBox(wrapper)
        high_spin = QtWidgets.QSpinBox(wrapper)
        low_spin.setRange(1, 88)
        high_spin.setRange(1, 88)
        low_spin.setValue(int(rng[0]))
        high_spin.setValue(int(rng[1]))
        low_spin.setVisible(not is_auto)
        high_spin.setVisible(not is_auto)

        layout.addWidget(manual_cb)
        layout.addWidget(auto_label)
        layout.addWidget(low_spin)
        layout.addWidget(high_spin)
        layout.addStretch(1)

        def _apply_range_state() -> None:
            is_manual = bool(manual_cb.isChecked())
            auto_label.setVisible(not is_manual)
            low_spin.setVisible(is_manual)
            high_spin.setVisible(is_manual)
            if is_manual:
                lb.stave_range = [int(low_spin.value()), int(high_spin.value())]
            else:
                lb.stave_range = 'auto'
            self.valuesChanged.emit()

        def _range_changed(_v: int) -> None:
            if manual_cb.isChecked():
                lb.stave_range = [int(low_spin.value()), int(high_spin.value())]
                self.valuesChanged.emit()

        manual_cb.toggled.connect(lambda _v: _apply_range_state())
        low_spin.valueChanged.connect(_range_changed)
        high_spin.valueChanged.connect(_range_changed)

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

    def _capture_original_state(self) -> None:
        self._original_state = {}
        for lb in self._line_breaks:
            margin_mm, stave_range, page_break = self._values_from_line_break(lb)
            self._original_state[id(lb)] = (margin_mm, stave_range, page_break)

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
        self.msg_label.setText("")
        self.accept()
