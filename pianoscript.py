import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from imports.gui.gui import Gui
from imports.style import stylesheet
from PySide6.QtGui import QKeyEvent, Qt
from imports.utils.drawutil import DrawUtil
from imports.savefile import Score
from imports.editor.editor import Editor
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
            # save file object
            'score':{}
        }
        
        # add the score object to the io dict and load a new score from the template
        self.io['score'] = Score(self.io)
        self.io['score'].new()
        
        # add the editor object to the io dict
        self.io['editor'] = Editor(self.io)

        # run the application
        sys.exit(self.app.exec())

if __name__ == '__main__':
    PianoScript()