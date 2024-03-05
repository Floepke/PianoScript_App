#! python3.11
# coding: utf8

""" 2d Drawing routines, most copied from Philip Bergwerf's drawutil.py """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

# pylint: disable=no-name-in-module
from PySide6.QtCore import Qt
from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF

from PySide6.QtGui import QBrush
from PySide6.QtGui import QPen
from PySide6.QtGui import QPolygonF
from PySide6.QtGui import QFont
from PySide6.QtGui import QFontDatabase
from PySide6.QtGui import QColor

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QGraphicsItem
# pylint: enable=no-name-in-module


class DrawHelper:
    """ helper functions for drawing """

    @staticmethod
    def create_pen(**kwargs):
        """ create a pen for drawing lines or outlines """

        pen = QPen()

        key = 'width'
        if 'outline_width' in kwargs:
            key = 'outline_width'
        width = kwargs.get(key, 1)

        key = 'color'
        if 'outline_color' in kwargs:
            key = 'outline_color'
        color = kwargs.get(key, '#000000')

        if width == 0 or color == '':
            pen.setStyle(Qt.NoPen)
            return pen

        pen.setWidthF(width)
        pen.setCapStyle(kwargs.get('cap_style', Qt.RoundCap))
        pen.setJoinStyle(kwargs.get('join_style', Qt.RoundJoin))
        pen.setColor(QColor(color))

        dash = kwargs.get('dash', None)
        if dash is not None:
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern(dash)
        elif dash is None:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])
        elif not dash:
            pen.setStyle(Qt.SolidLine)
            pen.setDashPattern([])

        return pen

    @staticmethod
    def create_brush(**kwargs) -> QBrush:
        """ create a brush """

        brush = QBrush()
        fill_color = kwargs.get('fill_color', '#FFFFFF')
        if fill_color == '':
            brush.setStyle(Qt.NoBrush)
        else:
            brush.setColor(QColor(fill_color))
            brush.setStyle(Qt.SolidPattern)

        return brush

    @staticmethod
    def create_font(**kwargs):
        """ Create a font with the given properties """

        family = kwargs.get('family', 'Arial')
        size = int(kwargs.get('size', 12.0))

        if (family.endswith('.ttf') or family.endswith('.otf')) and family.startswith('/'):
            # If the font is a path to a ttf or otf font:
            font_id = QFontDatabase.addApplicationFont(family)
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
        elif not QFontDatabase.hasFamily(family):
            # Use Courier New as default font:
            family = 'Courier New'

        return QFont(family, size)


class Draw2d:
    """
        This class has methods for basic drawing operations on a QGraphicsScene.
        The class is based on tkinter's Canvas class drawing methods.

        The following methods are available:
        - new_line()
        - new_rectangle()
        - new_oval()
        - new_polygon()
        - new_text()
        - delete_with_tag()
        - delete_all()
        - find_with_tag()
        - tag_raise()
        - tag_lower()
        - find_items()
        - get_viewport()
        """

    def __init__(self, scene: QGraphicsScene):
        """ initialize the class """

        self.scene = scene
        self._background_color = 'white'

    # basic shapes
    def create_line(self,
                    x1: float, y1: float,
                    x2: float, y2: float,
                    **kwargs) -> None:
        """
            :param float x1: x-coordinate of the start point
            :param float y1: y-coordinate of the start point
            :param float x2: x-coordinate of the end point
            :param float y2: y-coordinate of the end point
            :param list dash: list of dash lengths (e.g. [2, 4] for a dash
                              of length 2 and a gap of length 4)
            :param int width: width of the line
            :param CapStyle capstyle: cap style of the line (Qt.RoundCap,
                              Qt.FlatCap, Qt.SquareCap) default: Qt.RoundCap
            :param JoinStyle joinstyle: join style of the line (Qt.RoundJoin,
                              Qt.MiterJoin, Qt.BevelJoin) default: Qt.RoundJoin
            :param str color: color of the line (e.g. '#FF0000' for red)
            :param str tag: tag of the line (e.g. 'line1')Create a line from (x1, y1) to (x2, y2)
        """

        # Create a pen with the given properties
        pen = DrawHelper.create_pen(**kwargs)

        line = self.scene.addLine(x1, y1, x2, y2, pen)

        # Add a tag to the line item
        line.setData(0, kwargs.get('tag', []))

    def create_rectangle(self,
                         x1: float, y1: float,
                         x2: float, y2: float,
                         **kwargs) -> None:
        """
            :param float x1: x-coordinate of the top left corner
            :param float y1: y-coordinate of the top left corner
            :param float x2: x-coordinate of the bottom right corner
            :param float y2: y-coordinate of the bottom right corner
            :param list dash: list of dash lengths (e.g. [2, 4] for a dash
                              of length 2 and a gap of length 4)
            :param  int width: width of the outline
            :param CapStyle capstyle: cap style of the outline (Qt.RoundCap,
                                      Qt.FlatCap, Qt.SquareCap) default: Qt.RoundCap
            :param str outline_color: color of the outline (e.g. '#FF0000' for red)
            :param str fill_color: color of the fill (e.g. '#FF0000' for red)
            :param str tag: tag of the rectangle (e.g. 'rectangle1')
        """

        pen = DrawHelper.create_pen(**kwargs)
        brush = DrawHelper.create_brush(**kwargs)

        # Add the rectangle to the scene
        rect = self.scene.addRect(x1,
                                  y1,
                                  x2 - x1,
                                  y2 - y1,
                                  pen,
                                  brush)

        # Add a tag to the line item
        rect.setData(0, kwargs.get('tag', []))

    def create_oval(self,
                    x1: float, y1: float,
                    x2: float, y2: float,
                    **kwargs):
        """
            :param float x1: x-coordinate of the top left corner
            :param float y1: y-coordinate of the top left corner
            :param float x2: x-coordinate of the bottom right corner
            :param float y2: y-coordinate of the bottom right corner
            :param str dash: list of dash lengths (e.g. [2, 4] for a dash of
                             length 2 and a gap of length 4)
            :param int outline_width: width of the outline
            :param str outline_color: color of the outline (e.g. '#FF0000' for red)
            :param str fill_color: color of the fill (e.g. '#FF0000' for red)
            :param str tag: tag of the oval (e.g. 'oval1')
        """

        # Create a new pen and a new brush object with the given properties
        pen = DrawHelper.create_pen(**kwargs)
        brush = DrawHelper.create_brush(**kwargs)

        # Create an oval from (x1, y1) to (x2, y2)
        oval = self.scene.addEllipse(x1, y1,
                                     abs(x2 - x1),  # width
                                     abs(y2 - y1),  # height
                                     pen,
                                     brush)

        # Add a tag to the line item
        oval.setData(0, kwargs.get('tag', []))

    def create_polygon(self,
                       points: list,
                       **kwargs):
        """
            :param [tuple] points: list of xy points (e.g.
                                   [(50, 200), (150, 200), (150, 300), (40, 400)])
            :param list dash: list of dash lengths (e.g. [2, 4] for a dash of
                              length 2 and a gap of length 4)
            :param int width: width of the outline
            :param str outline_color: color of the outline (e.g. '#FF0000' for red)
            :param str fill_color: color of the fill (e.g. '#FF0000' for red)
            :param str tag: tag of the polygon (e.g. 'polygon1')
        """

        # Create a polygon from the given points
        polygon = QPolygonF([QPointF(x, y) for x, y in points])

        # Create a new pen and a new brush object with the given properties
        pen = DrawHelper.create_pen(**kwargs)
        brush = DrawHelper.create_brush(**kwargs)

        # Add the polygon to the scene
        polygon_item = self.scene.addPolygon(polygon, pen, brush)

        # Add a tag to the line item
        polygon_item.setData(0, kwargs.get('tag', []))

    def create_text(self,
                    x: float,
                    y: float,
                    text: str,
                    **kwargs):
        """
            :param float x: x-coordinate of the text
            :param float y: y-coordinate of the text
            :param str text: text to be displayed
            :param str font: font of the text (e.g. 'Arial') or path to a
                             ttf or otf font (e.g. '/home/user/fonts/arial.ttf')
            :param float size: size of the text (e.g. 12.0)
            :param str color: color of the text (e.g. '#FF0000' for red)
            :param str tag: tag of the text (e.g. 'text1')
            :param str anchor: anchor of the text (options: 'c', 'n', 'ne', 'e',
                               'se', 's', 'sw', 'w', 'nw')
        """

        # Create a font with the given properties
        font = DrawHelper.create_font(**kwargs)
        color = kwargs.get('color', '#000000')
        angle = kwargs.get('angle', 0.0)

        # Add the text to the scene and set its position, angle and color
        text_item = self.scene.addText(text, font)
        text_item.setDefaultTextColor(QColor(color))
        text_item.setRotation(angle)

        bounding_rect = text_item.boundingRect()
        width = bounding_rect.width()
        height = bounding_rect.height()

        # Set the anchor of the text item
        anchor = kwargs.get('anchor', 'c')
        match anchor:
            case 'n':
                text_item.setPos(x - width / 2, y)

            case 'ne':
                text_item.setPos(x - width, y)

            case 'e':
                text_item.setPos(x - width, y - height / 2)

            case 'se':
                text_item.setPos(x - width, y - height)

            case 's':
                text_item.setPos(x - width / 2, y - height)

            case 'sw':
                text_item.setPos(x, y - height)

            case 'w':
                text_item.setPos(x, y - height / 2)

            case 'nw':
                text_item.setPos(x, y)

            case _:  # also 'c'
                text_item.setPos(x - width / 2, y - height / 2)

        text_item.setTransformOriginPoint(width / 2, height / 2)

        # Add a tag to the line item
        text_item.setData(0, kwargs.get('tag', []))

    # This part are the methods that handle the tags of the items.
    def find_with_tag(self, tag: list):
        """ Find all items with the given tag or tags and return a list of items. """

        items = []
        for item in self.scene.items():
            item_data = item.data(0)
            for t in tag:
                if t in item_data:
                    items.append(item)
        return items

    def delete_with_tag(self, tag: list):
        """ Delete all items with the given tag or tags.
            :param str tag: or tuple of tags (e.g. 'line1' or ('line1', 'line2'))
        """

        for item in self.find_with_tag(tag):
            self.scene.removeItem(item)

    def delete_item(self, item: QGraphicsItem):
        """ Delete the given item.
            :param QGraphicsItem item: the item to delete
        """
        self.scene.removeItem(item)

    def delete_all(self):
        """ Delete all items. """

        self.scene.clear()

    def delete_if_with_all_tags(self, tags: list):
        """ Delete all items with all the given tags.
            :param list tags: list of tags from items to be deleted
        """

        for item in self.scene.items():
            item_data = item.data(0)
            if all(t in item_data for t in tags):
                self.scene.removeItem(item)

    def tag_raise(self, tag: list):
        """ Raise items with the given tag or tags to the top of the scene.
            :param [str] tag: the tag of the items to be raised
        """

        try:
            zvalue = self.scene.items()[-1].zValue()  # noqa
        except IndexError:
            zvalue = 0  # noqa

        for t in tag:
            for item in self.find_with_tag([t]):
                item.setZValue(zvalue)
                zvalue += 1

    def tag_lower(self, tag: list):
        """ Lower items with the given tag or tags to the bottom of the scene.
            :param [str] tag: the tag of the items to be lowered
        """

        zvalue = self.scene.items()[0].zValue()  # noqa
        for t in tag:
            for item in self.find_with_tag([t]):
                item.setZValue(zvalue)
                zvalue -= 1

    def find_items(self, x: float, y: float, tag: list = None):
        """ Find all items at the given position that are
            in the tag list and return a list of items.
            :param float x: the x coordinate
            :param float y: the y coordinate
            :param [str] tag: the list of tags
        """

        scene_items = self.scene.items(QPointF(x, y))
        if tag is not None:
            return [item for item in scene_items if item.data(0) in tag]
        return scene_items

    def get_xy_tags(self, x: float, y: float):
        """ Get all tags at the given position. """

        point = QPointF(x, y)
        items = self.scene.items(point)
        detect = [item.data(0) for item in items]
        out = []
        for d in detect:
            for t in d:
                out.append(t)
        return out

    # get viewport coordinates
    def get_viewport_coords(self) -> QRectF:  # noqa
        """ Get the viewport coordinates.
            :returns QRectF: the recangle of the viewport
        """

        return self.scene.sceneRect()

    def background(self, color: str):
        """ set the background color """

        self.scene.setBackgroundBrush(QColor(color))
