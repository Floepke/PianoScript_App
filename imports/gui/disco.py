from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QSlider, QWidget
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
import time, math

class ColorTransitionThread(QThread):
    colorChanged = Signal(QColor, QColor)

    def __init__(self, main_window, amp=1, speed=0.1, phase=0, min_val=30, max_val=60):
        super().__init__()
        self.main_window = main_window
        self.amp = amp
        self.speed = speed
        self.phase = phase
        self.min_val = min_val
        self.max_val = max_val
        self.time = 0

    def sine_wave(self, amp, speed, phase, min_val, max_val, time):
        return int((amp * math.sin(2 * math.pi * speed * time + phase) + 1) / 2 * (max_val - min_val) + min_val)

    def run(self):
        hue = 0
        while True:
            val = self.sine_wave(amp=.6, speed=self.speed, phase=self.phase, min_val=self.min_val, max_val=self.max_val, time=self.time)
            saturation = self.sine_wave(amp=.6, speed=self.speed, phase=self.phase, min_val=65, max_val=75, time=self.time)
            color = QColor.fromHsv(hue, saturation, val)
            color2 = QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())
            self.colorChanged.emit(color, color2)
            hue = self.sine_wave(amp=.6, speed=self.speed, phase=self.phase, min_val=150, max_val=200, time=self.time)
            self.time += 0.01
            time.sleep(0.01)