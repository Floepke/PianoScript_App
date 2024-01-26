'''
    In this file we dump all the calculations for the engraver.
    Like the calctools.py it stores all solutions to little 
    problems but for the engraver.
'''
from imports.utils.constants import *

def note_processor(io, note):
    '''
        note_processor processes the notes in such way that it generates a list of neccesary 
        note, notesplit, continuationdot, notestop events that are ready for being drawn.
    '''

    # the output list of draw events
    output = []

    # variables for calculations
    unit = STAFF_X_UNIT_EDITOR / 2
    color = '#000000'
    note_start = note['time']
    note_end = note['time']+note['duration']
    stopflag = True

    # add the continuation dot
    def continuation_dot(time, pitch):
        dot = {
            'time':time,
            'pitch':pitch,
            'type':'continuationdot',
            'staff':note['staff']
        }
        output.append(dot)
    
    def stop_sign(time, pitch):
        stop = {
            'time':time,
            'pitch':pitch,
            'type':'notestop',
            'staff': note['staff']
        }
        output.append(stop)

    for n in io['score']['events']['note']: # N == THE COMPARED NOTE TODO: change folder structure in measures
        # connect chords (if two or more notes start at the same time)
        if note['hand'] == n['hand'] and EQUALS(n['time'], note['time']):
            connect = {
                'time':n['time'],
                'pitch':n['pitch'],
                'time2':note['time'],
                'pitch2':note['pitch'],
                'type':'connectstem',
                'staff':n['staff']
            }
            output.append(connect)
        
        # continuation dot:
        # there are 5 possible situations where we have to draw a continuation dot
        # if we draw one, we have also to check if this continuation dot is on the 
        # same hand as the note and if the pitch is one semitone higher or lower, 
        # so that we can draw the notehead upwards further in the code.
        comp_start = n['time']
        comp_end = n['time']+n['duration']
        # GREATER, LESS and EQUALS are defined in constants.py and applies a small treshold to the comparison
        if GREATER(comp_end, note_start) and LESS(comp_end, note_end) and note['hand'] == n['hand']:
            continuation_dot(n['time']+n['duration'], note['pitch'])

        if LESS(note_end, comp_end) and GREATER(note_end, comp_start) and note['hand'] == n['hand']:
            continuation_dot(note['time']+note['duration'], n['pitch'])

        if GREATER(note_start, comp_start) and LESS(note_start, comp_end) and note['hand'] == n['hand']:
            continuation_dot(note['time'], n['pitch'])

        if GREATER(comp_start, note_start) and LESS(comp_start, note_end) and note['hand'] == n['hand']:
            continuation_dot(n['time'], note['pitch'])

        # stop sign desicion:
        if EQUALS(comp_start, note_end) and note['hand'] == n['hand']:
            stopflag = False
    
    # notestop sign:
    if stopflag:
        stop_sign(note['time']+note['duration'], note['pitch'])

    note_start = note['time']
    note_end = note['time']+note['duration']

    # create list with all barline times
    barline_times = io['calc'].get_barline_ticks()
    
    # check if there is a barline in between n_start and n_end
    bl_times = []
    for bl in barline_times:
        if note_start < bl < note_end:
            bl_times.append(bl)
            continuation_dot(bl, note['pitch'])
    
    # if there is no barline in between n_start and n_end
    if not bl_times:
        note['type'] = 'note'
        output.append(note)
        return output
    
    # process the barlines
    first = True
    for bl in bl_times:
        new = dict(note)
        new['duration'] = bl - note_start
        new['time'] = note_start
        if first:
            new['type'] = 'note'
        else:
            new['type'] = 'notesplit'
        output.append(new)
        note_start = bl
        first = False

    # add the last split note
    new = dict(note)
    new['duration'] = note_end - note_start
    new['time'] = note_start
    new['type'] = 'notesplit'
    output.append(new)

    return output


def calculate_staff_width(key_min, key_max):
    '''
        based on mn, mx (min and max pitch) it calculates 
        the width of the staff for the engraver.
    '''
    # if there is no key_min and key_max return 0
    if key_min == 0 and key_max == 0:
        return 0
    
    # trim the key_min, key_max to force the range to be at the outer sides of the staff
    # we measure the width of the staff from the outer left position to the outer right position
    key_min, key_max = min(key_min, 40), max(key_max, 44)
    mn_offset = {4:0, 5:-1, 6:-2, 7:-3, 8:-4, 9:0, 10:-1, 11:-2, 12:-3, 1:-4, 2:-5, 3:-6}
    mx_offset = {4:4, 5:3, 6:2, 7:1, 8:0, 9:6, 10:5, 11:4, 12:3, 1:2, 2:1, 3:0}
    key_min += mn_offset[((key_min-1)%12)+1]
    key_max += mx_offset[((key_max-1)%12)+1]
    key_min, key_max = max(key_min, 1), min(key_max, 88)

    # calculate the width
    width = 0
    for n in range(key_min-1, key_max+1): # NOTE: not sure about the +1 and -1
        width += PITCH_UNIT * 2 if ((n-1)%12)+1 in [4, 9] and not n == key_min else PITCH_UNIT
    return width


def range_staffs(io, line, linebreak):
    '''
        range_staffs calculates the range of the staffs
        based on the line and linebreak messages.
    '''
    ranges = [
        linebreak['staff1']['range'], 
        linebreak['staff2']['range'], 
        linebreak['staff3']['range'], 
        linebreak['staff4']['range']
    ]

    pitches = {
        0:[0, 0],
        1:[0, 0],
        2:[0, 0],
        3:[0, 0]
    }

    for i in range(4):
        if io['score']['properties']['staffs'][i]['onoff']:
            pitches[i][0] = 40
            pitches[i][1] = 44
    
    for idx, range1 in enumerate(ranges):
        if range1 == 'auto': 
            ...
        else:
            # a custom range is set; we have to calculate the width of the staff with it.
            pitches[idx].append(range1[0])
            pitches[idx].append(range1[1])
    
    for evt in line:
        if 'pitch' in evt and 'staff' in evt:
            pitches[evt['staff']].append(evt['pitch'])
    
    out = [
        [min(pitches[0]), max(pitches[0])],
        [min(pitches[1]), max(pitches[1])],
        [min(pitches[2]), max(pitches[2])],
        [min(pitches[3]), max(pitches[3])]
    ]

    return out


def trim_key_to_outer_sides_staff(key_min, key_max):

    # if there is no key_min and key_max return 0
    if not key_min and not key_max:
        print('no key_min and key_max')
        return 0

    # trim the key_min, key_max to force the range to be at the outer sides of the staff
    key_min, key_max = min(key_min, 40), max(key_max, 44)
    mn_offset = {4:0, 5:-1, 6:-2, 7:-3, 8:-4, 9:0, 10:-1, 11:-2, 12:-3, 1:-4, 2:-5, 3:-6}
    mx_offset = {4:4, 5:3, 6:2, 7:1, 8:0, 9:6, 10:5, 11:4, 12:3, 1:2, 2:1, 3:0}
    key_min += mn_offset[((key_min-1)%12)+1]
    key_max += mx_offset[((key_max-1)%12)+1]
    key_min, key_max = max(key_min, 1), min(key_max, 88)

    return key_min, key_max


def draw_staff(x_cursor: float, 
               y_cursor: float, 
               staff_min: int, 
               staff_max: int,
               draw_min: int, 
               draw_max: int,
               io: dict, 
               staff_length: float):

    staff_min, staff_max = trim_key_to_outer_sides_staff(staff_min, staff_max)
    if not staff_min and not staff_max:
        draw_min, draw_max = staff_min, staff_max
    draw_min, draw_max = trim_key_to_outer_sides_staff(draw_min, draw_max)

    # draw the staff
    x = x_cursor
    for n in range(staff_min, draw_max+1):
        
        # calculate the new x_cursor
        remainder = ((n-1)%12)+1
        scale = io['score']['properties']['draw_scale']
        x += PITCH_UNIT * 2 * scale if remainder in [4, 9] and not n == staff_min else PITCH_UNIT * scale
        
        if n >= draw_min and n <= draw_max:
            if remainder in [5, 7]: # if it's one of the c# d# keys
                # draw line thin for the group of two
                if n in [41, 43]:
                    # dashed clef lines, the central lines of the staff
                    io['view'].new_line(x, y_cursor, x, y_cursor+staff_length, 
                                    width=.2, 
                                    color='#000000',
                                    dash=[5, 5],
                                    tag=['staffline'])
                else:
                    # normal group of two lines
                    io['view'].new_line(x, y_cursor, x, y_cursor+staff_length, 
                                    width=.2, 
                                    color='#000000',
                                    tag=['staffline'])
            elif remainder in [10, 12, 2]: # if it's one of the f# g# a# keys
                # draw line thick for the group of three
                io['view'].new_line(x, y_cursor, x, y_cursor+staff_length, 
                                    width=.6, 
                                    color='#000000',
                                    tag=['staffline'])
            

def get_system_ticks(io):

    linebreaks = io['score']['events']['linebreak'] # get all linebreaks
    linebreaks = sorted(linebreaks, key=lambda x: x['time']) # sort the linebreaks on time
    linebreaks = [lb['time'] for lb in linebreaks] # get only the times of the linebreaks
    last_tick = io['calc'].get_total_score_ticks()

    # get the system ticks
    system_ticks = []
    for idx, lb in enumerate(linebreaks):
        system_ticks.append([lb, last_tick if idx == len(linebreaks)-1 else linebreaks[idx+1]])
    
    return system_ticks


def tick2y_view(time: float, io: dict, staff_height: float, line_number: int):
    '''
        time2y_view converts a time value to a y value in the print view.
    '''

    system_ticks = get_system_ticks(io)
    line_ticks = system_ticks[line_number]
    
    # claculate the y from the staff_height
    y = staff_height * (time - line_ticks[0]) / (line_ticks[1] - line_ticks[0])
    
    return y


def pitch2x_view(pitch: int, staff_range: list, scale: float, x_cursor: float):
    '''
        pitch2x_view converts a pitch value to a x value in the print view.
    '''

    key_min = staff_range[0]
    key_max = staff_range[1]

    key_min, key_max = trim_key_to_outer_sides_staff(key_min, key_max)

    # calculate the x position
    x = x_cursor
    for n in range(key_min, key_max+1):
        remainder = ((n-1)%12)+1
        x += PITCH_UNIT * 2 * scale if remainder in [4, 9] and not n == key_min else PITCH_UNIT * 2 * scale / 2
        if n == pitch:
            break
    
    return x


def update_barnumber(DOC, idx_page):

    # calculate the barnumber
    barnumber = 1
    for idx, page in enumerate(DOC):
        if idx == idx_page:
            break
        for line in page:
            for evt in line:
                if evt['type'] == 'barline':
                    if float(evt['time']).is_integer():
                        barnumber += 1

    return barnumber


























