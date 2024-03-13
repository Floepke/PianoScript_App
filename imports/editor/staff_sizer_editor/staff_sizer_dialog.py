#! python3.11
# coding: utf8

""" editor for the line breaks """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

# Ik denk een dialoogje wanneer je op de linebreak marker klikt met de linker
# muisknop waar de volgende eigenschapen in te stellen zijn:
# margin left(staff1-4),
# marginright(staff1-4),
# staff range toets x tot y(staff1-4)

from typing import Optional
from typing import Any
from typing import List
from typing import Callable

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QListWidget
from PySide6.QtWidgets import QHBoxLayout

# from PySide6.QtGui import QPixmap
from PySide6.QtCore import QModelIndex
# pylint: enable=no-name-in-module

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer
from imports.editor.staff_sizer_editor.staff_sizer_control import StaffSizerControl
from imports.editor.grideditor.dialog_result import DialogResult

from imports.editor.staff_sizer_editor.keyboard_view import KeyboardView
from imports.editor.staff_sizer_editor.staff_io import LineBreakIo
from imports.icons.icons import get_pixmap

class StaffSizerDialog(QDialog):
    """ the example with four line breaks """

    # the following parameters depend on the font, QFontMetrics does not help

    # metr = QFontMetrics(list_measures.font())
    # rect_m = metr.boundingRect('M', Qt.AlignCenter)
    # width = rect_m.width()
    # descent = metr.descent()
    #
    # offset = 2
    # height = rect_m.height() + descent + offset

    _char_width = 9
    _line_spacing = 21  # char_height + descent + 2 for the used font
    _count_lines = 7
    _count_characters = 8
    _list_width = _char_width * _count_characters
    _list_height = _line_spacing * _count_lines

    def __init__(self,
                 parent: Optional[Any] = None,
                 callback: Optional[Callable] = None,
                 linebreaks: list = None,
                 time_calc: Callable = None):
        """ initialize the dialog """

        super().__init__(parent=parent)

        self.setWindowIcon(get_pixmap('grideditor.png'))

        self.callback = callback
        self.result = DialogResult.CLOSE_WINDOW

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
        list_measures.setMaximumWidth(StaffSizerDialog._list_width)
        list_measures.setMinimumHeight(StaffSizerDialog._list_height)
        list_measures.setMaximumHeight(StaffSizerDialog._list_height)
        list_measures.clicked.connect(self.changed_list_index)
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

        self.staff_index = 0
        self.select_linebreak(0)

    def changed_list_index(self, index: QModelIndex):
        """ list index changed """

        self.select_linebreak(index.row())

    def select_linebreak(self, row: int):

        self.staff_index = row
        linebreak = self.linebreaks[row]
        self.staff_sizers = linebreak.staffs

        measure = linebreak.measure_nr
        self.control.set_measure_nr(measure)

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
