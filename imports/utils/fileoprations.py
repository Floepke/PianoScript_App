import json, copy
from PySide6.QtWidgets import QFileDialog
from imports.utils.constants import SCORE_TEMPLATE
from PySide6.QtWidgets import QMessageBox
from imports.utils.savefilestructure import empty_events_folder

class FileOperations:
    '''
        The Score class handles all file IO for the application. methods:
            - load(); loads a score from a file
            - save(); saves a score to a file
            - saveas(); saves a score to a file with a new name
    '''
    def __init__(self, io):
        self.io = io
        self.savepath = None
        self.init = True

    def new(self):
        if not self.init:
            # check if there is a score loaded
            yesnocancel = QMessageBox()
            yesnocancel.setText("Do you wish to save current file?")
            yesnocancel.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            yesnocancel.setDefaultButton(QMessageBox.Yes)
            response = yesnocancel.exec()
            if response == QMessageBox.Yes:
                self.save()
            elif response == QMessageBox.No:
                ...
            elif response == QMessageBox.Cancel:
                return
        self.init = False
        
        # reset the saved flag
        self.io['saved'] = True
        # reset the savepath
        self.savepath = None
        # reset the new_tag counter
        self.io['new_tag'] = 0
        # reset the selection
        self.io['selection']['active'] = False
        self.io['selection']['rectangle_on'] = False
        self.io['selection']['selection_buffer'] = empty_events_folder()
        
        # load the score into the editor
        # for now, we just load the hardcoded template into the score. later, we will add a template system.
        self.io['score'] = json.load(open('Fur_elise.pianoscript', 'r'))
        self.io['score'] = copy.deepcopy(SCORE_TEMPLATE)

        # renumber tags
        self.io['calc'].renumber_tags()

        # redraw the editor
        self.io['maineditor'].update('loadfile')

        # reset the ctlz buffer
        self.io['ctlz'].reset_ctlz()

    def load(self):
        # check if we want to save the current score
        yesnocancel = QMessageBox()
        yesnocancel.setText("Do you wish to save the file?")
        yesnocancel.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        yesnocancel.setDefaultButton(QMessageBox.Yes)
        response = yesnocancel.exec()
        if response == QMessageBox.Yes:
            self.save()
        elif response == QMessageBox.No:
            ...
        elif response == QMessageBox.Cancel:
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            # load a score from a file into the score dict io['score']
            with open(file_path, 'r') as file:
                self.io['score'] = json.load(file)
            self.savepath = file_path

            # renumber tags
            self.io['calc'].renumber_tags()

            # draw the editor
            self.io['maineditor'].update('loadfile')

            # reset the ctlz buffer
            self.io['ctlz'].reset_ctlz()

    def save(self):
        if self.savepath:
            with open(self.savepath, 'w') as file:
                json.dump(self.io['score'], file, indent=4)
        else:
            self.saveas()

    def saveas(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(filter='*.pianoscript')
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.io['score'], file, indent=4)


