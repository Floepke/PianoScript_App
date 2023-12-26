import json
from PySide6.QtWidgets import QFileDialog
from imports.utils.CONSTANT import SCORE_TEMPLATE

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

    def new(self):
        # for now, we just load the hardcoded template into the score. later, we will add a template system.
        self.io['score'] = SCORE_TEMPLATE

        # redraw the editor
        self.io['maineditor'].redraw(self.io)

    def load(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            # load a score from a file into the score dict io['score']
            with open(file_path, 'r') as file:
                self.io['score'] = json.load(file)
            self.savepath = file_path

            # redraw the editor
            self.io['maineditor'].redraw(self.io)

    def save(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(filter='*.pianoscript')
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.io['score'], file)

    def saveas(self):
        if self.savepath:
            file_path = self.savepath
        else:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(filter='*.pianoscript')
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.io['score'], file)


