'''
    In this file we dump all the calculations for the engraver.
    Like the calctools.py it stores all solutions to little 
    problems but for the engraver.
'''
from imports.utils.constants import *

def note_split_processor(io, note):
    '''
        note_split_processor splits a note message into different parts
        if the note is crossing a linebreak point. This is neccesary because
        we have to draw the note in two parts in this case.
    '''

    output = []
    n_start = note['time']
    n_end = note['time']+note['duration']

    # create list with all linebreak times
    linebreak_times = []
    for lb in io['score']['events']['linebreak']:
        linebreak_times.append(lb['time'])
    
    # check if there is a linebreak in between n_start and n_end
    nb_times = []
    for lb in linebreak_times:
        if n_start < lb < n_end:
            nb_times.append(lb)
    
    # if there is no linebreak in between n_start and n_end
    if not nb_times:
        note['type'] = 'note'
        output.append(note)
        return output
    
    # process the linebreaks
    first = True
    for nb in nb_times:
        new = dict(note)
        new['duration'] = nb - n_start
        new['time'] = n_start
        if first:
            new['type'] = 'note'
        else:
            new['type'] = 'notesplit'
        output.append(new)
        n_start = nb
        first = False

    # add the last split note
    new = dict(note)
    new['duration'] = n_end - n_start
    new['time'] = n_start
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
    # we measure the width of the staff from the outer left position to the outer right position
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

    # draw the staff
    for n in range(staff_min, staff_max):
        remainder = ((n-1)%12)+1
        scale = io['score']['properties']['draw_scale']
        x_cursor += PITCH_UNIT * 2 * scale if remainder in [4, 9] and not n == staff_min else PITCH_UNIT * scale
        if remainder in [5, 7]: # if it's one of the c# d# keys
            # draw line thin for the group of two
            if n in [41, 43]:
                # dashed clef lines, the central lines of the staff
                io['view'].new_line(x_cursor, y_cursor, x_cursor, y_cursor+staff_length, 
                                width=.2, 
                                color='#000000',
                                dash=[5, 5])
            else:
                # normal group of two lines
                io['view'].new_line(x_cursor, y_cursor, x_cursor, y_cursor+staff_length, 
                                width=.2, 
                                color='#000000')
        elif remainder in [10, 12, 2]: # if it's one of the f# g# a# keys
            # draw line thick for the group of three
            io['view'].new_line(x_cursor, y_cursor, x_cursor, y_cursor+staff_length, 
                                width=.4, 
                                color='#000000')
            

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


























