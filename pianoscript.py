import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from imports.gui import Gui
from imports.style import stylesheet
from PySide6.QtGui import QKeyEvent, Qt

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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_F11:
            if self.root.isFullScreen():
                self.root.showNormal()
            else:
                self.root.showFullScreen()

if __name__ == '__main__':
    PianoScript()