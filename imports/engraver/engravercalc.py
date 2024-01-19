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
    for n in range(key_min, key_max):
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
            pitches[0][0] = 40
            pitches[0][1] = 44

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
        






















