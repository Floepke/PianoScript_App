'''
    In this file we dump all the calculations for the engraver.
    Like the calctools.py it stores all solutions to little
    problems but for the engraver.
'''
from imports.utils.constants import *
import copy


def continuation_dot(time, pitch, note):
    return {
        'time': time,
        'pitch': pitch,
        'type': 'continuationdot',
        'staff': note['staff'],
        'hand': note['hand']
    }


def stop_sign(time, pitch, note):
    return {
        'time': time,
        'pitch': pitch,
        'type': 'notestop',
        'staff': note['staff'],
        'hand': note['hand']
    }


def continuation_dot_stopsign_and_connectstem_processor(io, DOC):
    '''
        note_processor processes the notes in such way that it generates a list of neccesary
        note, notesplit, continuationdot, notestop and connectstem events that are then ready
        for being drawn.
    '''

    # making a list of noteon and noteoff messages like a linear midi file
    note_on_off = []
    for note in sorted(io['score']['events']['note'], key=lambda y: y['time']):
        evt = copy.deepcopy(note)
        evt['endtime'] = evt['time'] + evt['duration']
        note_on_off.append(copy.deepcopy(evt))
        evt = copy.deepcopy(evt)
        evt['type'] = 'noteoff'
        note_on_off.append(copy.deepcopy(evt))

    # sorting the list
    note_on_off = sorted(
        note_on_off, key=lambda y: (
            round(
                y['time']) if y['type'] == 'note' else round(
                y['endtime']), round(
                    y['endtime'])))

    # we add the notestop and continuationdot events
    active_notes = []
    for idx, note in enumerate(note_on_off):

        if note['type'] == 'note':
            active_notes.append(note)
            for n in active_notes:
                # continuation dots for note start:
                if n['tag'] != note['tag']:
                    if (not EQUALS(n['time'], note['time']) and
                        note['staff'] == n['staff'] and
                            note['hand'] == n['hand']):
                        DOC.append(
                            continuation_dot(
                                note['time'],
                                n['pitch'],
                                note))

        elif note['type'] == 'noteoff':
            for n in active_notes:
                if (n['duration'] == note['duration'] and
                    n['pitch'] == note['pitch'] and
                    n['staff'] == note['staff'] and
                        n['hand'] == note['hand']):
                    active_notes.remove(n)
                    break

            for idx_n, n in enumerate(active_notes):
                # continuation dots for note end:
                if n['tag'] != note['tag']:
                    if (not EQUALS(n['endtime'], note['endtime']) and
                        note['staff'] == n['staff'] and
                            note['hand'] == n['hand']):
                        DOC.append(
                            continuation_dot(
                                note['endtime'],
                                n['pitch'],
                                note))

        if note['type'] == 'noteoff':
            continue

        stop_flag = False

        # stop sign:
        for n in note_on_off[idx + 1:]:
            if (n['type'] == 'note' and
                EQUALS(n['time'], note['time'] + note['duration']) and
                n['staff'] == note['staff'] and
                    n['hand'] == note['hand']):
                break
            if (n['type'] == 'note' and
                GREATER(n['time'], note['time'] + note['duration']) and
                n['staff'] == note['staff'] and
                    n['hand'] == note['hand']):
                stop_flag = True
                break
            if n == note_on_off[-1]:
                stop_flag = True

        if stop_flag:
            DOC.append(
                stop_sign(
                    note['time'] +
                    note['duration'] -
                    FRACTION,
                    note['pitch'],
                    note))

        # connect stem
        for n in note_on_off[idx + 1:]:
            if (EQUALS(n['time'], note['time']) and
                n['staff'] == note['staff'] and
                    n['hand'] == note['hand']):
                DOC.append(
                    {
                        'type': 'connectstem',
                        'time': note['time'],
                        'pitch': note['pitch'],
                        'time2': note['time'],
                        'pitch2': n['pitch'],
                        'staff': note['staff']
                    }
                )
            if n['time'] > note['time']:
                break

    return DOC


def note_processor(io, note):
    """
    Processes a note and returns a list of output data.

    Args:
        io (dict): The IO dictionary containing all necessary data.
        note (dict): The note to be processed.

    Returns:
        list: A list of output data.

    """

    output = []

    # split notes on barlines
    note_start = note['time']
    note_end = note['time'] + note['duration']

    # create list with all barline times
    barline_times = io['calc'].get_barline_ticks()

    # check if there is a barline in between note_start and note_end
    bl_times = []
    for bl in barline_times:
        if note_start < bl < note_end:
            bl_times.append(bl)
            output.append(continuation_dot(bl, note['pitch'], note))

    # if there is no barline in between note_start and note_end
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
    # we measure the width of the staff from the outer left position to the
    # outer right position
    key_min, key_max = min(key_min, 40), max(key_max, 44)
    mn_offset = {
        4: 0,
        5: -1,
        6: -2,
        7: -3,
        8: -4,
        9: 0,
        10: -1,
        11: -2,
        12: -3,
        1: -4,
        2: -5,
        3: -6}
    mx_offset = {
        4: 4,
        5: 3,
        6: 2,
        7: 1,
        8: 0,
        9: 6,
        10: 5,
        11: 4,
        12: 3,
        1: 2,
        2: 1,
        3: 0}
    key_min += mn_offset[((key_min - 1) % 12) + 1]
    key_max += mx_offset[((key_max - 1) % 12) + 1]
    key_min, key_max = max(key_min, 1), min(key_max, 88)

    # calculate the width
    width = 0
    for n in range(
            key_min -
            1,
            key_max +
            1):  # NOTE: not sure about the +1 and -1
        width += PITCH_UNIT * 2 if ((n - 1) % 12) + \
            1 in [4, 9] and not n == key_min else PITCH_UNIT
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
        0: [0, 0],
        1: [0, 0],
        2: [0, 0],
        3: [0, 0]
    }

    for i in range(4):
        if io['score']['properties']['staffs'][i]['onoff']:
            pitches[i][0] = 40
            pitches[i][1] = 44

    for idx, range1 in enumerate(ranges):
        if range1 == 'auto':
            ...
        else:
            # a custom range is set; we have to calculate the width of the
            # staff with it.
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

    # trim the key_min, key_max to force the range to be at the outer sides of
    # the staff
    key_min, key_max = min(key_min, 40), max(key_max, 44)
    mn_offset = {
        4: 0,
        5: -1,
        6: -2,
        7: -3,
        8: -4,
        9: 0,
        10: -1,
        11: -2,
        12: -3,
        1: -4,
        2: -5,
        3: -6}
    mx_offset = {
        4: 4,
        5: 3,
        6: 2,
        7: 1,
        8: 0,
        9: 6,
        10: 5,
        11: 4,
        12: 3,
        1: 2,
        2: 1,
        3: 0}
    key_min += mn_offset[((key_min - 1) % 12) + 1]
    key_max += mx_offset[((key_max - 1) % 12) + 1]
    key_min, key_max = max(key_min, 1), min(key_max, 88)

    return key_min, key_max


def draw_staff(x_cursor: float,
               y_cursor: float,
               staff_min: int,
               staff_max: int,
               draw_min: int,
               draw_max: int,
               staff_idx: int,
               io: dict,
               staff_length: float,
               minipiano: bool):

    # prepare the staff
    staff_min, staff_max = trim_key_to_outer_sides_staff(staff_min, staff_max)
    if not staff_min and not staff_max:
        draw_min, draw_max = staff_min, staff_max
    draw_min, draw_max = trim_key_to_outer_sides_staff(draw_min, draw_max)
    scale = io['score']['properties']['draw_scale'] * \
        io['score']['properties']['staffs'][staff_idx]['staff_scale']

    # draw the staff
    x = x_cursor

    if minipiano:
        x1 = x - PITCH_UNIT * 2 * scale
        y1 = y_cursor + staff_length
        y2 = y_cursor + staff_length + PITCH_UNIT * 8 * scale

    for n in range(staff_min, draw_max + 1):

        # calculate the new x_cursor
        remainder = ((n - 1) % 12) + 1
        x += PITCH_UNIT * 2 * \
            scale if remainder in [
                4, 9] and not n == staff_min else PITCH_UNIT * scale

        if n >= draw_min and n <= draw_max:
            if remainder in [5, 7]:  # if it's one of the c# d# keys
                # draw line thin for the group of two
                if n in [41, 43]:
                    # dashed clef lines, the central lines of the staff
                    io['view'].new_line(
                        x,
                        y_cursor,
                        x,
                        y_cursor +
                        staff_length,
                        width=io['score']['properties']['staff_twoline_width'] * scale,
                        color='#000000',
                        dash=[
                            5,
                            5],
                        tag=['staffline'])
                    if minipiano:
                        io['view'].new_line(
                            x,
                            y_cursor +
                            staff_length,
                            x,
                            y_cursor +
                            staff_length +
                            PITCH_UNIT *
                            4 *
                            scale,
                            width=1 * scale,
                            color='#888',
                            tag=['minipiano'])
                else:
                    # normal group of two lines
                    io['view'].new_line(
                        x,
                        y_cursor,
                        x,
                        y_cursor +
                        staff_length,
                        width=io['score']['properties']['staff_twoline_width'] * scale,
                        color='#000000',
                        tag=['staffline'])
                    if minipiano:
                        io['view'].new_line(
                            x,
                            y_cursor +
                            staff_length,
                            x,
                            y_cursor +
                            staff_length +
                            PITCH_UNIT *
                            4 *
                            scale,
                            width=1 * scale,
                            color='#000',
                            tag=['minipiano'])
            elif remainder in [10, 12, 2]:  # if it's one of the f# g# a# keys
                # draw line thick for the group of three
                io['view'].new_line(
                    x,
                    y_cursor,
                    x,
                    y_cursor +
                    staff_length,
                    width=io['score']['properties']['staff_threeline_width'] * scale,
                    color='#000000',
                    tag=['staffline'])
                if minipiano:
                    io['view'].new_line(
                        x,
                        y_cursor +
                        staff_length,
                        x,
                        y_cursor +
                        staff_length +
                        PITCH_UNIT *
                        4 *
                        scale,
                        width=1 *
                        scale,
                        color='#000',
                        tag=['minipiano'])

    if minipiano:
        io['view'].new_rectangle(x1,
                                 y1,
                                 x + PITCH_UNIT * 3 * scale,
                                 y2,
                                 width=0.2 * scale,
                                 outline_color='#000',
                                 fill_color='',
                                 tag=['minipiano'])


def get_system_ticks(io):

    linebreaks = io['score']['events']['linebreak']  # get all linebreaks
    # sort the linebreaks on time
    linebreaks = sorted(linebreaks, key=lambda x: x['time'])
    # get only the times of the linebreaks
    linebreaks = [lb['time'] for lb in linebreaks]
    last_tick = io['calc'].get_total_score_ticks()

    # get the system ticks
    system_ticks = []
    for idx, lb in enumerate(linebreaks):
        system_ticks.append([lb, last_tick if idx == len(
            linebreaks) - 1 else linebreaks[idx + 1]])

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
    for n in range(1, key_min):
        remainder = ((n - 1) % 12) + 1
        x -= PITCH_UNIT * 2 * \
            scale if remainder in [4, 9] else PITCH_UNIT * 2 * scale / 2
    for n in range(1, 88):
        remainder = ((n - 1) % 12) + 1
        x += PITCH_UNIT * 2 * \
            scale if remainder in [
                4, 9] and not n == key_min else PITCH_UNIT * 2 * scale / 2
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


def beam_processor(io, DOC):
    '''
        In this stage of preprocessing, the beam data is processed. We add
        the beam data coords along with a time stamp in order for it to be properly
        sorted into the lines and pages.
        If the staff doesn't contain any beam, we group the beams onto the base-grid-lines.
    '''

    # get calculation data
    system_ticks = get_system_ticks(io)
    beams = sorted(io['score']['events']['beam'], key=lambda y: y['time'])
    left_beams = [beam for beam in beams if beam['hand'] == 'l']
    right_beams = [beam for beam in beams if beam['hand'] == 'r']

    left_beam_list = []
    for idx_beam, beam in enumerate(left_beams):

        try:
            # Find the next beam with the same 'staff' value
            next_beam = next(
                b for b in left_beams[idx_beam + 1:] if b['staff'] == beam['staff'])
            next_marker = next_beam['time']
        except StopIteration:
            # If no such beam is found, use 'total_ticks'
            next_marker = io['total_ticks']

        size = beam['duration']
        if not size:
            amount = 0
        else:
            amount = int(round((next_marker - beam['time']) / size))

        time = beam['time']
        for _ in range(amount):
            bm = copy.deepcopy(beam)
            bm['time'] = time
            bm['notes'] = []
            left_beam_list.append(bm)
            time += size

    right_beam_list = []
    for idx_beam, beam in enumerate(right_beams):

        try:
            # Find the next beam with the same 'staff' value
            next_beam = next(
                b for b in right_beams[idx_beam + 1:] if b['staff'] == beam['staff'])
            next_marker = next_beam['time']
        except StopIteration:
            # If no such beam is found, use 'total_ticks'
            next_marker = io['total_ticks']

        size = beam['duration']
        if not size:
            amount = 0
        else:
            amount = int(round((next_marker - beam['time']) / size))

        time = beam['time']
        for _ in range(amount):
            bm = copy.deepcopy(beam)
            bm['time'] = time
            bm['notes'] = []
            right_beam_list.append(bm)
            time += size

    # 8mar2024 -- we implement the auto beam grouping here:
    if not left_beam_list:

        splitpoints = sorted([note for note in DOC if note['type'] in [
                             'barline', 'gridline']], key=lambda y: y['time'])
        splitpoints = [sp['time'] for sp in splitpoints]
        splitpoints.append(io['total_ticks'])

        for idx, sp in enumerate(splitpoints):
            if idx == len(splitpoints) - 1:
                break
            for i in range(4):
                new = {
                    'time': sp,
                    'duration': splitpoints[idx+1] - sp,
                    'type': 'beam',
                    'staff': i,
                    'hand': 'l'
                }
                left_beam_list.append(new)

    if not right_beam_list:

        splitpoints = sorted([note for note in DOC if note['type'] in [
                             'barline', 'gridline']], key=lambda y: y['time'])
        splitpoints = [sp['time'] for sp in splitpoints]
        splitpoints.append(io['total_ticks'])

        for idx, sp in enumerate(splitpoints):
            if idx == len(splitpoints) - 1:
                break
            for i in range(4):
                new = {
                    'time': sp,
                    'duration': splitpoints[idx+1] - sp,
                    'type': 'beam',
                    'staff': i,
                    'hand': 'r'
                }
                right_beam_list.append(new)

    # filling the left beam list with attached notes
    for idx_beam, beam in enumerate(left_beam_list + right_beam_list):

        beam['notes'] = [
            note for note in DOC if note['type'] in [
                'note', 'continuationdot']]
        beam['notes'] = [note for note in beam['notes']
                         if beam['time'] <= note['time'] < beam['time'] + beam['duration'] and
                         note['staff'] == beam['staff'] and
                         note['hand'] == beam['hand']]
        beam['notes'] = sorted(beam['notes'], key=lambda y: y['time'])

        DOC.append(beam)

    # removing the orginal beam msg from the DOC
    for i in io['score']['events']['beam']:
        DOC.remove(i)

    return DOC


def normalize(x, y, z):
    return (z - x) / (y - x)


def units2x_view(value, staff_range, scale, x_cursor):
    c4_xpos = pitch2x_view(40, staff_range, scale, x_cursor)
    return (c4_xpos + (value * scale * (PITCH_UNIT * 2)))
