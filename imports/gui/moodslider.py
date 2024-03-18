from PySide6.QtWidgets import QSlider
from PySide6.QtCore import QPoint 


class MoodSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.startPos = QPoint()
        self.slidery = 0.0

    def mousePressEvent(self, event):
        self.slidery = 0.0
        self.startPos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        mainwindow_height = 1000
        self.slidery = 1 - event.pos().y() / mainwindow_height * 255
        self.setValue(self.slidery)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.startPos = QPoint()
        super().mouseReleaseEvent(event)
