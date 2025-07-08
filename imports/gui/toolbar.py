from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from imports.icons.icons import get_icon
from imports.gui.staffswitcher import StaffSwitcher

class ToolBar(QWidget):
    ''' toolbar widget for the main window '''

    def __init__(self, io, parent=None):
        super().__init__(parent)

        self.io = io

        # Create and set the widgets
        self.previous_button = QPushButton('', self)
        self.previous_button.setIcon(get_icon('previous.png'))
        self.previous_button.setToolTip("Previous page")
        self.previous_button.setIconSize(QSize(30, 30))
        self.previous_button.clicked.connect(self._previous_page)

        self.next_button = QPushButton('', self)
        self.next_button.setIcon(get_icon('next.png'))
        self.next_button.setToolTip("Next page")
        self.next_button.setIconSize(QSize(30, 30))
        self.next_button.clicked.connect(self._next_page)

        self.refresh_button = QPushButton('', self)
        self.refresh_button.setIcon(get_icon('engrave.png'))
        self.refresh_button.setStyleSheet("color: #ffdddd; font-size: 35px;")
        self.refresh_button.setToolTip("Engrave the document [E]")
        self.refresh_button.setIconSize(QSize(30, 30))
        self.refresh_button.clicked.connect(self._refresh)

        self.separator1 = QWidget()
        self.separator1.setFixedHeight(1)
        self.separator1.setStyleSheet("background-color: #000000;")
        
        self.play_button = QPushButton('', self)
        self.play_button.setIcon(get_icon('play.png'))
        self.play_button.setToolTip("Play MIDI")
        self.play_button.setIconSize(QSize(30, 30))

        self.stop_button = QPushButton('', self)
        self.stop_button.setIcon(get_icon('stop.png'))
        self.stop_button.setToolTip("Stop MIDI")
        self.stop_button.setIconSize(QSize(30, 30))

        self.separator2 = QWidget()
        self.separator2.setFixedHeight(1)
        self.separator2.setStyleSheet("background-color: #000000;")

        self.note2left_button = QPushButton('', self)
        self.note2left_button.setIcon(get_icon('note2left.png'))
        self.note2left_button.setToolTip("Left hand")
        self.note2left_button.setIconSize(QSize(30, 30))
        self.note2left_button.clicked.connect(lambda: self.io['maineditor'].update('handleft'))

        self.note2right_button = QPushButton('', self)
        self.note2right_button.setIcon(get_icon('note2right.png'))
        self.note2right_button.setToolTip("Right hand")
        self.note2right_button.setIconSize(QSize(30, 30))
        self.note2right_button.clicked.connect(lambda: self.io['maineditor'].update('handright'))

        self.separator3 = QWidget()
        self.separator3.setFixedHeight(1)
        self.separator3.setStyleSheet("background-color: #000000;")
        
        self.staff_switcher = StaffSwitcher(self.io)

        # Set the layout and add the widgets in order
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.previous_button)
        self.layout.addWidget(self.next_button)
        self.layout.addWidget(self.refresh_button)
        self.layout.addWidget(self.separator1)
        self.layout.addWidget(self.staff_switcher)
        self.layout.addWidget(self.separator2)
        self.layout.addWidget(self.play_button)
        self.layout.addWidget(self.stop_button)
        self.layout.addWidget(self.separator3)
        self.layout.addWidget(self.note2left_button)
        self.layout.addWidget(self.note2right_button)
        self.setLayout(self.layout)

    def _previous_page(self):
        self.io['selected_page'] -= 1
        self.io['maineditor'].update('page_change')

    def _next_page(self):
        self.io['selected_page'] += 1
        self.io['maineditor'].update('page_change')

    def _refresh(self):
        self.io['maineditor'].update('page_change')

