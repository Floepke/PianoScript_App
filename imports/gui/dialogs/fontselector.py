from PySide6.QtWidgets import QVBoxLayout, QDialog, QSpinBox, QCheckBox, QFontComboBox, QPushButton
from PySide6.QtGui import Qt


class FontSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.font_combobox = QFontComboBox(self)
        self.font_combobox.currentFontChanged.connect(self.font_selected)

        self.font_size_spinbox = QSpinBox(self)
        self.font_size_spinbox.setRange(1, 100)  # Set the range of the spinbox
        self.font_size_spinbox.valueChanged.connect(self.font_size_changed)

        self.bold_checkbox = QCheckBox("Bold", self)
        self.bold_checkbox.stateChanged.connect(self.bold_changed)

        self.italic_checkbox = QCheckBox("Italic", self)
        self.italic_checkbox.stateChanged.connect(self.italic_changed)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        layout.addWidget(self.font_combobox)
        layout.addWidget(self.font_size_spinbox)
        layout.addWidget(self.bold_checkbox)
        layout.addWidget(self.italic_checkbox)
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def font_selected(self, font):
        # This method is called when the user selects a font from the combobox
        print(font.family())

    def font_size_changed(self, size):
        # This method is called when the user changes the font size
        print(size)

    def bold_changed(self, state):
        # This method is called when the user changes the bold checkbox
        print(state == Qt.Checked)

    def italic_changed(self, state):
        # This method is called when the user changes the italic checkbox
        print(state == Qt.Checked)
