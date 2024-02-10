from typing import Tuple

class SaveFileStructureSource:
    '''
        Stores all event types standard json structures for saving 
        to a score file or creating new messages from. That way we 
        can add new preferences to for example note_msg() and change 
        that only in this file.
    '''
    
    def new_events_folder():
        '''returns the structure of the events folder in a score file'''
        return {
            'note':[],
            'linebreak':[],
            'gracenote':[],
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
            'stop':[],
            'dot':[],
        }
    
    def new_events_folder_viewport():
        '''returns the structure of the events folder in a score file'''
        return {
            'note':[],
            'linebreak':[],
            'gracenote':[],
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
            'dot':[],
            'stop':[],
        }

    def new_note(
            tag: str, # note+tagnumber to make tag unique
            pitch: int, # piano note number 1 to 88
            time: float, # in linear time in pianoticks 0 to infinity (quarter note == 256)
            duration: float, # in linear time in pianoticks 0 to infinity
            hand: str, # 'l' or 'r'
            staff: int, # staff number 0 to 3 there is a total of 4 staffs available
            attached: str = '' # possible are the following symbols in any order: '>' = accent, '.' = staccato, '-' = tenuto, 'v' = staccatissimo, '#' = sharp, 'b' = flat, '^' = marcato
            ):
        '''The note event structure.'''
        return {
            'tag':tag,
            'pitch':pitch,
            'time':time,
            'duration':duration,
            'hand':hand,
            'staff':staff,
            'attached':attached
        }
    
    def new_grid(
            amount: int, # amount of measures to repeat
            numerator: int, # numerator of the grid
            denominator: int, # denominator of the grid
            grid: list, # list of ticks relative to the start of every measure. every tick is a gridline
            visible: bool = True, # are the stafflines and the gridlines visible if False in the editor the background is redish
            ):
        '''The grid event structure.'''
        return {
            'tag':'grid',
            'amount':amount,
            'numerator':numerator,
            'denominator':denominator,
            'grid':grid,
            'visible':visible
        }

    def new_countline(
            tag: str, # countline+tagnumber to make tag unique
            time: float, # in linear time in pianoticks 0 to infinity
            pitch1: int, # piano note number 1 to 88
            pitch2: int, # piano note number 1 to 88
            staff: int = 0, # staff number 0 to 3 there is a total of 4 staffs available
            ):
        '''The countline event structure.'''
        return {
            'tag':tag,
            'time':time,
            'pitch1':pitch1,
            'pitch2':pitch2,
            'staff':staff
        }
    
    def new_linebreak(
            tag: str, # linebreak+tagnumber to make tag unique
            time: float, # in linear time in pianoticks 0 to infinity
            staff1_lr_margins: list = [10.0, 10.0], # list with two values: (leftmargin, rightmargin) in mm
            staff2_lr_margins: list = [10.0, 10.0], # ...
            staff3_lr_margins: list = [10.0, 10.0], 
            staff4_lr_margins: list = [10.0, 10.0],
            staff1_range: list or str = 'auto', # list with two values: (lowestnote, highestnote) or string 'auto'
            staff2_range: list or str = 'auto', # ...
            staff3_range: list or str = 'auto',
            staff4_range: list or str = 'auto'
            ):
        '''The linebreak event structure.'''
        return {
            'tag':tag,
            'time':time,
            'staff1':{
                'margins':staff1_lr_margins,
                'range':staff1_range
            },
            'staff2':{
                'margins':staff2_lr_margins,
                'range':staff2_range
            },
            'staff3':{
                'margins':staff3_lr_margins,
                'range':staff3_range
            },
            'staff4':{
                'margins':staff4_lr_margins,
                'range':staff4_range
            }
        }
    
    def new_beam(
            tag: str, # beam+tagnumber to make tag unique
            time: float, # in linear time in pianoticks 0 to infinity
            duration: float, # in linear time in pianoticks 0 to infinity
            hand: str, # 'l' or 'r'
            staff: int, # staff number 0 to 3 there is a total of 4 staffs available
            ):
        '''The beam event structure.'''
        return {
            'tag':tag,
            'time':time,
            'duration':duration,
            'hand':hand,
            'staff':staff
        }
    
    def new_gracenote(
            tag: str, # note+tagnumber to make tag unique
            pitch: int, # piano note number 1 to 88
            time: float, # in linear time in pianoticks 0 to infinity (quarter note == 256)
            hand: str, # 'l' or 'r'
            staff: int, # staff number 0 to 3 there is a total of 4 staffs available
            ):
        '''The note event structure.'''
        return {
            'tag':tag,
            'pitch':pitch,
            'time':time,
            'hand':hand,
            'staff':staff,
        }