from __future__ import annotations

import html

from PySide6 import QtCore, QtWidgets

from settings_manager import get_preferences_manager


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(550, 420)
        # Light styling to make the dialog feel intentional and readable
        self.setStyleSheet(
            "#PrefsHeader { font-size: 18px; font-weight: 600; padding: 4px 2px; }"
            "#PrefsSubtitle { color: #555; margin-bottom: 6px; }"
            "#PrefsForm QLabel { color: #222; }"
        )

        self._pm = get_preferences_manager()
        self._initial_values = dict(self._pm._values)
        self._fields: dict[str, tuple[str, QtWidgets.QWidget]] = {}

        layout = QtWidgets.QVBoxLayout(self)

        # Header copy
        header = QtWidgets.QWidget(self)
        header_layout = QtWidgets.QVBoxLayout(header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        title = QtWidgets.QLabel("Preferences", self)
        title.setObjectName("PrefsHeader")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        subtitle = QtWidgets.QLabel("Fine-tune how keyTAB looks, feels, and plays.", self)
        subtitle.setObjectName("PrefsSubtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header, stretch=0)

        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, stretch=1)

        body = QtWidgets.QWidget()
        body.setObjectName("PrefsForm")
        form = QtWidgets.QFormLayout(body)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.setContentsMargins(12, 8, 12, 8)
        scroll.setWidget(body)

        for key, pref in self._pm.iter_schema():
            widget, kind = self._build_editor(key, pref)
            label = self._build_label(key, pref.description or "")
            form.addRow(label, widget)
            self._fields[key] = (kind, widget)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, stretch=0)

    def _build_label(self, key: str, description: str) -> QtWidgets.QLabel:
        pretty = self._pretty_label(key)
        safe_desc = html.escape(description)
        label = QtWidgets.QLabel()
        label.setWordWrap(True)
        label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        desc_html = f"<div style='color:#666; font-size:11px; margin-top:2px;'>{safe_desc}</div>" if description else ""
        label.setText(f"<div style='font-weight:600'>{html.escape(pretty)}</div>{desc_html}")
        return label

    def _pretty_label(self, key: str) -> str:
        parts = key.split("_")
        pretty_parts = []
        for p in parts:
            if len(p) <= 3:
                pretty_parts.append(p.upper())
            else:
                pretty_parts.append(p.capitalize())
        return " ".join(pretty_parts)

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
        QtWidgets.QMessageBox.information(
            self,
            "Preferences",
            "Changes take effect after restarting the app.",
        )
        self.accept()

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
