from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np
from appdata_manager import get_appdata_manager


# Settable sample count for wavetable canvases
SAMPLE_COUNT = 512


class WaveCanvas(QtWidgets.QWidget):
    samplesChanged = QtCore.Signal(object)

    def __init__(self, count: int = SAMPLE_COUNT, parent=None) -> None:
        super().__init__(parent)
        self._count = int(count)
        self._samples = np.zeros(self._count, dtype=np.float32)
        self.setMinimumSize(240, 120)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self._last_idx = None

    def set_samples(self, arr) -> None:
        a = np.asarray(arr, dtype=np.float32)
        if a.shape[0] != self._count:
            # Resample via linear interpolation
            x_old = np.linspace(0.0, 1.0, a.shape[0], endpoint=False)
            x_new = np.linspace(0.0, 1.0, self._count, endpoint=False)
            a = np.interp(x_new, x_old, a).astype(np.float32)
        self._samples = a
        self.update()
        try:
            self.samplesChanged.emit(self._samples.copy())
        except Exception:
            pass

    def get_samples(self):
        return self._samples.copy()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        # Background
        p.fillRect(rect, self.palette().color(QtGui.QPalette.ColorRole.Base))
        # Mid line
        mid_y = rect.center().y()
        pen_mid = QtGui.QPen(self.palette().color(QtGui.QPalette.ColorRole.Mid))
        pen_mid.setWidth(1)
        p.setPen(pen_mid)
        p.drawLine(rect.left(), mid_y, rect.right(), mid_y)
        # Waveform polyline
        pen_wave = QtGui.QPen(self.palette().color(QtGui.QPalette.ColorRole.Highlight))
        pen_wave.setWidth(2)
        p.setPen(pen_wave)
        if self._samples.size > 1:
            pts = []
            w = max(1, rect.width() - 2)
            h = max(1, rect.height() - 2)
            for i in range(self._count):
                x = rect.left() + 1 + int((i / (self._count - 1)) * w)
                # Map -1..1 to top..bottom
                val = float(np.clip(self._samples[i], -1.0, 1.0))
                y = rect.top() + 1 + int(((1.0 - (val + 1.0) * 0.5)) * h)
                pts.append(QtCore.QPoint(x, y))
            p.drawPolyline(QtGui.QPolygon(pts))

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self._apply_mouse(ev)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self._apply_mouse(ev)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        self._last_idx = None

    def _apply_mouse(self, ev: QtGui.QMouseEvent) -> None:
        rect = self.rect()
        x = float(np.clip(ev.position().x(), rect.left(), rect.right()))
        y = float(np.clip(ev.position().y(), rect.top(), rect.bottom()))
        w = max(1.0, rect.width() - 2.0)
        h = max(1.0, rect.height() - 2.0)
        idx = int(np.clip(round(((x - rect.left() - 1.0) / w) * (self._count - 1)), 0, self._count - 1))
        val = 1.0 - ((y - rect.top() - 1.0) / h) * 2.0
        val = float(np.clip(val, -1.0, 1.0))
        if self._last_idx is None:
            self._samples[idx] = val
        else:
            # Interpolate between last and current index for continuous strokes
            i0, i1 = int(self._last_idx), int(idx)
            if i0 == i1:
                self._samples[i1] = val
            else:
                step = 1 if i1 > i0 else -1
                n = abs(i1 - i0)
                for k, i in enumerate(range(i0, i1 + step, step)):
                    t = float(k) / float(max(1, n))
                    self._samples[i] = (1.0 - t) * float(self._samples[i0]) + t * val
        self._last_idx = idx
        self.update()
        try:
            self.samplesChanged.emit(self._samples.copy())
        except Exception:
            pass


def gen_wave(shape: str, n: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n, endpoint=False, dtype=np.float32)
    if shape == 'sine':
        return np.sin(2 * np.pi * t).astype(np.float32)
    if shape == 'square':
        return np.sign(np.sin(2 * np.pi * t)).astype(np.float32)
    if shape == 'saw':
        return (2.0 * (t - np.floor(t + 0.5))).astype(np.float32)
    if shape == 'triangle':
        return (2.0 * np.abs(2.0 * (t - np.floor(t + 0.5))) - 1.0).astype(np.float32)
    if shape == 'hsin':
        # Half-sine over one period (0..pi), mapped to -1..1 around center
        return (np.sin(np.pi * t) * 2.0 - 1.0).astype(np.float32)
    if shape == 'asin':
        # Absolute sine (0..1)
        return np.abs(np.sin(2 * np.pi * t)).astype(np.float32)
    return np.sin(2 * np.pi * t).astype(np.float32)


class WavetableEditor(QtWidgets.QDialog):
    wavetablesApplied = QtCore.Signal(object, object, float, float, float, float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Synth FX")
        self.resize(720, 520)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)

        # Left/Right canvas rows with waveform buttons
        self.left_canvas = WaveCanvas(SAMPLE_COUNT, self)
        self.right_canvas = WaveCanvas(SAMPLE_COUNT, self)

        layout.addLayout(self._make_canvas_row("L", self.left_canvas))
        layout.addLayout(self._make_canvas_row("R", self.right_canvas))

        # ADSR + Gain controls (sliders)
        grid = QtWidgets.QGridLayout()

        # Time sliders (0..10s) and sustain slider (0..1)
        # Use curve_power>1.0 to get finer control at lower values
        curve = 3.0
        self.attack = self._make_float_slider(0.0, 10.0, 0.005, suffix=" s", decimals=3, scale=1000, curve_power=curve)
        self.decay = self._make_float_slider(0.0, 10.0, 0.05, suffix=" s", decimals=3, scale=1000, curve_power=curve)
        self.sustain = self._make_float_slider(0.0, 1.0, 0.6, suffix="", decimals=3, scale=1000, curve_power=curve)
        self.release = self._make_float_slider(0.0, 10.0, 0.1, suffix=" s", decimals=3, scale=1000, curve_power=curve)
        # Keep gain as a slider too for convenience (0..1.5) with milder curve
        self.gain = self._make_float_slider(0.0, 1.5, 0.35, suffix="", decimals=2, scale=100, curve_power=2.0)

        grid.addWidget(QtWidgets.QLabel("Attack"), 0, 0)
        grid.addWidget(self.attack, 0, 1)
        grid.addWidget(QtWidgets.QLabel("Decay"), 1, 0)
        grid.addWidget(self.decay, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Sustain"), 2, 0)
        grid.addWidget(self.sustain, 2, 1)
        grid.addWidget(QtWidgets.QLabel("Release"), 3, 0)
        grid.addWidget(self.release, 3, 1)
        grid.addWidget(QtWidgets.QLabel("Gain"), 4, 0)
        grid.addWidget(self.gain, 4, 1)
        layout.addLayout(grid)

        # Close-only button box
        btns = QtWidgets.QDialogButtonBox()
        close_btn = btns.addButton("Close", QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(btns)
        close_btn.clicked.connect(self.reject)

        # Debounced auto-apply timer
        self._emit_timer = QtCore.QTimer(self)
        self._emit_timer.setSingleShot(True)
        self._emit_timer.setInterval(30)  # ms
        self._emit_timer.timeout.connect(self._emit_current)

        # Initialize from appdata if available
        try:
            adm = get_appdata_manager()
            lw = adm.get("synth_left_wavetable", []) or []
            rw = adm.get("synth_right_wavetable", []) or []
            if lw:
                self.left_canvas.set_samples(np.asarray(lw, dtype=np.float32))
            if rw:
                self.right_canvas.set_samples(np.asarray(rw, dtype=np.float32))
            self.attack.setValue(float(adm.get("synth_attack", 0.005) or 0.005))
            self.decay.setValue(float(adm.get("synth_decay", 0.05) or 0.05))
            self.sustain.setValue(float(adm.get("synth_sustain", 0.6) or 0.6))
            self.release.setValue(float(adm.get("synth_release", 0.1) or 0.1))
            self.gain.setValue(float(adm.get("synth_gain", 0.35) or 0.35))
        except Exception:
            pass

        # Auto-apply on any change
        self.left_canvas.samplesChanged.connect(lambda *_: self._schedule_emit())
        self.right_canvas.samplesChanged.connect(lambda *_: self._schedule_emit())
        self.attack.valueChanged.connect(lambda *_: self._schedule_emit())
        self.decay.valueChanged.connect(lambda *_: self._schedule_emit())
        self.sustain.valueChanged.connect(lambda *_: self._schedule_emit())
        self.release.valueChanged.connect(lambda *_: self._schedule_emit())
        self.gain.valueChanged.connect(lambda *_: self._schedule_emit())

    def _make_canvas_row(self, label: str, canvas: WaveCanvas) -> QtWidgets.QHBoxLayout:
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(label))
        row.addWidget(canvas, stretch=1)
        # Waveform preset buttons
        btns = QtWidgets.QVBoxLayout()
        for shape in ("sine", "saw", "triangle", "square", "hsin", "asin"):
            b = QtWidgets.QPushButton(shape.capitalize())
            b.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            b.clicked.connect(lambda _=False, sh=shape: canvas.set_samples(gen_wave(sh, SAMPLE_COUNT)))
            btns.addWidget(b)
        row.addLayout(btns)
        return row

    class _FloatSlider(QtWidgets.QWidget):
        valueChanged = QtCore.Signal(float)

        def __init__(self, mn: float, mx: float, val: float, decimals: int = 3, scale: int = 1000, suffix: str = "", curve_power: float = 1.0, parent=None) -> None:
            super().__init__(parent)
            self._mn = float(mn)
            self._mx = float(mx)
            self._dec = int(max(0, decimals))
            self._scale = int(max(1, scale))
            self._pow = float(max(0.1, curve_power))
            lay = QtWidgets.QHBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            self._slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
            self._slider.setRange(0, int(round((self._mx - self._mn) * self._scale)))
            self._spin = QtWidgets.QDoubleSpinBox(self)
            self._spin.setRange(self._mn, self._mx)
            self._spin.setDecimals(self._dec)
            self._spin.setSingleStep(1.0 / float(self._scale))
            if suffix:
                self._spin.setSuffix(suffix)
            lay.addWidget(self._slider, 1)
            lay.addWidget(self._spin)
            self.setValue(float(val))
            # wire
            self._slider.valueChanged.connect(self._on_slider)
            self._spin.valueChanged.connect(self._on_spin)

        def _on_slider(self, iv: int) -> None:
            # Map slider integer to value using power curve for finer control near 0
            frac = float(iv) / float(self._slider.maximum() if self._slider.maximum() > 0 else 1)
            v = self._mn + (self._mx - self._mn) * (frac ** self._pow)
            try:
                self._spin.blockSignals(True)
                self._spin.setValue(v)
            finally:
                self._spin.blockSignals(False)
            self.valueChanged.emit(float(self.value()))

        def _on_spin(self, v: float) -> None:
            # Map spin value back to slider position using inverse power curve
            if self._mx <= self._mn:
                iv = 0
            else:
                frac = float(max(0.0, min(1.0, (float(v) - self._mn) / (self._mx - self._mn))))
                # Inverse mapping of x^p -> x = frac^(1/p)
                sfrac = frac ** (1.0 / self._pow)
                iv = int(round(sfrac * float(self._slider.maximum())))
                iv = max(0, min(self._slider.maximum(), iv))
            try:
                self._slider.blockSignals(True)
                self._slider.setValue(iv)
            finally:
                self._slider.blockSignals(False)
            self.valueChanged.emit(float(self.value()))

        def value(self) -> float:
            return float(self._spin.value())

        def setValue(self, v: float) -> None:
            v = float(max(self._mn, min(self._mx, v)))
            # Apply inverse power mapping to set slider
            if self._mx <= self._mn:
                iv = 0
            else:
                frac = (v - self._mn) / (self._mx - self._mn)
                sfrac = float(frac) ** (1.0 / self._pow)
                iv = int(round(sfrac * float(self._slider.maximum())))
            try:
                self._slider.blockSignals(True)
                self._spin.blockSignals(True)
                self._slider.setValue(iv)
                self._spin.setValue(v)
            finally:
                self._slider.blockSignals(False)
                self._spin.blockSignals(False)

    def _make_float_slider(self, mn: float, mx: float, val: float, suffix: str = "", decimals: int = 3, scale: int = 1000, curve_power: float = 1.0) -> QtWidgets.QWidget:
        return self._FloatSlider(mn, mx, val, decimals=decimals, scale=scale, suffix=suffix, curve_power=curve_power)

    def _schedule_emit(self) -> None:
        # Restart debounce timer to group rapid changes during drawing
        try:
            if self._emit_timer.isActive():
                self._emit_timer.stop()
            self._emit_timer.start()
        except Exception:
            # Fallback: emit immediately
            self._emit_current()

    def _emit_current(self) -> None:
        left = self.left_canvas.get_samples()
        right = self.right_canvas.get_samples()
        self.wavetablesApplied.emit(left, right,
                        float(self.attack.value()), float(self.decay.value()),
                        float(self.sustain.value()), float(self.release.value()),
                        float(self.gain.value()))
