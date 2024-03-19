import json
import copy
import os
import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QAction
from imports.utils.constants import SCORE_TEMPLATE
from imports.utils.savefilestructure import SaveFileStructureSource


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
        self.savepath = None

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

    def new(self):

        if self.savepath:
            if not self.save_check():
                return

        # reset the saved flag
        self.io['saved'] = True
        # reset the savepath
        self.savepath = None
        # reset the new_tag counter
        self.io['new_tag'] = 0
        # reset the selection
        self.io['selection']['active'] = False
        self.io['selection']['rectangle_on'] = False
        self.io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()

        # ensure there is a template.pianoscript in ~/.pianoscript
        path = os.path.expanduser('~/.pianoscript/template.pianoscript')
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if not os.path.exists(path):
            with open(path, 'w') as file:
                json.dump(SCORE_TEMPLATE, file, indent=4)

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

    def load(self, file_path=None):

        if not self.save_check():
            return

        if not file_path:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName()

        if file_path:
            # load a score from a file into the score dict io['score']
            with open(file_path, 'r') as file:
                self.io['score'] = json.load(file)

            self.io['score'] = self.backwards_compitability_check(
                self.io['score'], SCORE_TEMPLATE)  # TODO: Test

            # set to None to prevent auto save from overwriting the previously loaded file
            self.savepath = None

            # renumber tags
            self.io['calc'].renumber_tags()

            # draw the editor
            self.io['maineditor'].update('loadfile')

            # reset the ctlz buffer
            self.io['ctlz'].reset_ctlz()

            # reset the saved flag
            self.io['saved'] = True

            # reset the selection
            self.io['selection']['active'] = False
            self.io['selection']['rectangle_on'] = False
            self.io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()

            # update page dimensions in the printview
            self.io['gui'].print_view.update_page_dimensions()

            # set save path
            self.savepath = file_path

            # set window title
            self.io['gui'].main.setWindowTitle(f'PianoScript - {file_path}')

            # statusbar message
            self.io['gui'].main.statusBar().showMessage(
                'File loaded...', 10000)

            self.add_recent_file(file_path)
            self.update_recent_file_menu()

    def save(self):
        if self.savepath:
            with open(self.savepath, 'w') as file:
                json.dump(self.io['score'], file, indent=4)
            self.io['gui'].main.statusBar().showMessage('File saved...', 10000)
        else:
            self.saveas()

    def saveas(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(filter='*.pianoscript')
        if file_path:
            self.io['gui'].main.statusBar().showMessage('Save as...', 10000)
            with open(file_path, 'w') as file:
                json.dump(self.io['score'], file, indent=4)
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
        if self.savepath and self.io['autosave']:
            with open(self.savepath, 'w') as file:
                json.dump(self.io['score'], file, indent=4)

    def toggle_autosave(self):
        self.io['autosave'] = not self.io['autosave']

    def quit(self):

        # if not self.save_check(): # TODO: uncomment on publish
        #     return

        self.io['root'].close()

    def save_check(self):

        # check if current file was changed
        if self.savepath:
            with open(self.savepath, 'r') as file:
                if json.load(file) != self.io['score']:
                    ...
        # check if we want to save the current score
        yesnocancel = QMessageBox()
        yesnocancel.setText("Do you wish to save the file?")
        yesnocancel.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        yesnocancel.setDefaultButton(QMessageBox.Yes)
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
        # Define the path to the recent.json file
        recent_file_path = os.path.expanduser('~/.pianoscript/recent.json')

        # Check if the directory for the recent.json file exists
        recent_file_dir = os.path.dirname(recent_file_path)
        if not os.path.exists(recent_file_dir):
            # If the directory doesn't exist, create it
            os.makedirs(recent_file_dir)

        # Check if the recent.json file exists
        if not os.path.exists(recent_file_path):
            # If the file doesn't exist, create it with an empty list
            with open(recent_file_path, 'w') as file:
                json.dump([], file)

        # Load the list of recent files from the recent.json file
        with open(recent_file_path, 'r') as file:
            recent_files = json.load(file)

        # Check if the path is already in the list
        if path not in recent_files:
            # If the path is not in the list, append it
            recent_files.append(path)
            if len(recent_files) > 10:
                recent_files.pop(0)

            # Save the updated list back to the recent.json file
            with open(recent_file_path, 'w') as file:
                json.dump(recent_files, file)

    def update_recent_file_menu(self):
        # Define the path to the recent.json file
        recent_file_path = os.path.expanduser('~/.pianoscript/recent.json')

        # Check if the recent.json file exists
        if os.path.exists(recent_file_path):
            # Load the list of recent files from the recent.json file
            with open(recent_file_path, 'r') as file:
                recent_files = json.load(file)

            # Update the menu items with the list of recent files max 10
            for i, path in enumerate(recent_files):
                action = self.recent_file_actions[i]
                action.setText(os.path.basename(path))
                action.setVisible(True)
                action.triggered.disconnect()
                action.setData(path)
                action.triggered.connect(
                    lambda checked=False, action=action: self.open_recent_file(action))

            # Hide any unused QAction objects
            for i in range(len(recent_files), 10):
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
        recent_file_path = os.path.expanduser('~/.pianoscript/recent.json')

        # Check if the recent.json file exists
        if os.path.exists(recent_file_path):
            # Clear the list of recent files in the recent.json file
            with open(recent_file_path, 'w') as file:
                json.dump([], file)

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
