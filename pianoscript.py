#
from imports.utils.constants import *

# pyside6 imports
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QSlider, QWidget, QDockWidget, QTabWidget, QMenuBar, QMenu, QRadioButton, QSplitter, QDialog, QTreeView, QGraphicsView, QToolBar
from imports.gui.gui import Gui, Qt, QColor
from imports.utils.drawutil import DrawUtil
from imports.utils.calctools import CalcTools
from imports.utils.fileoprations import FileOperations
from imports.editor.editor import Editor
from imports.editor.zoom import Zoom
from imports.utils.savefilestructure import SaveFileStructureSource
from imports.editor.selectoperations import SelectOperations
from PySide6.QtGui import QShortcut, QKeySequence
from imports.editor.ctlz import CtlZ
from imports.utils.midi import Midi
from imports.engraver.engraver import Engraver
from imports.gui.disco import ColorSliderWindow, ColorTransitionThread
import math

from imports.editor.grideditor.dialog_result import DialogResult
from imports.editor.grideditor.grid_editor_dialog import GridDialog
from imports.editor.grideditor.popup import Popup
from imports.gui.style import STYLE, color1, color2

from imports.editor.staff_sizer_editor.staff_io import StaffIo
from imports.editor.staff_sizer_editor.staff_sizer_dialog import StaffSizerDialog

class PianoScript():

    def __init__(self):

        self.color1 = color1
        self.color2 = color2

        # io == all objects in the application in one dict
        self.io = {
            # save file json structure loaded here
            'score': {},

            # new_tag; counter to keep track of new tags for notation elements
            'new_tag': 0,

            # everything about the selection:
            'selection': {
                # True if there is a selection rectangle drawn on the editor
                'rectangle_on': False,
                # True if there is a active selection
                'active': False,
                'inrectangle': [],
                # coords for the selection rectangle
                'x1': 0,
                'y1': 0,
                'x2': 0,
                'y2': 0,
                # the buffer that holds any selected element; it's a dictionary that holds the structure of the 'events' folder in a score file
                'selection_buffer': SaveFileStructureSource.new_events_folder(),
                # the buffer that holds any copied or cutted selection; same structure as above
                'copycut_buffer': SaveFileStructureSource.new_events_folder(),
                # all event types that are alowed to copy, cut, paste
                'copy_types': ['note', 'gracenote', 'beam', 'countline', 'slur', 'text', 'pedal'],
                # all event types that are alowed to transpose (are pitch based)
                'transpose_types': ['note', 'text', 'gracenote', 'slur'],
                # all event types that have the time property (are time based)
                'move_types': ['note', 'gracenote', 'beam', 'countline', 'slur', 'text', 'pedal'],
                # all event types that have the hand property
                'hand_types': ['note', 'gracenote', 'beam']
            },

            # all info for the mouse:
            'mouse': {
                'x': 0,  # x position of the mouse in the editor view
                'y': 0,  # y position of the mouse in the editor view
                'pitch': 0,  # event x note position of the mouse in the editor view
                'time': 0,  # event y pianotick position of the mouse in the editor view
                'button1': False,  # True if the button is clicked, False if not pressed
                'button2': False,  # ...
                'button3': False,  # ...
                # keep track wether an object on the editor is clicked; this variable is the
                # unique id from a clicked object on the editor canvas if an object is clicked+hold
                'hold_tag': ''
            },

            # keep track of keys pressed
            'keyboard': {
                'shift': False,
                'ctl': False,
                'alt': False
            },

            # current selected grid
            'snap_grid': 128,

            # current selected tool (note, gracenote, beam, countline, slur, text, pedal, ...)
            'tool': 'note',

            # current selected hand (l, r)
            'hand': 'l',

            # viewport
            'viewport': {
                'toptick': 0,
                'bottomtick': 0,
                'events': SaveFileStructureSource.new_events_folder_viewport(),
                'already_drawn': []
            },

            # total ticks
            'total_ticks': 0,

            # drawn_objects
            'drawn_obj': [],

            # wheter the score is saved or not
            'saved': True,

            # edit_obj == the object that is being edited
            'edit_obj': None,

            # selected page number for the engraver
            'selected_page': 0,

            # keep track of the total page numbers
            'total_pages': 0,

            # keep track of the number of pages in the document
            'num_pages': 0,

            # auto save onoff
            'autosave': False,

            # current selected staff to edit
            'selected_staff': 0,

            # checkbox auto engrave
            'auto_engrave': True
        }

        # setup
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLE)
        self.root = QMainWindow()
        self.gui = Gui(self.root, self.io)
        self.gui.show()
        self.io['app'] = self.app
        self.io['root'] = self.root
        self.root.showFullScreen()
        self.io['gui'] = self.gui

        # EE
        self.io['gui'].slider.valueChanged.connect(lambda: self.change_color())
        self.change_color()
        
        self.io['editor'] = DrawUtil(self.gui.editor_scene)
        self.io['view'] = DrawUtil(self.gui.print_scene)
        self.io['calc'] = CalcTools(self.io)
        self.io['engraver'] = Engraver(self.io)
        self.io['maineditor'] = Editor(self.io)
        self.io['zoom'] = Zoom(self.io)
        self.io['selectoperations'] = SelectOperations(self.io)
        self.io['ctlz'] = CtlZ(self.io)
        self.io['midi'] = Midi(self.io)
        self.io['fileoperations'] = FileOperations(self.io)
        self.editor_dialog = None
        self.line_break_dialog = None

        # connect the file operations to the gui menu
        self.gui.new_action.triggered.connect(self.io['fileoperations'].new)
        self.gui.load_action.triggered.connect(self.io['fileoperations'].load)
        self.gui.save_action.triggered.connect(self.io['fileoperations'].save)
        self.gui.saveas_action.triggered.connect(
            self.io['fileoperations'].saveas)
        self.gui.save_template_action.triggered.connect(
            self.io['fileoperations'].save_template)

        self.gui.autosave_action.triggered.connect(
            self.io['fileoperations'].toggle_autosave)
        self.gui.auto_engrave_action.triggered.connect(
            self.io['maineditor'].toggle_auto_engrave)
        self.gui.exit_action.triggered.connect(self.root.close)

        self.gui.grid_edit_action.triggered.connect(self.open_grid_editor)
        self.gui.line_break_editor_action.triggered.connect(
            self.open_line_break_editor)
        # shortcuts
        cut_shortcut = QShortcut(QKeySequence("Ctrl+X"), self.root)
        cut_shortcut.activated.connect(self.io['selectoperations'].cut)
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self.root)
        copy_shortcut.activated.connect(self.io['selectoperations'].copy)
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self.root)
        paste_shortcut.activated.connect(self.io['selectoperations'].paste)
        delete_shortcut = QShortcut(QKeySequence("Delete"), self.root)
        delete_shortcut.activated.connect(self.io['selectoperations'].delete)
        transpose_up_shortcut = QShortcut(QKeySequence("Right"), self.root)
        transpose_up_shortcut.activated.connect(
            self.io['selectoperations'].transpose_up)
        transpose_down_shortcut = QShortcut(QKeySequence("Left"), self.root)
        transpose_down_shortcut.activated.connect(
            self.io['selectoperations'].transpose_down)
        move_backward_shortcut = QShortcut(QKeySequence("Up"), self.root)
        move_backward_shortcut.activated.connect(
            self.io['selectoperations'].move_backward)
        move_forward_shortcut = QShortcut(QKeySequence("Down"), self.root)
        move_forward_shortcut.activated.connect(
            self.io['selectoperations'].move_forward)
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self.root)
        undo_shortcut.activated.connect(self.io['ctlz'].undo)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self.root)
        redo_shortcut.activated.connect(self.io['ctlz'].redo)
        hand_left_shortcut = QShortcut(QKeySequence("["), self.root)
        hand_left_shortcut.activated.connect(
            self.io['selectoperations'].hand_left)
        hand_right_shortcut = QShortcut(QKeySequence("]"), self.root)
        hand_right_shortcut.activated.connect(
            self.io['selectoperations'].hand_right)
        escape_shortcut = QShortcut(QKeySequence("Escape"), self.root)
        escape_shortcut.activated.connect(self.io['fileoperations'].quit)
        engrave_shortcut = QShortcut(QKeySequence("/"), self.root)
        engrave_shortcut.activated.connect(self.io['engraver'].do_engrave)
        next_page_shortcut = QShortcut(QKeySequence("."), self.root)
        next_page_shortcut.activated.connect(self.io['gui'].next_page)
        prev_page_shortcut = QShortcut(QKeySequence(","), self.root)
        prev_page_shortcut.activated.connect(self.io['gui'].previous_page)

        self.root.closeEvent = self.cleanup
        # run the application
        sys.exit(self.app.exec())

    def cleanup(self, event):
        """ close open dialogs """

        if self.editor_dialog:
            self.editor_dialog.close()

        if self.line_break_dialog:
            self.line_break_dialog.close()

    def open_grid_editor(self):
        """ open the Grid Editor """

        grid_dct = self.io['score']['events']['grid']

        self.editor_dialog = GridDialog(parent=None,
                                        grid_dct=grid_dct)
        self.editor_dialog.set_close_event(self.dialog_close_callback)
        self.editor_dialog.show()

    def dialog_close_callback(self, result: DialogResult, grids: [dict]):
        """ the dialog has closed """

        self.editor_dialog = None

        if result == DialogResult.OK:
            for item in grids:
                nr = self.io['calc'].add_and_return_tag()
                item['tag'] = f'grid{nr}'

            self.io['score']['events']['grid'] = grids
            self.io['maineditor'].update('grid_editor')

    def open_line_break_editor(self):
        """ open the Staff Sizer Editor """

        linebreaks = self.io['score']['events']['linebreak']

        self.line_break_dialog = StaffSizerDialog(parent=None,
                                                  callback=self.close_line_break_editor,
                                                  linebreaks=linebreaks,
                                                  time_calc=self.io['calc'].get_measure_number)

        self.line_break_dialog.show()

    def close_line_break_editor(self, result: DialogResult, line_breaks: [dict]):
        """ the line break editor has closed """

        self.line_break_dialog = None

        if result == DialogResult.OK:
            # self.io['score']['events']['linebreak'] = line_breaks

            Popup(message=f'Line break Editor has closed\n{result}\nNOT UPDATED',
                  max_lines=3,
                  text_size=(100, 21))

            # self.io['maineditor'].update('grid_editor')

    def change_color(self):
        
        complementary_color = QColor.fromHsv(self.io['gui'].slider.value(), 175, 80)
        self.color1 = complementary_color.name()

        # Get the negative color
        color1_hex = int(self.color1.lstrip('#'), 16)  # Convert color1 to hexadecimal
        color2_hex = color1_hex ^ 0xFFFFFF  # Get the complementary color
        self.color2 = f'#{color2_hex:06X}'  # Convert the complementary color back to a string

        # Get the RGB values of color1 and add 50 to each component
        add = 75
        r = min(QColor(self.color1).red() + add, 255)
        g = min(QColor(self.color1).green() + add, 255)
        b = min(QColor(self.color1).blue() + add, 255)

        # Create a new color from the modified RGB values
        lighter_color = QColor(r, g, b).darker(150)
        self.color1 = lighter_color.name()

        style = f'''
        QTreeView, QGraphicsView, 
        QMainWindow, QToolBar, QToolBar,
        QToolBar QAction, 
        QMainWindow QMenuBar, QMenu, 
        QRadioButton, QLabel, QDockWidget, 
        QSplitter, QDialog, QVBoxLayout, QHBoxLayout {{
            background-color: {self.color1};
            color: {self.color2};
            font-size: 16px;
            font-family: Bookman Old Style;
        }}
        QMenuBar::item, QMenuBar::item:selected {{
            background-color: {self.color1};
            color: {self.color2};
        }}
        QTabWidget, QTabWidget::pane, QTabWidget::tab-bar {{
            background-color: {self.color1};
            color: {self.color2};
        }}
        QTabWidget::tab-bar::tab:selected {{
            background-color: {self.color2};
            color: {self.color1};
        }}
        QPushButton {{
            background-color: #000000;
            color: {self.color2};
        }}
        QSlider::groove:horizontal {{
            border: 15px solid #999999;
            height: 15px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
            margin: 2px 0;
        }}

        QSlider::add-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.color1}, stop:1 {self.color2});
        }}

        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.color2}, stop:1 {self.color1});
        }}
        '''

        self.root.setStyleSheet(style)
        

        # complementary_color = QColor.fromHsv((value, 220, 220))
        # print(complementary_color.name())
        # self.root.setStyleSheet(f"background-color: {complementary_color.name()}")





if __name__ == '__main__':
    PianoScript()
    exit(0)
