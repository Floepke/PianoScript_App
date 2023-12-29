from imports.utils.constants import *
from imports.utils.calctools import CalcTools
from imports.design.note import Note

def tool_note(io, event_type: str, x: int, y: int):
    '''handles the note tool'''

    # left mouse button handling:
    if event_type == 'leftclick':
        ...

    elif event_type == 'leftclick+hold':
        ...
    
    elif event_type == 'leftrelease':
        ...

    # middle mouse button handling:
    elif event_type == 'middleclick':
        ...

    elif event_type == 'middleclick+hold':
        ...

    elif event_type == 'middlerelease':
        ...

    # right mouse button handling:
    elif event_type == 'rightclick':
        ...

    elif event_type == 'rightclick+hold':
        ...
    
    elif event_type == 'rightrelease':
        ...

    # move mouse handling: (mouse is moved while no button is pressed)
    elif event_type == 'move':
        # draw the note cursor
        cursor = {
            "tag":"notecursor",
            "time":io['calctools'].y2tick_editor(y, snap=True),
            "duration":0,
            "pitch":io['calctools'].x2pitch_editor(x),
            "hand":"r",
            "stem_visible":True,
            "accidental":0,
            "staff":None,
            "notestop":False,
        }

        # draw the note cursor on the editor
        Note.draw_editor(io, cursor)

    