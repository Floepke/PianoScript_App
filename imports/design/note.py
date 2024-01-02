from imports.utils.constants import *

class Note:
    '''
        The Note class handles:
            - mouse handling for the note tool in the editor
            - drawing the note in the editor (design)
            - drawing the note in the engraver (design)
    '''

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the note tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # delete note cursor
            io['editor'].delete_with_tag(['notecursor'])

            # detect if we clicked on a note
            detect = io['editor'].detect_object(io['score'], float(x), float(y), object_type='note')
            if detect:
                # if we clicked on a note, we want to edit it
                io['editnote'] = detect
            else:
                # we have to create a new note:
                io['editnote'] = {
                    'tag':'editnote',
                    'time':io['calc'].y2tick_editor(y, snap=True),
                    'duration':0,
                    'pitch':io['calc'].x2pitch_editor(x),
                    'hand':io['hand'],
                    'stem_visible':True,
                    'accidental':0,
                    'staff':1
                }
                Note.draw_editor(io, io['editnote'])
                io['editor'].delete_with_tag(['notecursor'])

        elif event_type == 'leftclick+move':
            # prevent the note from being too short
            duration = io['calc'].y2tick_editor(y, snap=True) - io['editnote']['time']
            if duration < io['snap_grid']:
                duration = io['snap_grid']
            io['editnote']['duration'] = duration

            # edit the pitch if the mouse is before the start position of the note
            mouse_time = io['calc'].y2tick_editor(y, snap=False)
            if mouse_time <= io['editnote']['time']:
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
            io['maineditor'].draw_viewport(io)

            # delete the editnote
            io['editnote'] = None


        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...


        # right mouse button handling:
        elif event_type == 'rightclick':
            # detect if we clicked on a note
            detect = io['editor'].detect_object(io['score'], float(x), float(y), object_type='note')
            if detect:
                # if we clicked on a note, we want to delete it
                io['score']['events']['note'].remove(detect)
                io['editor'].delete_with_tag([detect['tag']])
                io['maineditor'].draw_viewport(io)

        elif event_type == 'rightclick+move':
            ...
        
        elif event_type == 'rightrelease':
            ...


        # move mouse handling: (mouse is moved while no button is pressed)
        elif event_type == 'move':
            # detect if we clicked on a note
            detect = io['editor'].detect_object(io['score'], float(x), float(y), object_type='note')
            if detect:
                # note cursor on detected note position
                io['cursor'] = detect.copy()
                io['cursor']['tag'] = 'notecursor'
            else:
                # note cursor on mouse position
                io['cursor'] = {
                    'tag':'notecursor',
                    'time':io['calc'].y2tick_editor(y, snap=True),
                    'duration':0,
                    'pitch':io['calc'].x2pitch_editor(x),
                    'hand':'r' if io['hand'] == 'r' else 'l',
                    'stem_visible':True,
                    'accidental':0,
                    'staff':None,
                    'notestop':False,
                }
            Note.draw_editor(io, io['cursor'])

        elif event_type == 'space':
            io['hand'] = 'r' if io['hand'] == 'l' else 'l'
            io['cursor']['hand'] = io['hand']
            Note.draw_editor(io, io['cursor'])

        elif event_type == 'leave':
            io['editor'].delete_with_tag(['notecursor'])
    
    @staticmethod
    def draw_editor(io, note, inselection=False):
        # delete the old note
        io['editor'].delete_with_tag([note['tag']])

        # get the x and y position of the note
        x = io['calc'].pitch2x_editor(note['pitch'])
        y = io['calc'].tick2y_editor(note['time'])

        # set colors
        if note['tag'] == 'notecursor' or inselection:
            color = '#009cff' # TODO: set color depending on settings
        else:
            color = 'black' # TODO: set color depending on settings

        # draw the notehead
        unit = STAFF_X_UNIT_EDITOR / 2
        thickness = 5
        if note['pitch'] in BLACK_KEYS:
            io['editor'].new_oval(x - (unit * .75),
                                y,
                                x + (unit * .75),
                                y + unit * 2,
                                tag=[note['tag'], 'noteheadblack'],
                                fill_color=color,
                                outline_width=2,
                                outline_color=color)
        else:
            io['editor'].new_oval(x - unit,
                                y,
                                x + unit,
                                y + unit * 2,
                                tag=[note['tag'], 'noteheadwhite'],
                                fill_color='white',
                                outline_width=2,
                                outline_color=color)
        
        # draw the left dot
        if note['hand'] == 'l' and note['pitch'] in BLACK_KEYS:
            yy = y + unit
            radius = (unit * .5) / 2
            io['editor'].new_oval(x - radius,
                                yy - radius,
                                x + radius,
                                yy + radius,
                                tag=[note['tag'], 'leftdotblack'],
                                fill_color='white',
                                outline_width=1,
                                outline_color='white')
        elif note['hand'] == 'l' and note['pitch'] not in BLACK_KEYS:
            yy = y + unit
            radius = (unit * .5) / 2
            io['editor'].new_oval(x - radius,
                                yy - radius,
                                x + radius,
                                yy + radius,
                                tag=[note['tag'], 'leftdotwhite'],
                                fill_color=color,
                                outline_width=1,
                                outline_color=color)
            
        # draw the stem
        if note['hand'] == 'l' and note['stem_visible']:
            io['editor'].new_line(x, y, x - (unit * 5), y,
                                tag=[note['tag'], 'stem'],
                                width=thickness,
                                color=color)
        elif note['hand'] == 'r' and note['stem_visible']:
            io['editor'].new_line(x, y, x + (unit * 5), y,
                                tag=[note['tag'], 'stem'],
                                width=thickness,
                                color=color)
            
        # draw the midi note
        if note['tag'] != 'notecursor':
            if not inselection:
                color = '#bbbbbb'
            endy = io['calc'].tick2y_editor(note['time'] + note['duration'])
            io['editor'].new_polygon([(x, y), (x + unit, y + (unit/2)), (x + unit, endy), (x - unit, endy), (x - unit, y + (unit/2))],
                                    tag=[note['tag'], 'midinote'], 
                                    fill_color=color, 
                                    width=0,
                                    outline_color=color)
            

    @staticmethod
    def draw_engraver(io, note):
        # Code to draw the note in the engraver view
        ...
