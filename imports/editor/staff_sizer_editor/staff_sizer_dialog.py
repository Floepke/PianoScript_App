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

        self.control = StaffSizerControl(
            layout=layout,
            row=0,
            parent=self)

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
        staff_sizers = []
        if self.result == DialogResult.OK:
            staff_sizers = self.staff_sizers

        if self.callback is not None:
            self.callback(self.result, staff_sizers)

    # pylint: enable=invalid-name
