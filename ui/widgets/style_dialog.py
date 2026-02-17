from __future__ import annotations
from dataclasses import asdict, fields
from typing import Any, get_args, get_origin, get_type_hints, Literal, TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from file_model.layout import LAYOUT_FLOAT_CONFIG, LayoutFont
from appdata_manager import get_appdata_manager
from file_model.layout import Layout
from file_model.SCORE import SCORE


FONT_OFFSET_FIELDS = {
    'font_title',
    'font_composer',
    'font_copyright',
    'font_arranger',
    'font_lyricist',
}


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
        self._edit.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"[0-9.,]+"), self))
        self._dec_btn = QtWidgets.QToolButton(self)
        self._dec_btn.setText("-")
        self._inc_btn = QtWidgets.QToolButton(self)
        self._inc_btn.setText("+")
        for btn in (self._dec_btn, self._inc_btn):
            btn.setAutoRepeat(True)
            btn.setAutoRepeatDelay(300)
            btn.setAutoRepeatInterval(75)
            btn.setFixedWidth(28)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._slider, 1)
        layout.addWidget(self._edit, 0)
        layout.addWidget(self._dec_btn, 0)
        layout.addWidget(self._inc_btn, 0)
        self._apply_range()
        self.set_value(value)
        self._slider.valueChanged.connect(self._on_slider_changed)
        self._edit.editingFinished.connect(self._on_edit_finished)
        self._dec_btn.clicked.connect(lambda: self._nudge(-1))
        self._inc_btn.clicked.connect(lambda: self._nudge(1))
        self._slider.installEventFilter(self)

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
            val = float(text.replace(',', '.'))
        except Exception:
            val = self.value()
        val = self._snap(self._clamp(val))
        self.set_value(val)
        self.valueChanged.emit(val)

    def eventFilter(self, obj: QtCore.QObject, ev: QtCore.QEvent) -> bool:
        if obj is self._slider and ev.type() == QtCore.QEvent.Type.Wheel:
            delta = ev.angleDelta().y() or ev.angleDelta().x()
            if delta:
                steps = int(delta / 120)
                if steps != 0:
                    self.set_value(self.value() + steps * self._step)
                    self.valueChanged.emit(self.value())
                    ev.accept()
                    return True
        return super().eventFilter(obj, ev)

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

    def _nudge(self, direction: int) -> None:
        base_step = self._step if self._step > 0 else max((self._max - self._min) / 200.0, 0.01)
        new_val = self.value() + float(direction) * base_step
        self.set_value(new_val)
        self.valueChanged.emit(self.value())


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


class FontPicker(QtWidgets.QWidget):
    valueChanged = QtCore.Signal()

    def __init__(self, value: LayoutFont, parent=None, show_offsets: bool = False) -> None:
        super().__init__(parent)
        self._font_cls = type(value)
        self._show_offsets = bool(show_offsets)
        self._combo = QtWidgets.QFontComboBox(self)
        self._size = QtWidgets.QSpinBox(self)
        self._size.setRange(1, 200)
        try:
            # Emit changes while typing in the spinbox
            self._size.setKeyboardTracking(True)
        except Exception:
            pass
        self._bold = QtWidgets.QCheckBox("Bold", self)
        self._italic = QtWidgets.QCheckBox("Italic", self)
        self._x_offset: FlexibleDoubleSpinBox | None = None
        self._y_offset: FlexibleDoubleSpinBox | None = None
        if self._show_offsets:
            self._x_offset = FlexibleDoubleSpinBox(self)
            self._y_offset = FlexibleDoubleSpinBox(self)
            for spin, axis in ((self._x_offset, 'X'), (self._y_offset, 'Y')):
                spin.setRange(-500.0, 500.0)
                spin.setDecimals(2)
                spin.setSingleStep(0.25)
                spin.setMinimumWidth(70)
                spin.setKeyboardTracking(True)
                spin.setToolTip(f"{axis}-offset (mm)")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._combo, 1)
        layout.addWidget(self._size, 0)
        layout.addWidget(self._bold, 0)
        layout.addWidget(self._italic, 0)
        if self._show_offsets and self._x_offset and self._y_offset:
            layout.addWidget(self._x_offset, 0)
            layout.addWidget(self._y_offset, 0)

        self.set_value(value)
        self._combo.currentFontChanged.connect(lambda _f: self.valueChanged.emit())
        self._size.valueChanged.connect(lambda _v: self.valueChanged.emit())
        try:
            self._size.editingFinished.connect(lambda: self.valueChanged.emit())
        except Exception:
            pass
        self._bold.stateChanged.connect(lambda _v: self.valueChanged.emit())
        self._italic.stateChanged.connect(lambda _v: self.valueChanged.emit())
        if self._show_offsets and self._x_offset and self._y_offset:
            self._x_offset.valueChanged.connect(lambda _v: self.valueChanged.emit())
            self._y_offset.valueChanged.connect(lambda _v: self.valueChanged.emit())

    def set_value(self, value: LayoutFont) -> None:
        try:
            self._combo.setCurrentFont(QtGui.QFont(str(value.family)))
        except Exception:
            pass
        try:
            self._size.setValue(int(value.size_pt))
        except Exception:
            self._size.setValue(10)
        self._bold.setChecked(bool(value.bold))
        self._italic.setChecked(bool(value.italic))
        if self._show_offsets and self._x_offset and self._y_offset:
            try:
                self._x_offset.setValue(float(getattr(value, 'x_offset', 0.0) or 0.0))
                self._y_offset.setValue(float(getattr(value, 'y_offset', 0.0) or 0.0))
            except Exception:
                self._x_offset.setValue(0.0)
                self._y_offset.setValue(0.0)

    def set_family(self, family: str) -> None:
        self._combo.setCurrentFont(QtGui.QFont(str(family)))

    def value(self) -> LayoutFont:
        font_cls = self._font_cls or LayoutFont
        x_off = float(self._x_offset.value()) if self._x_offset is not None else 0.0
        y_off = float(self._y_offset.value()) if self._y_offset is not None else 0.0
        return font_cls(
            family=str(self._combo.currentFont().family()),
            size_pt=float(self._size.value()),
            bold=bool(self._bold.isChecked()),
            italic=bool(self._italic.isChecked()),
            x_offset=x_off,
            y_offset=y_off,
        )


class StyleDialog(QtWidgets.QDialog):
    values_changed = QtCore.Signal()
    tab_changed = QtCore.Signal(int)

    def __init__(self, parent=None, layout: Layout | None = None, score: SCORE | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Style")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)
        try:
            screen = QtWidgets.QApplication.primaryScreen()
            if screen is not None:
                max_h = int(screen.availableGeometry().height() / 3)
        except Exception:
            pass
        try:
            self.setMinimumWidth(600)
            self.resize(750, 400)
        except Exception:
            pass

        self._layout = layout or Layout()
        self._editors: dict[str, QtWidgets.QWidget] = {}
        self._score: SCORE | None = score
        self._tab_scrolls: list[QtWidgets.QScrollArea] = []
        self._tab_contents: list[QtWidgets.QWidget] = []
        self._tabs: QtWidgets.QTabWidget | None = None
        self._applying_style: bool = False
        self._all_fonts_combo: QtWidgets.QFontComboBox | None = None

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        tabs = QtWidgets.QTabWidget(self)
        self._tabs = tabs
        lay.addWidget(tabs, 1)
        try:
            tabs.currentChanged.connect(self.tab_changed.emit)
        except Exception:
            pass

        tab_order = [
            "Page",
            "Grid",
            "Time signature",
            "Stave",
            "Fonts",
            "Note",
            "Grace note",
            "Beam",
            "Slur",
            "Text",
            "Countline",
            "Pedal",
        ]

        def _make_tab(title: str) -> QtWidgets.QFormLayout:
            tab = QtWidgets.QWidget(self)
            tab_layout = QtWidgets.QVBoxLayout(tab)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(6)
            scroll = QtWidgets.QScrollArea(tab)
            scroll.setWidgetResizable(True)
            content = QtWidgets.QWidget(scroll)
            form = QtWidgets.QFormLayout(content)
            form.setContentsMargins(8, 8, 8, 8)
            form.setSpacing(6)
            content.setLayout(form)
            scroll.setWidget(content)
            tab_layout.addWidget(scroll, 1)
            tabs.addTab(tab, title)
            self._tab_scrolls.append(scroll)
            self._tab_contents.append(content)
            return form

        tab_forms: dict[str, QtWidgets.QFormLayout] = {t: _make_tab(t) for t in tab_order}

        field_tabs: dict[str, str] = {
            # Page
            'page_width_mm': 'Page',
            'page_height_mm': 'Page',
            'page_top_margin_mm': 'Page',
            'page_bottom_margin_mm': 'Page',
            'page_left_margin_mm': 'Page',
            'page_right_margin_mm': 'Page',
            'header_height_mm': 'Page',
            'footer_height_mm': 'Page',
            'scale': 'Page',
            # Note
            'black_note_rule': 'Note',
            'note_head_visible': 'Note',
            'note_stem_visible': 'Note',
            'note_stem_length_semitone': 'Note',
            'note_stem_thickness_mm': 'Note',
            'note_stopsign_thickness_mm': 'Note',
            'note_continuation_dot_size_mm': 'Note',
            'note_leftdot_visible': 'Note',
            'note_midinote_visible': 'Note',
            'note_midinote_left_color': 'Note',
            'note_midinote_right_color': 'Note',
            # Beam
            'beam_visible': 'Beam',
            'beam_thickness_mm': 'Beam',
            # Pedal
            'pedal_lane_enabled': 'Pedal',
            'pedal_lane_width_mm': 'Pedal',
            # Grace note
            'grace_note_visible': 'Grace note',
            'grace_note_outline_width_mm': 'Grace note',
            'grace_note_scale': 'Grace note',
            # Text
            'text_visible': 'Text',
            'text_font_family': 'Text',
            'text_font_size_pt': 'Text',
            # Slur
            'slur_visible': 'Slur',
            'slur_width_sides_mm': 'Slur',
            'slur_width_middle_mm': 'Slur',
            # Countline
            'countline_visible': 'Countline',
            'countline_dash_pattern': 'Countline',
            'countline_thickness_mm': 'Countline',
            # Grid
            'grid_barline_thickness_mm': 'Grid',
            'grid_gridline_thickness_mm': 'Grid',
            'grid_gridline_dash_pattern_mm': 'Grid',
            'repeat_start_visible': 'Grid',
            'repeat_end_visible': 'Grid',
            # Time signature
            'time_signature_indicator_type': 'Time signature',
            'time_signature_indicator_lane_width_mm': 'Time signature',
            'time_signature_indicator_guide_thickness_mm': 'Time signature',
            'time_signature_indicator_divide_guide_thickness_mm': 'Time signature',
            # Stave
            'stave_two_line_thickness_mm': 'Stave',
            'stave_three_line_thickness_mm': 'Stave',
            'stave_clef_line_dash_pattern_mm': 'Stave',
            # Fonts
            'font_title': 'Fonts',
            'font_composer': 'Fonts',
            'font_copyright': 'Fonts',
            'font_arranger': 'Fonts',
            'font_lyricist': 'Fonts',
            'time_signature_indicator_classic_font': 'Fonts',
            'time_signature_indicator_klavarskribo_font': 'Fonts',
            'measure_numbering_font': 'Fonts',
        }

        type_hints = {}
        try:
            type_hints = get_type_hints(Layout)
        except Exception:
            type_hints = {}
        self._type_hints = type_hints
        _hide_fields = {
            "measure_grouping",
        }
        for f in fields(Layout):
            name = f.name
            if name in _hide_fields:
                continue
            label = name.replace('_', ' ').capitalize() + ":"
            value = getattr(self._layout, name)
            field_type = type_hints.get(name, f.type)
            editor = self._make_editor(field_type, value, name)
            if editor is None:
                continue
            self._editors[name] = editor
            tab_name = field_tabs.get(name, 'Page')
            form = tab_forms.get(tab_name, tab_forms['Page'])
            form.addRow(QtWidgets.QLabel(label, self), editor)
            self._wire_editor_change(editor)

        self._add_all_fonts_control(tab_forms.get('Fonts'))

        action_row = QtWidgets.QHBoxLayout()
        self._action_row = action_row
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)
        self.style_combo = QtWidgets.QComboBox(self)
        action_row.addWidget(self.style_combo, 1)
        self.new_style_btn = QtWidgets.QPushButton("New Style", self)
        self.save_style_btn = QtWidgets.QPushButton("Save Style", self)
        self.clear_styles_btn = QtWidgets.QPushButton("Clear Styles", self)
        action_row.addWidget(self.new_style_btn, 0)
        action_row.addWidget(self.save_style_btn, 0)
        action_row.addWidget(self.clear_styles_btn, 0)
        action_row.addStretch(1)
        lay.addLayout(action_row)

        self.msg_label = QtWidgets.QLabel("", self)
        pal = self.msg_label.palette()
        pal.setColor(self.msg_label.foregroundRole(), QtCore.Qt.GlobalColor.darkGreen)
        self.msg_label.setPalette(pal)
        lay.addWidget(self.msg_label)

        self.btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self,
        )
        self.btns.accepted.connect(self._on_accept_clicked)
        self.btns.rejected.connect(self.reject)
        lay.addWidget(self.btns)

        self.new_style_btn.clicked.connect(self._new_style)
        self.save_style_btn.clicked.connect(self._save_style)
        self.clear_styles_btn.clicked.connect(self._clear_custom_styles)
        try:
            self.style_combo.currentTextChanged.connect(self._on_style_selected)
        except Exception:
            pass
        try:
            self.values_changed.connect(self._on_values_changed)
        except Exception:
            pass
        QtCore.QTimer.singleShot(0, self._init_styles_ui)
        QtCore.QTimer.singleShot(0, self._fit_to_contents)

    # ---- Style name helpers ----
    def _normalize_style_name(self, name: str) -> str:
        nm = str(name or "").strip()
        # Collapse internal whitespace
        nm = " ".join(nm.split())
        return nm

    def _validate_style_name(self, name: str) -> tuple[bool, str]:
        nm = self._normalize_style_name(name)
        if not nm:
            return False, "Style name cannot be empty."
        if nm == "keyTAB":
            return False, "'keyTAB' is reserved for the factory style."
        # Basic character policy: letters, digits, spaces, - _ .
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.")
        if any(ch not in allowed for ch in nm):
            return False, "Style name contains invalid characters."
        if len(nm) > 48:
            return False, "Style name is too long (max 48)."
        return True, nm

    def _confirm_overwrite(self, name: str) -> bool:
        try:
            resp = QtWidgets.QMessageBox.question(
                self,
                "Overwrite Style",
                f"A style named '{name}' already exists. Overwrite it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            return resp == QtWidgets.QMessageBox.Yes
        except Exception:
            return True

    def _fit_to_contents(self) -> None:
        tabs = self._tabs
        if tabs is None or not self._tab_scrolls or not self._tab_contents:
            return
        try:
            screen = QtWidgets.QApplication.primaryScreen()
            max_h = int(screen.availableGeometry().height()) if screen is not None else 800
            max_w = int(screen.availableGeometry().width()) if screen is not None else 1200
        except Exception:
            max_h = 800
            max_w = 1200

        max_content_h = 0
        max_content_w = 0
        for content in self._tab_contents:
            try:
                max_content_h = max(max_content_h, int(content.sizeHint().height()))
                max_content_w = max(max_content_w, int(content.sizeHint().width()))
            except Exception:
                continue

        tab_bar_h = int(tabs.tabBar().sizeHint().height())
        tab_bar_w = int(tabs.tabBar().sizeHint().width())
        action_h = int(self._action_row.sizeHint().height()) if hasattr(self, '_action_row') else 0
        action_w = int(self._action_row.sizeHint().width()) if hasattr(self, '_action_row') else 0
        msg_h = int(self.msg_label.sizeHint().height())
        msg_w = int(self.msg_label.sizeHint().width())
        btns_h = int(self.btns.sizeHint().height())
        btns_w = int(self.btns.sizeHint().width())

        lay = self.layout()
        margins = lay.contentsMargins() if lay is not None else QtCore.QMargins()
        spacing = int(lay.spacing()) if lay is not None else 0
        gaps = 3

        non_scroll_h = margins.top() + margins.bottom() + tab_bar_h + action_h + msg_h + btns_h + (spacing * gaps)
        desired_scroll_h = max_content_h
        max_scroll_h = max(1, max_h - non_scroll_h)
        scroll_h = min(desired_scroll_h, max_scroll_h)

        non_scroll_w = margins.left() + margins.right()
        desired_w = max(tab_bar_w, max_content_w, action_w, msg_w, btns_w) + non_scroll_w
        total_w = min(desired_w, max_w)

        for scroll in self._tab_scrolls:
            frame = int(scroll.frameWidth()) * 2
            scroll.setMinimumHeight(scroll_h + frame)
            scroll.setMaximumHeight(scroll_h + frame)
            scroll.setMinimumWidth(total_w - non_scroll_w + frame)
            scroll.setMaximumWidth(total_w - non_scroll_w + frame)

        total_h = non_scroll_h + scroll_h
        if total_h > max_h:
            total_h = max_h
        self.setMinimumHeight(total_h)
        self.setMaximumHeight(total_h)
        self.setMinimumWidth(total_w)
        self.setMaximumWidth(total_w)
        self.resize(total_w, total_h)

    def set_current_tab(self, index: int) -> None:
        tabs = self._tabs
        if tabs is None:
            return
        try:
            safe = max(0, min(int(index), tabs.count() - 1))
            tabs.setCurrentIndex(safe)
        except Exception:
            pass

    def current_tab_index(self) -> int:
        tabs = self._tabs
        if tabs is None:
            return 0
        try:
            return int(tabs.currentIndex())
        except Exception:
            return 0

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
            try:
                # Ensure immediate updates while typing
                sb.setKeyboardTracking(True)
            except Exception:
                pass
            return sb

        if field_type is float:
            if field_name in LAYOUT_FLOAT_CONFIG:
                cfg = LAYOUT_FLOAT_CONFIG[field_name]
                return FloatSliderEdit(float(value), cfg['min'], cfg['max'], cfg['step'], self)
            is_mm = field_name.endswith('_mm')
            is_pt = field_name.endswith('_pt')
            if is_mm:
                return FloatSliderEdit(float(value), 0.0, 1000.0, 0.25, self)
            if is_pt:
                return FloatSliderEdit(float(value), 1.0, 200.0, 0.5, self)
            return FloatSliderEdit(float(value), -1000.0, 1000.0, 0.01, self)

        if field_type is str and (field_name.startswith('color_') or field_name.endswith('_color')):
            return ColorPickerEdit(str(value or ''), self)

        if field_type is str:
            le = QtWidgets.QLineEdit(self)
            le.setText(str(value) if value is not None else "")
            return le

        if field_type is LayoutFont:
            if isinstance(value, dict):
                try:
                    value = LayoutFont(**value)
                except Exception:
                    value = LayoutFont()
            show_offsets = field_name in FONT_OFFSET_FIELDS
            return FontPicker(value, self, show_offsets=show_offsets)

        if origin is list and args and args[0] is float:
            le = QtWidgets.QLineEdit(self)
            le.setText(self._format_float_list(value))
            le.setValidator(
                QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"[0-9., ]*"), self)
            )
            return le

        return None

    def _wire_editor_change(self, editor: QtWidgets.QWidget) -> None:
        try:
            if isinstance(editor, QtWidgets.QCheckBox):
                editor.stateChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, QtWidgets.QSpinBox):
                editor.valueChanged.connect(lambda _v: self.values_changed.emit())
                try:
                    editor.editingFinished.connect(lambda: self.values_changed.emit())
                except Exception:
                    pass
            elif isinstance(editor, FloatSliderEdit):
                editor.valueChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, FontPicker):
                editor.valueChanged.connect(lambda: self.values_changed.emit())
            elif isinstance(editor, QtWidgets.QComboBox):
                editor.currentTextChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, QtWidgets.QLineEdit):
                editor.textChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(editor, ColorPickerEdit):
                editor.valueChanged.connect(lambda _v: self.values_changed.emit())
        except Exception:
            pass

    def _add_all_fonts_control(self, form: QtWidgets.QFormLayout | None) -> None:
        if form is None:
            return
        label = QtWidgets.QLabel("Apply family to all fonts:", self)
        combo = QtWidgets.QFontComboBox(self)
        self._all_fonts_combo = combo
        try:
            font_title = getattr(self._layout, 'font_title', LayoutFont())
            combo.setCurrentFont(QtGui.QFont(str(font_title.family)))
        except Exception:
            pass
        combo.currentFontChanged.connect(lambda f: self._set_all_font_families(f.family()))
        try:
            form.insertRow(0, label, combo)
        except Exception:
            form.addRow(label, combo)

    def _set_all_font_families(self, family: str) -> None:
        if not family:
            return
        for editor in self._editors.values():
            if isinstance(editor, FontPicker):
                editor.blockSignals(True)
                editor.set_family(family)
                editor.blockSignals(False)
        self.values_changed.emit()

    def _set_editor_value(self, editor: QtWidgets.QWidget, field_type: Any, value: Any) -> None:
        origin = get_origin(field_type)
        args = get_args(field_type)
        if isinstance(editor, QtWidgets.QCheckBox):
            editor.setChecked(bool(value))
        elif isinstance(editor, QtWidgets.QSpinBox):
            try:
                editor.setValue(int(value))
            except Exception:
                pass
        elif isinstance(editor, FloatSliderEdit):
            try:
                editor.set_value(float(value))
            except Exception:
                pass
        elif isinstance(editor, FontPicker):
            try:
                # Convert dict payloads to LayoutFont when loading from appdata
                if isinstance(value, dict):
                    try:
                        value = LayoutFont(**value)
                    except Exception:
                        pass
                editor.set_value(value)
            except Exception:
                pass
        elif isinstance(editor, ColorPickerEdit):
            editor.set_value(str(value or ''))
        elif origin is list and args and args[0] is float and isinstance(editor, QtWidgets.QLineEdit):
            editor.setText(self._format_float_list(value))
        elif isinstance(editor, QtWidgets.QComboBox):
            try:
                editor.setCurrentText(str(value))
            except Exception:
                pass
        elif isinstance(editor, QtWidgets.QLineEdit):
            editor.setText(str(value) if value is not None else "")

    def _apply_layout_to_editors(self, layout_obj: Layout) -> None:
        for f in fields(Layout):
            name = f.name
            editor = self._editors.get(name)
            if editor is None:
                continue
            field_type = self._type_hints.get(name, f.type)
            value = getattr(layout_obj, name, None)
            self._set_editor_value(editor, field_type, value)
        if self._all_fonts_combo is not None:
            try:
                self._all_fonts_combo.blockSignals(True)
                font_title = getattr(layout_obj, 'font_title', LayoutFont())
                self._all_fonts_combo.setCurrentFont(QtGui.QFont(str(font_title.family)))
            finally:
                self._all_fonts_combo.blockSignals(False)
        self.values_changed.emit()

    def _build_style_template(self) -> dict:
        base: dict = {}
        try:
            if self._score is not None:
                base = dict(self._score.get_dict() or {})
        except Exception:
            base = {}
        base.pop('events', None)
        try:
            bg_list = base.get('base_grid')
            if isinstance(bg_list, list):
                for bg in bg_list:
                    if isinstance(bg, dict):
                        bg['measure_amount'] = 1
        except Exception:
            pass
        try:
            base['layout'] = asdict(self.get_values())
        except Exception:
            base['layout'] = self.get_values().__dict__
        return base

    def _save_custom_style(self) -> None:
        try:
            name, ok = QtWidgets.QInputDialog.getText(self, "Save Custom Style", "Style name:")
            if not ok:
                return
            valid, nm_or_msg = self._validate_style_name(str(name))
            if not valid:
                self.msg_label.setText(nm_or_msg)
                return
            name = nm_or_msg
            layout_dict = asdict(self.get_values())
            adm = get_appdata_manager()
            styles = adm.get("user_styles", []) or []
            if not isinstance(styles, list):
                styles = []
            # Replace if exists, else append
            found = False
            for s in styles:
                if isinstance(s, dict) and str(s.get("name", "")) == name:
                    # Confirm overwrite
                    if not self._confirm_overwrite(name):
                        self.msg_label.setText("Save cancelled.")
                        return
                    s["layout"] = layout_dict
                    found = True
                    break
            if not found:
                styles.append({"name": name, "layout": layout_dict})
            adm.set("user_styles", styles)
            adm.set("selected_style_name", name)
            adm.save()
            # Update combo and select
            self._populate_styles_combo(styles)
            try:
                self.style_combo.setCurrentText(name)
            except Exception:
                pass
            # Apply immediately
            self._apply_style_by_name(name)
            self.msg_label.setText(f"Saved and applied style '{name}'.")
        except Exception:
            self.msg_label.setText("Failed to save style.")

    def _new_style(self) -> None:
        # Create a new named style from current dialog values and select it
        self._save_custom_style()

    def _save_style(self) -> None:
        # Save current values into the selected style; if 'keyTAB', ask for new name
        try:
            current = str(self.style_combo.currentText() or '').strip()
            if not current or current in ('keyTAB', 'Custom Style'):
                # Treat save on factory selection as "New Style"
                self._save_custom_style()
                return
            layout_dict = asdict(self.get_values())
            adm = get_appdata_manager()
            styles = adm.get("user_styles", []) or []
            if not isinstance(styles, list):
                styles = []
            updated = False
            for s in styles:
                if isinstance(s, dict) and str(s.get('name','')) == current:
                    s['layout'] = layout_dict
                    updated = True
                    break
            if not updated:
                # If the selected name vanished, create it
                styles.append({"name": current, "layout": layout_dict})
            adm.set("user_styles", styles)
            adm.set("selected_style_name", current)
            adm.save()
            self._populate_styles_combo(styles)
            try:
                self.style_combo.setCurrentText(current)
            except Exception:
                pass
            self._apply_style_by_name(current)
            self.msg_label.setText(f"Saved style '{current}'.")
        except Exception:
            self.msg_label.setText("Failed to save style.")

    def _init_styles_ui(self) -> None:
        try:
            adm = get_appdata_manager()
            styles = adm.get("user_styles", []) or []
            if not isinstance(styles, list):
                styles = []
            self._populate_styles_combo(styles)
            # Do not auto-apply any preset at startup; reflect current file model
            try:
                self.style_combo.setCurrentText('Custom Style')
            except Exception:
                pass
        except Exception:
            pass

    def _populate_styles_combo(self, styles: list) -> None:
        try:
            self.style_combo.blockSignals(True)
            self.style_combo.clear()
            # Always include custom marker and factory default
            self.style_combo.addItem('Custom Style')
            self.style_combo.addItem('keyTAB')
            # Append user styles by name
            names = []
            for s in styles:
                if isinstance(s, dict):
                    nm = str(s.get('name', '')).strip()
                    if nm:
                        names.append(nm)
            # Deduplicate preserving order
            seen = set()
            for nm in names:
                if nm in seen:
                    continue
                seen.add(nm)
                self.style_combo.addItem(nm)
        finally:
            self.style_combo.blockSignals(False)

    def _style_dict_by_name(self, name: str) -> dict | None:
        try:
            adm = get_appdata_manager()
            styles = adm.get("user_styles", []) or []
            if not isinstance(styles, list):
                return None
            for s in styles:
                if isinstance(s, dict) and str(s.get('name', '')) == name:
                    return s
            return None
        except Exception:
            return None

    def _apply_style_by_name(self, name: str) -> None:
        if str(name) == 'keyTAB' or not name:
            try:
                self._applying_style = True
                self._apply_layout_to_editors(Layout())
                self._applying_style = False
                self.msg_label.setText("Applied factory style.")
            except Exception:
                self.msg_label.setText("Failed to apply factory style.")
            try:
                adm = get_appdata_manager()
                adm.set("selected_style_name", "keyTAB")
                adm.save()
            except Exception:
                pass
            return
        s = self._style_dict_by_name(str(name))
        if not isinstance(s, dict):
            self.msg_label.setText("Style not found.")
            return
        lay = s.get('layout')
        if not isinstance(lay, dict):
            self.msg_label.setText("Invalid style layout.")
            return
        try:
            self._applying_style = True
            self._apply_layout_to_editors(Layout(**lay))
            self._applying_style = False
            try:
                self.values_changed.emit()
            except Exception:
                pass
            self.msg_label.setText(f"Applied style '{name}'.")
            try:
                adm = get_appdata_manager()
                adm.set("selected_style_name", str(name))
                adm.save()
            except Exception:
                pass
        except Exception:
            self.msg_label.setText("Failed to apply style.")

    def _on_style_selected(self, name: str) -> None:
        nm = str(name or '')
        if nm == 'Custom Style':
            # Do not apply; reflect that edits are custom/unsaved
            try:
                adm = get_appdata_manager()
                adm.set("selected_style_name", "custom")
                adm.save()
            except Exception:
                pass
            return
        self._apply_style_by_name(nm)

    def _on_values_changed(self) -> None:
        # If user edits while a preset is selected, switch to Custom Style marker
        if self._applying_style:
            return
        try:
            current = str(self.style_combo.currentText() or '')
            if current != 'Custom Style':
                self.style_combo.blockSignals(True)
                self.style_combo.setCurrentText('Custom Style')
                self.style_combo.blockSignals(False)
                try:
                    adm = get_appdata_manager()
                    adm.set("selected_style_name", "custom")
                    adm.save()
                except Exception:
                    pass
        except Exception:
            pass

    def _clear_custom_styles(self) -> None:
        try:
            resp = QtWidgets.QMessageBox.question(
                self,
                "Clear Custom Styles",
                "Are you sure you want to remove all custom styles?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if resp != QtWidgets.QMessageBox.Yes:
                return
            adm = get_appdata_manager()
            adm.set("user_styles", [])
            adm.set("selected_style_name", "keyTAB")
            adm.save()
            self._populate_styles_combo([])
            try:
                self.style_combo.setCurrentText('keyTAB')
            except Exception:
                pass
            self._apply_style_by_name('keyTAB')
            self.msg_label.setText("Cleared styles.")
        except Exception:
            self.msg_label.setText("Failed to clear styles.")

    def _delete_selected_style(self) -> None:
        try:
            name = str(self.style_combo.currentText() or '').strip()
            if not name or name == 'keyTAB':
                # Ignore deletion for factory style
                self.msg_label.setText("Cannot delete factory style.")
                return
            adm = get_appdata_manager()
            styles = adm.get("user_styles", []) or []
            if not isinstance(styles, list):
                styles = []
            styles = [s for s in styles if not (isinstance(s, dict) and str(s.get('name','')) == name)]
            adm.set("user_styles", styles)
            adm.set("selected_style_name", "keyTAB")
            adm.save()
            self._populate_styles_combo(styles)
            try:
                self.style_combo.setCurrentText('keyTAB')
            except Exception:
                pass
            self._apply_style_by_name('keyTAB')
            self.msg_label.setText(f"Deleted style '{name}'.")
        except Exception:
            self.msg_label.setText("Failed to delete style.")

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
            elif isinstance(editor, FontPicker):
                data[name] = editor.value()
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
