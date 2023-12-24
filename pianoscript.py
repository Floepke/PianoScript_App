from PySide6.QtGui import QKeyEvent
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from imports.gui.gui import Gui
from imports.style import stylesheet
from PySide6.QtGui import Qt
from imports.utils.drawutil import DrawUtil
from imports.utils.calctools import CalcTools
from imports.savefile import Score
from imports.editor.editor import Editor
import time
from imports.utils.HARDCODE import QUARTER_PIANOTICK

class PianoScript():

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
            'score':{},
            # constant quarter piano tick
            'QUARTER_PIANOTICK':QUARTER_PIANOTICK
        }
        
        # add the score object to the io dict and load a new score from the template
        self.io['score'] = Score(self.io)
        self.io['score'].new()

        # draw test line if I hit escape
        self.gui.editor_view.keyPressEvent = self.keyPressEvent
        
        # add the calctools object to the io dict
        self.io['calctools'] = CalcTools(self.io)

        # add the editor object to the io dict
        self.io['maineditor'] = Editor(self.io)

        # run the application
        sys.exit(self.app.exec())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.io['editor'].new_line(0,0,100,100)
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    PianoScript()