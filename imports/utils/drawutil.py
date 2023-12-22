from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPolygonF, QFont
from typing import Union, Tuple
from PySide6.QtGui import QFontDatabase

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
                 anchor: str = 'c'):
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

        # Add the text to the scene and set its position, anchor and color
        text_item = self.canvas.addText(text, font)
        text_item.setPos(x, y)
        text_item.setDefaultTextColor(QColor(color))

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
            return [item for item in scene_items if item.data(0) in tag]
        else:
            return [item for item in scene_items if item.data(0) == tag]
    















# Test the DrawBasicShapes class
if __name__ == "__main__":
    # Create the application
    app = QApplication([])

    # Create a QGraphicsScene and set its size
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 400, 400)

    # Create a QGraphicsView to display the scene
    view = QGraphicsView(scene)
    view.setWindowTitle("Test Application")
    view.show()

    # Create an instance of DrawBasicShapes
    draw_tools = DrawUtil(scene)

    # Create a rectangle without dash
    draw_tools.new_rectangle(50, 50, 150, 100, 
                             outline_color='#FF0000', 
                             fill_color='#FFFF00', 
                             tag='rectangle')

    # Create a rectangle with dash
    draw_tools.new_rectangle(200, 50, 300, 100, 
                             dash=[2, 4], 
                             outline_color='#FF0000', 
                             fill_color='#FFFF00', 
                             tag='rectangle')

    # Create a line without dash
    draw_tools.new_line(350, 75, 450, 75, 
                        width=2.0, 
                        color='#00FF00', 
                        tag='line')

    # Create a line with dash
    draw_tools.new_line(500, 75, 600, 75, 
                        width=2.0, 
                        color='#00FF00', 
                        dash=[2, 4], 
                        tag='line')

    # Create an oval without dash
    draw_tools.new_oval(650, 50, 750, 150, 
                        outline_color='#0000FF', 
                        fill_color='#00FFFF', 
                        tag='oval')

    # Create an oval with dash
    draw_tools.new_oval(800, 50, 900, 150, 
                        outline_color='#0000FF', 
                        fill_color='#00FFFF', 
                        dash=[2, 4], 
                        tag='oval')

    # Create a polygon without dash
    draw_tools.new_polygon([(50, 200), (150, 200), (150, 300), (40, 400)], 
                           outline_color='#0000FF', 
                           fill_color='#FF00FF', 
                           tag='polygon', 
                           dash=[2, 4], 
                           width=2.0)

    # Run the application event loop
    app.exec()
