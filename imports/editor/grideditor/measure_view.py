#! python3.11
# coding: utf8

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QGraphicsView
# pylint: enable=no-name-in-module

from imports.editor.grideditor.draw_2d import Draw2d
from imports.utils.constants import BACKGROUND_COLOR

from imports.editor.grideditor.grid import Grid


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
                     data: Grid,
                     indicator: int):
        """ draw the measure counting lines """

        count_lines = [] if data.grid is None else data.grid

        drawer = self._drawer
        drawer.delete_all()
        drawer.background(BACKGROUND_COLOR)
        rect = drawer.get_viewport_coords()
        right = rect.width()
        bottom = rect.height()
        margin = 3

        if data.visible:
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

        top_bottom = [(margin, 2, right), (bottom - margin, 2, right)]

        for y_pos, width, size in top_bottom:
            drawer.create_line(x1=20,
                               y1=y_pos,
                               x2=size,
                               y2=y_pos,
                               width=width,
                               color='black')

        lines = []
        if data.visible:
            scale = Grid.base(data.denominator)
            step = bottom / data.numerator

            # for 3/4 we get 0, 256, 512
            # [1]  0    is not drawn
            # [2]  256  on bottom / 3
            # [3]  512  on bottom * 2 / 3
            # step = bottom / 3 (the numerator)
            # scale = 256 (from denominator)

            # for 4/4 we get 0, 256, 512, 1024, bottom is 1024
            # [1]  0    is not drawn
            # [2]  256  on bottom / 4
            # [3]  512  on bottom * 2 / 4
            # [4]  768  on bottom * 3 /4
            # step = bottom / 4 (the numerator)
            # scale = 256 (from denominator)

            # 256 / scale * step -> step
            # 512 / scale * step -> 2 * step
            # 768 / scale * step -> 3 * step

            font_size = max(min(step - 6, 12), 4)

            for count_line in count_lines:
                # size = 30 if meas_line + 1 in hidden else right
                y_pos = int(float(count_line) / scale * step)
                lines.append((y_pos, 1, right))

            for idx in range(0, data.numerator):
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
                               color='black',
                               dash=(5, 5))

        # the indicator line:
        min_y = margin
        max_y = bottom - margin
        delta = Grid.base(data.denominator)
        # print(f'denom {data.denominator} delta {delta}')
        top = delta * data.numerator
        y_pos  = int(min_y + (max_y - min_y) * indicator / top)
        width = 1
        drawer.create_line(x1=20,
                           y1=y_pos,
                           x2=right,
                           y2=y_pos,
                           width=width,
                           color='blue',
                           dash=(10, 10))