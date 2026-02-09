from __future__ import annotations
from dataclasses import asdict, fields
from typing import Any, get_args, get_origin, get_type_hints, Literal, TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from file_model.layout import LAYOUT_FLOAT_CONFIG
from appdata_manager import get_appdata_manager
from file_model.header import Header, HeaderText, FontSpec
from file_model.layout import Layout
from file_model.SCORE import SCORE


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


class FontPicker(QtWidgets.QWidget):
    valueChanged = QtCore.Signal()

    def __init__(self, value: FontSpec, parent=None) -> None:
        super().__init__(parent)
        self._combo = QtWidgets.QFontComboBox(self)
        self._size = QtWidgets.QSpinBox(self)
        self._size.setRange(1, 200)
        self._bold = QtWidgets.QCheckBox("Bold", self)
        self._italic = QtWidgets.QCheckBox("Italic", self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._combo, 1)
        layout.addWidget(self._size, 0)
        layout.addWidget(self._bold, 0)
        layout.addWidget(self._italic, 0)

        self.set_value(value)
        self._combo.currentFontChanged.connect(lambda _f: self.valueChanged.emit())
        self._size.valueChanged.connect(lambda _v: self.valueChanged.emit())
        self._bold.stateChanged.connect(lambda _v: self.valueChanged.emit())
        self._italic.stateChanged.connect(lambda _v: self.valueChanged.emit())

    def set_value(self, value: FontSpec) -> None:
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

    def value(self) -> FontSpec:
        return FontSpec(
            family=str(self._combo.currentFont().family()),
            size_pt=float(self._size.value()),
            bold=bool(self._bold.isChecked()),
            italic=bool(self._italic.isChecked()),
        )


class StyleDialog(QtWidgets.QDialog):
    values_changed = QtCore.Signal()
    tab_changed = QtCore.Signal(int)

    def __init__(self, parent=None, layout: Layout | None = None, header: Header | None = None, score: SCORE | None = None) -> None:
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
        self._header = header or Header()
        self._editors: dict[str, QtWidgets.QWidget] = {}
        self._score: SCORE | None = score
        self._tab_scrolls: list[QtWidgets.QScrollArea] = []
        self._tab_contents: list[QtWidgets.QWidget] = []
        self._tabs: QtWidgets.QTabWidget | None = None

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
            "Stave",
            "Titles",
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

        fonts_form = tab_forms.get("Titles")
        self._title_text = QtWidgets.QLineEdit(self)
        self._composer_text = QtWidgets.QLineEdit(self)
        self._copyright_text = QtWidgets.QLineEdit(self)
        self._title_font = FontPicker(self._header.title, self)
        self._composer_font = FontPicker(self._header.composer, self)
        self._copyright_font = FontPicker(self._header.copyright, self)
        self._title_text.setText(str(self._header.title.text))
        self._composer_text.setText(str(self._header.composer.text))
        self._copyright_text.setText(str(self._header.copyright.text))
        if fonts_form is not None:
            fonts_form.addRow(QtWidgets.QLabel("Title text:", self), self._title_text)
            fonts_form.addRow(QtWidgets.QLabel("Title font:", self), self._title_font)
            fonts_form.addRow(QtWidgets.QLabel("Composer text:", self), self._composer_text)
            fonts_form.addRow(QtWidgets.QLabel("Composer font:", self), self._composer_font)
            fonts_form.addRow(QtWidgets.QLabel("Copyright text:", self), self._copyright_text)
            fonts_form.addRow(QtWidgets.QLabel("Copyright font:", self), self._copyright_font)
        self._wire_header_change(self._title_text)
        self._wire_header_change(self._composer_text)
        self._wire_header_change(self._copyright_text)
        self._wire_header_change(self._title_font)
        self._wire_header_change(self._composer_font)
        self._wire_header_change(self._copyright_font)

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
            'time_signature_indicator_type': 'Grid',
            'repeat_start_visible': 'Grid',
            'repeat_end_visible': 'Grid',
            # Stave
            'stave_two_line_thickness_mm': 'Stave',
            'stave_three_line_thickness_mm': 'Stave',
            'stave_clef_line_dash_pattern_mm': 'Stave',
        }

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
            tab_name = field_tabs.get(name, 'Page')
            form = tab_forms.get(tab_name, tab_forms['Page'])
            form.addRow(QtWidgets.QLabel(label, self), editor)
            self._wire_editor_change(editor)

        action_row = QtWidgets.QHBoxLayout()
        self._action_row = action_row
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)
        self.apply_default_btn = QtWidgets.QPushButton("Apply Default Style", self)
        self.save_default_btn = QtWidgets.QPushButton("Save Style as Default", self)
        self.reset_default_btn = QtWidgets.QPushButton("Reset Factory Defaults", self)
        action_row.addWidget(self.apply_default_btn, 0)
        action_row.addWidget(self.save_default_btn, 0)
        action_row.addWidget(self.reset_default_btn, 0)
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

        self.save_default_btn.clicked.connect(self._save_style_default)
        self.reset_default_btn.clicked.connect(self._reset_factory_defaults)
        self.apply_default_btn.clicked.connect(self._apply_default_style)
        QtCore.QTimer.singleShot(0, self._fit_to_contents)

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

    def _wire_header_change(self, widget: QtWidgets.QWidget) -> None:
        try:
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.textChanged.connect(lambda _v: self.values_changed.emit())
            elif isinstance(widget, FontPicker):
                widget.valueChanged.connect(lambda: self.values_changed.emit())
        except Exception:
            pass

    def _apply_header_to_editors(self, header_obj: Header) -> None:
        self._header = header_obj
        self._title_text.setText(str(header_obj.title.text))
        self._composer_text.setText(str(header_obj.composer.text))
        self._copyright_text.setText(str(header_obj.copyright.text))
        self._title_font.set_value(header_obj.title)
        self._composer_font.set_value(header_obj.composer)
        self._copyright_font.set_value(header_obj.copyright)
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
            base['layout'] = asdict(self.get_values())
        except Exception:
            base['layout'] = self.get_values().__dict__
        try:
            header = self.get_header_values()
            base['header'] = asdict(header)
        except Exception:
            pass
        return base

    def _save_style_default(self) -> None:
        try:
            layout = self.get_values()
            template = {k: getattr(layout, k) for k in layout.__dataclass_fields__.keys()}
            adm = get_appdata_manager()
            adm.set("layout_template", template)
            adm.set("score_template", self._build_style_template())
            adm.save()
            self.msg_label.setText("Saved style defaults.")
        except Exception:
            self.msg_label.setText("Failed to save defaults.")

    def _apply_default_style(self) -> None:
        try:
            adm = get_appdata_manager()
            template = adm.get("score_template", {})
            applied = False
            if isinstance(template, dict) and template:
                data = dict(template)
                data.pop('events', None)
                data.pop('base_grid', None)

                layout_data = data.get('layout')
                if isinstance(layout_data, dict):
                    try:
                        self._apply_layout_to_editors(Layout(**layout_data))
                        applied = True
                    except Exception:
                        pass

                header_data = data.get('header')
                if isinstance(header_data, dict):
                    def _text_from(d: dict | None, fallback: HeaderText) -> HeaderText:
                        if not isinstance(d, dict):
                            return fallback
                        return HeaderText(
                            text=str(d.get('text', fallback.text)),
                            family=str(d.get('family', fallback.family)),
                            size_pt=float(d.get('size_pt', fallback.size_pt)),
                            bold=bool(d.get('bold', fallback.bold)),
                            italic=bool(d.get('italic', fallback.italic)),
                            x_offset_mm=float(d.get('x_offset_mm', fallback.x_offset_mm)),
                            y_offset_mm=float(d.get('y_offset_mm', fallback.y_offset_mm)),
                        )
                    base = Header()
                    header_obj = Header(
                        title=_text_from(header_data.get('title') if isinstance(header_data, dict) else None, base.title),
                        composer=_text_from(header_data.get('composer') if isinstance(header_data, dict) else None, base.composer),
                        copyright=_text_from(header_data.get('copyright') if isinstance(header_data, dict) else None, base.copyright),
                    )
                    self._apply_header_to_editors(header_obj)
                    applied = True

            if not applied:
                layout_template = adm.get("layout_template", {})
                if isinstance(layout_template, dict) and layout_template:
                    try:
                        self._apply_layout_to_editors(Layout(**layout_template))
                        applied = True
                    except Exception:
                        pass

            self.msg_label.setText("Applied default style." if applied else "No default style found.")
        except Exception:
            self.msg_label.setText("Failed to apply defaults.")

    def _reset_factory_defaults(self) -> None:
        try:
            try:
                adm = get_appdata_manager()
                adm.remove("layout_template")
                adm.remove("score_template")
                adm.save()
            except Exception:
                pass
            self._apply_layout_to_editors(Layout())
            self._apply_header_to_editors(Header())
            self.msg_label.setText("")
        except Exception:
            self.msg_label.setText("Failed to reset defaults.")

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

    def get_header_values(self) -> Header:
        title_font = self._title_font.value()
        composer_font = self._composer_font.value()
        copyright_font = self._copyright_font.value()
        title = HeaderText(
            text=str(self._title_text.text()),
            family=title_font.family,
            size_pt=title_font.size_pt,
            bold=title_font.bold,
            italic=title_font.italic,
            x_offset_mm=float(getattr(self._header.title, 'x_offset_mm', 0.0) or 0.0),
            y_offset_mm=float(getattr(self._header.title, 'y_offset_mm', 0.0) or 0.0),
        )
        composer = HeaderText(
            text=str(self._composer_text.text()),
            family=composer_font.family,
            size_pt=composer_font.size_pt,
            bold=composer_font.bold,
            italic=composer_font.italic,
            x_offset_mm=float(getattr(self._header.composer, 'x_offset_mm', 0.0) or 0.0),
            y_offset_mm=float(getattr(self._header.composer, 'y_offset_mm', 0.0) or 0.0),
        )
        copyright_text = HeaderText(
            text=str(self._copyright_text.text()),
            family=copyright_font.family,
            size_pt=copyright_font.size_pt,
            bold=copyright_font.bold,
            italic=copyright_font.italic,
            x_offset_mm=float(getattr(self._header.copyright, 'x_offset_mm', 0.0) or 0.0),
            y_offset_mm=float(getattr(self._header.copyright, 'y_offset_mm', 0.0) or 0.0),
        )
        return Header(title=title, composer=composer, copyright=copyright_text)

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
