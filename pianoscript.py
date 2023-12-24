from PySide6.QtGui import QKeyEvent
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from imports.gui.gui import Gui
from imports.gui.style import stylesheet
from PySide6.QtGui import Qt
from imports.utils.drawutil import DrawUtil
from imports.utils.calctools import CalcTools
from imports.utils.fileoprations import FileOperations
from imports.editor.editor import Editor
from imports.utils.HARDCODE import EDITOR_MARGIN, QUARTER_PIANOTICK, EDITOR_X_UNIT
from imports.utils.HARDCODE import LEFT, RIGHT, TOP, WIDTH

class PianoScript():

    def __init__(self):
        
        # setup
        self.app = QApplication(sys.argv)
        self.root = QMainWindow()
        self.gui = Gui(self.root)
        self.gui.show()

        # io == all objects in the application in one dict
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
            'QUARTER_PIANOTICK':QUARTER_PIANOTICK,
            # constants for editor: margin; left, right and top positions; width; x unit
            'EDITOR_MARGIN':EDITOR_MARGIN,
            'LEFT':LEFT,
            'RIGHT':RIGHT,
            'TOP':TOP,
            'WIDTH':WIDTH,
            'EDITOR_X_UNIT':EDITOR_X_UNIT
        }
        
        # add the score object to the io dict and load a new score from the template
        self.io['fileoperations'] = FileOperations(self.io)

        # draw test line if I hit escape
        self.gui.editor_view.keyPressEvent = self.keyPressEvent
        
        # add the calctools object to the io dict
        self.io['calctools'] = CalcTools(self.io)

        # add the editor object to the io dict
        self.io['maineditor'] = Editor(self.io)

        # connect the file operations to the gui menu
        self.gui.new_action.triggered.connect(self.io['fileoperations'].new)
        self.gui.load_action.triggered.connect(self.io['fileoperations'].load)
        self.gui.save_action.triggered.connect(self.io['fileoperations'].save)
        self.gui.saveas_action.triggered.connect(self.io['fileoperations'].saveas)
        self.gui.exit_action.triggered.connect(self.root.close)

        # run the application
        self.io['fileoperations'].new()
        sys.exit(self.app.exec())

    # handle all keypresses here
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.root.close()

if __name__ == '__main__':
    PianoScript()