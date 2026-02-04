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
                 indicator_type: Optional[str] = None,
                 editor_widget: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Set Time Signature")
        self.setModal(True)
        self.setWindowModality(QtCore.Qt.NonModal)
        #self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._editor_widget = editor_widget
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
        self.setFocusProxy(self.ts_edit)

        # Validation message
        self.msg_label = QtWidgets.QLabel("", self)
        pal = self.msg_label.palette()
        pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor(200, 0, 0))
        self.msg_label.setPalette(pal)
        lay.addWidget(self.msg_label)

        # Beat grouping entry
        self.info_label = QtWidgets.QLabel(
            "Beat grouping: enter space-separated numbers."
            "Each group starts with 1.\n"
            "Examples:"
            "\n6/8 with two groups of 3 → "
            "'1 2 3 1 2 3'."
            "\n7/8 grouped in 3+4 → "
            "'1 2 3 1 2 3 4'."
            "\n\nGroups must start with '1' and the amount of numbers must match the given time-signature numerator (the first number of the signature).",
            self,
        )
        self.info_label.setWordWrap(True)
        lay.addWidget(self.info_label)
        grouping_row = QtWidgets.QHBoxLayout()
        grouping_row.setContentsMargins(0, 0, 0, 0)
        grouping_row.setSpacing(6)
        self.grouping_label = QtWidgets.QLabel("Beat grouping:", self)
        self.grouping_edit = QtWidgets.QLineEdit(self)
        self.grouping_edit.setPlaceholderText("e.g., 1 2 3 1 2 3")
        # Allow digits and spaces
        self._grouping_validator = QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"^[0-9\s]+$"), self.grouping_edit)
        self.grouping_edit.setValidator(self._grouping_validator)
        grouping_row.addWidget(self.grouping_label)
        grouping_row.addWidget(self.grouping_edit, 1)
        lay.addLayout(grouping_row)

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
        ok_btn = self.btns.button(QtWidgets.QDialogButtonBox.Ok)
        if ok_btn is not None:
            ok_btn.setDefault(True)
            ok_btn.setAutoDefault(True)

        # State
        self._numer = int(initial_numer)
        self._denom = int(initial_denom) if int(initial_denom) in VALID_DENOMS else 4
        # Indicator type (affects initial checkbox states)
        self._indicator_type: str = str(indicator_type or 'classical')
        if self._indicator_type not in ('classical', 'klavarskribo', 'both'):
            self._indicator_type = 'classical'
        # Initialize beat grouping sequence (one digit per beat)
        init_gp = list(initial_grid_positions or [])
        if init_gp:
            seq = [int(p) for p in init_gp if isinstance(p, int) and int(p) >= 1]
            if len(seq) != int(self._numer):
                seq = []
            self._grid_positions = seq
        else:
            self._grid_positions = []
        if not self._grid_positions:
            # Default: 1..numer (single group across the measure)
            self._grid_positions = list(range(1, int(self._numer) + 1))
        # Initialize indicator state
        self._indicator_enabled: bool = bool(initial_indicator_enabled if initial_indicator_enabled is not None else True)
        self.indicator_enabled_cb.setChecked(self._indicator_enabled)

        # Initialize grouping string from grid positions
        self._update_grouping_text_from_positions()
        # Initialize entry text
        self.ts_edit.setText(f"{self._numer}/{self._denom}")
        # React to changes
        self.ts_edit.textChanged.connect(self._on_text_changed)
        self.grouping_edit.textChanged.connect(self._on_grouping_changed)

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
                # Reset grouping sequence to 1..numer
                self._grid_positions = list(range(1, numer + 1))
                self._update_grouping_text_from_positions()
            self._denom = denom

        # Keep indicator enabled in sync with widget
        self._indicator_enabled = bool(self.indicator_enabled_cb.isChecked())

    def _on_accept_clicked(self) -> None:
        s = self.ts_edit.text().strip()
        numer, denom, err = self._parse_ts(s)
        if err or numer is None or denom is None:
            return
        if not self._apply_grouping_text():
            return
        self._numer = numer
        self._denom = denom
        # Sync indicator values before accept
        self._indicator_enabled = bool(self.indicator_enabled_cb.isChecked())
        self.accept()

    def _parse_ts(self, s: str) -> tuple[Optional[int], Optional[int], Optional[str]]:
        if not s:
            return None, None, "Enter '<numerator>/<denominator>' with digits and '/'."
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

    def _update_grouping_text_from_positions(self) -> None:
        # Build grouping string from per-beat sequence (e.g., [1,2,3,1,2,3,4] -> "1 2 3 1 2 3 4")
        if not self._grid_positions:
            txt = ""
        else:
            seq = [int(p) for p in self._grid_positions if int(p) >= 1]
            if len(seq) != int(self._numer):
                seq = list(range(1, int(self._numer) + 1))
            txt = " ".join(str(p) for p in seq)
        try:
            self.grouping_edit.blockSignals(True)
            self.grouping_edit.setText(txt)
        finally:
            self.grouping_edit.blockSignals(False)

    def _on_grouping_changed(self, s: str) -> None:
        # Live-validate grouping string
        if not s:
            self.msg_label.setText("Enter a beat grouping string (digits only).")
            return
        if any(ch not in "0123456789 " for ch in s):
            self.msg_label.setText("Beat grouping must contain digits and spaces only.")
            return
        if not self._apply_grouping_text(quiet=True):
            return
        # Clear error if parsing is ok
        self.msg_label.setText("")

    def _apply_grouping_text(self, quiet: bool = False) -> bool:
        s = (self.grouping_edit.text() or "").strip()
        if not s:
            if not quiet:
                self.msg_label.setText("Enter a beat grouping string (space-separated).")
            return False
        # Parse: per-beat sequence; must start with 1 and follow reset-to-1 rule
        parts = [p for p in s.split(" ") if p.strip() != ""]
        try:
            seq: list[int] = [int(p) for p in parts]
        except Exception:
            if not quiet:
                self.msg_label.setText("Grouping must be space-separated integers.")
            return False
        if not seq or seq[0] != 1:
            if not quiet:
                self.msg_label.setText("Grouping must start with '1'.")
            return False
        if len(seq) != int(self._numer):
            if not quiet:
                self.msg_label.setText(f"Grouping length must match the time signatures measure length.\nPlease enter {int(self._numer)} digits.")
            return False
        for prev, cur in zip(seq, seq[1:]):
            if cur != 1 and cur != prev + 1:
                if not quiet:
                    self.msg_label.setText("Beat grouping must count up or reset to 1 (e.g., '1 2 3 1 2 3 4').")
                return False
        self._grid_positions = seq
        return True

    def get_values(self) -> tuple[int, int, list[int], bool]:
        return int(self._numer), int(self._denom), list(self._grid_positions), bool(self._indicator_enabled)

# Test
if __name__ == '__main__':
    # Simple standalone test harness to verify dialog mouse/keyboard interaction
    import sys
    from PySide6 import QtWidgets, QtCore

    app = QtWidgets.QApplication(sys.argv)
    # Optional: use Fusion style for consistent visuals across platforms
    QtWidgets.QApplication.setStyle('Fusion')

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
        # Ensure dialog is visible and focused
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
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
