from PySide6.QtWidgets import QDialog, QMainWindow, QVBoxLayout, QSpinBox, QPushButton, QLabel

class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dialog")
        self.resize(400, 300)
        
        # Create the main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # create label
        label = QLabel("Set the value:")
        layout.addWidget(label)


        # Create spinbox
        spinbox = QSpinBox()
        spinbox.setMinimum(0)
        spinbox.setMaximum(100)
        spinbox.setValue(50)
        layout.addWidget(spinbox)

        # create ok and cancel buttons
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        layout.addWidget(ok_button)
        layout.addWidget(cancel_button)

        # connect the buttons
        ok_button.clicked.connect(self.ok_)
        cancel_button.clicked.connect(self.cancel_)

    def ok_(self):

        print("ok")

    def cancel_(self):

        print("cancel")




if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    dialog = Dialog(mainWindow)
    dialog.show()
    sys.exit(app.exec())
