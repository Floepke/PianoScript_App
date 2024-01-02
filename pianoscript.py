# 
from imports.utils.constants import *

# pyside6 imports
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

class PianoScript():

    def __init__(self):

        # io == all objects in the application in one dict
        self.io = {
            # save file json structure loaded here
            'score':{},
            
            # new_tag; counter to keep track of new tags for notation elements
            'new_tag':0,
            
            # everything about the selection:
            'selection':{
                # True if there is a selection rectangle drawn on the editor
                'rectangle_on':False,
                # True if there is a active selection
                'active':False,
                # coords for the selection rectangle
                'x1':None,
                'y1':None,
                'x2':None,
                'y2':None,
                # the buffer that holds any selected element; it's a dictionary that holds the structure of the 'events' folder in a score file
                'selection_buffer':{
                    'note':[],
                    'ornament':[],
                    'text':[],
                    'beam':[],
                    'slur':[],
                    'pedal':[],
                    'countline':[],
                    'staffsizer':[],
                    'startrepeat':[],
                    'endrepeat':[],
                    'starthook':[],
                    'endhook':[],
                    'countline':[]
                },
                # the buffer that holds any copied or cutted selection; same structure as above
                'copycut_buffer':{
                    'note':[],
                    'ornament':[],
                    'text':[],
                    'beam':[],
                    'slur':[],
                    'pedal':[],
                    'countline':[],
                    'staffsizer':[],
                    'startrepeat':[],
                    'endrepeat':[],
                    'starthook':[],
                    'endhook':[]
                },
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
                'button1':False, # True if the button is clicked, False if not pressed
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

            # current selected grid
            'snap_grid':128,

            # current selected tool (note, ornament, beam, countline, slur, text, pedal, ...)
            'tool':'note',

            # current selected hand (l, r)
            'hand':'l',

            # viewport
            'viewport':{
                'toptick':0,
                'bottomtick':0
            },

            # total ticks
            'total_ticks':0,

            # drawn_objects
            'drawn_obj':[],
        }

        # setup
        self.app = QApplication(sys.argv)
        self.root = QMainWindow()
        self.gui = Gui(self.root, self.io)
        self.gui.show()
        self.io['gui'] = self.gui
        self.io['editor'] = DrawUtil(self.gui.editor_scene)
        self.io['view'] = DrawUtil(self.gui.print_scene)
        self.io['fileoperations'] = FileOperations(self.io)
        self.io['calc'] = CalcTools(self.io)
        self.io['maineditor'] = Editor(self.io)

        # connect the file operations to the gui menu
        self.gui.new_action.triggered.connect(self.io['fileoperations'].new)
        self.gui.load_action.triggered.connect(self.io['fileoperations'].load)
        self.gui.save_action.triggered.connect(self.io['fileoperations'].save)
        self.gui.saveas_action.triggered.connect(self.io['fileoperations'].saveas)
        self.gui.exit_action.triggered.connect(self.root.close)

        # create initial new file
        self.io['fileoperations'].new()

        # set stylesheet
        self.root.setStyleSheet("""
        background-color: #1d5242;
        color: #eeeeee;
        font-family: Courier;
        font-size: 16px;
        selection-background-color: #666666;
        selection-color: #eeeeee;
        """)

        # run the application
        sys.exit(self.app.exec())

if __name__ == '__main__':
    PianoScript()