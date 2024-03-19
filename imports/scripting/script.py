from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from imports.utils.savefilestructure import SaveFileStructureSource
# TODO: add a openfile and savefile dialog for scripting


class Script:
    '''
    This class contains script functionality:
        * User input functions:
            - ask_str(message); creates a basic dialog for passing a string and returns the string if the user clicked ok.
            - ask_int(message, min_value max_value, default_value); same as above but for integers
            - ask_float(...); ...
            - ask_yesno(message); asks the user something and the user can click yes or no
            - ask_list(message, list_of_options); the user can choose an option from a list and click ok or cancel.
        * Message functions:
            - error(message); creates a warning dialog
            - warning(message); ...
            - info(message); ...
        * .pianoscript file edit functions:
            - add_note(pitch, time, etc...); add a note according to the arguments like pitch, time, duration etc...
            - delete_note(); deletes the given note
        * Get useful info about the score:
            - get_score_ticks(); returns the length of the score in ticks
            - get_barline_ticks(); returns a list of barline positions in ticks
            - get_measure_number(time); returns the measure number that is happening at the given time parameter
            - get_relative_measure_tick(time); returns the tick relative to the start of the current measure at the given time parameter
    '''

    def __init__(self, io):
        self.__io = io
        self.score = io['score']

    # User input functions:
    def ask_str(self, message='Enter text:'):
        '''Opens a input dialog for the script and returns the input.'''

        text, ok = QInputDialog.getText(
            self.__io['root'], self.__io['script_name'], message)
        if ok:
            return text
        else:
            return None

    def ask_int(self, message='Enter an integer:', min_value=0, max_value=100, default_value=0):
        '''Opens an input dialog for the script and returns the input integer.'''

        value, ok = QInputDialog.getInt(
            self.__io['root'], self.__io['script_name'], message, default_value, min_value, max_value)
        if ok:
            return value
        else:
            return None

    def ask_float(self, message='Enter a float:', min_value=0, max_value=100, default_value=0):
        '''Opens an input dialog for the script and returns the input float.'''

        value, ok = QInputDialog.getDouble(
            self.__io['root'], self.__io['script_name'], message, default_value, min_value, max_value)
        if ok:
            return value
        else:
            return None

    def ask_yesno(self, message='Yes or No?'):
        '''Opens a yes/no dialog for the script and returns the input.'''

        return QMessageBox.question(self.__io['root'], self.__io['script_name'], message)

    def ask_list(self, message='Select an item:', items=['Item 1', 'Item 2', 'Item 3']):
        '''Opens a combobox dialog for the script and returns the input.'''

        item, ok = QInputDialog.getItem(
            self.__io['root'], self.__io['script_name'], message, items, 0, False)
        if ok:
            return item
        else:
            return None

    # Message functions:
    def error(self, message='Error'):
        '''Opens an error dialog for the script.'''

        return QMessageBox.critical(self.__io['root'], self.__io['script_name'], message)

    def warning(self, message='Warning'):
        '''Opens a warning dialog for the script.'''

        return QMessageBox.warning(self.__io['root'], self.__io['script_name'], message)

    def info(self, message='Info'):
        '''Opens an info dialog for the script.'''

        return QMessageBox.information(self.__io['root'], self.__io['script_name'], message)

    
    # PianoScript basic add and remove functions:
    def add_note(self,
                 pitch: int = 40,  # piano note number 1 to 88
                 # in linear time in pianoticks 0 to infinity (quarter note == 256)
                 time: float = 0,
                 duration: float = 256,  # in linear time in pianoticks 0 to infinity
                 hand: str = 'l',  # 'l' or 'r'
                 staff: int = 0,  # staff number 0 to 3 there is a total of 4 staffs available
                 attached: str = ''  # possible are the following symbols in any order: '>' = accent, '.' = staccato, '-' = tenuto, 'v' = staccatissimo, '#' = sharp, 'b' = flat, '^' = marcato
                 ):
        '''
        It adds a note to the score with the 
        given parameters and adds a tag automatically. For 
        the biggest part it is a binding to the 
        SaveFileStructureSource class.
        '''
        note_folder = self.__io['score']['events']['note']
        new = SaveFileStructureSource.new_note(
            tag='note' + str(self.__io['calc'].add_and_return_tag()),
            pitch=pitch,
            time=time,
            duration=duration,
            hand=hand,
            staff=staff,
            attached=attached
        )
        note_folder.append(new)

    def delete_note(self, note_or_tag):
        '''
        It deletes the given note based on the literal note obj dict.
        Or if the argument is a string it's going to search for a note 
        with that exact tag and deletes it.
        '''
        if isinstance(note_or_tag, str):
            # search the tag and delete the note if found
            self.score['events']['note'] = [note for note in self.score['events']['note'] if note['tag'] != note_or_tag]
        else:
            # delete the note obj from score['events]['note']
            self.score['events']['note'].remove(note_or_tag)

    def add_linebreak(self, 
            time: float = 0,  # in linear time in pianoticks 0 to infinity
            # list with two values: (leftmargin, rightmargin) in mm
            staff1_lr_margins: list = [10.0, 10.0],
            staff2_lr_margins: list = [10.0, 10.0],  # ...
            staff3_lr_margins: list = [10.0, 10.0],
            staff4_lr_margins: list = [10.0, 10.0],
            # list with two values: [lowestnote, highestnote] or string 'auto'
            staff1_range: list or str = 'auto',
            staff2_range: list or str = 'auto',  # ...
            staff3_range: list or str = 'auto',
            staff4_range: list or str = 'auto',
            tag: str = None
    ):
        '''Adds a linebreak based on the input. TODO: finish this docstring'''
        
        if not tag:
            # assign unique tag
            tag = 'linebreak' + str(self.__io['calc'].add_and_return_tag())
        
        linebreak_folder = self.__io['score']['events']['linebreak']
        new = SaveFileStructureSource.new_linebreak(
            tag = tag,
            time = time,
            staff1_lr_margins = staff1_lr_margins,
            staff2_lr_margins = staff2_lr_margins,  # ...
            staff3_lr_margins = staff3_lr_margins,
            staff4_lr_margins = staff4_lr_margins,
            staff1_range = staff1_range,
            staff2_range = staff2_range,
            staff3_range = staff3_range,
            staff4_range = staff4_range
        )
        linebreak_folder.append(new)

    
    # get useful values functions:
    def get_score_ticks(self):
        '''Returns the length of the score in ticks'''
        return self.__io['calc'].get_total_score_ticks()
    
    def get_barline_ticks(self):
        '''Returns a list of the barline positions in ticks'''
        return self.__io['calc'].get_barline_ticks()
    
    def get_measure_number(self, time = 0):
        '''Returns the measure number in which the time parameter happens'''
        measure_number, _, _ = self.__io['calc'].get_measure_number_and_tick(time)
        return measure_number
    
    def get_relative_measure_tick(self, time = 0):
        '''Returns the distance in ticks from the start from the current measure in which the time parameter happens'''
        _, tick, _ = self.__io['calc'].get_measure_number_and_tick(time)
        return tick
    
    @staticmethod
    def get_measure_length(numerator, denominator):
        '''
            returns the length of a measure in pianoticks
            based on the numerator and denominator
        '''
        return int(numerator * ((256 * 4) / denominator))
    
