import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from imports.gui import Gui
from imports.style import stylesheet

class PianoScript:

    def __init__(self):
        
        # setup
        self.app = QApplication(sys.argv)
        self.root = QMainWindow()
        self.root.setStyleSheet(stylesheet)
        self.gui = Gui(self.root)
        self.gui.show()

        # io == all objects in the application in one organized dict
        self.io = {
            'app':self.app,
            'root':self.root,
            'gui':self.gui
        }
        
        # run
        sys.exit(self.app.exec())

if __name__ == '__main__':
    PianoScript()