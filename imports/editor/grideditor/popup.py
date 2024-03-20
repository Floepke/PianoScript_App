#! python3.11
# coding: utf8

""" Popup window implemented for PySide6 """

__copyright__ = '© Sihir 2024-2024 all rights reserved'

from os.path import abspath

from typing import Callable

from threading import Timer

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt
# pylint: enable=no-name-in-module

from imports.editor.grideditor.dialog_result import DialogResult
from imports.editor.grideditor.string_builder import StringBuilder


class Popup(QDialog):
    """ popup window """

    def __init__(self,
                 message: str,
                 text_size: tuple = (400, 240),
                 max_lines: int = 16,
                 result_callback: Callable = None,
                 timeout: int = None):
        """ initialize the class """

        super().__init__(parent=None)

        self.result = DialogResult.CLOSE_WINDOW
        self.size = text_size
        self.callback = result_callback
        self.max_lines = max_lines

        popup_ico = abspath('./imports/icons/PopUp.png')
        dialog_icon = QIcon(popup_ico)
        self.setWindowIcon(dialog_icon)
        self.setWindowTitle('Notification')

        popup_layout = QGridLayout()

        lbl_message = QLabel(parent=self)
        lbl_message.setMinimumSize(*text_size)
        lbl_message.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        popup_layout.addWidget(lbl_message, 0, 0, 1, 3)

        self.lbl_message = lbl_message

        ok_button = QPushButton('OK')
        # when this is True, entering a new line position
        ok_button.setDefault(True)
        ok_button.clicked.connect(self._ok_click)
        ok_button.setMinimumSize(60, 24)
        ok_button.setMaximumSize(60, 24)
        popup_layout.addWidget(ok_button, 1, 0)

        cancel_button = QPushButton('Cancel')
        cancel_button.setDefault(True)
        cancel_button.clicked.connect(self._cancel_click)
        cancel_button.setMinimumSize(60, 24)
        cancel_button.setMaximumSize(60, 24)
        popup_layout.addWidget(cancel_button, 1, 2)

        # pylint: disable=invalid-name
        self.closeEvent = self.dialog_closes
        # pylint: enable=invalid-name
        self.setLayout(popup_layout)
        self.append(message)

        if timeout is not None:
            self.timer = Timer(interval=timout, function=self.close)

        self.show()

    def _ok_click(self):
        """ OK button """

        self.result = DialogResult.OK
        self.close()

    def _cancel_click(self):
        """ Cancel button """

        self.result = DialogResult.CANCEL
        self.close()

    def dialog_closes(self, event):
        """ this dialog closes """

        if self.callback:
            self.callback(self.result)

        event.accept()

    @property
    def text(self):
        """ get the text """

        return self.lbl_message.text()

    def append(self, text: str):
        """ set the text """

        if text.startswith('[CLEAR]'):
            self.lbl_message.clear()
            return

        builder = StringBuilder()
        popup_list = self.text.split('\n') + text.split('\n')
        for line in popup_list[-self.max_lines:]:
            if line:
                builder.append_line(line)

        self.lbl_message.setText(builder.to_string())
