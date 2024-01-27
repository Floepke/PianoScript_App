import threading, traceback

# we genereally import everything from this file for usage in the engraver, later we add the engraver specific imports here
from imports.engraver.engraverstorage import *
from imports.utils.constants import *
from PySide6.QtCore import QThread, Signal, QObject, Slot


from pprint import pprint

'''
    The Renderer is a really long script. I chose to write it only in functions because 
    I like to program that way. I try to program it in a steps way. First we pre_calculate() 
    then we draw(). pre_calculate() calculates a dict of events which the draw function can 
    use to draw.

    We need to first pre calculate how the music will fit on the page. Then we can draw it.
'''

def pre_render(io, render_type='default'): # render_type = 'default' (render only the current page) | 'export' (render all pages for exporting to pdf)

    # set scene dimensions
    scene_width = io['score']['properties']['page_width']
    scene_height = io['score']['properties']['page_height']

    # set scene rectangle
    io['gui'].print_scene.setSceneRect(0, 0, scene_width, scene_height) # TODO: check if it looks ok

    # page dimentions
    page_margin_left = io['score']['properties']['page_margin_left']
    page_margin_right = io['score']['properties']['page_margin_right']
    page_margin_top = io['score']['properties']['page_margin_up']
    page_margin_bottom = io['score']['properties']['page_margin_down']
    page_width = io['score']['properties']['page_width']
    page_height = io['score']['properties']['page_height']

    # staff dimentions
    draw_scale = io['score']['properties']['draw_scale']
    linebreaks = sorted(io['score']['events']['linebreak'], key=lambda y: y['time'])

    def pre_calculate(io):
        print('-------------------------START-------------------------')
        
        #--------------------------------------------------------------------------------------------------------------------------------------
        # DOC structure:
        # the events are the literal dicts of the json score file like:
        # {"tag": "note6", "pitch": 56, "time": 1024.0, "duration": 256.0, "hand": "r", "staff": 1, "attached": "."}
        # so the DOC list is a structured list of pages and lines within that page and events within that line.

        # the doc we need to fill
        DOC = []

        # data to collect
        leftover_page_space = []
        staff_dimensions = []

        '''
        first we add all types of events:
            - barlines
            - gridlines
            - timesignature changes
            - notes and split them if they are crossing a new line point
        '''
        
        # time signature, barlines and grid
        time = 0
        for gr in io['score']['events']['grid']:
            # calculate the length of one measure based on the numerator and denominator.
            numerator = gr['numerator']
            denominator = gr['denominator']
            measure_length = int(numerator * ((QUARTER_PIANOTICK * 4) / denominator))
            amount = gr['amount']
            grid = gr['grid']
            tsig_length = 0
            
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
        DOC.append({'type': 'endbarline', 'time': io['calc'].get_total_score_ticks()-FRACTION})

        # add all events from io['score]['events] to the doc
        for key in io['score']['events'].keys():
            if key not in ['grid', 'linebreak']:
                for evt in io['score']['events'][key]:
                    new = evt
                    new['type'] = key
                    if evt['type'] in ['endrepeat', 'endsection']:
                        # for certain kinds of objects like end repeat and end section
                        # we need to set the time a fraction earlier because otherwise they
                        # appear at the start of a line while they should appear at the end.
                        new['time'] -= FRACTION
                        DOC.append(new)
                    elif key == 'note':
                        new = note_processor(io, evt)
                        for note in new:
                            DOC.append(note)
                    else:
                        DOC.append(new)
        

        # process the notes for creating continuation dots and stopsigns
        DOC = continuation_dot_and_stopsign_processor(io, DOC)

        # now we sort the events on time-key
        DOC = sorted(DOC, key=lambda y: y['time'])

        '''
            organizing all events in lists of lines:
        '''

        # make a list of tuples for each line: (start_time, end_time)
        linebreak_time_sets = []
        for idx, lb in enumerate(sorted(linebreaks, key=lambda y: y['time'])):
            try: nxt = linebreaks[idx+1]['time']
            except IndexError: nxt = float('inf')
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
        staff_dimensions = []
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
                    staff1_width['staff_width'] = calculate_staff_width(res[0], res[1]) * draw_scale
                elif idx == 1:
                    staff2_width['staff_width'] = calculate_staff_width(res[0], res[1]) * draw_scale
                elif idx == 2:
                    staff3_width['staff_width'] = calculate_staff_width(res[0], res[1]) * draw_scale
                elif idx == 3:
                    staff4_width['staff_width'] = calculate_staff_width(res[0], res[1]) * draw_scale

            # add the margins to the staff width if the staff is on
            if staff1_width['staff_width']: 
                staff1_width['margin_left'] = (lb['staff1']['margins'][0]) * draw_scale
                staff1_width['margin_right'] = (lb['staff1']['margins'][1]) * draw_scale
            else:
                staff1_width['margin_left'] = 0
                staff1_width['margin_right'] = 0
            if staff2_width['staff_width']: 
                staff2_width['margin_left'] = (lb['staff2']['margins'][0]) * draw_scale
                staff2_width['margin_right'] = (lb['staff2']['margins'][1]) * draw_scale
            else:
                staff2_width['margin_left'] = 0
                staff2_width['margin_right'] = 0
            if staff3_width['staff_width']: 
                staff3_width['margin_left'] = (lb['staff3']['margins'][0]) * draw_scale
                staff3_width['margin_right'] = (lb['staff3']['margins'][1]) * draw_scale
            else:
                staff3_width['margin_left'] = 0
                staff3_width['margin_right'] = 0
            if staff4_width['staff_width']: 
                staff4_width['margin_left'] = (lb['staff4']['margins'][0]) * draw_scale
                staff4_width['margin_right'] = (lb['staff4']['margins'][1]) * draw_scale
            else:
                staff4_width['margin_left'] = 0
                staff4_width['margin_right'] = 0

            staff_dimensions.append([staff1_width, staff2_width, staff3_width, staff4_width])
        
        # calculate how many lines will fit on the page / split the line list in parts of pages:
        doc = []
        page = []
        leftover_page_space = []
        remaining_space = 0
        x_cursor = 0
        total_print_width = page_width - page_margin_left - page_margin_right
        for idx, lw, line in zip(range(len(staff_dimensions)), staff_dimensions, DOC):
            # calculate the total width of the line
            total_line_width = 0
            for width in lw:
                total_line_width += width['staff_width'] + width['margin_left'] + width['margin_right']

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
            if idx == len(DOC)-1:
                doc.append(page)
                leftover_page_space.append(remaining_space)

        '''
            FINALLY: place the now structured data in a structured dictionary
            we have now: [pages[lines[events]lines]pages]
        '''

        DOC = doc
        
        # print('-------------------------START-------------------------')
        # for idxpg, pg in enumerate(DOC):
        #     print('new page:', idxpg+1)
        #     for idxln, ln in enumerate(pg):
        #         print('new line:', idxln+1)
        #         for evt in ln:
        #             ...#print(evt)
        # print('--------------------------END--------------------------')
        return DOC, leftover_page_space, staff_dimensions, staff_ranges

    DOC, leftover_page_space, staff_dimensions, staff_ranges = pre_calculate(io)

    # set pageno
    pageno = io['selected_page'] % len(DOC)

    io['num_pages'] = len(DOC)

    return DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale
    
    
    
    
    
    
    
    
def render(io, DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale):
    
    
    def draw(io):

        # delete old drawing
        io['view'].delete_all()

        # define the page dimensions
        page_margin_left = io['score']['properties']['page_margin_left']
        page_margin_right = io['score']['properties']['page_margin_right']
        page_margin_top = io['score']['properties']['page_margin_up']
        page_margin_bottom = io['score']['properties']['page_margin_down']
        page_width = io['score']['properties']['page_width']
        page_height = io['score']['properties']['page_height']

        Left = 0
        Right = page_width
        Top = 0
        Bottom = page_height
        
        # looping trough the DOC structure and drawing the events:
        x_cursor = 0
        y_cursor = 0
        idx_line = 0
        barnumber = 1
        for idx_page, page, leftover in zip(range(len(DOC)), DOC, leftover_page_space):
            if idx_page != pageno:
                idx_line += len(DOC[idx_page])
                barnumber = update_barnumber(DOC, idx_page+1)
                continue
                
            print('new page:')

            # update the cursors
            x_cursor = page_margin_left
            y_cursor = page_margin_top

            # check if this is the frst page; if so we draw the title and composer header
            if idx_page == 0:
                # draw the title
                io['view'].new_text(page_margin_left, 
                                    y_cursor, 
                                    io['score']['header']['title'],
                                    size=8,
                                    tag=['title'],
                                    font='Courier new',
                                    anchor='nw')
                # draw the composer
                io['view'].new_text(Right-page_margin_right, 
                                    y_cursor,
                                    io['score']['header']['composer'],
                                    size=4,
                                    tag=['composer'],
                                    font='Courier new',
                                    anchor='ne') 
                
                staff_height = page_height - page_margin_top - page_margin_bottom - io['score']['properties']['header_height'] - io['score']['properties']['footer_height']
                y_cursor += io['score']['properties']['header_height']
            else:
                staff_height = page_height - page_margin_top - page_margin_bottom - io['score']['properties']['footer_height']
            
            # draw footer copyright pagenumbering and title
            io['view'].new_text(page_margin_left,
                                page_height-page_margin_bottom,
                                f'page {idx_page+1} of {len(DOC)} - '+io['score']['header']['copyright'],
                                size=4,
                                tag=['copyright'],
                                font='Courier new',
                                anchor='sw')
            
            for line, dimensions, staff_range in zip(page, staff_dimensions[idx_line:], staff_ranges[idx_line:]):
                print('new line:')

                # draw the staffs
                for idx_staff, width in enumerate(dimensions):
                    
                    enabled_staffs = 0
                    
                    if width['staff_width']:
                        
                        # update the x_cursor
                        for w in dimensions:
                            if w['staff_width']:
                                enabled_staffs += 1
                        x_cursor += width['margin_left'] + (leftover / (len(page) * enabled_staffs + 1))

                        # draw the staff
                        if linebreaks[idx_line][f'staff{idx_staff+1}']['range'] == 'auto':
                            draw_start = staff_range[idx_staff][0] # calculated in pre_calculate
                            draw_end = staff_range[idx_staff][1]
                        else:
                            draw_start = linebreaks[idx_line][f'staff{idx_staff+1}']['range'][0] # given in file
                            draw_end = linebreaks[idx_line][f'staff{idx_staff+1}']['range'][1]
                        draw_staff(x_cursor, 
                                   y_cursor, 
                                   staff_range[idx_staff][0], 
                                   staff_range[idx_staff][1],
                                   draw_start,
                                   draw_end,
                                   io, 
                                   staff_length=staff_height)

                    for evt in line:

                        if idx_staff == 0:
                            # draw the barlines or endbarline
                            if evt['type'] in ['barline', 'endbarline', 'barlinedouble']:
                                x1 = x_cursor + (PITCH_UNIT * 2 * draw_scale)
                                x2 = x_cursor
                                last_r_marg = 0
                                for i, w in enumerate(dimensions):
                                    if w['staff_width']:
                                        if i > 0: 
                                            x2 += w['margin_left']
                                        x2 += w['staff_width'] + w['margin_right'] + (leftover / (len(page) * enabled_staffs + 1))
                                        last_r_marg = w['margin_right']
                                x2 -= last_r_marg + (leftover / (len(page) * enabled_staffs + 1)) + (PITCH_UNIT * 2 * draw_scale)
                                #x2 += 10 # overlapping barlines
                                #if evt['type'] == 'barlinedouble': x2 -= last_r_marg
                                y = tick2y_view(evt['time'], io, staff_height, idx_line)
                                if evt['type'] in ['barline', 'barlinedouble']: w = 0.2*draw_scale
                                else: w = 1*draw_scale
                                io['view'].new_line(x1,
                                                    y_cursor+y,
                                                    x2,
                                                    y_cursor+y,
                                                    width=w,
                                                    color='black',
                                                    tag=['barline'])
                                # draw barnumbering
                                if float(evt['time']).is_integer():
                                    io['view'].new_text(x2-2, 
                                                    y_cursor+y-4, 
                                                    str(barnumber),
                                                    size=4,
                                                    tag=['barnumbering'],
                                                    font='Courier new',
                                                    anchor='nw')
                                    barnumber += 1
                        
                        if width['staff_width']:
                            # draw the gridlines
                            if evt['type'] in ['gridline', 'gridlinedouble']:
                                x1 = x_cursor + (PITCH_UNIT * 2 * draw_scale)
                                x2 = x_cursor + width['staff_width'] - (PITCH_UNIT * 2 * draw_scale)
                                y = tick2y_view(evt['time'], io, staff_height, idx_line)
                                io['view'].new_line(x1,
                                                    y_cursor+y,
                                                    x2,
                                                    y_cursor+y,
                                                    width=.1*draw_scale,
                                                    color='black',
                                                    dash=[14, 20],
                                                    tag=['gridline'])
                        
                        # draw the notes
                        if evt['type'] in ['note', 'notesplit']:

                            if idx_staff == evt['staff']:
                                x = pitch2x_view(evt['pitch'], staff_range[idx_staff], draw_scale, x_cursor)
                                y1 = tick2y_view(evt['time'], io, staff_height, idx_line)
                                y2 = tick2y_view(evt['time']+evt['duration'], io, staff_height, idx_line)
                                
                                if evt['type'] == 'note':
                                    if evt['pitch'] in BLACK_KEYS:
                                        io['view'].new_oval(x-PITCH_UNIT*.75*draw_scale,
                                                        y_cursor+y1,
                                                        x+PITCH_UNIT*.75*draw_scale,
                                                        y_cursor+y1-(PITCH_UNIT*2.25*draw_scale),
                                                        fill_color='#000000',
                                                        outline_color='#000000',
                                                        outline_width=.4*draw_scale,
                                                        tag=['noteheadblack'])
                                    else:
                                        io['view'].new_oval(x-PITCH_UNIT*draw_scale,
                                                        y_cursor+y1,
                                                        x+PITCH_UNIT*draw_scale,
                                                        y_cursor+y1+(PITCH_UNIT*2.25*draw_scale),
                                                        fill_color='#ffffff',
                                                        outline_color='#000000',
                                                        outline_width=.4*draw_scale,
                                                        tag=['noteheadwhite'])
                                        
                                    # left hand dot
                                    if evt['hand'] == 'l':
                                        if not evt['pitch'] in BLACK_KEYS:
                                            io['view'].new_oval(x-PITCH_UNIT*.25*draw_scale,
                                                        y_cursor+y1+(PITCH_UNIT*(2.25/2-.25)*draw_scale),
                                                        x+PITCH_UNIT*.25*draw_scale,
                                                        y_cursor+y1+(PITCH_UNIT*(2.25/2+.25)*draw_scale),
                                                        fill_color='#000000',
                                                        outline_color='',
                                                        tag=['leftdotwhite'])
                                        else:
                                            io['view'].new_oval(x-PITCH_UNIT*.25*draw_scale,
                                                        y_cursor+y1+(PITCH_UNIT*(2.25/2-.25)*draw_scale),
                                                        x+PITCH_UNIT*.25*draw_scale,
                                                        y_cursor+y1+(PITCH_UNIT*(2.25/2+.25)*draw_scale),
                                                        fill_color='#ffffff',
                                                        outline_color='',
                                                        tag=['leftdotblack'])
                                    
                                    # draw stem
                                    if evt['hand'] == 'r': 
                                        io['view'].new_line(x,
                                                        y_cursor+y1,
                                                        x+PITCH_UNIT*5*draw_scale,
                                                        y_cursor+y1,
                                                        width=.6*draw_scale,
                                                        tag=['stem'])
                                    else:
                                        io['view'].new_line(x,
                                                        y_cursor+y1,
                                                        x-PITCH_UNIT*5*draw_scale,
                                                        y_cursor+y1,
                                                        width=.6*draw_scale,
                                                        tag=['stem'])
                                
                                # draw midinote
                                io['view'].new_polygon([(x, y_cursor+y1),
                                                        (x+PITCH_UNIT*draw_scale, y_cursor+y1+PITCH_UNIT*draw_scale),
                                                        (x+PITCH_UNIT*draw_scale, y_cursor+y2),
                                                        (x-PITCH_UNIT*draw_scale, y_cursor+y2),
                                                        (x-PITCH_UNIT*draw_scale, y_cursor+y1+PITCH_UNIT*draw_scale)],
                                                        fill_color='#aaa',
                                                        outline_color='',
                                                        width=0,
                                                        tag=['midinote']),
                        
                        if evt['type'] == 'notestop':
                            if idx_staff == evt['staff']:
                                x = pitch2x_view(evt['pitch'], staff_range[idx_staff], draw_scale, x_cursor)
                                y = tick2y_view(evt['time'], io, staff_height, idx_line)
                                io['view'].new_polygon([(x, y_cursor+y-PITCH_UNIT*2*draw_scale), 
                                                        (x+PITCH_UNIT*draw_scale, y_cursor+y),
                                                        (x-PITCH_UNIT*draw_scale, y_cursor+y)],
                                                    fill_color='#000000',
                                                    outline_color='',
                                                    tag=['notestop'])

                                    
                        # draw continuation dot
                        if evt['type'] == 'continuationdot':
                            if idx_staff == evt['staff']:
                                x = pitch2x_view(evt['pitch'], staff_range[idx_staff], draw_scale, x_cursor)
                                y = tick2y_view(evt['time'], io, staff_height, idx_line)
                                io['view'].new_oval(x-PITCH_UNIT*.5*draw_scale,
                                                    y_cursor+y+(PITCH_UNIT*.5*draw_scale),
                                                    x+PITCH_UNIT*.5*draw_scale,
                                                    y_cursor+y+(PITCH_UNIT*1.5*draw_scale),
                                                    fill_color='#000000',
                                                    outline_color='',
                                                    tag=['continuationdot'])
                        
                        # connect stem
                        if evt['type'] == 'connectstem':
                            if idx_staff == evt['staff']:
                                x1 = pitch2x_view(evt['pitch'], staff_range[idx_staff], draw_scale, x_cursor)
                                y1 = tick2y_view(evt['time'], io, staff_height, idx_line)
                                x2 = pitch2x_view(evt['pitch2'], staff_range[idx_staff], draw_scale, x_cursor)
                                y2 = tick2y_view(evt['time2'], io, staff_height, idx_line)
                                io['view'].new_line(x1, y_cursor+y1, 
                                                    x2, y_cursor+y2,
                                                    color='#000000',
                                                    width=.6*draw_scale, 
                                                    tag=['connectstem'])
                                

                    x_cursor += width['staff_width'] + width['margin_right']

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
            'staffline',
            'titlebackground',
            'titletext',
            'barline', 
            'gridline', 
            'barnumbering',
            'stem',
            'continuationdot',
            'connectstem',
            'noteheadwhite',
            'leftdotwhite',
            'noteheadblack',
            'leftdotblack',
            'timesignature', 
            'measurenumber',
            'selectionrectangle',
            'notestop',
            'cursor',
            'countline',
            'handle',
            'linebreak'
        ]
        io['view'].tag_raise(drawing_order)
    
    drawing_order()

    io['total_pages'] = len(DOC)


from PySide6.QtCore import QThread, Signal

class Worker(QThread):
    pre_render_finished = Signal(tuple)

    def __init__(self, io):
        super().__init__()
        self.io = io

    def run(self):
        result = pre_render(self.io)
        self.pre_render_finished.emit(result)

class Engraver:
    def __init__(self, io):
        self.io = io
        self.worker = Worker(self.io)
        self.worker.pre_render_finished.connect(self.render_start)

    def pre_render_start(self):
        self.worker.start()

    def render_start(self, result):
        DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale = result
        render(self.io, DOC, leftover_page_space, staff_dimensions, staff_ranges, pageno, linebreaks, draw_scale)

    def do_engrave(self):
        self.pre_render_start()








































































