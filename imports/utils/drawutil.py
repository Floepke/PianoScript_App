from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPolygonF, QFont
from typing import Union, Tuple
from PySide6.QtGui import QFontDatabase

import sys
import time
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from typing import Tuple

class DrawUtil:
    '''
        This class has methods for basic drawing operations on a QGraphicsScene.
        The class is based on tkinter's Canvas class drawing methods.

        The following methods are available:
        - new_line(); add a line to the scene
            * x1: x-coordinate of the start point
            * y1: y-coordinate of the start point
            * x2: x-coordinate of the end point
            * y2: y-coordinate of the end point
            * dash: list of dash lengths (e.g. [2, 4] for a dash of length 2 and a gap of length 4)
            * width: width of the line
            * capstyle: cap style of the line (Qt.RoundCap, Qt.FlatCap, Qt.SquareCap) default: Qt.RoundCap
            * joinstyle: join style of the line (Qt.RoundJoin, Qt.MiterJoin, Qt.BevelJoin) default: Qt.RoundJoin
            * color: color of the line (e.g. '#FF0000' for red)
            * tag: tag of the line (e.g. 'line1')
        - new_rectangle(); add a rectangle to the scene
            * x1: x-coordinate of the top left corner
            * y1: y-coordinate of the top left corner
            * x2: x-coordinate of the bottom right corner
            * y2: y-coordinate of the bottom right corner
            * dash: list of dash lengths (e.g. [2, 4] for a dash of length 2 and a gap of length 4)
            * width: width of the outline
            * capstyle: cap style of the outline (Qt.RoundCap, Qt.FlatCap, Qt.SquareCap) default: Qt.RoundCap
            * outline_color: color of the outline (e.g. '#FF0000' for red)
            * fill_color: color of the fill (e.g. '#FF0000' for red)
            * tag: tag of the rectangle (e.g. 'rectangle1')
        - new_oval(); add an oval to the scene
            * x1: x-coordinate of the top left corner
            * y1: y-coordinate of the top left corner
            * x2: x-coordinate of the bottom right corner
            * y2: y-coordinate of the bottom right corner
            * dash: list of dash lengths (e.g. [2, 4] for a dash of length 2 and a gap of length 4)
            * outline_width: width of the outline
            * outline_color: color of the outline (e.g. '#FF0000' for red)
            * fill_color: color of the fill (e.g. '#FF0000' for red)
            * tag: tag of the oval (e.g. 'oval1')
        - new_polygon()
            * points: list of xy points (e.g. [(50, 200), (150, 200), (150, 300), (40, 400)])
            * dash: list of dash lengths (e.g. [2, 4] for a dash of length 2 and a gap of length 4)
            * width: width of the outline
            * outline_color: color of the outline (e.g. '#FF0000' for red)
            * fill_color: color of the fill (e.g. '#FF0000' for red)
            * tag: tag of the polygon (e.g. 'polygon1')
        - new_text(); add text to the scene
            * x: x-coordinate of the text
            * y: y-coordinate of the text
            * text: text to be displayed
            * font: font of the text (e.g. 'Arial') or path to a ttf or otf font (e.g. '/home/user/fonts/arial.ttf')
            * size: size of the text (e.g. 12.0)
            * color: color of the text (e.g. '#FF0000' for red)
            * tag: tag of the text (e.g. 'text1')
            * anchor: anchor of the text (options: 'c', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw')
        - delete_with_tag(); delete all items with the given tag or tags
            * tag: tag or tuple of tags (e.g. 'line1' or ('line1', 'line2'))
        - delete_all(); delete all items
        - find_with_tag() (not yet implemented); find all items with the given tag or tags and return a list of items
            * tag: tag or tuple of tags (e.g. 'line1' or ('line1', 'line2'))
    '''
    def __init__(self, canvas: QGraphicsScene):
        self.canvas = canvas

    # basic shapes
    def new_line(self, x1: float, y1: float, x2: float, y2: float,
                  dash: list = None,
                  width: float = 1.0, 
                  capstyle: Qt.PenCapStyle = Qt.RoundCap,
                  joinstyle: Qt.PenJoinStyle = Qt.RoundJoin,
                  color: str = '#000000',
                  tag: str = 'undefined'):
        '''Add a line to the scene.'''
        
        # Create a line from (x1, y1) to (x2, y2)
        start = QPointF(x1, y1)
        end = QPointF(x2, y2)
        
        # Create a pen with the given properties
        pen = QPen()
        pen.setWidthF(width)
        pen.setCapStyle(capstyle)
        pen.setJoinStyle(joinstyle)
        pen.setColor(QColor(color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        
        # Add the line to the scene
        line = self.canvas.addLine(start.x(), start.y(), end.x(), end.y(), pen)
        
        # Add a tag to the line item
        line.setData(0, tag)
    
    def new_rectangle(self, x1: float, y1: float, x2: float, y2: float,
                        dash: list = None,
                        width: float = 1.0, 
                        capstyle: Qt.PenCapStyle = Qt.RoundCap,
                        outline_color: str = '#000000',
                        fill_color: str = '#FFFFFF',
                        tag: str = 'undefined'):
        '''Add a rectangle to the scene.'''
        
        # Create a rectangle from (x1, y1) to (x2, y2)
        start = QPointF(x1, y1)
        end = QPointF(x2, y2)
        
        # Create a pen with the given properties
        pen = QPen()
        pen.setWidthF(width)
        pen.setCapStyle(capstyle)
        pen.setColor(QColor(outline_color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)

        # Add the rectangle to the scene
        rect = self.canvas.addRect(start.x(), start.y(), end.x() - start.x(), end.y() - start.y(), pen, QBrush(QColor(fill_color)))
        
        # Add a tag to the rectangle item
        rect.setData(0, tag)

    def new_oval(self, x1: float, y1: float, x2: float, y2: float,
                    dash: list = None,
                    outline_width: float = 1.0,
                    outline_color: str = '#000000',
                    fill_color: str = '#FFFFFF',
                    tag: str = 'undefined'):
        '''Add an oval to the scene.'''
        
        # Create an oval from (x1, y1) to (x2, y2)
        start = QPointF(x1, y1)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Create a pen with the given properties
        pen = QPen()
        pen.setWidthF(outline_width)
        pen.setColor(QColor(outline_color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        
        # Add the oval to the scene
        oval = self.canvas.addEllipse(start.x(), start.y(), width, height, pen, QBrush(QColor(fill_color)))
        
        # Add a tag to the oval item
        oval.setData(0, tag)

    def new_polygon(self, points: list,
                    dash: list = None,
                    width: float = 1.0,
                    outline_color: str = '#000000',
                    fill_color: str = '#FFFFFF',
                    tag: str = 'undefined'):
        '''Add a polygon to the scene.'''
        
        # Create a polygon from the given points
        polygon = QPolygonF([QPointF(x, y) for x, y in points])
        
        # Create a pen with the given properties
        pen = QPen()
        pen.setWidthF(width)
        pen.setColor(QColor(outline_color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        
        # Add the polygon to the scene
        polygon_item = self.canvas.addPolygon(polygon, pen, QBrush(QColor(fill_color)))
        
        # Add a tag to the polygon item
        polygon_item.setData(0, tag)

    def new_text(self, x: float, y: float, text: str,
                 font: str = 'Arial',
                 size: float = 12.0, 
                 color: str = '#000000', 
                 tag: str = 'undefined',
                 anchor: str = 'c',
                 angle: float = 0.0):
        '''Add text to the scene.'''
        
        # Create a font with the given properties
        if (font.endswith('.ttf') or font.endswith('.otf')) and font.startswith('/'):
            # If the font is a path to a ttf or otf font:
            font_id = QFontDatabase.addApplicationFont(font)
            font = QFontDatabase.applicationFontFamilies(font_id)[0]
            font = QFont(font, size)
        elif QFontDatabase.hasFamily(font):
            # If the font is available for QFont:
            font = QFont(font, size)
        else:
            # Use Arial as default font:
            font = QFont('Courier New', size)

        # Add the text to the scene and set its position, angle and color
        text_item = self.canvas.addText(text, font)
        text_item.setPos(x, y)
        text_item.setDefaultTextColor(QColor(color))
        text_item.setRotation(angle)

        # Set the anchor of the text item (options: 'c', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw')
        if anchor == 'c' or anchor not in ['c', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']:
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width() / 2, y - bounding_rect.height() / 2)
        elif anchor == 'n':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width() / 2, y)
        elif anchor == 'ne':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width(), y)
        elif anchor == 'e':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width(), y - bounding_rect.height() / 2)
        elif anchor == 'se':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width(), y - bounding_rect.height())
        elif anchor == 's':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width() / 2, y - bounding_rect.height())
        elif anchor == 'sw':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x, y - bounding_rect.height())
        elif anchor == 'w':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x, y - bounding_rect.height() / 2)
        elif anchor == 'nw':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x, y)

        text_item.setTransformOriginPoint(bounding_rect.width() / 2, bounding_rect.height() / 2)

        # Add a tag to the text item
        text_item.setData(0, tag)

    def delete_with_tag(self, tag: Union[str, Tuple[str, ...]]):
        '''Delete all items with the given tag or tags.'''
        
        # Loop through all items in the scene and delete the ones with the given tag or tags
        for item in self.canvas.items():
            item_data = item.data(0)
            if isinstance(tag, tuple):
                if any(t == item_data for t in tag):
                    self.canvas.removeItem(item)
            else:
                if item_data == tag:
                    self.canvas.removeItem(item)

    def delete_all(self):
        '''Delete all items.'''
        self.canvas.clear()

    def find_with_tag(self, tag: Union[str, Tuple[str, ...]]):
        '''Find all items with the given tag or tags and return a list of items.'''
        scene_items = self.canvas.items()
        if isinstance(tag, tuple):
            items = [item for item in scene_items if item.data(0) in tag]
            items.sort(key=lambda item: tag.index(item.data(0)))
            return items
        else:
            return [item for item in scene_items if item.data(0) == tag]

    def tag_raise(self, tag: Union[str, Tuple[str, ...]]):
        '''Raise items with the given tag or tags to the top of the scene.'''
        items = self.find_with_tag(tag)
        highest_z = max(item.zValue() for item in self.canvas.items()) if self.canvas.items() else 0
        for item in items:
            item.setZValue(highest_z + 1.0)
    
    def tag_lower(self, tag: Union[str, Tuple[str, ...]]):
        '''Lower items with the given tag or tags to the bottom of the scene.'''
        items = self.find_with_tag(tag)
        lowest_z = min(item.zValue() for item in self.canvas.items()) if self.canvas.items() else 0
        for item in items:
            item.setZValue(lowest_z - 1.0)


# class TestApplication(QApplication):
#     def __init__(self, sys_argv):
#         super().__init__(sys_argv)
        
#         # Create the graphics view and scene
#         self.view = QGraphicsView()
#         self.scene = QGraphicsScene()
#         self.view.setScene(self.scene)
        
#         # Set the size of the graphics view
#         self.view.setFixedSize(800, 600)

#         # use the drawutil class
#         self.drawutil = DrawUtil(self.scene)
        
#         # Add rectangles to the scene
#         self.add_rectangles()
        
#         # Show the graphics view
#         self.view.show()

#         self.raise_rectangles()

#     def keyPressEvent(self, event):
#         if event.key() == Qt.Key_Escape:
#             self.raise_rectangles()
#         else:
#             super().keyPressEvent(event)
        
#     def add_rectangles(self):
#         colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#FF8000', '#8000FF', '#0080FF', '#FF0080']
#         for i, color in enumerate(colors):
#             x = i * 50
#             y = i * 50
#             width = 200
#             height = 200
#             self.drawutil.new_rectangle(x, y, x + width, y + height, fill_color=color, tag=f'rectangle{i}')
        
#     def raise_rectangles(self):
#         # for i in reversed(range(10)):
#         #     tag = f'rectangle{i}'
#         #     self.drawutil.tag_raise(tag)
#         #     time.sleep(0.1)
#         self.drawutil.tag_raise(('rectangle0', 'rectangle4', 'rectangle2', 'rectangle3', 'rectangle1', 'rectangle5', 'rectangle9', 'rectangle7', 'rectangle8', 'rectangle6'))

# if __name__ == '__main__':
#     app = TestApplication(sys.argv)
#     sys.exit(app.exec())
