from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from imports.icons.icons import get_icon
from imports.gui.staffswitcher import StaffSwitcher


class ToolBar(QWidget):
    ''' toolbar widget for the main window '''

    def __init__(self, io, parent=None):
        super().__init__(parent)

        self.io = io

        # previous page button
        self.previous_button = QPushButton('', self)
        self.previous_button.setIcon(get_icon('previous.png'))
        self.previous_button.setToolTip("Previous Page")
        self.previous_button.setIconSize(QSize(30, 30))
        self.previous_button.clicked.connect(self._previous_page)

        # next page button
        self.next_button = QPushButton('', self)
        self.next_button.setIcon(get_icon('next.png'))
        self.next_button.setToolTip("Next Page")
        self.next_button.setIconSize(QSize(30, 30))
        self.next_button.clicked.connect(self._next_page)

        # refresh button
        self.refresh_button = QPushButton('', self)
        self.refresh_button.setIcon(get_icon('engrave.png'))
        self.refresh_button.setToolTip("Engrave The Document [E]")
        self.refresh_button.setIconSize(QSize(30, 30))
        self.refresh_button.clicked.connect(self._refresh)

        self.separator1 = QWidget()
        self.separator1.setFixedHeight(1)
        self.separator1.setStyleSheet("background-color: #000000;")

        # play button
        self.play_button = QPushButton('', self)
        self.play_button.setIcon(get_icon('play.png'))
        self.play_button.setToolTip("Play MIDI")
        self.play_button.setIconSize(QSize(30, 30))

        # stop button
        self.stop_button = QPushButton('', self)
        self.stop_button.setIcon(get_icon('stop.png'))
        self.stop_button.setToolTip("Stop MIDI")
        self.stop_button.setIconSize(QSize(30, 30))
        
        self.separator2 = QWidget()
        self.separator2.setFixedHeight(1)
        self.separator2.setStyleSheet("background-color: #000000;")

        # selection to left button
        self.note2left_button = QPushButton('', self)
        self.note2left_button.setIcon(get_icon('note2left.png'))
        self.note2left_button.setToolTip("Selection to Left Hand")
        self.note2left_button.setIconSize(QSize(30, 30))
        self.note2left_button.clicked.connect(self.selection2left)

        # selection to right button
        self.note2right_button = QPushButton('', self)
        self.note2right_button.setIcon(get_icon('note2right.png'))
        self.note2right_button.setToolTip("Selection to Right Hand")
        self.note2right_button.setIconSize(QSize(30, 30))
        self.note2right_button.clicked.connect(self.selection2right)

        self.separator3 = QWidget()
        self.separator3.setFixedHeight(1)
        self.separator3.setStyleSheet("background-color: #000000;")
        
        # staff switcher widget
        self.staff_switcher = StaffSwitcher(self.io)

        self.separator4 = QWidget()
        self.separator4.setFixedHeight(1)
        self.separator4.setStyleSheet("background-color: #000000;")

        # left note input button
        self.left_note_input_button = QPushButton('', self)
        self.left_note_input_button.setIcon(get_icon('noteLeft.png'))
        self.left_note_input_button.setToolTip("Left Hand Note Input")
        self.left_note_input_button.setIconSize(QSize(30, 30))
        self.left_note_input_button.clicked.connect(self.noteleft)

        # right note input button
        self.right_note_input_button = QPushButton('', self)
        self.right_note_input_button.setIcon(get_icon('noteRight.png'))
        self.right_note_input_button.setToolTip("Right Hand Note Input")
        self.right_note_input_button.setIconSize(QSize(30, 30))
        self.right_note_input_button.clicked.connect(self.note2right)

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
        self.layout.addWidget(self.separator4)
        self.layout.addWidget(self.left_note_input_button)
        self.layout.addWidget(self.right_note_input_button)
        self.setLayout(self.layout)

    def _previous_page(self):
        '''goes to the previous page'''
        self.io['selected_page'] -= 1
        self.io['maineditor'].update('page_change')

    def _next_page(self):
        '''goes to the next page'''
        self.io['selected_page'] += 1
        self.io['maineditor'].update('page_change')

    def _refresh(self):
        '''refreshes the current page'''
        self.io['maineditor'].update('page_change')

    def selection2left(self):
        '''Moves the selected events to the left hand'''
        self.io['selectoperations'].hand_left()
        self.io['maineditor'].update('keyedit')

    def selection2right(self):
        '''Moves the selected events to the right hand'''
        self.io['selectoperations'].hand_right()
        self.io['maineditor'].update('keyedit')

    def noteleft(self):
        '''Sets the note input to the left hand in note edit mode'''
        self.io['hand'] = 'l'
        self.io['maineditor'].update('keyedit')

    def note2right(self):
        '''Sets the note input to the right hand in note edit mode'''
        self.io['hand'] = 'r'
        self.io['maineditor'].update('keyedit')
