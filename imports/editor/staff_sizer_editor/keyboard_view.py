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
_KEYBOARDVIEW_HEIGHT = 120


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
            -1: (0, 'auto'),
            # start notes
            1: (10, 'A0'),#changed from 0 to 10
            4: (30, 'C1'),
            9: (60, 'F1'),
            16: (100, 'C2'),
            21: (130, 'F2'),
            28: (170, 'C3'),
            33: (200, 'F3'),
            40: (240, 'C4'),
            45: (270, 'F4'),
            52: (310, 'C5'),
            57: (340, 'F5'),
            64: (380, 'C6'),
            69: (410, 'F6'),
            76: (450, 'C7'),
            81: (480, 'F7'),
            # finish notes
            3: (20, 'B0'),
            8: (50, 'E1'),
            15: (90, 'B1'),
            20: (120, 'E2'),
            27: (160, 'B2'),
            32: (190, 'E3'),
            39: (230, 'B3'),
            44: (260, 'E4'),
            51: (300, 'B4'),
            56: (330, 'E5'),
            63: (370, 'B5'),
            68: (400, 'E6'),
            75: (440, 'B6'),
            80: (470, 'E7'),
            87: (510, 'B7'),
        }

        self._octave_nrs = [
            (4,  30, '1'),
            (16, 100, '2'),
            (28, 170, '3'),
            (40, 240, '4'),
            (52, 310, '5'),
            (64, 380, '6'),
            (76, 450, '7'),
            (87, 530, '8'),
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

        octave = [
            (0, 1, 5), (10, 1, 7),  # Cis1, Dis1
            (30, 2, 10), (40, 2, 12), (50, 2, 14),  # Fis1, Gis1, Ais2
            ]

        octaves = [
            #(5, 2, 2),  # A0
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
        if not self._auto:
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
                                    y1=25,
                                    x2=x2,
                                    y2=150,
                                    width=width,
                                    dash=dash,
                                    fill='black')

            top_bottom = [(25, 2)]
            _x1, _ = self._mapping.get(self._start, 40)
            _x2, _ = self._mapping.get(self._finish, 45)

            for y_pos, width in top_bottom:
                drawer.create_line(x1=self.scale_x(_x1)+5,
                                y1=y_pos,
                                x2=self.scale_x(_x2),
                                y2=y_pos,
                                width=width,
                                color='black')
                drawer.create_line(x1=self.scale_x(_x1)+5,
                                y1=y_pos+40,
                                x2=self.scale_x(_x2),
                                y2=y_pos+40,
                                width=1,
                                dash=(3, 3))
                drawer.create_line(x1=self.scale_x(_x1)+5,
                                y1=y_pos+80,
                                x2=self.scale_x(_x2),
                                y2=y_pos+80,
                                width=1,
                                dash=(3, 3))

            pos, name = self._mapping.get(self._start, 4)

            drawer.create_text(x=self.scale_x(pos),
                            y=40,
                            text=name + '  >',
                            anchor='e',
                            family='Arial',
                            size=12)

            pos, name = self._mapping.get(self._finish, (37, 'None'))

            drawer.create_text(x=self.scale_x(pos),
                            y=40,
                            text='<  ' + name,
                            anchor='w',
                            family='Arial',
                            size=12)

            # draw the octave numbers
            for note, pos, oct in self._octave_nrs:
                flg = self._start < note < self._finish
                if flg or self._auto:
                    drawer.create_text(x=self.scale_x(pos) + 2,
                                    y=5,
                                    text=oct,
                                    anchor='n',
                                    family='Arial',
                                    size=12)
        else:
            drawer.create_text(x=right / 2,
                            y=rect.height() / 2,
                            anchor='c',
                            text='Automatic',
                            family='Edwin',
                            size=32)

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

        return 1

    def valid_finish(self, value: int):
        """ check the finish position """

        if value in self._mapping:
            return value

        return 87
