from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QGraphicsView

class Mouse:
    '''class that updates all mouse events in the io dict'''

    def __init__(self, io, graphics_view:QGraphicsView):
        
        self.io = io
        self.graphics_view = graphics_view

        # setup mouse tracking:
        self.graphics_view.mouse_position.connect(self.mouse_move)
        self.graphics_view.mouse_pressed.connect(self.mouse_pressed)
        self.graphics_view.mouse_released.connect(self.mouse_released)

    def mouse_move(self, x, y):
        '''updates the relative mouse position on the graphicsview in the io dict'''
        scene_point = self.graphics_view.mapToScene(x, y)
        relative_x = scene_point.x()
        relative_y = scene_point.y()
        self.io['mouse']['x'] = relative_x
        self.io['mouse']['y'] = relative_y
        self.io['mouse']['pitch'] = self.io['calctools'].x2pitch_editor(relative_x)
        self.io['mouse']['time'] = self.io['calctools'].y2tick_editor(relative_y)
    
    def mouse_pressed(self, x, y):
        '''updates the mouse position in the io dict'''
        self.mouse_move(x, y)
    
    def mouse_released(self, x, y):
        '''updates the mouse position in the io dict'''
        self.mouse_move(x, y)
