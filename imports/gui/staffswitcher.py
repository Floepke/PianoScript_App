from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout

class StaffSwitcher(QWidget):
    """ staff switcher widget for the Toolbar """
    def __init__(self, io, parent=None):
        super().__init__(parent)

        self.io = io
        self.io['selected_staff'] = 0

        self.buttons = []
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        for i in range(4):
            button = QPushButton(str(i + 1), self)
            button.setCheckable(True)
            button.clicked.connect(self.make_button_callback(i))
            self.layout.addWidget(button)
            self.buttons.append(button)

        self.buttons[0].setChecked(True)
        self.update_button_colors()

        self.setToolTip("Selected staff...")

    def make_button_callback(self, i):
        return lambda: self.select_staff(i)

    def select_staff(self, i):
        self.io['selected_staff'] = i
        for button in self.buttons:
            button.setChecked(False)
        self.buttons[i].setChecked(True)
        self.update_button_colors()

        # redraw editor
        self.io['maineditor'].redraw_editor()

    def update_button_colors(self):
        for i, button in enumerate(self.buttons):
            if button.isChecked():
                button.setStyleSheet("background-color: blue; color: white")
            else:
                button.setStyleSheet("background-color: white; color: black")