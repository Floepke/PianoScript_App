#! python3.11
# coding: utf8

""" the keyboard view control, used for the staff_sizer """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtWidgets import QGraphicsView
# pylint: enable=no-name-in-module

from imports.editor.grideditor.draw_2d import Draw2d
from imports.utils.constants import BACKGROUND_COLOR

_KEYBOARDVIEW_WIDTH = 550
_KEYBOARDVIEW_HEIGHT = 60


class KeyboardView():
    """ display a measure """

    def __init__(self, scale: float = 0.50):
        """ draw a measure example """

        self._scene = None
        self._view = None
        self._drawer = None
        self._start = 0
        self._finish = 86
        self._auto = True
        self._scale = scale

        self._mapping = {
            # auto
            -1: (240, 'auto'),
            # start notes
            3: (30, 'C1'),
            8: (60, 'F1'),
            15: (100, 'C2'),
            20: (130, 'F2'),
            27: (170, 'C3'),
            32: (200, 'F3'),
            39: (240, 'C4'),
            44: (270, 'F4'),
            51: (310, 'C5'),
            56: (340, 'F5'),
            63: (380, 'C6'),
            68: (410, 'F6'),
            75: (450, 'C7'),
            80: (480, 'F7'),
            # finish notes
            2: (20, 'B0'),
            7: (50, 'E1'),
            14: (90, 'B1'),
            19: (120, 'E2'),
            26: (160, 'B2'),
            31: (190, 'E3'),
            38: (230, 'B3'),
            43: (260, 'E4'),
            50: (300, 'B4'),
            55: (330, 'E5'),
            62: (370, 'B5'),
            67: (400, 'E6'),
            74: (440, 'B6'),
            79: (470, 'E7'),
            86: (510, 'B7'),
        }

        self._octave_nrs = [
            (3,  30, '1'),
            (15, 100, '2'),
            (27, 170, '3'),
            (39, 240, '4'),
            (51, 310, '5'),
            (63, 380, '6'),
            (75, 450, '7'),
            # (87, 530, '8'),
        ]

    @property
    def view(self) -> QGraphicsView:
        """ the view for the measure """

        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0.0, 0.0,
                                 self.scale_x(_KEYBOARDVIEW_WIDTH),
                                 _KEYBOARDVIEW_HEIGHT)
        self._view = QGraphicsView(self._scene)
        self._drawer = Draw2d(scene=self._scene)

        return self._view

    def scale_x(self, value: int):
        """ the x size scaler """
        return int(value * self._scale)

    # pylint: disable=too-many-locals
    def draw_keyboard(self):
        """ draw the measure counting lines """

        drawer = self._drawer
        drawer.delete_all()
        drawer.background(BACKGROUND_COLOR)
        rect = drawer.get_viewport_coords()
        right = rect.width()
        margin = 0

        octave = [
            (0, 1, 5), (10, 1, 7),  # Cis1, Dis1
            (30, 2, 10), (40, 2, 12), (50, 2, 14),  # Fis1, Gis1, Ais2
            ]

        octaves = [
            (10, 2, 2)  # Bis1
        ]

        for idx1 in range(7):
            for key, mode, nr in octave:
                if idx1 == 3 and mode == 1:
                    mode = 3
                pos = 30 + key + idx1 * 70
                note = nr + 12 * idx1
                elem = (pos, mode, note)
                octaves.append(elem)

        # draw the lines for the bar
        for x_pos, mode, note in octaves:
            flg = self._start <= note <= self._finish
            if flg or self._auto:
                width = 1
                dash = None
                match mode:
                    case 2:
                        width = 2
                    case 3:
                        dash = (3, 3)

                x1 = self.scale_x(x_pos + 10)
                x2 = self.scale_x(x_pos + 10)
                drawer.create_line(x1=x1,
                                   y1=17,
                                   x2=x2,
                                   y2=40,
                                   width=width,
                                   dash=dash,
                                   fill='black')

        top_bottom = [(17, 2), (40, 2)]

        for y_pos, width in top_bottom:
            drawer.create_line(x1=0,
                               y1=y_pos,
                               x2=right,
                               y2=y_pos,
                               width=width,
                               color='black')

        pos, name = self._mapping.get(self._start, 3)

        drawer.create_text(x=self.scale_x(pos),
                           y=40,
                           text=name,
                           anchor='nw',
                           family='Arial',
                           size=8)

        pos, name = self._mapping.get(self._finish, 2)

        drawer.create_text(x=self.scale_x(pos),
                           y=40,
                           text=name,
                           anchor='nw',
                           family='Arial',
                           size=8)

        for note, pos, oct in self._octave_nrs:
            flg = self._start < note < self._finish
            if flg or self._auto:
                drawer.create_text(x=self.scale_x(pos) - 5,
                                   y=0,
                                   text=oct,
                                   anchor='nw',
                                   family='Arial',
                                   size=8)

    def start(self, value: int, auto: bool):
        """ the staff start """

        self._start = value
        self._auto = auto
        self.draw_keyboard()

    def finish(self, value: int, auto: bool):
        """ the staff finish """

        self._finish = value
        self._auto = auto
        self.draw_keyboard()

    def valid_start(self, value: int):
        """ check the start position """

        if value in self._mapping:
            return value

        return 3

    def valid_finish(self, value: int):
        """ check the finish position """

        if value in self._mapping:
            return value

        return 86
