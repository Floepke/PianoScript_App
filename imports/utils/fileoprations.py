import json, copy, datetime
from PySide6.QtWidgets import QFileDialog
from imports.utils.constants import SCORE_TEMPLATE
from PySide6.QtWidgets import QMessageBox
from imports.utils.savefilestructure import SaveFileStructureSource

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
        
        # load the score into the editor
        try:
            with open('template.pianoscript', 'r') as file:
                self.io['score'] = json.load(file)
        except FileNotFoundError:
            self.io['score'] = copy.deepcopy(SCORE_TEMPLATE)
            with open('template.pianoscript', 'w') as file:
                json.dump(SCORE_TEMPLATE, file, indent=4)

        # write timestamp
        self.io['score']['header']['timestamp'] = datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S')

        # load test file only for debug purposes:
        #self.io['score'] = json.load(open('pianoscriptfiles/Lamp.pianoscript', 'r'))

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


    def load(self):
        
        if not self.save_check():
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            # load a score from a file into the score dict io['score']
            with open(file_path, 'r') as file:
                self.io['score'] = json.load(file)
            
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
            self.io['gui'].main.statusBar().showMessage('File loaded...', 10000)

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
        with open('template.pianoscript', 'w') as file:
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
        yesnocancel.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        yesnocancel.setDefaultButton(QMessageBox.Yes)
        response = yesnocancel.exec()
        if response == QMessageBox.Yes:
            self.save()
            return True
        elif response == QMessageBox.No:
            return True
        elif response == QMessageBox.Cancel:
            return False































