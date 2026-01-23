from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets

VALID_DENOMS = [1, 2, 4, 8, 16, 32]

class TimeSignatureDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, initial_numer: int = 4, initial_denom: int = 4):
        super().__init__(parent)
        self.setWindowTitle("Set Time Signature")
        self.setModal(True)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Numerator control row: [-] [label] [+]
        num_row = QtWidgets.QHBoxLayout()
        num_row.setContentsMargins(0, 0, 0, 0)
        num_row.setSpacing(0)

        self.minus_btn = QtWidgets.QToolButton(self)
        ic_minus = None
        try:
            from icons.icons import get_qicon
            ic_minus = get_qicon('minus', size=(36, 36))
        except Exception:
            ic_minus = None
        if ic_minus:
            self.minus_btn.setIcon(ic_minus)
            self.minus_btn.setIconSize(QtCore.QSize(34, 34))
            self.minus_btn.setText("")
        else:
            self.minus_btn.setText("-")
        self.minus_btn.setFixedSize(54, 54)
        # Improve hover/press UX
        try:
            self.minus_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.minus_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        except Exception:
            pass
        fbtn = self.minus_btn.font()
        try:
            base_sz = fbtn.pointSize()
            target = (base_sz * 2 if base_sz > 0 else 20)
            fbtn.setPointSize(int(round(target * 0.75)))
        except Exception:
            fbtn.setPointSize(15)
        self.minus_btn.setFont(fbtn)
        self.minus_btn.clicked.connect(self._dec_numer)

        self.num_label = QtWidgets.QLabel(self)
        self.num_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        fl = self.num_label.font()
        try:
            szl = fl.pointSize()
            fl.setPointSize(szl * 2 if szl > 0 else 20)
        except Exception:
            fl.setPointSize(20)
        self.num_label.setFont(fl)
        self.num_label.setMinimumHeight(54)

        self.plus_btn = QtWidgets.QToolButton(self)
        ic_plus = None
        try:
            from icons.icons import get_qicon
            ic_plus = get_qicon('plus', size=(36, 36))
        except Exception:
            ic_plus = None
        if ic_plus:
            self.plus_btn.setIcon(ic_plus)
            self.plus_btn.setIconSize(QtCore.QSize(34, 34))
            self.plus_btn.setText("")
        else:
            self.plus_btn.setText("+")
        self.plus_btn.setFixedSize(54, 54)
        try:
            self.plus_btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.plus_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        except Exception:
            pass
        fbtn2 = self.plus_btn.font()
        try:
            base_sz2 = fbtn2.pointSize()
            target2 = (base_sz2 * 2 if base_sz2 > 0 else 20)
            fbtn2.setPointSize(int(round(target2 * 0.75)))
        except Exception:
            fbtn2.setPointSize(15)
        self.plus_btn.setFont(fbtn2)
        self.plus_btn.clicked.connect(self._inc_numer)

        num_row.addWidget(self.minus_btn)
        num_row.addWidget(self.num_label, 1)
        num_row.addWidget(self.plus_btn)
        lay.addLayout(num_row)

        # Denominator dropdown
        denom_row = QtWidgets.QHBoxLayout()
        denom_row.setContentsMargins(0, 0, 0, 0)
        denom_row.setSpacing(6)
        denom_label = QtWidgets.QLabel("Denominator:", self)
        self.denom_combo = QtWidgets.QComboBox(self)
        for v in VALID_DENOMS:
            self.denom_combo.addItem(str(v), v)
        denom_row.addWidget(denom_label)
        denom_row.addWidget(self.denom_combo, 1)
        lay.addLayout(denom_row)

        # Buttons
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)
        # Make OK the default button for Enter/Return
        try:
            ok_btn = btns.button(QtWidgets.QDialogButtonBox.Ok)
            if ok_btn is not None:
                ok_btn.setDefault(True)
                ok_btn.setAutoDefault(True)
        except Exception:
            pass

        # State
        self._numer = int(initial_numer)
        self._denom = int(initial_denom) if int(initial_denom) in VALID_DENOMS else 4
        self._update_ui()
        # Select denom row
        try:
            idx = VALID_DENOMS.index(self._denom)
            self.denom_combo.setCurrentIndex(idx)
        except Exception:
            pass

        # Wheel control over label/buttons
        self.num_label.installEventFilter(self)
        self.minus_btn.installEventFilter(self)
        self.plus_btn.installEventFilter(self)

    def _update_ui(self) -> None:
        self.num_label.setText(str(self._numer))
        # Enable minus only above 1
        self.minus_btn.setEnabled(self._numer > 1)

    def _dec_numer(self) -> None:
        if self._numer > 1:
            self._numer -= 1
            self._update_ui()

    def _inc_numer(self) -> None:
        # Arbitrary cap to prevent runaway
        if self._numer < 64:
            self._numer += 1
            self._update_ui()

    def eventFilter(self, obj: QtCore.QObject, ev: QtCore.QEvent) -> bool:
        try:
            if ev.type() == QtCore.QEvent.Type.Wheel and obj in (self.minus_btn, self.plus_btn, self.num_label):
                delta = 0
                if isinstance(ev, QtGui.QWheelEvent):
                    delta = ev.angleDelta().y()
                if delta > 0:
                    self._inc_numer()
                elif delta < 0:
                    self._dec_numer()
                return True
        except Exception:
            pass
        return super().eventFilter(obj, ev)

    def get_values(self) -> tuple[int, int]:
        denom = int(self.denom_combo.currentData()) if self.denom_combo.currentData() is not None else int(self.denom_combo.currentText())
        return int(self._numer), int(denom)


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
        dlg = TimeSignatureDialog(parent=win, initial_numer=4, initial_denom=4)
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
            numer, denom = dlg.get_values()
            print(f"[accepted] numer={numer}, denom={denom}")
            lbl.setText(f"Result: {numer}/{denom}")
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
