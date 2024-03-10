from PySide6.QtWidgets import QMainWindow, QSlider, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QSizePolicy

class ColorTransitionThread(QThread):
    colorChanged = pyqtSignal(QColor)

    def __init__(self):
        super().__init__()
        self.hue = 0

    def run(self):
        while True:
            color = QColor.fromHsv(self.hue, 255, 255)
            self.colorChanged.emit(color)
            self.msleep(100)

    def set_hue(self, hue):
        self.hue = hue

class ColorSliderWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.valueChanged.connect(self.change_hue)
        
        self.slider.setSizePolicy(
            self.slider.sizePolicy().horizontalPolicy(),
            QSizePolicy.Expanding)  # Expand to fill


        self.statusBar().addWidget(self.slider)
        self.statusBar().show()  # Ensure the status bar is visible

        self.colorThread = ColorTransitionThread()
        self.colorThread.colorChanged.connect(self.change_color)
        self.colorThread.start()

    def change_hue(self, value):
        self.colorThread.set_hue(value)

    def change_color(self, color):
        self.setStyleSheet(f"background-color: {color.name()}")


def test_color_slider_window():
    app = QApplication([])

    window = ColorSliderWindow()
    window.show()

    result = app.exec()

    window.colorThread.quit()
    window.colorThread.wait()

    return result


if __name__ == "__main__":
    test_color_slider_window()

