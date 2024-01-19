# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *

# pyside6 imports
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPainter

class GraphicsViewEditor(QGraphicsView):

    def __init__(self, scene, io, parent=None):
        super().__init__(scene, parent)
        self.io = io
        self.standard_width = EDITOR_WIDTH
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resetTransform()
        scale_factor = self.width() / self.standard_width
        self.scale(scale_factor, scale_factor)
        self.resizeEvent(None)
        self.setScene(scene)

        # Settings for the qgraphicsview
        self.setRenderHint(QPainter.Antialiasing)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)

        # mouse buttons
        self.left_mouse_button = False
        self.middle_mouse_button = False
        self.right_mouse_button = False

        self.scene = scene

        self.verticalScrollBar().valueChanged.connect(lambda: self.io['maineditor'].update('scroll'))

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

        try: self.io['maineditor'].update('resize')
        except KeyError: pass

        # call the original resizeEvent
        super().resizeEvent(event)

    def mousePressEvent(self, event):

        scene_point = self.mapToScene(event.pos())
        x = scene_point.x()
        y = scene_point.y()

        if event.button() == Qt.LeftButton:
            self.left_mouse_button = True
            self.io['maineditor'].update('leftclick', x, y)
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_button = True
            self.io['maineditor'].update('middleclick', x, y)
        elif event.button() == Qt.RightButton:
            self.right_mouse_button = True
            self.io['maineditor'].update('rightclick', x, y)
        
        self.scene.update()
        

    def mouseMoveEvent(self, event):

        scene_point = self.mapToScene(event.pos())
        x = scene_point.x()
        y = scene_point.y()
        
        if not any([self.left_mouse_button, self.middle_mouse_button, self.right_mouse_button]):
            self.io['maineditor'].update('move', x, y)
        elif self.left_mouse_button:
            self.io['maineditor'].update('leftclick+move', x, y)
        elif self.middle_mouse_button:
            self.io['maineditor'].update('middleclick+move', x, y)
        elif self.right_mouse_button:
            self.io['maineditor'].update('rightclick+move', x, y)

        #self.scene.update()
        

    def mouseReleaseEvent(self, event):

        scene_point = self.mapToScene(event.pos())
        x = scene_point.x()
        y = scene_point.y()
        
        if event.button() == Qt.LeftButton:
            self.left_mouse_button = False
            self.io['maineditor'].update('leftrelease', x, y)
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_button = False
            self.io['maineditor'].update('middlerelease', x, y)
        elif event.button() == Qt.RightButton:
            self.right_mouse_button = False
            self.io['maineditor'].update('rightrelease', x, y)
        
        self.scene.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # if the space key is pressed, switch the hand
        if event.key() == Qt.Key_Space:
            self.io['maineditor'].update('space')
        return super().keyPressEvent(event)
    
    # connect a action if mouse leaves the view
    def leaveEvent(self, event):
        self.io['maineditor'].update('leave')

    # connect a action if mouse enters the view
    def enterEvent(self, event):
        self.io['maineditor'].update('enter')

    def wheelEvent(self, event):
        super().wheelEvent(event)
        scene_point = self.mapToScene(event.position().toPoint())
        x = scene_point.x()
        y = scene_point.y()
        self.io['maineditor'].update('scroll', x, y)

        