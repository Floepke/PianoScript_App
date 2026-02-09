from __future__ import annotations

from PySide6 import QtCore, QtWidgets
import sys

from settings_manager import get_preferences_manager
from ui.style import Style
from fonts import install_default_ui_font


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(550, 420)

        self._pm = get_preferences_manager()
        self._initial_values = dict(self._pm._values)
        self._fields: dict[str, tuple[str, QtWidgets.QWidget]] = {}

        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, stretch=1)

        body = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(body)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        scroll.setWidget(body)

        for key, pref in self._pm.iter_schema():
            widget, kind = self._build_editor(key, pref)
            label = QtWidgets.QLabel(key)
            label.setToolTip(pref.description or "")
            widget.setToolTip(pref.description or "")
            form.addRow(label, widget)
            self._fields[key] = (kind, widget)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, stretch=0)

    def _build_editor(self, key: str, pref) -> tuple[QtWidgets.QWidget, str]:
        value = self._pm.get(key, pref.default)
        if key == "theme":
            combo = QtWidgets.QComboBox()
            combo.addItems(["light", "dark"])
            try:
                idx = combo.findText(str(value))
                combo.setCurrentIndex(idx if idx >= 0 else 0)
            except Exception:
                combo.setCurrentIndex(0)
            return combo, "theme"
        if isinstance(pref.default, bool):
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(bool(value))
            return checkbox, "bool"
        if isinstance(pref.default, int) and not isinstance(pref.default, bool):
            spin = QtWidgets.QSpinBox()
            spin.setRange(-1000000000, 1000000000)
            spin.setSingleStep(1)
            try:
                spin.setValue(int(value))
            except Exception:
                spin.setValue(int(pref.default))
            return spin, "int"
        if isinstance(pref.default, float):
            spin = QtWidgets.QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setRange(-1000000000.0, 1000000000.0)
            spin.setSingleStep(0.05)
            try:
                spin.setValue(float(value))
            except Exception:
                spin.setValue(float(pref.default))
            return spin, "float"
        line = QtWidgets.QLineEdit()
        line.setText(str(value) if value is not None else "")
        return line, "str"

    def _on_accept(self) -> None:
        self._apply_changes()
        self._restart_app()

    def _apply_changes(self) -> None:
        for key, (kind, widget) in self._fields.items():
            try:
                if kind == "theme":
                    value = str(widget.currentText())
                elif kind == "bool":
                    value = bool(widget.isChecked())
                elif kind == "int":
                    value = int(widget.value())
                elif kind == "float":
                    value = float(widget.value())
                else:
                    value = str(widget.text())
                self._pm.set(key, value)
            except Exception:
                continue
        try:
            self._pm.save()
        except Exception:
            pass
        self._apply_live_updates()

    def _apply_live_updates(self) -> None:
        try:
            theme = self._pm.get("theme", "light")
            if theme != self._initial_values.get("theme"):
                sty = Style()
                if str(theme).lower() == "dark":
                    sty.set_dark_theme()
                else:
                    sty.set_dynamic_theme(0.75)
        except Exception:
            pass

    def _restart_app(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            self.accept()
            return
        main_win = self.window()
        try:
            if hasattr(main_win, "prepare_close"):
                main_win.prepare_close()
        except Exception:
            pass
        try:
            QtCore.QProcess.startDetached(sys.executable, sys.argv)
        except Exception:
            pass
        app.quit()
        try:
            ui_scale = float(self._pm.get("ui_scale", 1.0) or 1.0)
            if ui_scale != self._initial_values.get("ui_scale"):
                base_size = 10
                size_pt = max(6, int(round(base_size * ui_scale)))
                install_default_ui_font(point_size=size_pt)
        except Exception:
            pass
