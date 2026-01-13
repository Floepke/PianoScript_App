# we genereally import everything from this file for usage in the
# engraver, later we add the engraver specific imports here
from imports.engraver.engraver_helpers import *
from imports.utils.constants import *

'''
    The Renderer is a really long script. I chose to write it only in functions because
    I like to program that way. I try to program it in a steps way. First we pre_calculate()
    then we draw(). pre_calculate() calculates a dict of events which the draw function can
    use to draw.

    We need to first pre calculate how the music will fit on the page. Then we can draw it.
'''


# render_type = 'default' (render only the current page) | 'export'
# (render all pages for exporting to pdf)
def pre_render(io, render_type='default'):

    # set scene dimensions
    scene_width = io['score']['properties']['page_width']
    scene_height = io['score']['properties']['page_height']

    # set scene rectangle
    io['gui'].print_scene.setSceneRect(
        0, 0, scene_width, scene_height)

    # page dimentions
    page_margin_left = io['score']['properties']['page_margin_left']
    page_margin_right = io['score']['properties']['page_margin_right']
    page_margin_top = io['score']['properties']['page_margin_up']
    page_margin_bottom = io['score']['properties']['page_margin_down']
    page_width = io['score']['properties']['page_width']
    page_height = io['score']['properties']['page_height']

    # staff dimentions
    draw_scale = io['score']['properties']['draw_scale']
    linebreaks = sorted(
        io['score']['events']['linebreak'],
        key=lambda y: y['time'])

    def pre_calculate(io):
        io['engrave_counter']
        print(f'...........ENGRAVING...........')
        io['engrave_counter'] += 1
        print(f"engraving number: {io['engrave_counter']}")
        print('pre calculating...')

        # --------------------------------------------------------------------------------------------------------------------------------------
        # DOC structure:
        # the events are the literal dicts of the json score file like:
        # {"tag": "note6", "pitch": 56, "time": 1024.0, "duration": 256.0, "hand": "r", "staff": 1, "attached": "."}
        # so the DOC list is a structured list of pages and lines within that
        # page and events within that line.

        # the doc we need to fill
        DOC = []

        # data to collect
        leftover_page_space = []
        staff_dimensions = []
        barline_times = []

        '''
        first we add all types of events:
            - barlines
            - gridlines
            - timesignature changes
            - notes and split them if they are crossing a new line point or a barline
            - other events like slurs, dynamics, pedal, etc...
        '''

        # time signature, barlines and grid
        time = 0
        for gr in io['score']['events']['grid']:
            # calculate the length of one measure based on the numerator and
            # denominator.
            numerator = gr['numerator']
            denominator = gr['denominator']
            measure_length = int(numerator * ((QUARTER_PIANOTICK * 4) / denominator))
            amount = gr['amount']
            grid = gr['grid']
            visible = gr['visible']
            tsig_length = 0

            # create time signature indicator
            DOC.append({
                'type': 'timesignature',
                'time': time,
                'numerator': numerator,
                'denominator': denominator,
                'visible': visible
            })

            # add barlines and gridlines
            for m in range(amount):
                # add barlines
                DOC.append({
                    'type': 'barline',
                    'time': time + measure_length * m
                })
                DOC.append({
                    'type': 'barlinedouble',
                    'time': time + measure_length * m - FRACTION
                })
                # simultaneously make a list of barline times
                barline_times.append(time + measure_length * m)
                for g in grid:
                    # add gridlines
                    DOC.append({
                        'type': 'gridline',
                        'time': time + measure_length * m + g
                    })
                    DOC.append({
                        'type': 'gridlinedouble',
                        'time': time + measure_length * m + g - FRACTION
                    })

                tsig_length += measure_length

            time += tsig_length

        # add endbarline event
        DOC.append({'type': 'endbarline',
                    'time': io['calc'].get_total_score_ticks() - FRACTION})

        # add all events from io['score]['events] to the doc
        for key in io['score']['events'].keys():
            if key not in ['grid', 'linebreak']:
                for evt in io['score']['events'][key]:
                    new = evt
                    new['type'] = key
                    if evt['type'] in ['endrepeat', 'endsection']:
                        # for certain kinds of objects like end repeat and end section
                        # we need to set the time a fraction earlier because otherwise they
                        # appear at the start of a line while they should
                        # appear at the end.
                        new['time'] -= FRACTION
                        DOC.append(new)
                    elif key == 'note':
                        new = note_processor(io, evt)
                        for note in new:
                            DOC.append(note)
                    else:
                        DOC.append(new)

        # process the notes for creating continuation dots and stopsigns
        DOC = continuation_dot_stopsign_and_connectstem_processor(io, DOC)

        DOC = beam_processor(io, DOC)

        # now we sort the events on time-key
        DOC = sorted(DOC, key=lambda y: y['time'])

        '''
            organizing all events in lists of lines:
        '''

        # make a list of tuples for each line: (start_time, end_time)
        linebreak_time_sets = []
        for idx, lb in enumerate(sorted(linebreaks, key=lambda y: y['time'])):
            try:
                nxt = linebreaks[idx + 1]['time']
            except IndexError:
                nxt = float('inf')
            linebreak_time_sets.append((lb['time'], nxt))

        def split_doc_by_linebreaks(DOC, linebreak_time_sets):
            # Initialize the list of line-docs
            line_docs = []

            # Iterate over the linebreak_time_sets
            for start_time, next_start_time in linebreak_time_sets:
                # Create a new line-doc for each linebreak
                line_doc = []

                # Iterate over the events in the DOC
                for event in DOC:
                    event_time = event['time']

                    # Check if the event falls within the current line
                    if start_time <= event_time < next_start_time:
                        # Add the event to the line-doc
                        line_doc.append(event)

                # Add the line-doc to the list of line-docs
                line_docs.append(line_doc)

            return line_docs

        DOC = split_doc_by_linebreaks(DOC, linebreak_time_sets)

        '''
            organizing all lines in lists of pages. We do this
            by pre calculating the width and margins of every
            staff and test if the line fit on the page. If it
            doesn't fit we add it to the next page and so on:
        '''

        # get the line width of every line [[widthstaff1, widthstaff2, widthstaff3, widthstaff4], ...]]
        # if a staff is off the width is zero
        staff_ranges = []
        for lb, line in zip(linebreaks, DOC):

            staff1_width = {}
            staff2_width = {}
            staff3_width = {}
            staff4_width = {}

            # get the highest and lowest pitch of every staff
            range_every_staff = range_staffs(io, line, lb)
            staff_ranges.append(range_every_staff)

            # calculate the width of every staff
            for idx, res in enumerate(range_every_staff):
                if idx == 0:
                    if io['score']['properties']['staffs'][idx]['onoff']:
                        staff1_width['staff_width'] = calculate_staff_width(
                            res[0], res[1]) * draw_scale * io['score']['properties']['staffs'][idx]['staff_scale']
                    else:
                        staff1_width['staff_width'] = 0
                elif idx == 1:
                    if io['score']['properties']['staffs'][idx]['onoff']:
                        staff2_width['staff_width'] = calculate_staff_width(
                            res[0], res[1]) * draw_scale * io['score']['properties']['staffs'][idx]['staff_scale']
                    else:
                        staff2_width['staff_width'] = 0
                elif idx == 2:
                    if io['score']['properties']['staffs'][idx]['onoff']:
                        staff3_width['staff_width'] = calculate_staff_width(
                            res[0], res[1]) * draw_scale * io['score']['properties']['staffs'][idx]['staff_scale']
                    else:
                        staff3_width['staff_width'] = 0
                elif idx == 3:
                    if io['score']['properties']['staffs'][idx]['onoff']:
                        staff4_width['staff_width'] = calculate_staff_width(
                            res[0], res[1]) * draw_scale * io['score']['properties']['staffs'][idx]['staff_scale']
                    else:
                        staff4_width['staff_width'] = 0

            # add the margins to the staff width if the staff is on
            if staff1_width['staff_width']:
                staff1_width['margin_left'] = (
                    lb['staff1']['margins'][0]) * draw_scale
                staff1_width['margin_right'] = (
                    lb['staff1']['margins'][1]) * draw_scale
            else:
                staff1_width['margin_left'] = 0
                staff1_width['margin_right'] = 0
            if staff2_width['staff_width']:
                staff2_width['margin_left'] = (
                    lb['staff2']['margins'][0]) * draw_scale
                staff2_width['margin_right'] = (
                    lb['staff2']['margins'][1]) * draw_scale
            else:
                staff2_width['margin_left'] = 0
                staff2_width['margin_right'] = 0
            if staff3_width['staff_width']:
                staff3_width['margin_left'] = (
                    lb['staff3']['margins'][0]) * draw_scale
                staff3_width['margin_right'] = (
                    lb['staff3']['margins'][1]) * draw_scale
            else:
                staff3_width['margin_left'] = 0
                staff3_width['margin_right'] = 0
            if staff4_width['staff_width']:
                staff4_width['margin_left'] = (
                    lb['staff4']['margins'][0]) * draw_scale
                staff4_width['margin_right'] = (
                    lb['staff4']['margins'][1]) * draw_scale
            else:
                staff4_width['margin_left'] = 0
                staff4_width['margin_right'] = 0

            staff_dimensions.append(
                [staff1_width, staff2_width, staff3_width, staff4_width])

        # calculate how many lines will fit on the page / split the line list
        # in parts of pages:
        doc = []
        page = []
        leftover_page_space = []
        remaining_space = 0
        x_cursor = 0
        total_print_width = page_width - page_margin_left - page_margin_right
        for idx, lw, line in zip(
                range(len(staff_dimensions)), staff_dimensions, DOC):
            # calculate the total width of the line
            total_line_width = 0
            for width in lw:
                total_line_width += width['staff_width'] + \
                    width['margin_left'] + width['margin_right']

            # update the x_cursor
            x_cursor += total_line_width

            # if the line fits on paper:
            if x_cursor <= total_print_width:
                page.append(line)
                remaining_space = total_print_width - x_cursor
            # if the line does NOT fit on paper:
            else:
                x_cursor = total_line_width
                doc.append(page)
                page = []
                page.append(line)
                leftover_page_space.append(remaining_space)
                remaining_space = total_print_width - x_cursor
            # if this is the last line:
            if idx == len(DOC) - 1:
                doc.append(page)
                leftover_page_space.append(remaining_space)

        DOC = doc

        return DOC, leftover_page_space, staff_dimensions, staff_ranges, barline_times

    DOC, leftover_page_space, staff_dimensions, staff_ranges, barline_times = pre_calculate(
        io)

    # set pageno
    pageno = io['selected_page'] % len(DOC)

    io['num_pages'] = len(DOC)

    return DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale, barline_times, render_type


def render(
        io,
        DOC,
        leftover_page_space,
        staff_dimensions,
        staff_ranges,
        pageno,
        linebreaks,
        draw_scale,
        barline_times,
        render_type):

    def draw(io):
        print('starting to draw...')

        # delete old drawing
        io['view'].delete_all()

        # define the page dimensions
        page_margin_left = io['score']['properties']['page_margin_left']
        page_margin_right = io['score']['properties']['page_margin_right']
        page_margin_top = io['score']['properties']['page_margin_up']
        page_margin_bottom = io['score']['properties']['page_margin_down']
        page_width = io['score']['properties']['page_width']
        page_height = io['score']['properties']['page_height']
        black_note_rule = io['score']['properties']['black_note_rule']

        # onoff settings
        staff_onoff = io['score']['properties']['staff_onoff']
        minipiano_onoff = io['score']['properties']['minipiano_onoff']
        stem_onoff = io['score']['properties']['stem_onoff']
        beam_onoff = io['score']['properties']['beam_onoff']
        note_onoff = io['score']['properties']['note_onoff']
        midinote_onoff = io['score']['properties']['midinote_onoff']
        notestop_onoff = io['score']['properties']['notestop_onoff']
        page_numbering_onoff = io['score']['properties']['page_numbering_onoff']
        barlines_onoff = io['score']['properties']['barlines_onoff']
        basegrid_onoff = io['score']['properties']['basegrid_onoff']
        countline_onoff = io['score']['properties']['countline_onoff']
        measure_numbering_onoff = io['score']['properties']['measure_numbering_onoff']
        accidental_onoff = io['score']['properties']['accidental_onoff']
        continuationdot_onoff = io['score']['properties'].get('continuationdot_onoff', True)
        leftdot_onoff = io['score']['properties']['leftdot_onoff']
        text_onoff = io['score']['properties']['text_onoff']

        staffs_settings = io['score']['properties']['staffs']
        threeline_scale = io['score']['properties']['threeline_scale']
        stop_sign_style = io['score']['properties']['stop_sign_style']
        continuation_dot_style = io['score']['properties']['continuation_dot_style']

        # engraver settings:
        stem_thickness = io['score']['properties']['stem_width'] # .5
        beam_thickness = io['score']['properties']['beam_width'] # 1

        Left = 0
        Right = page_width
        Top = 0
        Bottom = page_height

        # looping trough the DOC structure and drawing the score:
        x_cursor = 0
        y_cursor = 0
        idx_line = 0
        barnumber = 1
        for idx_page, page, leftover in zip(range(len(DOC)), DOC, leftover_page_space):
            if idx_page != pageno:
                idx_line += len(DOC[idx_page])
                barnumber = update_barnumber(DOC, idx_page + 1)
                continue

            print(f'PAGE: {idx_page+1}')

            # draw the page outer bounds to see where the page is starting and ending
            if render_type == 'default':
                io['view'].new_line(
                    Left, Top, Right, Top, width=0.5, color='black', tag=['page'], dash=[5, 7])
                io['view'].new_line(
                    Left, Bottom, Right, Bottom, width=0.5, color='black', tag=['page'], dash=[5, 7])

            # update the cursors
            x_cursor = page_margin_left
            y_cursor = page_margin_top

            # check if this is the frst page; if so we draw the title and
            # composer header
            if idx_page == 0:
                # draw the title
                io['view'].new_text(page_margin_left,
                                    y_cursor-5,
                                    io['score']['header']['title'],
                                    size=int(io['score']['properties']['title_font_size'] * draw_scale),
                                    tag=['title'],
                                    font='Courier New',
                                    anchor='nw')
                # draw the composer
                composer_text = io['score']['header']['composer']
                if io['score']['properties']['timestamp_onoff']:
                    composer_text += '\n' + io['score']['header']['timestamp']
                io['view'].new_text(Right - page_margin_right,
                                    y_cursor-5,
                                    composer_text,
                                    size=int(io['score']['properties']['composer_font_size'] * draw_scale),
                                    tag=['composer'],
                                    font='Courier New',
                                    anchor='ne')

                y_cursor += io['score']['properties']['header_height']

            # draw footer copyright pagenumbering and title
            text = f"page {idx_page+1} of {len(DOC)} - {io['score']['header']['title']}"
            if idx_page == 0:
                text += f"\n{io['score']['header']['copyright']}"
            io['view'].new_text(
                page_margin_left,
                page_height -
                page_margin_bottom -
                PITCH_UNIT *
                4 *
                draw_scale,
                text,
                size=int(io['score']['properties']['footer_font_size'] * draw_scale),
                tag=['copyright'],
                font='Courier new',
                anchor='w')

            for line, dimensions, staff_range in zip(
                    page, staff_dimensions[idx_line:], staff_ranges[idx_line:]):

                # set staff height
                if idx_page == 0:
                    if idx_line == 0 and minipiano_onoff:
                        staff_height = page_height - page_margin_top - page_margin_bottom - \
                            io['score']['properties']['header_height'] - \
                            io['score']['properties']['footer_height'] - \
                            PITCH_UNIT * 8 * draw_scale
                    else:
                        staff_height = page_height - page_margin_top - page_margin_bottom - \
                            io['score']['properties']['header_height'] - \
                            io['score']['properties']['footer_height']
                else:
                    staff_height = page_height - page_margin_top - \
                        page_margin_bottom - \
                        io['score']['properties']['footer_height']

                # draw the staffs
                for idx_staff, staff_prefs in enumerate(dimensions):

                    staff_scale = io['score']['properties']['staffs'][idx_staff]['staff_scale']

                    enabled_staffs = 0

                    if staff_prefs['staff_width']:

                        # update the x_cursor
                        for w in dimensions:
                            if w['staff_width']:
                                enabled_staffs += 1
                        x_cursor += staff_prefs['margin_left'] + \
                            (leftover / (len(page) * enabled_staffs + 1))

                        # draw the staff
                        if linebreaks[idx_line][f'staff{idx_staff+1}']['range'] == 'auto':
                            # calculated in pre_calculate
                            draw_start = staff_range[idx_staff][0]
                            draw_end = staff_range[idx_staff][1]
                        else:
                            # given in file
                            draw_start = linebreaks[idx_line][f'staff{idx_staff+1}']['range'][0]
                            draw_end = linebreaks[idx_line][f'staff{idx_staff+1}']['range'][1]
                        if staff_onoff:
                            draw_staff(
                                x_cursor,
                                y_cursor,
                                staff_range[idx_staff][0],
                                staff_range[idx_staff][1],
                                draw_start,
                                draw_end,
                                io=io,
                                staff_idx=idx_staff,
                                staff_length=staff_height,
                                minipiano=True if idx_line == 0 and minipiano_onoff else False)

                    for evt in line:

                        if idx_staff == 0:
                            # draw the barlines or endbarline
                            if evt['type'] in ['barline', 'endbarline', 'barlinedouble']:
                                x1 = x_cursor + (PITCH_UNIT * 2 * draw_scale * staff_scale)
                                x2 = x_cursor
                                last_r_marg = 0
                                for i, w in enumerate(dimensions):
                                    if w['staff_width']:
                                        if i > 0:
                                            x2 += w['margin_left']
                                        x2 += w['staff_width'] + w['margin_right'] + \
                                            (leftover / (len(page)
                                             * enabled_staffs + 1))
                                        last_r_marg = w['margin_right']
                                x2 -= last_r_marg + \
                                    (leftover / (len(page) * enabled_staffs + 1)) + \
                                    (PITCH_UNIT * 2 * draw_scale * staff_scale)
                                y = tick2y_view(
                                    evt['time'], io, staff_height, idx_line)
                                if evt['type'] in ['barline', 'barlinedouble']:
                                    w = io['score']['properties']['barline_width'] * draw_scale * staff_scale
                                else:
                                    # if it is the endbarline we draw it thicker
                                    w = io['score']['properties']['barline_width'] * 4 * draw_scale * staff_scale
                                if barlines_onoff:
                                    io['view'].new_line(x1,
                                                        y_cursor + y,
                                                        x2,
                                                        y_cursor + y,
                                                        width=w,
                                                        color='black',
                                                        tag=['barline'])
                                # draw barnumbering
                                if float(evt['time']).is_integer():
                                    if measure_numbering_onoff:
                                        io['view'].new_text(
                                            x2 + (PITCH_UNIT * 18 * draw_scale * staff_scale),
                                            y_cursor + y - 4,
                                            str(barnumber),
                                            size=io['score']['properties']['measure_numbering_font_size'] * draw_scale * staff_scale,
                                            tag=['barnumbering'],
                                            font='Courier new',
                                            anchor='ne')
                                        io['view'].new_line(
                                            x2,
                                            y_cursor + y,
                                            x2 + 10,
                                            y_cursor + y,
                                            width=0.2 * draw_scale * staff_scale,
                                            color='black',
                                            dash=[2, 4],
                                            tag=['barnumbering']
                                        )
                                    barnumber += 1

                        if staff_prefs['staff_width']:
                            # draw the gridlines (base-grid)
                            if evt['type'] in ['gridline', 'gridlinedouble']:
                                x1 = x_cursor + \
                                    (PITCH_UNIT * 2 * draw_scale * staff_scale)
                                x2 = x_cursor + \
                                    staff_prefs['staff_width'] - \
                                    (PITCH_UNIT * 2 * draw_scale * staff_scale)
                                y = tick2y_view(
                                    evt['time'], io, staff_height, idx_line)
                                if basegrid_onoff:
                                    io['view'].new_line(x1,
                                                        y_cursor + y,
                                                        x2,
                                                        y_cursor + y,
                                                        width=io['score']['properties']['basegrid_width'] * draw_scale * staff_scale,
                                                        color='black',
                                                        dash=[5, 7],
                                                        tag=['gridline'])

                        # draw the notes
                        if evt['type'] in ['note', 'notesplit']:

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff']:
                                x = pitch2x_view(
                                    evt['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y1 = tick2y_view(
                                    evt['time'], io, staff_height, idx_line)
                                y2 = tick2y_view(
                                    evt['time'] + evt['duration'], io, staff_height, idx_line)

                                if evt['type'] == 'note':
                                    # draw the notehead
                                    if note_onoff:
                                        if evt['pitch'] in BLACK_KEYS:
                                            if black_note_rule == 'Up':
                                                io['view'].new_oval(
                                                    x - PITCH_UNIT * draw_scale * staff_scale,
                                                    y_cursor + y1 - (
                                                        PITCH_UNIT * 2.25 * draw_scale * staff_scale),
                                                    x + PITCH_UNIT * draw_scale * staff_scale,
                                                    y_cursor + y1,
                                                    fill_color='#000000',
                                                    outline_color='#000000',
                                                    outline_width=.1 * draw_scale * staff_scale,
                                                    tag=['noteheadblack'])
                                            elif black_note_rule == 'Down':
                                                io['view'].new_oval(
                                                    x - PITCH_UNIT * .85 * draw_scale * staff_scale,
                                                    y_cursor + y1,
                                                    x + PITCH_UNIT * .85 * draw_scale * staff_scale,
                                                    y_cursor + y1 - (
                                                        PITCH_UNIT * 2.25 * draw_scale * staff_scale),
                                                    fill_color='#000000',
                                                    outline_color='#000000',
                                                    outline_width=.1 * draw_scale * staff_scale,
                                                    tag=['noteheadblack'])
                                        else:
                                            io['view'].new_oval(
                                                x - PITCH_UNIT * draw_scale * staff_scale,
                                                y_cursor + y1,
                                                x + PITCH_UNIT * draw_scale * staff_scale,
                                                y_cursor + y1 + (
                                                    PITCH_UNIT * 2.25 * draw_scale * staff_scale),
                                                fill_color='#ffffff',
                                                outline_color='#000000',
                                                outline_width=.3 * draw_scale * staff_scale,
                                                tag=['noteheadwhite'])

                                    # left hand dot
                                    if leftdot_onoff:
                                        if evt['hand'] == 'l':
                                            if not evt['pitch'] in BLACK_KEYS:
                                                io['view'].new_oval(x - PITCH_UNIT * .25 * draw_scale * staff_scale,
                                                                    y_cursor + y1 +
                                                                    (PITCH_UNIT * (2.25 / 2 - .25)
                                                                     * draw_scale * staff_scale),
                                                                    x + PITCH_UNIT * .25 * draw_scale * staff_scale,
                                                                    y_cursor + y1 +
                                                                    (PITCH_UNIT * (2.25 / 2 + .25)
                                                                     * draw_scale * staff_scale),
                                                                    fill_color='#000000',
                                                                    outline_color='',
                                                                    tag=['leftdotwhite'])

                                            else:
                                                if black_note_rule == 'Up':
                                                    io['view'].new_oval(x - PITCH_UNIT * .25 * draw_scale * staff_scale,
                                                                        y_cursor + y1 -
                                                                        (PITCH_UNIT * (2.25 / 2 + .25)
                                                                         * draw_scale * staff_scale),
                                                                        x + PITCH_UNIT * .25 * draw_scale * staff_scale,
                                                                        y_cursor + y1 -
                                                                        (PITCH_UNIT * (2.25 / 2 - .25)
                                                                         * draw_scale * staff_scale),
                                                                        fill_color='#ffffff',
                                                                        outline_color='',
                                                                        tag=['leftdotblack'])
                                                elif black_note_rule == 'Down':
                                                    io['view'].new_oval(x - PITCH_UNIT * .25 * draw_scale * staff_scale,
                                                                        y_cursor + y1 +
                                                                        (PITCH_UNIT * (2.25 / 2 - .25)
                                                                         * draw_scale * staff_scale),
                                                                        x + PITCH_UNIT * .25 * draw_scale * staff_scale,
                                                                        y_cursor + y1 +
                                                                        (PITCH_UNIT * (2.25 / 2 + .25)
                                                                         * draw_scale * staff_scale),
                                                                        fill_color='#ffffff',
                                                                        outline_color='',
                                                                        tag=['leftdotblack'])

                                    # draw stem
                                    if stem_onoff:
                                        if evt['hand'] == 'r':
                                            io['view'].new_line(
                                                x,
                                                y_cursor +
                                                y1,
                                                x +
                                                PITCH_UNIT *
                                                5 *
                                                draw_scale * staff_scale,
                                                y_cursor +
                                                y1,
                                                width=stem_thickness *
                                                draw_scale * staff_scale,
                                                tag=['stem'])
                                            if any(
                                                EQUALS(
                                                    evt['time'],
                                                    barline_time) for barline_time in barline_times):
                                                io['view'].new_line(
                                                    x - PITCH_UNIT * 1.5 * draw_scale * staff_scale,
                                                    y_cursor + y1,
                                                    x + PITCH_UNIT * 5 * draw_scale * staff_scale,
                                                    y_cursor + y1,
                                                    color='white',
                                                    width=stem_thickness * draw_scale * staff_scale,
                                                    tag=['whitespace'])
                                        else:
                                            io['view'].new_line(
                                                x,
                                                y_cursor +
                                                y1,
                                                x -
                                                PITCH_UNIT *
                                                5 *
                                                draw_scale * staff_scale,
                                                y_cursor +
                                                y1,
                                                width=stem_thickness *
                                                draw_scale * staff_scale,
                                                tag=['stem'])
                                            if any(
                                                EQUALS(
                                                    evt['time'],
                                                    barline_time) for barline_time in barline_times):
                                                io['view'].new_line(
                                                    x + PITCH_UNIT * 1.5 * draw_scale * staff_scale,
                                                    y_cursor + y1,
                                                    x - PITCH_UNIT * 5 * draw_scale * staff_scale,
                                                    y_cursor + y1,
                                                    color='white',
                                                    width=stem_thickness * draw_scale * staff_scale,
                                                    tag=['whitespace'])

                                # draw midinote
                                if midinote_onoff:
                                    if evt['hand'] == 'l':
                                        color = io['score']['properties']['color_left_midinote']
                                    else:
                                        color = io['score']['properties']['color_right_midinote']
                                    io['view'].new_polygon(
                                        [
                                            (x,
                                             y_cursor + y1),
                                            (x + PITCH_UNIT * draw_scale * staff_scale,
                                             y_cursor + y1 + PITCH_UNIT * draw_scale * staff_scale),
                                            (x + PITCH_UNIT * draw_scale * staff_scale,
                                             y_cursor + y2),
                                            (x - PITCH_UNIT * draw_scale * staff_scale,
                                             y_cursor + y2),
                                            (x - PITCH_UNIT * draw_scale * staff_scale,
                                             y_cursor + y1 + PITCH_UNIT * draw_scale * staff_scale)],
                                        fill_color=color,
                                        outline_color='',
                                        width=0,
                                        tag=['midinote'])

                        if evt['type'] == 'notestop':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff']:
                                x = pitch2x_view(
                                    evt['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y = tick2y_view(
                                    evt['time'], io, staff_height, idx_line)
                                if notestop_onoff:
                                    if stop_sign_style == 'Klavarskribo':
                                        # Traditional stopsign
                                        io['view'].new_line(
                                            x -
                                            PITCH_UNIT *
                                            draw_scale * staff_scale,
                                            y_cursor +
                                            y -
                                            PITCH_UNIT *
                                            2 *
                                            draw_scale * staff_scale,
                                            x,
                                            y_cursor +
                                            y,
                                            width=.4 *
                                            draw_scale * staff_scale,
                                            color='black',
                                            tag=['notestop'])
                                        io['view'].new_line(
                                            x +
                                            PITCH_UNIT *
                                            draw_scale * staff_scale,
                                            y_cursor +
                                            y -
                                            PITCH_UNIT *
                                            2 *
                                            draw_scale * staff_scale,
                                            x,
                                            y_cursor +
                                            y,
                                            width=.4 *
                                            draw_scale * staff_scale,
                                            color='black',
                                            tag=['notestop'])
                                    elif stop_sign_style == 'PianoScript':
                                        # triangle stopsign
                                        io['view'].new_polygon(
                                            [
                                                (x,
                                                 y_cursor + y - PITCH_UNIT * 2 * draw_scale * staff_scale),
                                                (x + PITCH_UNIT * .75 * draw_scale * staff_scale,
                                                 y_cursor + y),
                                                (x - PITCH_UNIT * .75 * draw_scale * staff_scale,
                                                 y_cursor + y)],
                                            fill_color='#000',
                                            outline_color='#000',
                                            width=.3 * draw_scale * staff_scale,
                                            tag=['notestop'])

                        # draw continuation dot
                        if evt['type'] == 'continuationdot':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff']:
                                x = pitch2x_view(
                                    evt['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y = tick2y_view(
                                    evt['time'], io, staff_height, idx_line)
                                if continuationdot_onoff:
                                    if continuation_dot_style == 'Klavarskribo':
                                        io['view'].new_oval(x - PITCH_UNIT * .5 * draw_scale * staff_scale,
                                                            y_cursor + y +
                                                            (PITCH_UNIT * .75 *
                                                             draw_scale * staff_scale),
                                                            x + PITCH_UNIT * .5 * draw_scale * staff_scale,
                                                            y_cursor + y +
                                                            (PITCH_UNIT * 1.75 *
                                                             draw_scale * staff_scale),
                                                            fill_color='#000000',
                                                            outline_color='',
                                                            tag=['continuationdot'])
                                    elif continuation_dot_style == 'PianoScript':
                                        io['view'].new_polygon(
                                            [
                                                (x + PITCH_UNIT * .75 * draw_scale * staff_scale,
                                                    y_cursor + y),
                                                (x,
                                                    y_cursor + y + PITCH_UNIT * 2 * draw_scale * staff_scale),
                                                (x - PITCH_UNIT * .75 * draw_scale * staff_scale,
                                                    y_cursor + y)],
                                            fill_color='#fff',
                                            outline_color='#000',
                                            width=.3 * draw_scale * staff_scale,
                                            tag=['continuationdot'])

                        # connect stem
                        if evt['type'] == 'connectstem':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff']:
                                x1 = pitch2x_view(
                                    evt['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y1 = tick2y_view(
                                    evt['time'], io, staff_height, idx_line)
                                x2 = pitch2x_view(
                                    evt['pitch2'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y2 = tick2y_view(
                                    evt['time2'], io, staff_height, idx_line)
                                if stem_onoff:
                                    io['view'].new_line(
                                        x1,
                                        y_cursor +
                                        y1,
                                        x2,
                                        y_cursor +
                                        y2,
                                        color='#000000',
                                        width=stem_thickness *
                                        draw_scale * staff_scale,
                                        tag=['connectstem'])

                        # beams
                        if evt['type'] == 'beam':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff'] and beam_onoff:
                                notes = [
                                    note for note in evt['notes'] if note['type'] == 'note']
                                if len(notes) < 2 or all(
                                    EQUALS(
                                        note['time'],
                                        notes[0]['time']) for note in notes):
                                    continue
                                notes = evt['notes']

                                # LEFT BEAM:
                                if evt['hand'] == 'l':
                                    # draw left beam
                                    min_pitch_note = min(
                                        notes, key=lambda x: x['pitch'])
                                    x = pitch2x_view(
                                        min_pitch_note['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                    y1 = tick2y_view(
                                        [note for note in notes if note['type'] == 'note'][0]['time'], io, staff_height, idx_line)
                                    y2 = tick2y_view(
                                        [note for note in notes if note['type'] == 'note'][-1]['time'], io, staff_height, idx_line)
                                    io['view'].new_line(
                                        x - PITCH_UNIT * 5 * draw_scale * staff_scale,
                                        y_cursor + y1,
                                        x - PITCH_UNIT * 6 * draw_scale * staff_scale,
                                        y_cursor + y2,
                                        color='black',
                                        width=beam_thickness * draw_scale * staff_scale,
                                        tag=['beam'])
                                    # connect the stems to the beam
                                    for n in notes:
                                        x1 = pitch2x_view(
                                            n['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                        y1 = tick2y_view(
                                            n['time'], io, staff_height, idx_line)
                                        if n['type'] == 'note':
                                            io['view'].new_line(x1,
                                                                y_cursor + y1,
                                                                x - PITCH_UNIT * 5 * draw_scale * staff_scale - PITCH_UNIT * normalize(notes[0]['time'],
                                                                                                                                       notes[-1]['time'],
                                                                                                                                       n['time']),
                                                                y_cursor + y1,
                                                                color='black',
                                                                width=stem_thickness * draw_scale * staff_scale,
                                                                tag=['beam'])
                                else:
                                    # RIGHT BEAM:
                                    # draw left beam
                                    max_pitch_note = max(
                                        notes, key=lambda x: x['pitch'])
                                    x = pitch2x_view(
                                        max_pitch_note['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                    y1 = tick2y_view(
                                        [note for note in notes if note['type'] == 'note'][0]['time'], io, staff_height, idx_line)
                                    y2 = tick2y_view(
                                        [note for note in notes if note['type'] == 'note'][-1]['time'], io, staff_height, idx_line)
                                    io['view'].new_line(
                                        x + PITCH_UNIT * 5 * draw_scale * staff_scale,
                                        y_cursor + y1,
                                        x + PITCH_UNIT * 6 * draw_scale * staff_scale,
                                        y_cursor + y2,
                                        color='black',
                                        width=beam_thickness * draw_scale * staff_scale,
                                        tag=['beam'])
                                    # connect the stems to the beam
                                    for n in notes:
                                        x1 = pitch2x_view(
                                            n['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                        y1 = tick2y_view(
                                            n['time'], io, staff_height, idx_line)
                                        if n['type'] == 'note':
                                            io['view'].new_line(x1,
                                                                y_cursor + y1,
                                                                x + PITCH_UNIT * 5 * draw_scale * staff_scale + PITCH_UNIT * normalize(notes[0]['time'],
                                                                                                                                       notes[-1]['time'],
                                                                                                                                       n['time']),
                                                                y_cursor + y1,
                                                                color='black',
                                                                width=stem_thickness * draw_scale * staff_scale,
                                                                tag=['beam'])

                        if evt['type'] == 'gracenote':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff'] and note_onoff:
                                # draw grace note
                                x = pitch2x_view(
                                    evt['pitch'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y = y_cursor + \
                                    tick2y_view(evt['time'], io,
                                                staff_height, idx_line)
                                if evt['pitch'] in BLACK_KEYS:
                                    io['view'].new_oval(x - (PITCH_UNIT * 0.75 * draw_scale * staff_scale),
                                                        y,
                                                        x +
                                                        (PITCH_UNIT * 0.75 *
                                                         draw_scale * staff_scale),
                                                        y +
                                                        (PITCH_UNIT * 2 * 0.75 *
                                                         draw_scale * staff_scale),
                                                        tag=[evt['tag'],
                                                             'noteheadblack'],
                                                        fill_color='black',
                                                        outline_width=0,
                                                        outline_color='black')
                                elif evt['pitch'] in WHITE_KEYS:
                                    io['view'].new_oval(x - (PITCH_UNIT * 0.75 * draw_scale * staff_scale),
                                                        y,
                                                        x +
                                                        (PITCH_UNIT * 0.75 *
                                                         draw_scale * staff_scale),
                                                        y +
                                                        (PITCH_UNIT * 2 * 0.75 *
                                                         draw_scale * staff_scale),
                                                        tag=[evt['tag'],
                                                             'noteheadblack'],
                                                        fill_color='white',
                                                        outline_width=0.3,
                                                        outline_color='black')

                        if evt['type'] == 'countline':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff'] and countline_onoff:
                                # draw countline
                                x1 = pitch2x_view(
                                    evt['pitch1'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                x2 = pitch2x_view(
                                    evt['pitch2'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                y = y_cursor + \
                                    tick2y_view(evt['time'], io,
                                                staff_height, idx_line)
                                io['view'].new_line(x1, y, x2, y,
                                                    color='black',
                                                    width=io['score']['properties']['countline_width'] * draw_scale * staff_scale,
                                                    tag=['countline'],
                                                    dash=[.1, 4]) # dotted line

                        if evt['type'] == 'timesignature':
                            if idx_staff == 0:
                                y = y_cursor + tick2y_view(evt['time'], io, staff_height, idx_line)
                                if evt['visible']:
                                    # numerator
                                    io['view'].new_text(x_cursor - (PITCH_UNIT * 7.5 * draw_scale * staff_scale),
                                                        y + (PITCH_UNIT * 4.5),
                                                        str(evt['numerator']),
                                                        color='black',
                                                        tag=['timesignature'],
                                                        size=io['score']['properties']['time_signature_font_size'] * draw_scale * staff_scale,
                                                        font='Courier New',
                                                        anchor='s')
                                    # time-signature middle line
                                    io['view'].new_line(x_cursor - (PITCH_UNIT * 5 * draw_scale * staff_scale),
                                                        y,
                                                        x_cursor - (PITCH_UNIT * 10 * draw_scale * staff_scale),
                                                        y,
                                                        color='black',
                                                        width=io['score']['properties']['barline_width'] * 4 * draw_scale * staff_scale, # same thickness as endbarline
                                                        tag=['timesignature'])
                                    # time-signature dashed line
                                    io['view'].new_line(x_cursor + (PITCH_UNIT * 2 * draw_scale * staff_scale),
                                                        y,
                                                        x_cursor - (PITCH_UNIT * 10 * draw_scale * staff_scale),
                                                        y,
                                                        color='black',
                                                        width=io['score']['properties']['countline_width'] * draw_scale * staff_scale,
                                                        tag=['timesignature'],
                                                        dash=[2, 2])
                                    # denominator
                                    io['view'].new_text(x_cursor - (PITCH_UNIT * 7.5 * draw_scale * staff_scale),
                                                        y - (PITCH_UNIT * 3.5),
                                                        str(evt['denominator']),
                                                        color='black',
                                                        tag=['timesignature'],
                                                        size=io['score']['properties']['time_signature_font_size'] * draw_scale * staff_scale,
                                                        font='Courier New',
                                                        anchor='n')

                        # slurs
                        if evt['type'] == 'slur':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if evt['staff'] == idx_staff:
                                # get coords
                                p0_x = units2x_view(
                                    evt['p0']['distance_c4units'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                p0_y = y_cursor + \
                                    tick2y_view(
                                        evt['p0']['time'], io, staff_height, idx_line)
                                p1_x = units2x_view(
                                    evt['p1']['distance_c4units'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                p1_y = y_cursor + \
                                    tick2y_view(
                                        evt['p1']['time'], io, staff_height, idx_line)
                                p2_x = units2x_view(
                                    evt['p2']['distance_c4units'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                p2_y = y_cursor + \
                                    tick2y_view(
                                        evt['p2']['time'], io, staff_height, idx_line)
                                p3_x = units2x_view(
                                    evt['p3']['distance_c4units'], staff_range[idx_staff], draw_scale * staff_scale, x_cursor)
                                p3_y = y_cursor + \
                                    tick2y_view(
                                        evt['p3']['time'], io, staff_height, idx_line)

                                # drawing the slur
                                points = io['calc'].bezier_curve(
                                    (p0_x, p0_y), (p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y), resolution=50)
                                num_points = len(points)
                                max_width = io['score']['properties']['slur_width_middle'] * draw_scale * staff_scale
                                min_width = io['score']['properties']['slur_width_sides'] * draw_scale * staff_scale
                                range_width = max_width - min_width
                                for i in range(num_points - 1):
                                    width = (
                                        (1 - abs(num_points / 2 - i) / (num_points / 2)) * range_width) + min_width
                                    io['view'].new_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                                                        tag=[
                                                            evt['tag'], 'slur'],
                                                        width=width)
                        
                        # text:
                        if evt['type'] == 'text':

                            if not io['score']['properties']['staffs'][evt['staff']]['onoff']:
                                continue

                            if idx_staff == evt['staff'] and text_onoff:
                                # get xy
                                if evt['side'] == '<':
                                    x = x_cursor - (PITCH_UNIT * evt['mm_from_side'] * draw_scale * staff_scale)
                                    anchor = 'n'
                                else:
                                    x = x_cursor + staff_prefs['staff_width'] + (PITCH_UNIT * evt['mm_from_side'] * draw_scale * staff_scale)
                                    anchor = 'n'
                                y = y_cursor + tick2y_view(evt['time'], io, staff_height, idx_line)

                                # draw:
                                y_correction = 4 # for some reason we need this stupid correction...
                                if evt['side'] == '<':
                                    # text to the left
                                    io['view'].new_text_left(
                                        x=x,
                                        y=y - y_correction,
                                        text=evt['text'],
                                        anchor=anchor,
                                        color='black',
                                        tag=[evt['tag'], 'text'],
                                        font='Courier New Italic',
                                        size=io['score']['properties']['text_font_size'] * draw_scale * staff_scale
                                    )
                                else:
                                    io['view'].new_text_right(
                                        x=x,
                                        y=y - y_correction,
                                        text=evt['text'],
                                        anchor=anchor,
                                        color='black',
                                        tag=[evt['tag'], 'text'],
                                        font='Courier New Italic',
                                        size=io['score']['properties']['text_font_size'] * draw_scale * staff_scale
                                    )

                    x_cursor += staff_prefs['staff_width'] + staff_prefs['margin_right']

                print(f'LINE: {idx_line+1}')
                idx_line += 1

    draw(io)

    # update drawing order
    def drawing_order():
        '''
            set drawing order on tags. the tags are hardcoded in the draweditor class
            they are background, staffline, titletext, barline, etc...
        '''

        drawing_order = [
            'background',
            'midinote',
            'barline',
            'whitespace',
            'staffline',
            'titlebackground',
            'titletext',
            'gridline',
            'barnumbering',
            'connectstem',
            'stem',
            'continuationdot',
            'continuationdot2',
            'countline',
            'noteheadwhite',
            'leftdotwhite',
            'noteheadblack',
            'leftdotblack',
            'timesignature',
            'measurenumber',
            'selectionrectangle',
            'notestop',
            'cursor',
            'handle',
            'linebreak',
            'beam',
            'debug',
            'slur'
        ]
        io['view'].tag_raise(drawing_order)

    drawing_order()

    io['total_pages'] = len(DOC)


class Engraver:
    def __init__(self, io):
        self.io = io

    def do_engrave(self):
        self.io['statusbar'].set_message(message='Engraver is working...')
        self.io['app'].processEvents()
        DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale, barline_times, render_type = pre_render(
            self.io)
        render(
            self.io,
            DOC,
            leftover_page_space,
            staff_dimensions,
            staff_ranges,
            pageno,
            linebreaks,
            draw_scale,
            barline_times,
            render_type)
        print('.......ENGRAVER FINISHED.......\n')
        self.io['statusbar'].set_message(message='Engraver finished :)')
