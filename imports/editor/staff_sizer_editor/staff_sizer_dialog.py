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

from PySide6.QtGui import QPixmap

from PySide6.QtCore import Qt
# pylint: enable=no-name-in-module

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer
from imports.editor.staff_sizer_editor.staff_sizer_control import StaffSizerControl
from imports.editor.grideditor.dialog_result import DialogResult


class StaffSizerDialog(QDialog):
    """ the example with four line breaks """

    def __init__(self,
                 parent: Optional[Any] = None,
                 callback: Optional[Callable] = None):
        """ initialize the dialog """

        super().__init__(parent=parent)

        self.my_pixmap = QPixmap('./icons/GridEditor.png')
        self.setWindowIcon(self.my_pixmap)

        self.callback = callback
        self.result = DialogResult.CLOSE_WINDOW

        self.setWindowTitle('Staff Sizer')

        layout = QGridLayout()

        label_left = QLabel()
        label_left.setText('Margins')
        label_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label_left, 0, 0, 1, 1)

        label_right = QLabel()
        label_right.setText('Staff')
        label_right.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label_right, 0, 1, 1, 1)

        self.controls = [
            StaffSizerControl(layout=layout,
                              row=1,
                              parent=self,
                              has_label=True),

            StaffSizerControl(layout=layout,
                              row=2,
                              parent=self,
                              has_label=False),

            StaffSizerControl(layout=layout,
                              row=3,
                              parent=self,
                              has_label=False),

            StaffSizerControl(layout=layout,
                              row=4,
                              parent=self,
                              has_label=False),
        ]

        ok_cancel = QGroupBox()
        layout.addWidget(ok_cancel, 5, 0, 1, 2)

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

    @property
    def staff_sizers(self) -> List:
        """ get the values """

        return [
            self.controls[0].staff_sizer,
            self.controls[1].staff_sizer,
            self.controls[2].staff_sizer,
            self.controls[3].staff_sizer,
            ]

    @staff_sizers.setter
    def staff_sizers(self, value: [StaffSizer]):
        """ set the value """

        self.controls[0].staff_sizer = value[0]
        self.controls[1].staff_sizer = value[1]
        self.controls[2].staff_sizer = value[2]
        self.controls[3].staff_sizer = value[3]

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
        line_breaks = []
        if self.result == DialogResult.OK:
            line_breaks = [
                self.controls[0].staff_sizer,
                self.controls[1].staff_sizer,
                self.controls[2].staff_sizer,
                self.controls[3].staff_sizer,
            ]

        if self.callback is not None:
            self.callback(self.result, line_breaks)

    # pylint: enable=invalid-name
