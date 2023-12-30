from imports.utils.constants import *
from imports.utils.calctools import CalcTools
from imports.design.note import Note

def tool_note(io, event_type: str, x: int, y: int):
    '''handles the note tool'''

    # left mouse button handling:
    if event_type == 'leftclick':
        io['editnote'] = {
            "tag":"editnote",
            "time":io['calc'].y2tick_editor(y, snap=True),
            "duration":0,
            "pitch":io['calc'].x2pitch_editor(x),
            "hand":io['hand'],
            "stem_visible":True,
            "accidental":0,
            "staff":None,
            "notestop":False,
        }
        Note.draw_editor(io, io['editnote'])

    elif event_type == 'leftclick+move':
        # prevent the note from being too short
        duration = io['calc'].y2tick_editor(y, snap=True) - io['editnote']['time']
        if duration < io['snap_grid']:
            duration = io['snap_grid']
        io['editnote']['duration'] = duration

        # edit the pitch if the mouse is before the start position of the note
        mouse_time = io['calc'].y2tick_editor(y, snap=True)
        if mouse_time < io['editnote']['time']:
            io['editnote']['pitch'] = io['calc'].x2pitch_editor(x)

        # draw the note
        Note.draw_editor(io, io['editnote'])
    
    elif event_type == 'leftrelease':
        # delete the editnote
        io['editor'].delete_with_tag(['editnote'])

        # prevent the note from being too short
        duration = io['calc'].y2tick_editor(y, snap=True) - io['editnote']['time']
        if duration < io['snap_grid']:
            duration = io['snap_grid']
        io['editnote']['duration'] = duration

        # create copy of the editnote, give it a identical tag and add it to the score
        new = io['editnote'].copy()
        new['tag'] = 'note' + str(io['calc'].add_and_return_tag())
        io['score']['events']['note'].append(new)

        # draw the note, redraw the editor
        Note.draw_editor(io, new)
        io['maineditor'].redraw(io)


    # middle mouse button handling:
    elif event_type == 'middleclick':
        ...

    elif event_type == 'middleclick+move':
        ...

    elif event_type == 'middlerelease':
        ...


    # right mouse button handling:
    elif event_type == 'rightclick':
        # find the note that is clicked
        mouse_items = io['editor'].find_items(float(x), float(y), ['note'])
        print(mouse_items)

    elif event_type == 'rightclick+move':
        ...
    
    elif event_type == 'rightrelease':
        ...


    # move mouse handling: (mouse is moved while no button is pressed)
    elif event_type == 'move':
        # draw the note cursor
        io['cursor'] = {
            "tag":"notecursor",
            "time":io['calc'].y2tick_editor(y, snap=True),
            "duration":0,
            "pitch":io['calc'].x2pitch_editor(x),
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
        io['editor'].delete_with_tag(['notecursor'])
    