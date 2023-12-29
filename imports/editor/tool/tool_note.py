from imports.utils.constants import *
from imports.utils.calctools import CalcTools
from imports.design.note import Note

def tool_note(io, event_type: str, x: int, y: int):
    '''handles the note tool'''

    # left mouse button handling:
    if event_type == 'leftclick':
        io['editnote'] = {
            "tag":"editnote",
            "time":io['calctools'].y2tick_editor(y, snap=True),
            "duration":0,
            "pitch":io['calctools'].x2pitch_editor(x),
            "hand":io['hand'],
            "stem_visible":True,
            "accidental":0,
            "staff":None,
            "notestop":False,
        }
        Note.draw_editor(io, io['editnote'])

    elif event_type == 'leftclick+hold':
        io['editnote']['duration'] = io['calctools'].y2tick_editor(y, snap=True) - io['editnote']['time']
        Note.draw_editor(io, io['editnote'])
    
    elif event_type == 'leftrelease':
        io['editnote']['duration'] = io['calctools'].y2tick_editor(y, snap=True) - io['editnote']['time']
        io['score']['events']['note'].append(io['editnote'])
        io['editor'].delete_with_tag('editnote')
        io['maineditor'].redraw(io)

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
        io['cursor'] = {
            "tag":"notecursor",
            "time":io['calctools'].y2tick_editor(y, snap=True),
            "duration":0,
            "pitch":io['calctools'].x2pitch_editor(x),
            "hand":"r" if io['hand'] == 'r' else 'l',
            "stem_visible":True,
            "accidental":0,
            "staff":None,
            "notestop":False,
        }
        Note.draw_editor(io, io['cursor'])

    elif event_type == 'space':
        io['hand'] = 'r' if io['hand'] == 'l' else 'l'
        io['cursor']['hand'] = io['hand']
        Note.draw_editor(io, io['cursor'])

    elif event_type == 'leave':
        io['editor'].delete_with_tag('notecursor')
    