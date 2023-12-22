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
        The following methods are available:
        - new_line()
        - new_rectangle()
        - new_oval()
        - new_polygon()
        - new_text()
        - delete_with_tag()
        - delete_all()
        - find_with_tag() (not yet implemented)
    '''
    def __init__(self, canvas: QGraphicsScene):
        self.canvas = canvas

    # basic shapes
    def new_line(self, x1: float, y1: float, x2: float, y2: float,
                  dash: list = None,
                  width: float = 1.0, 
                  capstyle: Qt.PenCapStyle = Qt.RoundCap,
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
