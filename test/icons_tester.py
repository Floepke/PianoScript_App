"""  show all icons """

from sys import exit as _exit

from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import QSize

from imports.icons.icons_data import image_dict

from imports.icons.icons import get_icon
from imports.icons.icons import get_pixmap


class SimpleTester:

    def __init__(self):
        app = QApplication()
        root = QMainWindow()
        root.setWindowTitle('ShowIcons')

        icon = get_icon('PopUp.png')
        root.setWindowIcon(icon)
        root.setGeometry(100, 100, 240, 200)

        layout = QGridLayout()
        button = QPushButton('Next',
                             parent=root,
                             icon=get_icon('pianoscript.png'))
        button.setFixedWidth(120)
        button.setIconSize(QSize(200, 200))
        button.setFixedSize(QSize(240, 200))
        button.clicked.connect(self.button_click)
        layout.addWidget(button, 0, 0, 1, 1)
        root.setLayout(layout)
        root.show()

        self.button = button
        self.keys = [key for key in image_dict.keys()]
        self.idx = 0
        self.mod = len(self.keys)
        app.exec()

    def next(self):
        """ get the next key"""

        self.idx = (self.idx + 1) % self.mod
        return self.keys[self.idx]

    def button_click(self):
        """ show the next icon """

        self.button.setIcon(get_icon(self.next()))


if __name__ == '__main__':
    _ = SimpleTester()
    _exit(0)
