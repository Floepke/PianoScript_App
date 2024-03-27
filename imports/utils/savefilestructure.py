

class SaveFileStructureSource:
    '''
        Stores all event types standard json structures for saving 
        to a score file or creating new messages from. That way we 
        can add new preferences to for example new_note() and change 
        that only in this file.
    '''

    def __init__(self, io):

        self.io = io

    def new_events_folder():
        '''returns the structure of the events folder in a score file'''
        return {
            'note': [],
            'linebreak': [],
            'gracenote': [],
            'text': [],
            'beam': [],
            'slur': [],
            'pedal': [],
            'countline': [],
            'startrepeat': [],
            'endrepeat': [],
            'starthook': [],
            'endhook': [],
            'stop': [],
            'dot': [],
        }

    def new_events_folder_viewport():
        '''returns the structure of the events folder in a score file'''
        return {
            'note': [],
            'linebreak': [],
            'gracenote': [],
            'text': [],
            'beam': [],
            'slur': [],
            'pedal': [],
            'countline': [],
            'startrepeat': [],
            'endrepeat': [],
            'starthook': [],
            'endhook': [],
            'dot': [],
            'stop': [],
        }

    def new_note(
            tag: str,  # note+tagnumber to make tag unique
            pitch: int = 40,  # piano note number 1 to 88
            # in linear time in pianoticks 0 to infinity (quarter note == 256)
            time: float = 0,
            duration: float = 256,  # in linear time in pianoticks 0 to infinity
            hand: str = 'l',  # 'l' or 'r'
            staff: int = 0,  # staff number 0 to 3 there is a total of 4 staffs available
            attached: str = '',  # possible are the following symbols in any order: '>' = accent, '.' = staccato, '-' = tenuto, 'v' = staccatissimo, '#' = sharp, 'b' = flat, '^' = marcato
            track: int = 0  # track number
    ):
        '''The note event structure.'''
        return {
            'tag': tag,
            'pitch': pitch,
            'time': time,
            'duration': duration,
            'hand': hand,
            'staff': staff,
            'attached': attached,
            'track': track
        }

    def new_grid(
            amount: int = 8,  # amount of measures to repeat
            numerator: int = 4,  # numerator of the grid
            denominator: int = 4,  # denominator of the grid
            grid: list = [256, 512, 768],  # list of ticks relative to the start of every measure. every tick is a gridline
            # are the stafflines and the gridlines visible if False in the editor the background is redish
            visible: bool = True,
    ):
        '''The grid event structure.'''
        return {
            'tag': 'grid',
            'amount': amount,
            'numerator': numerator,
            'denominator': denominator,
            'grid': grid,
            'visible': visible
        }

    def new_countline(
            tag: str,  # countline+tagnumber to make tag unique
            time: float = 0,  # in linear time in pianoticks 0 to infinity
            pitch1: int = 40,  # piano note number 1 to 88
            pitch2: int = 44,  # piano note number 1 to 88
            staff: int = 0,  # staff number 0 to 3 there is a total of 4 staffs available
    ):
        '''The countline event structure.'''
        return {
            'tag': tag,
            'time': time,
            'pitch1': pitch1,
            'pitch2': pitch2,
            'staff': staff
        }

    def new_linebreak(
            tag: str,  # linebreak+tagnumber to make tag unique
            time: float = 0,  # in linear time in pianoticks 0 to infinity
            # list with two values: (leftmargin, rightmargin) in mm
            staff1_lr_margins: list = [10.0, 10.0],
            staff2_lr_margins: list = [10.0, 10.0],  # ...
            staff3_lr_margins: list = [10.0, 10.0],
            staff4_lr_margins: list = [10.0, 10.0],
            # list with two values: (lowestnote, highestnote) or string 'auto'
            staff1_range: list or str = 'auto',
            staff2_range: list or str = 'auto',  # ...
            staff3_range: list or str = 'auto',
            staff4_range: list or str = 'auto'
    ):
        '''The linebreak event structure.'''
        return {
            'tag': tag,
            'time': time,
            'staff1': {
                'margins': staff1_lr_margins,
                'range': staff1_range
            },
            'staff2': {
                'margins': staff2_lr_margins,
                'range': staff2_range
            },
            'staff3': {
                'margins': staff3_lr_margins,
                'range': staff3_range
            },
            'staff4': {
                'margins': staff4_lr_margins,
                'range': staff4_range
            }
        }

    def new_beam(
            tag: str,  # beam+tagnumber to make tag unique
            time: float = 0,  # in linear time in pianoticks 0 to infinity
            duration: float = 256,  # in linear time in pianoticks 0 to infinity
            hand: str = 'l',  # 'l' or 'r'
            staff: int = 0,  # staff number 0 to 3 there is a total of 4 staffs available
    ):
        '''The beam event structure.'''
        return {
            'tag': tag,
            'time': time,
            'duration': duration,
            'hand': hand,
            'staff': staff
        }

    def new_gracenote(
            tag: str,  # note+tagnumber to make tag unique
            pitch: int = 40,  # piano note number 1 to 88
            # in linear time in pianoticks 0 to infinity (quarter note == 256)
            time: float = 0,
            hand: str = 'l',  # 'l' or 'r'
            staff: int = 0,  # staff number 0 to 3 there is a total of 4 staffs available
    ):
        '''The gracenote event structure.'''
        return {
            'tag': tag,
            'pitch': pitch,
            'time': time,
            'hand': hand,
            'staff': staff,
        }

    def new_text(
            tag: str,  # text+tagnumber to make tag unique
            text: str = 'text',  # text
            time: float = 0,  # in linear time in pianoticks 0 to infinity
            pitch: int = 40,  # piano note number 1 to 88
            font: str = 'Edwin',  # font
            font_size: int = 16,  # size
            staff: int = 0,  # staff number 0 to 3 there is a total of 4 staffs available
    ):
        '''The text event structure.'''
        return {
            'tag': tag,
            'text': text,
            'time': time,
            'pitch': pitch,
            'staff': staff
        }
    
