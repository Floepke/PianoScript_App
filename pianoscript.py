import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from imports.gui import Gui
from imports.style import stylesheet
from PySide6.QtGui import QKeyEvent, Qt
from imports.utils.drawutil import DrawUtil
from imports.editor.score import Score
import time

class PianoScript:

    def __init__(self):
        
        # setup
        self.app = QApplication(sys.argv)
        self.root = QMainWindow()
        self.gui = Gui(self.root)
        self.gui.show()

        # io == all objects in the application in one organized dict
        self.io = {
            # the gui class
            'gui':self.gui,
            # the editor drawutil class
            'editor':DrawUtil(self.gui.editor_scene),
            # the printview drawutil class
            'view':DrawUtil(self.gui.print_scene),
            # score object
            'score':{}
        }
        self.io['score'] = Score(self.io)
        self.io['score'].new()
        print(self.io['score'])

        # run the application
        sys.exit(self.app.exec())

if __name__ == '__main__':
    PianoScript()