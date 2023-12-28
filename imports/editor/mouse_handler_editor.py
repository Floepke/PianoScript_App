from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QGraphicsView

class MouseHandlerEditor(QGraphicsView):
    '''class that updates all mouse events in the io dict'''

    def __init__(self, io, parent=None):
        super().__init__(parent)
        self.io = io
        self.graphics_view = self.io['gui'].editor_scene.graphics_view

    def mouse_update(self, event):
        '''updates the relative mouse position on the graphicsview in the io dict'''
        scene_point = self.graphics_view.mapToScene(event.x(), event.y())
        relative_x = scene_point.x()
        relative_y = scene_point.y()
        self.io['mouse']['x'] = relative_x
        self.io['mouse']['y'] = relative_y
        self.io['mouse']['pitch'] = self.io['calctools'].x2pitch_editor(relative_x)
        self.io['mouse']['time'] = self.io['calctools'].y2tick_editor(relative_y)

    def mouse_press(self, event):
        '''updates the mouse position in the io dict and calls the mouse handler'''
        self.mouse_update(event)
        print('mouse press')
    
    def mouse_move(self, event):
        '''updates the mouse position in the io dict and calls the mouse handler'''
        self.mouse_update(event)
        print(self.io['calctools'].x2pitch_editor(event.x()))
        print('mouse move')
    
    def mouse_release(self, event):
        '''updates the mouse position in the io dict and calls the mouse handler'''
        self.mouse_update(event)
        print('mouse release')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print('Left button pressed')
        elif event.button() == Qt.RightButton:
            print('Right button pressed')
        elif event.button() == Qt.MiddleButton:
            print('Middle button pressed')
        print('Mouse position:', event.pos())

    def mouseMoveEvent(self, event):
        print('Mouse position:', event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            print('Left button released')
        elif event.button() == Qt.RightButton:
            print('Right button released')
        elif event.button() == Qt.MiddleButton:
            print('Middle button released')
        print('Mouse position:', event.pos())

    