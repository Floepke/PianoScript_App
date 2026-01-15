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
        old_max = vbar.maximum()
        old_pos = vbar.value()

        # Scale the view
        self.resetTransform()
        scale_factor = self.width() / self.standard_width
        self.scale(scale_factor, scale_factor)

        # Restore the old scroll position
        new_max = vbar.maximum()
        new_pos = (old_pos / old_max) * new_max if old_max > 0 else 0
        vbar.setValue(new_pos)

        # Refresh the view
        self.viewport().update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.io['selected_page'] -= 1
            self.io['maineditor'].update('page_change')
        elif event.button() == Qt.RightButton:
            self.io['selected_page'] += 1
            self.io['maineditor'].update('page_change')
        elif event.button() == Qt.MiddleButton:
            ...

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            ...
        elif event.button() == Qt.RightButton:
            ...
        elif event.button() == Qt.MiddleButton:
            ...

    def update_page_dimensions(self):
        self.standard_width = self.io['score']['properties']['page_width']

        # Recalculate the scale factor
        scale_factor = self.width() / self.standard_width

        # Apply the new scale
        self.resetTransform()
        self.scale(scale_factor, scale_factor)

        # Trigger a resize event to update the view
        self.resizeEvent(None)

    def wheelEvent(self, event):
        # Call the base class implementation first
        super().wheelEvent(event)

        # Then update the view
        self.update_page_dimensions()
