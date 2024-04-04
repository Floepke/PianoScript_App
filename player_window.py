#! python3.12
# coding: utf-8`

""" Player window """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2024-2024 all rights reserved'  # noqa

from typing import Callable
from typing import Optional

from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout

from PySide6.QtGui import QIcon

from PySide6.QtCore import Qt

from tools import to_dhms


class PlayerWindow(QMainWindow):
    """ player window """

    def __init__(self, closing: Callable):
        """ initialize the window """

        super().__init__()
        self.closing = closing
        self.setGeometry(200, 200,  100, 50)
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.closeEvent = self.closeEvent
        self.setWindowTitle('MIDI')
        self.setWindowIcon(QIcon('player.png'))
        # Create a central widget and set layout
        central_widget = QWidget(parent=self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout
        self.layout = QVBoxLayout(central_widget)

        self.setLayout(self.layout)
        self.title_label = QLabel(parent=self)
        self.layout.addWidget(self.title_label)
        self.progress_label = QLabel(parent=self)
        self.layout.addWidget(self.progress_label)
        self.set_progress(0.0)
        self.show()

    def set_text(self, text: str):
        """ set the label text """

        self.title_label.setText(text)

    def set_progress(self, progress: Optional[float]):
        """ show the progress, when finished progress becomes None """

        dms = '' if progress is None else to_dhms(round(progress))
        self.progress_label.setText(dms)

    def closeEvent(self, event):  # noqa
        # Perform any cleanup or additional actions before closing the window

        if self.closing:
            self.closing()

        event.accept()
