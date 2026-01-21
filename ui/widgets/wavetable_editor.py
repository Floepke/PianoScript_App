from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np

class WaveCanvas(QtWidgets.QWidget):
    changed = QtCore.Signal(np.ndarray)

    def __init__(self, parent=None, length: int = 512):
        super().__init__(parent)
        self.setMinimumSize(300, 150)
        self.length = int(length)
        self.arr = np.zeros(self.length, dtype=np.float32)
        self._drawing = False
        self._last_pos: QtCore.QPointF | None = None
        self.setMouseTracking(True)

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor('#222'))
        w = self.width()
        h = self.height()
        # axis
        p.setPen(QtGui.QPen(QtGui.QColor('#555'), 1))
        p.drawLine(0, h//2, w, h//2)
        # waveform
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor('#66ccff'), 2))
        for i in range(self.length-1):
            x1 = int(i * (w-1) / (self.length-1))
            x2 = int((i+1) * (w-1) / (self.length-1))
            y1 = int(h/2 - self.arr[i] * (h/2 - 6))
            y2 = int(h/2 - self.arr[i+1] * (h/2 - 6))
            p.drawLine(x1, y1, x2, y2)

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self._drawing = True
            self._last_pos = ev.position()
            self._apply_point(ev.position())

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._drawing:
            pos = ev.position()
            # Draw interpolated segment between last and current to avoid gaps
            if self._last_pos is not None:
                self._draw_segment(self._last_pos, pos)
            else:
                self._apply_point(pos)
            self._last_pos = pos

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        self._drawing = False
        self._last_pos = None

    def _apply_point(self, pos: QtCore.QPointF) -> None:
        w = self.width()
        h = self.height()
        x = int(np.clip(pos.x(), 0, w-1))
        y = int(np.clip(pos.y(), 0, h-1))
        idx = int(round(x * (self.length-1) / max(1, (w-1))))
        # map y to -1..+1
        v = np.clip((h/2 - y) / (h/2 - 6), -1.0, 1.0)
        self.arr[idx] = float(v)
        # simple smoothing
        if idx > 0:
            self.arr[idx-1] = (self.arr[idx-1] + v) * 0.5
        if idx < self.length-1:
            self.arr[idx+1] = (self.arr[idx+1] + v) * 0.5
        self.changed.emit(self.arr.copy())
        self.update()

    def _draw_segment(self, a: QtCore.QPointF, b: QtCore.QPointF) -> None:
        """Draw a line segment between two points, interpolating array indices to avoid jumps."""
        w = max(1, self.width())
        h = max(1, self.height())
        ax = int(np.clip(a.x(), 0, w-1))
        ay = int(np.clip(a.y(), 0, h-1))
        bx = int(np.clip(b.x(), 0, w-1))
        by = int(np.clip(b.y(), 0, h-1))
        # Ensure left-to-right iteration
        if bx < ax:
            ax, bx = bx, ax
            ay, by = by, ay
        if bx == ax:
            # vertical movement: just apply end point
            self._apply_point(b)
            return
        # Linear interpolation along x for y
        for x in range(ax, bx+1):
            t = (x - ax) / max(1, (bx - ax))
            y = int(round(ay + t * (by - ay)))
            idx = int(round(x * (self.length-1) / max(1, (w-1))))
            v = np.clip((h/2 - y) / (h/2 - 6), -1.0, 1.0)
            self.arr[idx] = float(v)
            # smooth neighbors
            if idx > 0:
                self.arr[idx-1] = (self.arr[idx-1] + v) * 0.5
            if idx < self.length-1:
                self.arr[idx+1] = (self.arr[idx+1] + v) * 0.5
        self.changed.emit(self.arr.copy())
        self.update()

    def set_sine(self) -> None:
        x = np.linspace(0, 1, self.length, endpoint=False)
        self.arr = np.sin(2*np.pi*x).astype(np.float32)
        self.changed.emit(self.arr.copy())
        self.update()


class WavetableEditor(QtWidgets.QDialog):
    # Emit left, right, attack(s), decay(s), sustain(level 0..1), release(s)
    wavetablesApplied = QtCore.Signal(np.ndarray, np.ndarray, float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Custom Synth FX')
        self.resize(700, 450)
        lay = QtWidgets.QVBoxLayout(self)

        # canvases
        canv_l = QtWidgets.QLabel('Left channel')
        canv_l.setStyleSheet('color: #000')
        lay.addWidget(canv_l)
        self.left = WaveCanvas(self, 512)
        lay.addWidget(self.left)
        btns_l = QtWidgets.QHBoxLayout()
        bsl = QtWidgets.QPushButton('Sine')
        bsl.clicked.connect(self.left.set_sine)
        btns_l.addWidget(bsl)
        lay.addLayout(btns_l)

        canv_r = QtWidgets.QLabel('Right channel')
        canv_r.setStyleSheet('color: #000')
        lay.addWidget(canv_r)
        self.right = WaveCanvas(self, 512)
        lay.addWidget(self.right)
        btns_r = QtWidgets.QHBoxLayout()
        bsr = QtWidgets.QPushButton('Sine')
        bsr.clicked.connect(self.right.set_sine)
        btns_r.addWidget(bsr)
        lay.addLayout(btns_r)

        # envelope settings (ADSR)
        form = QtWidgets.QFormLayout()
        self.attack_spin = QtWidgets.QDoubleSpinBox()
        self.attack_spin.setRange(0.0, 2.0)
        self.attack_spin.setSingleStep(0.01)
        self.attack_spin.setValue(0.01)
        self.decay_spin = QtWidgets.QDoubleSpinBox()
        self.decay_spin.setRange(0.0, 5.0)
        self.decay_spin.setSingleStep(0.05)
        self.decay_spin.setValue(0.10)
        self.sustain_spin = QtWidgets.QDoubleSpinBox()
        self.sustain_spin.setRange(0.0, 1.0)
        self.sustain_spin.setSingleStep(0.05)
        self.sustain_spin.setValue(0.70)
        self.release_spin = QtWidgets.QDoubleSpinBox()
        self.release_spin.setRange(0.0, 5.0)
        self.release_spin.setSingleStep(0.05)
        self.release_spin.setValue(0.20)
        form.addRow('Attack (s):', self.attack_spin)
        form.addRow('Decay (s):', self.decay_spin)
        form.addRow('Sustain level:', self.sustain_spin)
        form.addRow('Release (s):', self.release_spin)
        lay.addLayout(form)

        # apply/close
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        apply_btn = QtWidgets.QPushButton('Apply')
        close_btn = QtWidgets.QPushButton('Close')
        row.addWidget(apply_btn)
        row.addWidget(close_btn)
        lay.addLayout(row)
        apply_btn.clicked.connect(self._emit_apply)
        close_btn.clicked.connect(self.accept)

    def _emit_apply(self) -> None:
        l = self.left.arr.copy()
        r = self.right.arr.copy()
        a = float(self.attack_spin.value())
        d = float(self.decay_spin.value())
        s = float(self.sustain_spin.value())
        rr = float(self.release_spin.value())
        # Emit wavetables and ADSR params
        try:
            self.wavetablesApplied.emit(l, r, a, d, s, rr)
        except Exception:
            pass
