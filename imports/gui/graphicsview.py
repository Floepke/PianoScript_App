# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.CONSTANT import *

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QShowEvent

class GraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.standard_width = WIDTH
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scale_factor = self.width() / self.standard_width
        self.resetTransform()
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