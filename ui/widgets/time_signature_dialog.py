from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
from typing import Optional

VALID_DENOMS = [1, 2, 4, 8, 16, 32, 64, 128]

class TimeSignatureDialog(QtWidgets.QDialog):
    def __init__(self, parent=None,
                 initial_numer: int = 4,
                 initial_denom: int = 4,
                 initial_grid_positions: Optional[list[int]] = None,
                 initial_indicator_enabled: Optional[bool] = True,
                 indicator_type: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Set Time Signature")
        self.setModal(True)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Single entry: Time-Signature: "N/D"
        entry_row = QtWidgets.QHBoxLayout()
        entry_row.setContentsMargins(0, 0, 0, 0)
        entry_row.setSpacing(6)
        self.ts_label = QtWidgets.QLabel("Time-Signature:", self)
        self.ts_edit = QtWidgets.QLineEdit(self)
        self.ts_edit.setPlaceholderText("e.g., 4/4")
        self.ts_edit.setClearButtonEnabled(True)
        # Allow digits and '/'
        rx = QtCore.QRegularExpression(r"^[0-9]+/[0-9]+$")
        self._validator = QtGui.QRegularExpressionValidator(rx, self.ts_edit)
        self.ts_edit.setValidator(self._validator)
        entry_row.addWidget(self.ts_label)
        entry_row.addWidget(self.ts_edit, 1)
        lay.addLayout(entry_row)

        # Validation message
        self.msg_label = QtWidgets.QLabel("", self)
        pal = self.msg_label.palette()
        try:
            pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor(200, 0, 0))
            self.msg_label.setPalette(pal)
        except Exception:
            pass
        lay.addWidget(self.msg_label)

        # Instruction + checkboxes container
        self.info_label = QtWidgets.QLabel(
            "Enable/disable beats below. Checkbox 1 toggles the barline; higher numbers toggle beat grid lines.",
            self,
        )
        lay.addWidget(self.info_label)
        # Beats enabled label
        self.beats_label = QtWidgets.QLabel("Beats enabled:", self)
        lay.addWidget(self.beats_label)
        self.checkbox_container = QtWidgets.QWidget(self)
        self.checkbox_layout = QtWidgets.QHBoxLayout(self.checkbox_container)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox_layout.setSpacing(6)
        lay.addWidget(self.checkbox_container)

        # Indicator enabled toggle (global type comes from Layout; dialog no longer edits it)
        indicator_row = QtWidgets.QHBoxLayout()
        indicator_row.setContentsMargins(0, 0, 0, 0)
        indicator_row.setSpacing(6)
        self.indicator_enabled_cb = QtWidgets.QCheckBox("Indicator enabled", self)
        indicator_row.addWidget(self.indicator_enabled_cb)
        lay.addLayout(indicator_row)

        # Buttons
        self.btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self)
        self.btns.accepted.connect(self._on_accept_clicked)
        self.btns.rejected.connect(self.reject)
        lay.addWidget(self.btns)
        try:
            ok_btn = self.btns.button(QtWidgets.QDialogButtonBox.Ok)
            if ok_btn is not None:
                ok_btn.setDefault(True)
                ok_btn.setAutoDefault(True)
        except Exception:
            pass

        # State
        self._numer = int(initial_numer)
        self._denom = int(initial_denom) if int(initial_denom) in VALID_DENOMS else 4
        # Indicator type (affects initial checkbox states)
        self._indicator_type: str = str(indicator_type or 'classical')
        if self._indicator_type not in ('classical', 'klavarskribo', 'both'):
            self._indicator_type = 'classical'
        # Initialize grid positions. If provided, clamp to [1..numer]; otherwise default based on indicator type.
        init_gp = list(initial_grid_positions or [])
        if init_gp:
            self._grid_positions = [p for p in init_gp if isinstance(p, int) and 1 <= int(p) <= int(self._numer)]
            # Keep unique + sorted
            self._grid_positions = sorted(list(dict.fromkeys(self._grid_positions)))
            if not self._grid_positions:
                # Default: classical → all beats; klavarskribo/both → barline only
                self._grid_positions = [1] if self._indicator_type in ('klavarskribo', 'both') else list(range(1, int(self._numer) + 1))
        else:
            self._grid_positions = [1] if self._indicator_type in ('klavarskribo', 'both') else list(range(1, int(self._numer) + 1))
        # Ensure beat 1 is always present (cannot have ungrouped time)
        if 1 not in self._grid_positions:
            self._grid_positions.insert(0, 1)
        # Initialize indicator state
        self._indicator_enabled: bool = bool(initial_indicator_enabled if initial_indicator_enabled is not None else True)
        try:
            self.indicator_enabled_cb.setChecked(self._indicator_enabled)
        except Exception:
            pass

        self._build_checkboxes()
        # Initialize entry text
        try:
            self.ts_edit.setText(f"{self._numer}/{self._denom}")
        except Exception:
            pass
        # React to changes
        self.ts_edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, s: str) -> None:
        numer, denom, err = self._parse_ts(s)
        ok_btn = self.btns.button(QtWidgets.QDialogButtonBox.Ok)
        if err:
            self.msg_label.setText(err)
            if ok_btn is not None:
                ok_btn.setEnabled(False)
            return
        self.msg_label.setText("")
        if ok_btn is not None:
            ok_btn.setEnabled(True)
        if numer is not None and denom is not None:
            # Rebuild checkboxes if numerator changed
            if numer != self._numer:
                self._numer = numer
                # Reset grid positions: classical → all beats; klavarskribo/both → barline only
                self._grid_positions = [1] if self._indicator_type in ('klavarskribo', 'both') else list(range(1, numer + 1))
                self._build_checkboxes()
            self._denom = denom

        # Keep indicator enabled in sync with widget
        try:
            self._indicator_enabled = bool(self.indicator_enabled_cb.isChecked())
        except Exception:
            pass

    def _on_accept_clicked(self) -> None:
        s = self.ts_edit.text().strip()
        numer, denom, err = self._parse_ts(s)
        if err or numer is None or denom is None:
            return
        self._numer = numer
        self._denom = denom
        # Sync indicator values before accept
        try:
            self._indicator_enabled = bool(self.indicator_enabled_cb.isChecked())
        except Exception:
            pass
        self.accept()

    def _parse_ts(self, s: str) -> tuple[Optional[int], Optional[int], Optional[str]]:
        if not s:
            return None, None, "Enter N/D with digits and '/'."
        # validator already restricts pattern, but we further validate denominator set
        try:
            parts = s.split('/')
            if len(parts) != 2:
                return None, None, "Format must be N/D (e.g., 4/4)."
            n_str, d_str = parts[0], parts[1]
            if not n_str.isdigit() or not d_str.isdigit():
                return None, None, "Only digits and '/' allowed."
            n = int(n_str)
            d = int(d_str)
            if n <= 0:
                return None, None, "Numerator must be a positive integer."
            if d not in VALID_DENOMS:
                return None, None, f"Denominator must be one of {VALID_DENOMS}."
            return n, d, None
        except Exception:
            return None, None, "Invalid time signature."

    def _build_checkboxes(self) -> None:
        # Clear current
        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        # Build new set
        self._checkboxes: list[QtWidgets.QCheckBox] = []
        for i in range(1, int(self._numer) + 1):
            cb = QtWidgets.QCheckBox(str(i), self.checkbox_container)
            # Initial state reflects current grid_positions for all indicator types
            init_checked = (i in self._grid_positions)
            cb.setChecked(init_checked)
            cb.toggled.connect(lambda checked, idx=i: self._on_cb_toggled(idx, checked))
            if i == 1:
                # Beat 1 cannot be unchecked; lock the checkbox
                cb.setEnabled(False)
                cb.setChecked(True)
            self.checkbox_layout.addWidget(cb)
            self._checkboxes.append(cb)
        self.checkbox_layout.addStretch(1)

    def _on_cb_toggled(self, idx: int, checked: bool) -> None:
        # Prevent unchecking beat 1
        if idx == 1:
            # Force beat 1 to remain checked in internal state
            if 1 not in self._grid_positions:
                self._grid_positions.insert(0, 1)
            # If the UI somehow fires a toggle for idx==1, revert it
            cb = self._checkboxes[0]
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            return
        if checked:
            if idx not in self._grid_positions:
                self._grid_positions.append(idx)
                self._grid_positions.sort()
        else:
            try:
                self._grid_positions.remove(idx)
            except ValueError:
                pass

    def get_values(self) -> tuple[int, int, list[int], bool]:
        return int(self._numer), int(self._denom), list(self._grid_positions), bool(self._indicator_enabled)


if __name__ == '__main__':
    # Simple standalone test harness to verify dialog mouse/keyboard interaction
    import sys
    from PySide6 import QtWidgets, QtCore

    app = QtWidgets.QApplication(sys.argv)
    # Optional: use Fusion style for consistent visuals across platforms
    try:
        QtWidgets.QApplication.setStyle('Fusion')
    except Exception:
        pass

    win = QtWidgets.QMainWindow()
    win.setWindowTitle("TimeSignatureDialog Test")
    central = QtWidgets.QWidget(win)
    lay = QtWidgets.QVBoxLayout(central)
    lay.setContentsMargins(12, 12, 12, 12)
    lay.setSpacing(8)

    btn = QtWidgets.QPushButton("Open Time Signature Dialog", central)
    lbl = QtWidgets.QLabel("Result: (none)", central)

    def open_dialog():
        dlg = TimeSignatureDialog(parent=win, initial_numer=4, initial_denom=4, initial_grid_positions=[1, 2, 3, 4], initial_indicator_enabled=True)
        try:
            dlg.setWindowModality(QtCore.Qt.WindowModal)
        except Exception:
            pass
        # Ensure dialog is visible and focused
        try:
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()
        except Exception:
            pass
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            numer, denom, grid_positions, ind_enabled = dlg.get_values()
            print(f"[accepted] numer={numer}, denom={denom}, grid_positions={grid_positions}, indicator_enabled={ind_enabled}")
            lbl.setText(f"Result: {numer}/{denom} beats={grid_positions} indicator={'enabled' if ind_enabled else 'disabled'}")
        else:
            print("[rejected]")
            lbl.setText("Result: (cancel)")

    btn.clicked.connect(open_dialog)

    lay.addWidget(btn)
    lay.addWidget(lbl)
    win.setCentralWidget(central)
    win.resize(520, 260)
    win.show()
    sys.exit(app.exec())
