from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from PySide6.QtWidgets import QApplication

class ScriptUtils:

    def __init__(self, io):
        self.io = io

    # User input functions:
    def ask_str(self, message='Enter text:'):
        '''Opens a input dialog for the script and returns the input.'''
        
        text, ok = QInputDialog.getText(self.io['root'], message)
        if ok:
            return text
        else:
            return None
        
    def ask_int(self, message='Enter an integer:', min_value=0, max_value=100, default_value=0):
        '''Opens an input dialog for the script and returns the input integer.'''
        
        value, ok = QInputDialog.getInt(self.io['root'], 'PianoScript', message, default_value, min_value, max_value)
        if ok:
            return value
        else:
            return None
        
    def ask_float(self, message='Enter a float:', min_value=0, max_value=100, default_value=0):
        '''Opens an input dialog for the script and returns the input float.'''
        
        value, ok = QInputDialog.getDouble(self.io['root'], 'PianoScript', message, default_value, min_value, max_value)
        if ok:
            return value
        else:
            return None
  
    def ask_yesno(self, message='Yes or No?'):
        '''Opens a yes/no dialog for the script and returns the input.'''
        
        return QMessageBox.question(self.io['root'], 'PianoScript', message)
    
    def ask_list(self, message='Select an item:', items=['Item 1', 'Item 2', 'Item 3']):
        '''Opens a combobox dialog for the script and returns the input.'''
        
        item, ok = QInputDialog.getItem(self.io['root'], 'PianoScript', message, items, 0, False)
        if ok:
            return item
        else:
            return None
    
    # Message functions:
    def error(self, message='Error'):
        '''Opens an error dialog for the script.'''
        
        return QMessageBox.critical(self.io['root'], 'PianoScript', message)
    
    def warning(self, message='Warning'):
        '''Opens a warning dialog for the script.'''
        
        return QMessageBox.warning(self.io['root'], 'PianoScript', message)
    
    def info(self, message='Info'):
        '''Opens an info dialog for the script.'''
        
        return QMessageBox.information(self.io['root'], 'PianoScript', message)
    


