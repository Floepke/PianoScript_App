import json
import copy
import os
import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QAction
from imports.utils.constants import SCORE_TEMPLATE, BLUEPRINT
from imports.utils.savefilestructure import SaveFileStructureSource
import json


class File:
    '''
        The FileOperations class handles all file IO for the application. 
        It has the following methods:
            - load(); loads a score from a .pianoscript file
            - save(); saves a score to a .pianoscript file
            - saveas(); saves a score to a file with a new name
            - new(); creates a new score
            - save_check(); checks if the score has been saved
            - update_recent_file_menu(); updates the "Recent Files" menu
            - clear_recent_file_menu(); clears the "Recent Files" menu
            - load_recent_file(); loads a score from a recent file
            - backwards_compatibility_check(); handles the backwards compatibility of the .pianoscript file
    '''

    def __init__(self, io):
        self.io = io

        # keep track of opened files
        self.savepath = None
        self.filechanged = False

        # Initialize the list of recent file actions
        self.recent_file_actions = []
        for i in range(10):
            action = QAction(QAction(self.io['gui'].main))
            action.setVisible(False)
            self.recent_file_actions.append(action)
            self.io['gui'].recent_file_menu.addAction(action)

        self.io['gui'].clear_recent_action.triggered.connect(
            self.clear_recent_file_menu)

        # Update the "Recent Files" menu
        self.update_recent_file_menu()

        self.new()

        self.io['gui'].file_browser.tree_view.clicked.connect(
            self.file_browser_on_click)

    def new(self, _path=None):

        if self.filechanged:
            if not self.save_question():
                # if the user didn't click cancel
                return

        # reset the savepath
        self.savepath = None
        # reset the new_tag counter
        self.io['new_tag'] = 0
        # reset the selection
        self.io['selection']['active'] = False
        self.io['selection']['rectangle_on'] = False
        self.io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()

        # ensure there is a template.pianoscript in ~/.pianoscript
        path = self.io['calc'].ensure_json(
            '~/.pianoscript/template.pianoscript', SCORE_TEMPLATE)

        # load the template.pianoscript
        with open(path, 'r') as file:
            self.io['score'] = json.load(file)

        # write timestamp
        self.io['score']['header']['timestamp'] = datetime.datetime.now().strftime(
            '%d-%m-%Y_%H:%M:%S')

        # renumber tags
        self.io['calc'].renumber_tags()

        # set save path to None
        self.savepath = None
        self.filechanged = False

        # redraw the editor
        self.io['maineditor'].update('loadfile')

        # reset the ctlz buffer
        self.io['ctlz'].reset_ctlz()

        # update page dimensions in the printview
        self.io['gui'].print_view.update_page_dimensions()

        # update window title
        self.io['gui'].main.setWindowTitle('PianoScript - new file')

        # statusbar message
        self.io['gui'].main.statusBar().showMessage('New file...', 10000)

    def load(self, file_path):

        if self.filechanged:
            if not self.save_question():
                # if the user didn't click cancel
                return 

        if not file_path:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName()

        if file_path:
            # load a score from a file into the score dict io['score']
            with open(file_path, 'r') as file:
                self.io['score'] = json.load(file)

            self.io['score'] = self.backwards_compitability_check(
                self.io['score'], BLUEPRINT)  # TODO: Test

            # set to None to prevent auto save from overwriting the previously loaded file
            self.savepath = file_path

            # renumber tags
            self.io['calc'].renumber_tags()

            # draw the editor
            self.io['maineditor'].update('loadfile')

            # reset the ctlz buffer
            self.io['ctlz'].reset_ctlz()

            # reset the selection
            self.io['selection']['active'] = False
            self.io['selection']['rectangle_on'] = False
            self.io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()

            # update page dimensions in the printview
            self.io['gui'].print_view.update_page_dimensions()

            # set save path
            self.savepath = file_path
            self.filechanged = False

            # set window title
            self.io['gui'].main.setWindowTitle(f'PianoScript - {file_path}')

            # statusbar message
            self.io['gui'].main.statusBar().showMessage(
                'File loaded...', 10000)

            self.add_recent_file(file_path)
            self.update_recent_file_menu()

    def load_midi(self, file_path):

        if self.filechanged:
            if not self.save_question():
                # if the user didn't click cancel
                return 
        self.io['midi'].load_midi(file_path)
        self.filechanged = False
                
    def save(self):
        if self.savepath == '*import midi*':
            self.saveas()
        elif self.savepath:
            with open(self.savepath, 'w') as file:
                json.dump(self.io['score'], file, separators=(',', ':'))
            self.io['gui'].main.statusBar().showMessage('File saved...', 10000)
        else:
            self.saveas()

    def saveas(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(filter='*.pianoscript')
        if file_path:
            self.io['gui'].main.statusBar().showMessage('Save as...', 10000)
            with open(file_path, 'w') as file:
                json.dump(self.io['score'], file, separators=(',', ':'))
            self.savepath = file_path
            # set window title
            self.io['gui'].main.setWindowTitle(f'PianoScript - {file_path}')

    def save_template(self):
        '''This function overwrites the template.pianoscript file with the current score'''

        # ensure there is a template.pianoscript in ~/.pianoscript
        path = os.path.expanduser('~/.pianoscript/template.pianoscript')
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)

        # save the template.pianoscript
        with open(path, 'w') as file:
            json.dump(self.io['score'], file, indent=4)
        self.io['gui'].main.statusBar().showMessage('Template saved...', 10000)

    def auto_save(self):
        if self.savepath and self.io['settings']['autosave']:
            with open(self.savepath, 'w') as file:
                json.dump(self.io['score'], file, separators=(',', ':'))

    def toggle_autosave(self):
        self.io['settings']['autosave'] = not self.io['settings']['autosave']

    def quit(self):

        # if not self.save_check(): # TODO: uncomment on publish
        #     return

        self.io['root'].close()

    def save_question(self):

        # check if we want to save the current score
        yesnocancel = QMessageBox()
        yesnocancel.setText("Do you wish to save the file?")
        yesnocancel.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        yesnocancel.setDefaultButton(QMessageBox.Cancel)
        response = yesnocancel.exec()
        if response == QMessageBox.Yes:
            self.save()
            return True
        elif response == QMessageBox.No:
            return True
        elif response == QMessageBox.Cancel:
            return False

    # RECENT FILE FUNCTIONS:

    def add_recent_file(self, path):

        recent_files = self.io['settings']['recent_files']

        # Check if the path is already in the list
        if path not in recent_files:
            # If the path is not in the list, append it
            recent_files.append(path)
            if len(recent_files) > 10:
                recent_files.pop(0)

    def update_recent_file_menu(self):
        # Update the menu items with the list of recent files max 10
        for i, path in enumerate(self.io['settings']['recent_files']):
            action = self.recent_file_actions[i]
            action.setText(os.path.basename(path))
            action.setVisible(True)
            action.triggered.disconnect()
            action.setData(path)
            action.triggered.connect(
                lambda checked=False, action=action: self.open_recent_file(action))

        # Hide any unused QAction objects
        for i in range(len(self.io['settings']['recent_files']), 10):
            action = self.recent_file_actions[i]
            action.setVisible(False)

    def open_recent_file(self, file_path):
        if os.path.exists(file_path.data()):
            # Open the selected file
            self.load(file_path.data())
        else:
            self.load()

    def clear_recent_file_menu(self):
        # Define the path to the recent.json file
        recent_file_path = os.path.expanduser('~/.pianoscript/settings.json')

        # Check if the recent.json file exists
        if os.path.exists(recent_file_path):
            # Clear the list of recent files in the settings.json file
            ...

        # Update the "Recent Files" menu
        self.update_recent_file_menu()

    # function to make .pianoscript files backwards compitabel
    def backwards_compitability_check(self, score, template):
        for key, value in template.items():
            if key not in score:
                score[key] = value
            elif isinstance(value, dict):
                self.backwards_compitability_check(score[key], value)
            elif isinstance(value, list) and value:
                blueprint = value[0]
                if isinstance(score[key], list):
                    for item in score[key]:
                        if isinstance(item, dict):
                            self.backwards_compitability_check(item, blueprint)
        return score

    def file_browser_on_click(self, index):
        source_index = self.io['gui'].file_browser.tree_view.model(
        ).mapToSource(index)
        file_info = self.io['gui'].file_browser.model.fileInfo(source_index)
        if file_info.isFile():
            
            # check if we want to save if the autosave function is switched off
            if not self.io['settings']['autosave']:
                if not self.save_question():
                    return
            
            file_path = file_info.filePath()
            if file_path.endswith(".pianoscript"):
                self.load(file_path)
                self.savepath = file_path
            elif file_path.endswith(".mid"):
                self.load_midi(file_path)
                self.savepath = None

