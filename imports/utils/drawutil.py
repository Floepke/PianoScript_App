from PySide6.QtCore import Qt, QPointF, QThread, Signal
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPolygonF, QFont
from PySide6.QtGui import QFontDatabase

import sys
import re
import time
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import QRectF


class Worker(QThread):
    draw_line_signal = Signal(QPointF, QPointF)

    def run(self):
        # Emit signal to draw line from (0, 0) to (100, 100)
        self.draw_line_signal.emit(QPointF(0, 0), QPointF(100, 100))


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
        - find_with_tag(); find all items with the given tag or tags and return a list of items
            * tag: tag or tuple of tags (e.g. 'line1' or ('line1', 'line2'))
        - tag_raise(); raise items with the given tag or tags to the top of the scene
            * tag: list of tags (e.g. ['line1'] or ['line1', 'line2', ...])
        - tag_lower(); lower items with the given tag or tags to the bottom of the scene
            * tag: list of tags (e.g. ['line1'] or ['line1', 'line2', ...])
        - find_items(); find all items at the given position that are in the tag list and return a list of items
            * x: x-coordinate of the position
            * y: y-coordinate of the position
            * tag: list of tags (e.g. ['line1'] or ['line1', 'line2', ...])
        - detect_item(); find all items at the given position that have the given string in their tag and return a list of items
            * x: x-coordinate of the position
            * y: y-coordinate of the position
            * object_type: string that is in the tag of the object (e.g. 'note' or 'beam')
        - detect_objects_rectangle(); find all items in the given rectangle that have the given string in their tag and return a list of items
            * x1: x-coordinate of the top left corner
            * y1: y-coordinate of the top left corner
            * x2: x-coordinate of the bottom right corner
            * y2: y-coordinate of the bottom right corner
            * object_type: string that is in the tag of the object (e.g. 'note' or 'beam')
        - get_viewport(); get the viewport coordinates
        '''

    def __init__(self, canvas: QGraphicsScene):
        self.canvas = canvas

        # Create a pen & brush object
        self.pen = QPen()
        self.brush = QBrush()
        self.brush.setColor(QColor('#00008833'))
        self.brush.setStyle(Qt.SolidPattern)

    # basic shapes
    def new_line(self, x1: float, y1: float, x2: float, y2: float,
                 dash: list = None,
                 width: float = 1.0,
                 capstyle: Qt.PenCapStyle = Qt.RoundCap,
                 joinstyle: Qt.PenJoinStyle = Qt.RoundJoin,
                 color: str = '#000000',
                 tag: list = []):
        '''Add a line to the scene.'''

        # Create a line from (x1, y1) to (x2, y2)
        start = QPointF(x1, y1)
        end = QPointF(x2, y2)

        # Create a pen with the given properties
        pen = self.pen
        pen.setWidthF(width)
        pen.setCapStyle(capstyle)
        pen.setJoinStyle(joinstyle)
        pen.setColor(QColor(color))
        if dash is not None:
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern(dash)
        else:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])

        # Add the line to the scene
        line = self.canvas.addLine(start.x(), start.y(), end.x(), end.y(), pen)

        # Add a tag to the line item
        line.setData(0, tag)

    def new_line_list(self, points: list,
                 dash: list = None,
                 width: float = 1.0,
                 capstyle: Qt.PenCapStyle = Qt.RoundCap,
                 joinstyle: Qt.PenJoinStyle = Qt.RoundJoin,
                 color: str = '#000000',
                 tag: list = []):
        '''Add a line to the scene.'''

        # Create a pen with the given properties
        pen = self.pen
        pen.setWidthF(width)
        pen.setCapStyle(capstyle)
        pen.setJoinStyle(joinstyle)
        pen.setColor(QColor(color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        else:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])

        # Iterate over the list of points
        for i in range(len(points) - 1):
            # Create a line from points[i] to points[i+1]
            start = QPointF(*points[i])
            end = QPointF(*points[i+1])

            # Add the line to the scene
            line = self.canvas.addLine(start.x(), start.y(), end.x(), end.y(), pen)

            # Add a tag to the line item
            line.setData(0, tag)

    def new_rectangle(self, x1: float, y1: float, x2: float, y2: float,
                      dash: list = None,
                      width: float = 1.0,
                      capstyle: Qt.PenCapStyle = Qt.RoundCap,
                      outline_color: str = '#000000ff',
                      fill_color: str = '#404040ff',
                      tag: list = []):
        '''Add a rectangle to the scene.'''

        # Create a rectangle from (x1, y1) to (x2, y2)
        start = QPointF(x1, y1)
        end = QPointF(x2, y2)

        # Create a pen with the given properties
        pen = self.pen
        pen.setWidthF(width)
        pen.setCapStyle(capstyle)
        # set color and alpha
        pen.setColor(QColor(outline_color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        else:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])

        brush = self.brush
        if fill_color:
            brush.setColor(QColor(fill_color))
            brush.setStyle(Qt.SolidPattern)
        else:
            brush.setStyle(Qt.NoBrush)

        # Add the rectangle to the scene
        rect = self.canvas.addRect(start.x(), start.y(), end.x(
        ) - start.x(), end.y() - start.y(), pen, brush)

        # Add a tag to the line item
        rect.setData(0, tag)

    def new_oval(self, x1: float, y1: float, x2: float, y2: float,
                 dash: list = None,
                 outline_width: float = 1.0,
                 outline_color: str = '#000000',
                 fill_color: str = '#FFFFFF',
                 tag: list = []):
        '''Add an oval to the scene.'''

        # Create an oval from (x1, y1) to (x2, y2)
        start = QPointF(x1, y1)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # Change the pen with the given properties
        pen = self.pen
        pen.setWidthF(outline_width)
        pen.setColor(QColor(outline_color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        else:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])
        if width == 0 or outline_color == '':
            pen.setStyle(Qt.NoPen)

        # Create a new brush object with the given properties
        brush = self.brush
        if fill_color == '':
            brush.setStyle(Qt.NoBrush)
        else:
            brush.setColor(QColor(fill_color))
            brush.setStyle(Qt.SolidPattern)

        # Add the oval to the scene
        oval = self.canvas.addEllipse(
            start.x(), start.y(), width, height, pen, brush)

        # Add a tag to the line item
        oval.setData(0, tag)

    def new_polygon(self, points: list,
                    dash: list = None,
                    width: float = 1.0,
                    outline_color: str = '#000000ff',
                    fill_color: str = '#000000ff',
                    tag: list = []):
        '''Add a polygon to the scene.'''

        # Create a polygon from the given points
        polygon = QPolygonF([QPointF(x, y) for x, y in points])

        # change the pen with the given properties
        pen = self.pen
        pen.setWidthF(width)
        pen.setColor(QColor(outline_color))
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        elif dash is None:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])
        elif dash == []:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])
        if outline_color == '':
            pen.setStyle(Qt.NoPen)
        pen.setWidthF(width)

        # Create a new brush object with the given properties
        brush = self.brush
        if fill_color == '':
            brush.setStyle(Qt.NoBrush)
        else:
            brush.setColor(QColor(fill_color))
            brush.setStyle(Qt.SolidPattern)

        # Add the polygon to the scene
        polygon_item = self.canvas.addPolygon(polygon, pen, brush)

        # Add a tag to the line item
        polygon_item.setData(0, tag)

    def new_text(self, x: float, y: float, text: str,
                 font: str = 'Arial',
                 size: float = 12.0,
                 color: str = '#000000',
                 tag: list = [],
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
            text_item.setPos(x - bounding_rect.width() / 2,
                             y - bounding_rect.height() / 2)
        elif anchor == 'n':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width() / 2, y)
        elif anchor == 'ne':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width(), y)
        elif anchor == 'e':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width(),
                             y - bounding_rect.height() / 2)
        elif anchor == 'se':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width(),
                             y - bounding_rect.height())
        elif anchor == 's':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x - bounding_rect.width() /
                             2, y - bounding_rect.height())
        elif anchor == 'sw':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x, y - bounding_rect.height())
        elif anchor == 'w':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x, y - bounding_rect.height() / 2)
        elif anchor == 'nw':
            bounding_rect = text_item.boundingRect()
            text_item.setPos(x, y)

        text_item.setTransformOriginPoint(
            bounding_rect.width() / 2, bounding_rect.height() / 2)

        # Add a tag to the line item
        text_item.setData(0, tag)

    '''This part are the methods that handle the tags of the items.'''

    def find_with_tag(self, tag: list):  # TODO: check if it works
        '''Find all items with the given tag or tags and return a list of items.'''
        items = []
        for item in self.canvas.items():
            item_data = item.data(0)
            for t in tag:
                if t in item_data:
                    items.append(item)
        return items

    def delete_with_tag(self, tag: list):
        '''Delete all items with the given tag or tags.'''
        for item in self.find_with_tag(tag):
            self.canvas.removeItem(item)

    def delete_item(self, item: QGraphicsItem):
        '''Delete the given item.'''
        self.canvas.removeItem(item)

    def delete_all(self):
        '''Delete all items.'''
        self.canvas.clear()

    def delete_if_with_all_tags(self, tags: list):
        '''Delete all items with all the given tags.'''
        for item in self.canvas.items():
            item_data = item.data(0)
            if all(t in item_data for t in tags):
                self.canvas.removeItem(item)

    def tag_raise(self, tag: list):
        '''Raise items with the given tag or tags to the top of the scene.'''
        try:
            zvalue = self.canvas.items()[-1].zValue()
        except IndexError:
            zvalue = 0
        for t in tag:
            for item in self.find_with_tag([t]):
                item.setZValue(zvalue)
                zvalue += 1

    def tag_lower(self, tag: list):
        '''Lower items with the given tag or tags to the bottom of the scene.'''
        zvalue = self.canvas.items()[0].zValue()
        for t in tag:
            for item in self.find_with_tag([t]):
                item.setZValue(zvalue)
                zvalue -= 1

    def find_items(self, x: float, y: float, tag: list = None):
        '''Find all items at the given position that are in the tag list and return a list of items.'''
        scene_items = self.canvas.items(QPointF(x, y))
        if tag is not None:
            return [item for item in scene_items if item.data(0) in tag]
        return scene_items

    def detect_item(self, io, x: float, y: float, event_type: str = 'all', return_item=False):
        '''Find all items at the given position that have the given string in their tag and return a list of items.'''
        scene_items = self.canvas.items(QPointF(x, y))
        if event_type is not None:
            for item in scene_items:
                tag = item.data(0)[0]
                if event_type == 'all':
                    # we are searching for any object type; if ending on a number it means it is a object in the score file
                    if bool(re.search(r'\d$', tag)):  # if ending on a number
                        for evttypes in io['score']['events'].keys():
                            # skip all events that are not selectable by the selection rectangle
                            if evttypes in ['grid']:
                                continue
                            for obj in io['score']['events'][evttypes]:
                                if obj['tag'] == tag:
                                    if return_item:
                                        return item
                                    return obj
                else:
                    # we are searching for a specific object type
                    if event_type in tag and bool(re.search(r'\d$', tag)):
                        for obj in io['score']['events'][event_type]:
                            if obj['tag'] == tag:
                                if return_item:
                                    return item
                                return obj
        return None  # TODO: make compitable with all event types

    def detect_objects_rectangle(self, io, x1: float, y1: float, x2: float, y2: float, event_type: str = 'all'):
        '''Find all items at the given position that have the given string in their tag and return a list of items.'''
        # evaluate the rectangle coordinates
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        # find all items in the rectangle
        scene_items = self.canvas.items(
            QRectF(QPointF(x1, y1), QPointF(x2, y2)))
        if event_type is not None:
            detected_objects = []
            for item in scene_items:
                tag = item.data(0)[0]
                if event_type == 'all':
                    # we are searching for any object type; if ending on a number it means it is a object in the score file
                    if bool(re.search(r'\d$', tag)):  # if ending on a number
                        for evttypes in io['score']['events'].keys():
                            # skip all events that are not selectable by the selection rectangle
                            if evttypes in ['grid']:
                                continue
                            for obj in io['score']['events'][evttypes]:
                                if obj['tag'] == tag:
                                    detected_objects.append(obj)
                else:
                    # we are searching for a specific object type
                    if event_type in tag and bool(re.search(r'\d$', tag)):
                        for note in io['score']['events'][event_type]:
                            if note['tag'] == tag:
                                detected_objects.append(note)
            if detected_objects:
                # remove duplicates
                detected_objects = list(
                    {v['tag']: v for v in detected_objects}.values())
                return detected_objects
        return None

    def find_with_tag(self, tag: str):
        '''Find all items with the given tag or tags and return a list of items.'''
        items = []
        for item in self.canvas.items():
            item_data = item.data(0)
            for t in tag:
                if t in item_data:
                    items.append(item)
        return items
    
    def get_tags_from_item(self, item: QGraphicsItem):
        '''Returns the tags associated with the given item'''
        return item.data(0)

    def get_xy_tags(self, x: float, y: float):
        '''Get all tags at the given position.'''
        point = QPointF(x, y)
        items = self.canvas.items(point)
        detect = [item.data(0) for item in items]
        out = []
        for d in detect:
            for t in d:
                out.append(t)
        return out

    # get viewport coordinates

    def get_viewport_coords(self):
        '''Get the viewport coordinates.'''
        return self.canvas.sceneRect()

    def move_item(self, item: QGraphicsItem, x: float, y: float):
        '''Move the QGraphicsItem to the specified position (x, y).'''
        item.setPos(x, y)

    def move_item_to_with_tag(self, tags: list, x: float, y: float):
        '''Move items with the specified tags to the specified position (x, y).'''
        items = self.find_with_tag(tags)
        for item in items:
            self.move_item(item, x, y)
