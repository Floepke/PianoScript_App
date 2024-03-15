from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMenu
from PySide6.QtGui import QAction


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
                button.setStyleSheet('font-style: italic;')
            else:
                try:
                    style = "text-decoration: underline" if self.io['score']['properties']['staffs'][i]['onoff'] else ""
                except:
                    style = ""
                button.setStyleSheet(style)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        for i in range(4):
            action = QAction(f"Staff {i+1} on/off", self)
            action.setCheckable(True)
            action.setChecked(
                self.io['score']['properties']['staffs'][i]['onoff'])
            action.triggered.connect(self.make_menu_callback(i))
            context_menu.addAction(action)

        context_menu.exec_(event.globalPos())

    def make_menu_callback(self, i):
        return lambda checked: self.toggle_staff(i, checked)

    def toggle_staff(self, i, checked):
        if not i:
            return
        self.io['score']['properties']['staffs'][i]['onoff'] = checked
        self.update_button_colors()
        self.io['maineditor'].update('score_options')
