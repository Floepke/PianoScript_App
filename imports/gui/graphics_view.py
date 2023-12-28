# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *

# pyside6 imports
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtGui import QCursor

class GraphicsView(QGraphicsView):

    # setup mouse tracking:
    mouse_position = Signal(int, int)
    mouse_pressed = Signal(int, int)
    mouse_released = Signal(int, int)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.standard_width = WIDTH
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resetTransform()
        scale_factor = self.width() / self.standard_width
        self.scale(scale_factor, scale_factor)
        self.resizeEvent(None)
        self.setScene(scene)

        # Enable antialiasing
        self.setRenderHint(QPainter.Antialiasing)

    def resizeEvent(self, event):
        # get the old scroll position and maximum
        vbar = self.verticalScrollBar()
        old_scroll = vbar.value()
        old_max = vbar.maximum()

        # perform the resizing
        scale_factor = self.width() / self.standard_width
        self.resetTransform()
        self.scale(scale_factor, scale_factor)

        # calculate the new scroll position
        new_max = vbar.maximum()
        if old_max == 0:
            new_scroll = 0
        else:
            new_scroll = old_scroll * new_max / old_max
        vbar.setValue(new_scroll)

        # call the original resizeEvent
        super().resizeEvent(event)

    def mouseMoveEvent(self, event):
        self.mouse_position.emit(event.x(), event.y())
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        self.mouse_pressed.emit(event.x(), event.y())
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.mouse_released.emit(event.x(), event.y())
        super().mouseReleaseEvent(event)
