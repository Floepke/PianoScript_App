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

_KEYBOARDVIEW_WIDTH = 532
_KEYBOARDVIEW_HEIGHT = 60


class KeyboardView():
    """ display a measure """

    def __init__(self):
        """ draw a measure example """

        self._scene = None
        self._view = None
        self._drawer = None
        self.start_text = None
        self.finish_text = None

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
        return int(value * 0.5)

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
            (0, 1), (10, 1),  # Cis1, Dis1
            (30, 2), (40, 2), (50, 2),  # Fis1, Gis1, Ais2
            ]

        octaves = [
            (10, 2)  # Bis1
        ]

        for idx1 in range(7):
            for key, mode in octave:
                if idx1 == 3 and mode == 1:
                    mode = 3
                pos = 30 + key + idx1 * 70
                elem = (pos, mode)
                octaves.append(elem)

        # draw the lines for the bar
        for x_pos, mode in octaves:
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
                               y1=margin,
                               x2=x2,
                               y2=margin + 40,
                               width=width,
                               dash=dash,
                               fill='black')

        x1 = self.scale_x(margin)
        x2 = self.scale_x(margin + 40)
        top_bottom = [(x1, 2, right), (x2 + 40, 2, right)]

        for y_pos, width, size in top_bottom:
            drawer.create_line(x1=0,
                               y1=y_pos,
                               x2=size,
                               y2=y_pos,
                               width=width,
                               color='black')

    def start(self, value: int):
        """ the staff start """

        txt = self.start_text
        if txt is not None:
            self._scene.removeItem(txt)

        pos, name = self._mapping[value]
        txt = self._scene.addText(name)
        txt.setPos(self.scale_x(pos), 40)
        self.start_text = txt

    def finish(self, value: int):
        """ the staff finish """

        txt = self.finish_text
        if txt is not None:
            self._scene.removeItem(txt)

        pos, name = self._mapping[value]
        txt = self._scene.addText(name)
        txt.setPos(self.scale_x(pos), 40)
        self.finish_text = txt
