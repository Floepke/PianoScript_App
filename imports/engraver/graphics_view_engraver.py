# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *

# pyside6 imports
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtGui import QCursor


class GraphicsViewEngraver(QGraphicsView):

    def __init__(self, scene, io, parent=None):
        super().__init__(scene, parent)
        self.standard_width = EDITOR_WIDTH
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resetTransform()
        scale_factor = self.width() / self.standard_width
        self.scale(scale_factor, scale_factor)
        self.resizeEvent(None)
        self.setScene(scene)

        # Enable antialiasing
        self.setRenderHint(QPainter.Antialiasing)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)

        self.io = io

        # don't show scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        # get the old scroll position and maximum
        vbar = self.verticalScrollBar()
        old_scroll = vbar.value()
        old_max = vbar.maximum()

        # perform the resizing
        try:
            self.standard_width = self.io['score']['properties']['page_width']
        except AttributeError:
            ...
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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print('Left button pressed')
            self.io['selected_page'] -= 1
            self.io['maineditor'].update('page_change')
        elif event.button() == Qt.RightButton:
            print('Right button pressed')
            self.io['selected_page'] += 1
            self.io['maineditor'].update('page_change')
        elif event.button() == Qt.MiddleButton:
            print('Middle button pressed')
        print('Mouse position:', event.pos())

    def mouseMoveEvent(self, event):
        print('move', event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            print('Left button released')
        elif event.button() == Qt.RightButton:
            print('Right button released')
        elif event.button() == Qt.MiddleButton:
            print('Middle button released')
        print('Mouse position:', event.pos())

    def update_page_dimensions(self):
        self.standard_width = self.io['score']['properties']['page_width']

        # Recalculate the scale factor
        scale_factor = self.width() / self.standard_width

        # Apply the new scale
        self.resetTransform()
        self.scale(scale_factor, scale_factor)

        # Trigger a resize event to update the view
        self.resizeEvent(None)
