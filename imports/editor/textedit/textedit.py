from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox,
    QVBoxLayout, QWidget, QFontComboBox, QComboBox,
    QLineEdit
)
import sys
from PySide6.QtGui import QFont


from PySide6.QtWidgets import (
    QLabel, QHBoxLayout
)

class TextEdit(QDialog):
    def __init__(self, parent=None, json_font=None):
        super().__init__(parent)
        self.setWindowTitle("Text Edit")

        # Main layout for the dialog
        layout = QVBoxLayout(self)

        # Custom widgets area
        self.custom_area = QWidget(self)
        custom_layout = QVBoxLayout(self.custom_area)

        # Text input area with label
        text_row = QHBoxLayout()
        text_label = QLabel("Text:", self)
        text_label.setMinimumWidth(90)
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Enter your text here...")
        text_row.addWidget(text_label)
        text_row.addWidget(self.text_input)
        custom_layout.addLayout(text_row)

        # Font family selection with label
        font_row = QHBoxLayout()
        font_label = QLabel("Font:", self)
        font_label.setMinimumWidth(90)
        self.font_combo = QFontComboBox(self)
        self.font_combo.setEditable(False)
        self.font_combo.setCurrentFont(QFont("Edwin"))
        font_row.addWidget(font_label)
        font_row.addWidget(self.font_combo)
        custom_layout.addLayout(font_row)

        # Font size selection with label
        size_row = QHBoxLayout()
        size_label = QLabel("Size:", self)
        size_label.setMinimumWidth(90)
        self.size_combo = QComboBox(self)
        self.size_combo.addItems([str(i) for i in range(6, 73, 2)])
        self.size_combo.setCurrentText("12")
        size_row.addWidget(size_label)
        size_row.addWidget(self.size_combo)
        custom_layout.addLayout(size_row)

        # Font angle selection with label
        angle_row = QHBoxLayout()
        angle_label = QLabel("Angle:", self)
        angle_label.setMinimumWidth(90)
        self.angle_combo = QComboBox(self)
        self.angle_combo.addItems([
            "Horizontal",
            "Diagonal Left",
            "Vertical Left",
            "Diagonal Right",
            "Vertical Right"
        ])
        angle_row.addWidget(angle_label)
        angle_row.addWidget(self.angle_combo)
        custom_layout.addLayout(angle_row)

        self.custom_area.setLayout(custom_layout)
        layout.addWidget(self.custom_area)

        # OK / Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self.ok)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
    
    def ok(self):
        """Handles the OK button click event."""
        
        # evaluate the text input
        text = self.text_input.text()
        if not text.strip(): # check if text is empty or only whitespace
            self.text_input.setFocus()
            return
        
        # Get the selected font family, size, and angle
        font_family = self.font_combo.currentFont().family()
        font_size = int(self.size_combo.currentText())
        angle = self.angle_combo.currentText()

        # Convert angle to degrees
        if angle == "Horizontal":
            angle_value = 0.0
        elif angle == "Diagonal Left":
            angle_value = -45.0
        elif angle == "Vertical Left":
            angle_value = -90.0
        elif angle == "Diagonal Right":
            angle_value = 45.0
        elif angle == "Vertical Right":
            angle_value = 90.0

        self.accept()
        return {
            'text': text,
            'font_family': font_family,
            'font_size': font_size,
            'angle': angle_value
        }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TextEdit()
    if dialog.exec():
        print("Accepted")
    else:
        print("Canceled")
