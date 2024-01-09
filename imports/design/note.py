from imports.utils.constants import *
import copy

class Note:
    '''
        The Note class handles:
            - mouse handling for the note tool in the editor
            - drawing the note in the editor including:
                * notehead
                * stem
                * automatic sounding dot
                * automatic stopsign
            - drawing the note in the engraver (TODO)
    '''

    @staticmethod
    def trashold(x, y):
        return abs(x - y) < EQUALS_TRESHOLD

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the note tool mouse handling'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # delete note cursor
            io['editor'].delete_with_tag(['notecursor'])

            # detect if we clicked on a note
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='note')
            if detect:
                # if we clicked on a note, we want to edit it so we create a copy of the note
                io['editnote'] = detect
            else:
                # we have to create a (new) editnote:
                io['editnote'] = {
                    'tag':'editnote',
                    'time':io['calc'].y2tick_editor(y, snap=True),
                    'duration':io['snap_grid'],
                    'pitch':io['calc'].x2pitch_editor(x),
                    'hand':io['hand'],
                    'stem-visible':True,
                    'accidental':0,
                    'staff':1
                }
                Note.add_editor(io, io['editnote'])
                io['editor'].delete_with_tag(['notecursor'])

        elif event_type == 'leftclick+move':
            # get the mouse position in pianoticks and pitch
            mouse_time = io['calc'].y2tick_editor(y, snap=True, absolute=True)
            mouse_pitch = io['calc'].x2pitch_editor(x)
            note_start = io['editnote']['time']
            note_length = mouse_time - io['editnote']['time']

            # editing rules:
            if mouse_time >= note_start + io['snap_grid']:
                # edit the duration
                io['editnote']['duration'] = note_length
            elif mouse_time < io['editnote']['time']:
                # edit the pitch
                io['editnote']['pitch'] = mouse_pitch

            # draw the note
            Note.add_editor(io, io['editnote'])
        
        elif event_type == 'leftrelease':
            if io['editnote']:
                # delete the editnote
                io['editor'].delete_with_tag([io['editnote']['tag']])

                # delete the note from file
                try: io['score']['events']['note'].remove(io['editnote'])
                except ValueError: pass

                # create copy of the editnote, give it a identical tag and add it to the score
                new = copy.deepcopy(io['editnote'])
                new['tag'] = 'note' + str(io['calc'].add_and_return_tag())
                io['score']['events']['note'].append(new)

                # draw the note, redraw the editor viewport
                io['maineditor'].draw_viewport()

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
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='note')
            if detect:
                # if we clicked on a note, we want to delete it
                Note.delete_editor(io, detect)

        elif event_type == 'rightclick+move':
            ...
        
        elif event_type == 'rightrelease':
            ...


        # move mouse handling: (mouse is moved while no button is pressed)
        elif event_type == 'move':
            # detect if we clicked on a note
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='note')
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
                    'stem-visible':True,
                    'accidental':0,
                    'staff':None,
                    'notestop':False,
                }
            Note.add_editor(io, io['cursor'])

        elif event_type == 'space':
            io['hand'] = 'r' if io['hand'] == 'l' else 'l'
            io['cursor']['hand'] = io['hand']
            Note.add_editor(io, io['cursor'])

        elif event_type == 'leave':
            io['editor'].delete_with_tag(['notecursor'])
    
    
    
    
    








    @staticmethod
    def add_editor(io, note, inselection=False):
        '''
            draws a note on the editor
        '''

        # delete the old note
        io['editor'].delete_with_tag([note['tag']])

        # update drawn object
        try: io['drawn_obj'].remove(note['tag'])
        except ValueError: pass

        # get the x and y position of the note
        x = io['calc'].pitch2x_editor(note['pitch'])
        y = io['calc'].tick2y_editor(note['time'])

        # set colors
        if note['tag'] == 'notecursor' or inselection:
            color = '#009cff' # TODO: set color depending on settings
        else:
            color = '#000000' # TODO: set color depending on settings

        # draw notehead
        unit = STAFF_X_UNIT_EDITOR / 2
        if note['pitch'] in BLACK_KEYS and io['score']['properties']['black-note-style'] == 'PianoScript':
            io['editor'].new_oval(x - (unit * .75),
                                y,
                                x + (unit * .75),
                                y + unit * 2,
                                tag=[note['tag'], 'noteheadblack'],
                                fill_color=color,
                                outline_width=2,
                                outline_color=color)
        elif note['pitch'] in BLACK_KEYS and io['score']['properties']['black-note-style'] == 'Klavarskribo':
            io['editor'].new_oval(x - unit,
                                y - unit * 2,
                                x + unit,
                                y,
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
        if io['score']['properties']['black-note-style'] == 'PianoScript':
            yy = y + unit
        else:
            yy = y - unit
        if note['hand'] == 'l' and note['pitch'] in BLACK_KEYS:
            radius = (unit * .5) / 2
            io['editor'].new_oval(x - radius,
                                yy - radius,
                                x + radius,
                                yy + radius,
                                tag=[note['tag'], 'leftdotblack'],
                                fill_color='white',
                                outline_width=1,
                                outline_color='white')
        elif note['hand'] == 'l' and note['pitch'] not in BLACK_KEYS: # white note
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
        thickness = 5
        if note['hand'] == 'l' and note['stem-visible']:
            io['editor'].new_line(x, y, x - (unit * 5), y,
                                tag=[note['tag'], 'stem'],
                                width=thickness,
                                color=color)
        elif note['hand'] == 'r' and note['stem-visible']:
            io['editor'].new_line(x, y, x + (unit * 5), y,
                                tag=[note['tag'], 'stem'],
                                width=thickness,
                                color=color)
            
        # draw the midi note
        if note['tag'] == 'editnote':
            midicolor = '#ccc'
        elif inselection:# if note is in selection
            midicolor = '#009cff'
        else:# if normal note
            midicolor = '#eee'
        endy = io['calc'].tick2y_editor(note['time'] + note['duration'])

        io['editor'].new_polygon([(x, y), (x + unit, y + (unit/2)), (x + unit, endy), (x - unit, endy), (x - unit, y + (unit/2))],
                                tag=[note['tag'], 'midinote'], 
                                fill_color=midicolor, 
                                outline_color='')
        
        # draw the sounding dot
        def sounding_dot(x, y, n=None):
            if n:
                tag = [n['tag'], note['tag'], 'soundingdot']
            else:
                tag = [note['tag'], 'soundingdot']

            io['editor'].new_oval(x-(STAFF_X_UNIT_EDITOR/4),y+(STAFF_X_UNIT_EDITOR /4),
                x+(STAFF_X_UNIT_EDITOR/4),y+(STAFF_X_UNIT_EDITOR/4*3),
                outline_color='black',
                fill_color='#000000',
                tag=tag)
        
        barline_times = io['calc'].get_barline_ticks()
        # if note is sounding at the barline time we need always to draw a continuation dot
        for bl_time in barline_times:
            if LESS(note['time'], bl_time) and GREATER(note['time']+note['duration'], bl_time):
                x = io['calc'].pitch2x_editor(note['pitch'])
                y = io['calc'].tick2y_editor(bl_time)
                io['editor'].delete_if_with_all_tags([note['tag'], 'soundingdot'])
                sounding_dot(x, y)
                
        # now we need to loop through all notes to see if we need to draw a continuation dot or a notestop sign
        stopflag = True
        for n in io['score']['events']['note']: # N == THE COMPARED NOTE
            # connect chords (if two or more notes start at the same time)
            if note['hand'] == n['hand'] and n['time'] == note['time'] and not note['tag'] == 'notecursor':
                x1 = io['calc'].pitch2x_editor(note['pitch'])
                x2 = io['calc'].pitch2x_editor(n['pitch'])
                y = io['calc'].tick2y_editor(note['time'])
                io['editor'].new_line(x1,y,x2,y,
                    tag=[n['tag'], note['tag'], 'connectstem'],
                    width=5,
                    color='black')
            
            # continuation dot:
            # there are 5 possible situations where we have to draw a continuation dot:
            comp_start = n['time']
            comp_end = n['time']+n['duration']
            note_start = note['time']
            note_end = note['time']+note['duration']

            if not note['tag'] == 'notecursor':
                if GREATER(comp_end, note_start) and LESS(comp_end, note_end) and note['hand'] == n['hand']: # GREATER, LESS and EQUALS are defined in constants.py and applies a treshold to the comparison
                    x = io['calc'].pitch2x_editor(note['pitch'])
                    y = io['calc'].tick2y_editor(n['time']+n['duration'])
                    sounding_dot(x, y, n)

                if LESS(note_end, comp_end) and GREATER(note_end, comp_start) and note['hand'] == n['hand']:
                    x = io['calc'].pitch2x_editor(n['pitch'])
                    y = io['calc'].tick2y_editor(note['time']+note['duration'])
                    sounding_dot(x, y, n)

                if GREATER(note_start, comp_start) and LESS(note_start, comp_end) and note['hand'] == n['hand']:
                    x = io['calc'].pitch2x_editor(n['pitch'])
                    y = io['calc'].tick2y_editor(note['time'])
                    sounding_dot(x, y, n)

                if GREATER(comp_start, note_start) and LESS(comp_start, note_end) and note['hand'] == n['hand']:
                    x = io['calc'].pitch2x_editor(note['pitch'])
                    y = io['calc'].tick2y_editor(n['time'])
                    sounding_dot(x, y, n)

            # stop sign
            if EQUALS(comp_start, note_end) and note['hand'] == n['hand']:
                stopflag = False

            # delete notestop sign if the new note starts at the same time as the end time of another note
            if EQUALS(comp_end, note_start) and note['hand'] == n['hand'] and not note['tag'] == 'notecursor':
                io['editor'].delete_if_with_all_tags([n['tag'], 'notestop'])
        
        if stopflag and not note['tag'] == 'notecursor':
            # draw the notestop sign
            x = io['calc'].pitch2x_editor(note['pitch'])
            y = io['calc'].tick2y_editor(note['time']+note['duration'])
            io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR/2), y-(STAFF_X_UNIT_EDITOR),
                x, y,
                tag=[note['tag'], 'notestop'],
                width=2,
                color='black')
            io['editor'].new_line(x, y,
                x+(STAFF_X_UNIT_EDITOR/2), y-(STAFF_X_UNIT_EDITOR),
                tag=[note['tag'], 'notestop'],
                width=2,
                color='black')
            

    def delete_editor(io, note):
        '''deletes a note'''
        
        # delete from file and editor
        io['score']['events']['note'].remove(note)
        io['editor'].delete_with_tag([note['tag']])
        if note['tag'] in io['drawn_obj']:
            io['drawn_obj'].remove(note['tag'])
        
        # check for notes to be drawn again for correcting the stop sign
        for n in io['score']['events']['note']:
            if EQUALS(n['time']+n['duration'], note['time']) and n['hand'] == note['hand']:
                Note.add_editor(io, n)
            

    @staticmethod
    def draw_engraver(io, note):
        # Code to draw the note in the engraver view
        ...