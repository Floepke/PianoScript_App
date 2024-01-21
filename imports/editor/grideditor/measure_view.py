#! python3.11
# coding: utf8

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QGraphicsView
# pylint: enable=no-name-in-module

from imports.editor.grideditor.draw_2d import Draw2d


class MeasureView():
    """ display a measure """

    def __init__(self):
        """ draw a measure example """

        self._scene = None
        self._view = None
        self._drawer = None

    @property
    def view(self) -> QGraphicsView:
        """ the view for the measure """

        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0.0, 0.0, 200.0, 200.0)
        self._view = QGraphicsView(self._scene)
        self._drawer = Draw2d(scene=self._scene)

        return self._view

    # pylint: disable=too-many-locals
    def draw_measure(self,
                     visible: bool,
                     numerator: int,
                     hidden: list = None):
        """ draw the measure counting lines """

        if hidden is None:
            hidden = []

        drawer = self._drawer
        drawer.delete_all()

        rect = drawer.get_viewport_coords()
        right = rect.width()
        bottom = rect.height()
        margin = 3

        if visible:
            # draw the lines for the bar
            for x_pos, mode in [
                (25, 1), (35, 1),
                (55, 2), (65, 2), (75, 2),
                (95, 3), (105, 3),
                (125, 2), (135, 2), (145, 2),
                (165, 1), (175, 1)
            ]:
                width = 1
                dash = None
                match mode:
                    case 2:
                        width = 2
                    case 3:
                        dash = (3, 3)

                drawer.create_line(x1=x_pos + 10,
                                   y1=margin,
                                   x2=x_pos + 10,
                                   y2=bottom - margin,
                                   width=width,
                                   dash=dash,
                                   fill='black')
        else:
            drawer.create_text(x=20,
                               y=20,
                               anchor='w',
                               text='(left blank)')

        lines = [(margin, 2, right), (bottom - margin, 2, right)]

        if visible:
            step = bottom / numerator
            font_size = max(min(step - 6, 12), 4)

            pos = step
            for meas_line in range(1, numerator):
                size = 30 if meas_line + 1 in hidden else right
                lines.append((pos, 1, size))
                pos += step

            for idx in range(0, numerator):
                y_pos = 8 + idx * step
                x_pos = 10
                drawer.create_text(x=x_pos,
                                   y=y_pos,
                                   text=str(idx + 1),
                                   family='Arial',
                                   size=font_size)

        for y_pos, width, size in lines:
            drawer.create_line(x1=20,
                               y1=y_pos,
                               x2=size,
                               y2=y_pos,
                               width=width,
                               color='black')
