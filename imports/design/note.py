from imports.utils.constants import *
import copy
from imports.utils.savefilestructure import SaveFileStructureSource

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
                Note.delete_editor(io, detect)
                io['edit_obj'] = copy.deepcopy(detect)
                io['edit_obj']['hand'] = io['hand']
                io['edit_obj']['tag'] = 'edit_obj'
            else:
                # we have to create a (new) edit_obj:
                io['edit_obj'] = SaveFileStructureSource.new_note(
                    tag='edit_obj',
                    time=io['calc'].y2tick_editor(y, snap=True),
                    duration=io['snap_grid'],
                    pitch=io['calc'].x2pitch_editor(x),
                    hand=io['hand'],
                    staff=0,
                    attached=''
                )
                Note.draw_editor(io, io['edit_obj'])
                io['editor'].delete_with_tag(['notecursor'])

        elif event_type == 'leftclick+move':
            # get the mouse position in pianoticks and pitch
            mouse_time = io['calc'].y2tick_editor(y, snap=True, absolute=True)
            mouse_pitch = io['calc'].x2pitch_editor(x)
            note_start = io['edit_obj']['time']
            note_length = mouse_time - io['edit_obj']['time']

            # editing rules:
            if not LESS(mouse_time, note_start + io['snap_grid']):
                # edit the duration
                io['edit_obj']['duration'] = note_length
            elif mouse_time < io['edit_obj']['time']:
                # edit the pitch
                io['edit_obj']['pitch'] = mouse_pitch

            # draw the note
            Note.draw_editor(io, io['edit_obj'])
        
        elif event_type == 'leftrelease':
            if io['edit_obj']:
                # delete the edit_obj
                io['editor'].delete_with_tag([io['edit_obj']['tag']])

                # delete the note from file
                try: io['score']['events']['note'].remove(io['edit_obj']) 
                except ValueError: pass

                # create copy of the edit_obj, give it a identical tag and add it to the score
                new = copy.deepcopy(io['edit_obj'])
                new['tag'] = 'note' + str(io['calc'].add_and_return_tag())
                io['score']['events']['note'].append(new)

                # draw the note, redraw the editor viewport
                io['maineditor'].draw_viewport()

                # delete the edit_obj
                io['edit_obj'] = None


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
            # # detect if we clicked on a note
            # detect = io['editor'].detect_item(io, float(x), float(y), event_type='note')
            # if detect:
            #     # note cursor on detected note position
            #     io['cursor'] = detect.copy()
            #     io['cursor']['tag'] = 'notecursor'
            # else:
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
            Note.draw_editor(io, io['cursor'])

        elif event_type == 'space':
            io['hand'] = 'r' if io['hand'] == 'l' else 'l'
            io['cursor']['hand'] = io['hand']
            Note.draw_editor(io, io['cursor'])

        elif event_type == 'leave':
            io['editor'].delete_with_tag(['notecursor'])
    
    
    
    
    








    @staticmethod
    def draw_editor(io, note, inselection=False, noteheadup=False):
        '''
            draws a note on the editor
        '''

        # delete the old note
        io['editor'].delete_with_tag([note['tag']])

        # update drawn object
        if note in io['viewport']['events']['note']: 
            io['viewport']['events']['note'].remove(note)

        # get the x and y position of the note
        x = io['calc'].pitch2x_editor(note['pitch'])
        y = io['calc'].tick2y_editor(note['time'])

        # set colors
        if note['tag'] == 'notecursor' or inselection:
            color = '#009cff' # TODO: set color depending on settings
        else:
            color = '#000000' # TODO: set color depending on settings

        unit = STAFF_X_UNIT_EDITOR / 2
            
        # draw the stem
        thickness = 5
        if note['hand'] == 'l':
            io['editor'].new_line(x, y, x - (unit * 5), y,
                                tag=[note['tag'], 'stem'],
                                width=thickness,
                                color=color)
        elif note['hand'] == 'r':
            io['editor'].new_line(x, y, x + (unit * 5), y,
                                tag=[note['tag'], 'stem'],
                                width=thickness,
                                color=color)
            
        # draw the midi note
        if note['tag'] == 'edit_obj':
            midicolor = '#aa0'
        elif inselection:# if note is in selection
            midicolor = '#009cff'
        else:# if normal note
            midicolor = '#bbb'
        endy = io['calc'].tick2y_editor(note['time'] + note['duration'])

        io['editor'].new_polygon([(x, y), 
                                  (x + unit, y + (unit/2)), 
                                  (x + unit, endy), (x - unit, endy), 
                                  (x - unit, y + (unit/2))],
                                  tag=[note['tag'], 'midinote'], 
                                  fill_color=midicolor, 
                                  outline_color='')
        
        # # draw the sounding dot
        # def sounding_dot(x, y, n=None, fcolor='black'):
        #     if n:
        #         tag = [n['tag'], note['tag'], 'soundingdot']
        #     else:
        #         tag = [note['tag'], 'soundingdot']
        #     if io['score']['properties']['continuation_dot_style'] == 'Klavarskribo':
        #         # Klavarskribo continuation dot
        #         io['editor'].new_oval(x-(STAFF_X_UNIT_EDITOR/4),y+(STAFF_X_UNIT_EDITOR /4),
        #             x+(STAFF_X_UNIT_EDITOR/4),y+(STAFF_X_UNIT_EDITOR/4*3),
        #             outline_color='black',
        #             fill_color='#000000',
        #             tag=tag)
        #     elif io['score']['properties']['continuation_dot_style'] == 'PianoScript':
        #         # experimantal continuation symbol
        #         points = [(x-unit,y), (x,y+unit+unit), (x+unit,y)]
        #         io['editor'].new_polygon(points, fill_color='black', outline_color='', tag=tag)
        #     io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR), y, x+(STAFF_X_UNIT_EDITOR), y,
        #             tag=tag,
        #             width=.75,
        #             dash=[3, 3],
        #             color=color)

        # barline_times = io['calc'].get_barline_ticks()
        # # if note is sounding at the barline time we need always to draw a continuation dot
        # for bl_time in barline_times:
        #     if LESS(note['time'], bl_time) and GREATER(note['time']+note['duration'], bl_time):
        #         x = io['calc'].pitch2x_editor(note['pitch'])
        #         y = io['calc'].tick2y_editor(bl_time)
        #         io['editor'].delete_if_with_all_tags([note['tag'], 'soundingdot'])
        #         if note['pitch'] in BLACK_KEYS:
        #             sounding_dot(x, y, fcolor='black')
        #         else:
        #             sounding_dot(x, y, fcolor='white')

        # now we need to loop through all notes to see if we need to draw a continuation dot or a notestop sign
        stopflag = True
        noteheadupdownflag = False
        note_start = note['time']
        note_end = note['time']+note['duration']
        # for n in io['score']['events']['note']: # N == THE COMPARED NOTE TODO: change folder structure in measures
        #     # connect chords (if two or more notes start at the same time)
        #     if note['hand'] == n['hand'] and n['time'] == note['time'] and not note['tag'] == 'notecursor':
        #         x1 = io['calc'].pitch2x_editor(note['pitch'])
        #         x2 = io['calc'].pitch2x_editor(n['pitch'])
        #         y = io['calc'].tick2y_editor(note['time'])
        #         io['editor'].new_line(x1,y,x2,y,
        #             tag=[n['tag'], note['tag'], 'connectstem'],
        #             width=5,
        #             color='black')
            
        #     continuation dot:
        #     there are 5 possible situations where we have to draw a continuation dot
        #     if we draw one, we have also to check if this continuation dot is on the 
        #     same hand as the note and if the pitch is one semitone higher or lower, 
        #     so that we can draw the notehead upwards further in the code.
        #     comp_start = n['time']
        #     comp_end = n['time']+n['duration']
        #     # GREATER, LESS and EQUALS are defined in constants.py and applies a small treshold to the comparison
        #     if not note['tag'] == 'notecursor':
        #         if GREATER(comp_end, note_start) and LESS(comp_end, note_end) and note['hand'] == n['hand']: 
        #             x = io['calc'].pitch2x_editor(note['pitch'])
        #             y = io['calc'].tick2y_editor(n['time']+n['duration'])
        #             sounding_dot(x, y, n)

        #         if LESS(note_end, comp_end) and GREATER(note_end, comp_start) and note['hand'] == n['hand']:
        #             x = io['calc'].pitch2x_editor(n['pitch'])
        #             y = io['calc'].tick2y_editor(note['time']+note['duration'])
        #             sounding_dot(x, y, n)

        #         if GREATER(note_start, comp_start) and LESS(note_start, comp_end) and note['hand'] == n['hand']:
        #             x = io['calc'].pitch2x_editor(n['pitch'])
        #             y = io['calc'].tick2y_editor(note['time'])
        #             sounding_dot(x, y, n)

        #         if GREATER(comp_start, note_start) and LESS(comp_start, note_end) and note['hand'] == n['hand']:
        #             x = io['calc'].pitch2x_editor(note['pitch'])
        #             y = io['calc'].tick2y_editor(n['time'])
        #             sounding_dot(x, y, n)
                
        #         if note['pitch'] in [n['pitch']-1, n['pitch']+1] and not noteheadup:
        #             # check if n is sounding at note start time or note start == n start time
        #             if GREATER(note_start, comp_start) and LESS(note_start, comp_end) or EQUALS(note_start, comp_start):
        #                 noteheadup = True
        #                 if n['pitch'] in BLACK_KEYS:
        #                     try: io['drawn_obj'].remove(n['tag'])
        #                     except: ...

        #     # stop sign desicion:
        #     if EQUALS(comp_start, note_end) and note['hand'] == n['hand']:
        #         stopflag = False

        #     # delete notestop sign if the new note starts at the same time as the end time of another note
        #     if EQUALS(comp_end, note_start) and note['hand'] == n['hand'] and not note['tag'] == 'notecursor':
        #         io['editor'].delete_if_with_all_tags([n['tag'], 'notestop'])
        
        # # notestop sign:
        # if stopflag and not note['tag'] == 'notecursor':
        #     x = io['calc'].pitch2x_editor(note['pitch'])
        #     y = io['calc'].tick2y_editor(note['time']+note['duration'])

        #     if io['score']['properties']['stop_sign_style'] == 'Klavarskribo':
        #         # traditional stop sign:
        #         io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR/2), y-(STAFF_X_UNIT_EDITOR),
        #             x, y,
        #             tag=[note['tag'], 'notestop'],
        #             width=2,
        #             color=color)
        #         io['editor'].new_line(x, y,
        #             x+(STAFF_X_UNIT_EDITOR/2), y-(STAFF_X_UNIT_EDITOR),
        #             tag=[note['tag'], 'notestop'],
        #             width=2,
        #             color=color)
        #     elif io['score']['properties']['stop_sign_style'] == 'PianoScript':
        #         # experimental stopsign:
        #         points = [(x, y-(STAFF_X_UNIT_EDITOR)), (x+(STAFF_X_UNIT_EDITOR/2), y), (x-(STAFF_X_UNIT_EDITOR/2), y)]
        #         io['editor'].new_polygon(points,
        #             tag=[note['tag'], 'notestop'],
        #             width=0,
        #             fill_color=color)
        #     io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR), y, x+(STAFF_X_UNIT_EDITOR), y,
        #         tag=[note['tag'], 'notestop'],
        #         width=.75,
        #         dash=[3, 3],
        #         color=color)
        
        # draw notehead
        x = io['calc'].pitch2x_editor(note['pitch'])
        y = io['calc'].tick2y_editor(note['time'])
        if note['pitch'] in BLACK_KEYS and not noteheadup:
            # draw the black notehead down
            io['editor'].new_oval(x - (unit * .75),
                                y,
                                x + (unit * .75),
                                y + unit * 2,
                                tag=[note['tag'], 'noteheadblack'],
                                fill_color=color,
                                outline_width=2,
                                outline_color=color)
        elif note['pitch'] in BLACK_KEYS and noteheadup:
            # draw the black notehead up
            io['editor'].new_oval(x - (unit * .75), 
                                y - unit * 2,
                                x + (unit * .75),
                                y,
                                tag=[note['tag'], 'noteheadblack'],
                                fill_color=color,
                                outline_width=2,
                                outline_color=color)
        else:
            # draw the white notehead always down
            io['editor'].new_oval(x - unit,
                                y,
                                x + unit,
                                y + unit * 2,
                                tag=[note['tag'], 'noteheadwhite'],
                                fill_color='white',
                                outline_width=2,
                                outline_color=color)

        # draw left dot 
        yy = y + unit
        if noteheadup:
            # draw up
            yy = y - unit
        if note['hand'] == 'l' and note['pitch'] in BLACK_KEYS: # black note left dot
            radius = (unit * .5) / 2
            io['editor'].new_oval(x - radius,
                                yy - radius,
                                x + radius,
                                yy + radius,
                                tag=[note['tag'], 'leftdotblack'],
                                fill_color='white',
                                outline_width=1,
                                outline_color='white')
        elif note['hand'] == 'l' and note['pitch'] not in BLACK_KEYS: # white note left dot
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
            

    def delete_editor(io, note):
        '''deletes a note'''
        
        # delete from file and editor
        io['score']['events']['note'].remove(note)
        if note in io['viewport']['events']['note']:
            io['viewport']['events']['note'].remove(note)
        io['editor'].delete_with_tag([note['tag']])
        
        # # check for notes to be drawn again for correcting the stop sign
        # note_start = note['time']
        # note_end = note['time']+note['duration']
        # for n in io['viewport']['events']['note']: #TODO: change folder structure in measures
        #     comp_start = n['time']
        #     comp_end = n['time']+n['duration']

        #     if EQUALS(n['time']+n['duration'], note['time']) and n['hand'] == note['hand']:
        #         if n['tag'] in io['drawn_obj']: 
        #             io['drawn_obj'].remove(n['tag'])
        #         io['viewport']['events']['note'].remove(n)

        #     # check if there is another note thats one semitone hgher or lower then the removed
        #     if note['pitch'] in [n['pitch']-1, n['pitch']+1] and n['pitch'] in BLACK_KEYS:
        #         # check if start of the note is in between a note
        #         if GREATER(note_start, comp_start) and LESS(note_start, comp_end):
        #             if note['tag'] in io['drawn_obj']: 
        #                 io['drawn_obj'].remove(n['tag']) # redraw this note
        #             io['viewport']['events']['note'].remove(n)
                
        #         # check if note start is equal to the removed note
        #         if EQUALS(note_start, comp_start):
        #             if note['tag'] in io['drawn_obj']: 
        #                 io['drawn_obj'].remove(n['tag']) # redraw ...
        #             io['viewport']['events']['note'].remove(n)
        
        # io['maineditor'].draw_viewport()
            













    @staticmethod
    def draw_engraver(io, note):

        ...




















































