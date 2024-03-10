#! python3.11
# coding: utf8

""" editor for the line breaks """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

import pprint
# Ik denk een dialoogje wanneer je op de linebreak marker klikt met de linker
# muisknop waar de volgende eigenschapen in te stellen zijn:
# margin left(staff1-4),
# marginright(staff1-4),
# staff range toets x tot y(staff1-4)

from typing import Optional
from typing import Any
from typing import List
from typing import Callable
from typing import Self

# from jsons import dumps

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QListWidget
from PySide6.QtWidgets import QHBoxLayout

from PySide6.QtGui import QPixmap
from PySide6.QtGui import QFontMetrics

from PySide6.QtCore import Qt

# pylint: enable=no-name-in-module

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer
from imports.editor.staff_sizer_editor.staff_sizer_control import StaffSizerControl
from imports.editor.grideditor.dialog_result import DialogResult

from imports.editor.staff_sizer_editor.keyboard_view import KeyboardView
from imports.editor.staff_sizer_editor.staff_io import LineBreakIo


class StaffSizerDialog(QDialog):
    """ the example with four line breaks """

    def __init__(self,
                 parent: Optional[Any] = None,
                 callback: Optional[Callable] = None,
                 linebreaks: list = None,
                 time_calc: Callable = None):
        """ initialize the dialog """

        super().__init__(parent=parent)

        self.my_pixmap = QPixmap('./icons/GridEditor.png')
        self.setWindowIcon(self.my_pixmap)

        self.callback = callback
        self.result = DialogResult.CLOSE_WINDOW

        # contents = dumps(linebreaks)
        # with open(file='example.json', mode='w', encoding='utf8') as stream:
        #    stream.write(contents)

        self.linebreaks = LineBreakIo.importer(data=linebreaks,
                                               time_calc=time_calc)

        self.setWindowTitle('Line Preferences')

        layout = QGridLayout(parent=parent)

        measures = [str(brk.measure_nr) for brk in self.linebreaks]

        kbd = KeyboardView(scale=0.5)
        layout.addWidget(kbd.view, 0, 0, 1, 3)

        box_layout = QHBoxLayout()
        grp_measures = QGroupBox('Measures')
        grp_measures.setLayout(QGridLayout())
        grp_measures.setMaximumWidth(80)
        box_layout.addWidget(grp_measures)

        list_measures = QListWidget()
        # metr = QFontMetrics(list_measures.font())
        # rect_m = metr.boundingRect('M', Qt.AlignCenter)
        # width = rect_m.width()
        # descent = metr.descent()
        #
        # offset = 1
        # height = rect_m.height() + descent + offset
        # the following parameters depend on the font, QFontMetrics does not help
        width = 9
        height = 21
        count_lines = 7
        count_characters = 8
        list_measures.setMaximumWidth(count_characters * width)
        list_measures.setMinimumHeight(count_lines * height)
        list_measures.setMaximumHeight(count_lines * height)
        grp_measures.layout().addWidget(list_measures, 0, 0, 4, 1)
        list_measures.addItems(measures)

        self.control = StaffSizerControl(
            layout=box_layout,
            row=1,
            column=1,
            parent=self,
            keyboard=kbd)

        layout.addLayout(box_layout, 1, 0, 1, 1)
        ok_cancel = QGroupBox()
        layout.addWidget(ok_cancel, 6, 0, 1, 2)

        ok_cancel.setLayout(QGridLayout())
        ok_button = QPushButton(parent=parent)
        ok_button.setText('OK')
        ok_button.clicked.connect(self._on_ok)
        ok_cancel.layout().addWidget(ok_button, 0, 0, 1, 1)

        filler_label = QLabel()
        ok_cancel.layout().addWidget(filler_label, 0, 1, 1, 1)

        cancel_button = QPushButton(parent=parent)
        cancel_button.setText('Cancel')
        cancel_button.clicked.connect(self._on_cancel)
        ok_cancel.layout().addWidget(cancel_button, 0, 3, 1, 1)

        self.setLayout(layout)
        self.staff_sizers = self.linebreaks[0].staffs


    @property
    def staff_sizers(self) -> List[StaffSizer]:  # noqa
        """ get the values """

        return self.control.staff_sizers

    @staff_sizers.setter
    def staff_sizers(self, value: List[StaffSizer]):  # noqa
        """ set the value """

        self.control.staff_sizers = value  # noqa

    def _on_ok(self):
        """ OK clicked """

        self.result = DialogResult.OK
        self.close()

    def _on_cancel(self):
        """ cancel clicked """

        self.result = DialogResult.CANCEL
        self.close()


    # pylint: disable=invalid-name
    def closeEvent(self, event):
        """ the close window control 'x' is clicked"""

        event.accept()

        if self.result == DialogResult.OK and \
                self.callback is not None:

            data = LineBreakIo.exporter(self.linebreaks)
            self.callback(self.result, data)

    # pylint: enable=invalid-name
