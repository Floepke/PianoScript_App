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
from imports.editor.mouse import Mouse
from imports.utils.constant import *

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
            
            # new_tag; counter to keep track of new tags for notation elements
            'new_tag':0,
            
            # everything about the selection:
            'selection':{
                'rectangle_on':False,
                # True if there is a active selection
                'active':False,
                # coords for the selection rectangle
                'x1':None,
                'y1':None,
                'x2':None,
                'y2':None,
                # the buffer that holds any selected element; it's a dictionary that holds the structure of the 'events' folder in a score file
                'selection_buffer':{},
                # the buffer that holds any copied or cutted selection; same structure as above
                'copycut_buffer':{},
                # all event types that are alowed to copy, cut, paste
                'copy_types':['note', 'ornament', 'beam', 'countline', 'slur', 'text', 'pedal'],
                # all event types that are alowed to transpose
                'transpose_types':['note', 'text', 'ornament',],
                # all event types that are alowed to move forward or backward in time
                'move_types':['note', 'ornament', 'beam', 'countline', 'slur', 'text', 'pedal']
            },
            
            # all info for the mouse:
            'mouse':{
                'x':0, # x position of the mouse in the editor view
                'y':0, # y position of the mouse in the editor view
                'pitch':0, # event x note position of the mouse in the editor view
                'time':0, # event y pianotick position of the mouse in the editor view
                'button1':False, # True if the button is clicked and hold, False if not pressed
                'button2':False, # ...
                'button3':False, # ...
                # keep track wether an object on the editor is clicked; this variable is the
                # unique id from a clicked object on the editor canvas if an object is clicked+hold
                'hold_tag':''
            },

            # keep track of keys pressed
            'keyboard':{
                'shift':False,
                'ctl':False,
                'alt':False
            },

            # keep track of the current tool
            'tool':None,

            # current selected grid
            'snap_grid':128
        }
        
        # add the score object to the io dict and load a new score from the template
        self.io['fileoperations'] = FileOperations(self.io)
        
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

        # connect the editor mouse events to callback functions
        self.io['mouse_editor'] = Mouse(self.io, self.gui.editor_view)

        # run the application
        self.io['fileoperations'].new()
        sys.exit(self.app.exec())

if __name__ == '__main__':
    PianoScript()