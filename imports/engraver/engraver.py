import threading, traceback

# we genereally import everything from this file for usage in the engraver, later we add the engraver specific imports here
from imports.engraver.engraverstorage import *
from imports.utils.constants import *
from PySide6.QtCore import QThread, QMetaObject, Qt


from pprint import pprint

'''
    The Renderer is a really long script. I chose to write it only in functions because 
    I like to program that way. I try to program it in a steps way. First we pre_calculate() 
    then we draw(). pre_calculate() calculates a dict of events which the draw function can 
    use to draw.

    We need to first pre calculate how the music will fit on the page. Then we can draw it.
'''

def render(io, render_type='default', pageno=0): # render_type = 'default' (render only the current page) | 'export' (render all pages for exporting to pdf)

    # set scene dimensions
    if render_type == 'default':
        scene_width = io['score']['properties']['page_width']
        scene_height = io['score']['properties']['page_height']
    else:
        scene_width = io['score']['properties']['page_width']
        scene_height = 0 # TODO: calculate the height of the entire score by counting the pages

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
        for gr in io['score']['events']['grid']:
            # calculate the length of one measure based on the numerator and denominator.
            numerator = gr['numerator']
            denominator = gr['denominator']
            measure_length = int(numerator * ((QUARTER_PIANOTICK * 4) / denominator))
            amount = gr['amount']
            grid = gr['grid']
            
            # add barlines and gridlines
            for m in range(amount):
                # add barlines
                DOC.append({
                    'type': 'barline',
                    'time': measure_length * m
                })
                DOC.append({
                    'type': 'barline',
                    'time': measure_length * m - FRACTION
                })
                for g in grid:
                    # add gridlines
                    DOC.append({
                        'type': 'gridline',
                        'time': measure_length * m + g
                    })
                    DOC.append({
                        'type': 'gridline',
                        'time': measure_length * m + g - FRACTION
                    })
        
        # add endbarline event
        DOC.append({'type': 'endbarline', 'time': io['calc'].get_total_score_ticks()-FRACTION})

        # add all events from io['score]['events] to the doc
        for key in io['score']['events'].keys():
            if key not in ['grid', 'linebreak']:
                for evt in io['score']['events'][key]:
                    new = evt
                    new['type'] = key
                    if key == 'note':
                        new = note_split_processor(io, evt)
                        for note in new:
                            DOC.append(note)
                    elif evt['type'] in ['endrepeat', 'endsection']:
                        # for certain kinds of objects like end repeat and end section
                        # we need to set the time a fraction earlier because otherwise they
                        # appear at the start of a line while they should appear at the end.
                        new['time'] -= FRACTION
                        DOC.append(new)
                    else:
                        DOC.append(new)
        
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

    # NOTE: leftover_page_space = page
    # NOTE: staff_widths = line
    # NOTE: staff_ranges = line
    
    
    
    
    
    
    
    
    
    
    
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
        
        # draw test margin rectangle
        io['view'].new_rectangle(Left, 
                                 Top, 
                                 Right, 
                                 Bottom,
                                 fill_color='white',
                                 width=.2,
                                 tag=['paper'])
        
        # draw margin
        io['view'].new_rectangle(Left + page_margin_left, 
                                 Top + page_margin_top, 
                                 Right - page_margin_right, 
                                 Bottom - page_margin_bottom,
                                 outline_color='#0000ff',
                                 fill_color='',
                                 width=.2,
                                 tag=['margin'])
        
        
        # looping trough the DOC structure and drawing the events:
        x_cursor = 0
        y_cursor = 0
        idx_line = 0
        for idx_page, page, leftover in zip(range(len(DOC)), DOC, leftover_page_space):
            if idx_page != pageno:
                continue
            print('new page:', leftover)

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
                
                staff_length = page_height - page_margin_top - page_margin_bottom - io['score']['properties']['header_height'] - io['score']['properties']['footer_height']
                
                y_cursor += io['score']['properties']['header_height']

            else:
                staff_length = page_height - page_margin_top - page_margin_bottom - io['score']['properties']['footer_height']

            for line, staff_width, staff_range in zip(page, staff_dimensions, staff_ranges):
                print('new line:', staff_width, staff_range)

                # draw the staffs
                for idx_staff, width in enumerate(staff_width):
                    
                    if width['staff_width']:
                        
                        # update the x_cursor
                        enabled_staffs = 0
                        for w in staff_width:
                            if w['staff_width']:
                                enabled_staffs += 1
                        x_cursor += width['margin_left'] + (leftover / (len(page) * enabled_staffs + 1))

                        # draw the staff
                        draw_staff(x_cursor, 
                                   y_cursor, 
                                   staff_range[idx_staff][0], 
                                   staff_range[idx_staff][1], 
                                   io, 
                                   staff_length=staff_length)

                    for evt in line:
                        # print(evt, staff_width)

                        if width['staff_width']:
                            # draw the stafflines
                            if evt['type'] == 'barline':
                                x1 = x_cursor + (PITCH_UNIT * 2 * draw_scale)
                                x2 = x_cursor + width['staff_width'] - (PITCH_UNIT * 2 * draw_scale)
                                y = tick2y_view(evt['time'], io, staff_length, idx_line)
                                io['view'].new_line(x1,
                                                    y_cursor+y,
                                                    x2,
                                                    y_cursor+y,
                                                    width=0.2,
                                                    color='black',
                                                    tag=['barline'])
                                print('barline', x1, x2, x2-x1)
                        
                        if width['staff_width']:
                            # draw the gridlines
                            if evt['type'] == 'gridline':
                                x1 = x_cursor + (PITCH_UNIT * 2 * draw_scale)
                                x2 = x_cursor + width['staff_width'] - (PITCH_UNIT * 2 * draw_scale)
                                y = tick2y_view(evt['time'], io, staff_length, idx_line)
                                io['view'].new_line(x1,
                                                    y_cursor+y,
                                                    x2,
                                                    y_cursor+y,
                                                    width=.1,
                                                    color='black',
                                                    dash=[5, 5],
                                                    tag=['gridline'])

                    x_cursor += width['staff_width'] + width['margin_right']

                idx_line += 1

    draw(io)

# class Engraver(QThread):
#     def __init__(self, io):
#         super().__init__()
#         self.io = io

#     def run(self):
#         try:
#             render(self.io)
#         except Exception:
#             traceback.print_exc()

#     def do_engrave(self):
#         if not self.isRunning():
#             self.start()

class Engraver:
    '''
        This class cares for handling rendering requests. it prevents 
        unnecessary rendering. It checks if the previous request is 
        still in progress and runs after finishing the latest request.
        The requests are handled by a thread.
    '''
    
    def __init__(self, io):
        self.lock = threading.Lock()
        self.thread = None
        self.render_in_progress = False
        self.latest_request = False
        self.io = io

    def do_engrave(self):
        with self.lock:
            if self.render_in_progress:
                # Another render request is already in progress. Ignoring the current request.
                self.latest_request = True
                return
            self.latest_request = False
            self.render_in_progress = True
            self.thread = threading.Thread(target=self.renderer)
            self.thread.start()

    def renderer(self):
        try:
            render(self.io)
        except Exception:
            traceback.print_exc()
        finally:
            self.render_in_progress = False
            if self.latest_request:
                self.do_engrave()




































































