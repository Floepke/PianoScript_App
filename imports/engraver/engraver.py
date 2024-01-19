import threading, traceback

# we genereally import everything from this file for usage in the engraver, later we add the engraver specific imports here
from imports.engraver.engravercalc import *
from imports.utils.constants import *

from pprint import pprint

'''
    The Renderer is a really long script. I chose to write it only in functions because 
    I like to program that way. I try to program it in a steps way. First we pre_calculate() 
    then we draw(). pre_calculate() calculates a dict of events which the draw function can 
    use to draw.

    We need to first pre calculate how the music will fit on the page. Then we can draw it.
'''

def render(io, render_type='default'): # render_type = 'default' (render only the current page) | 'export' (render all pages for exporting to pdf)

    # set scene dimensions
    if render_type == 'default':
        scene_width = io['score']['properties']['page_width']
        scene_height = io['score']['properties']['page_height']
    else:
        scene_width = io['score']['properties']['page_width']
        scene_height = 0 # TODO: calculate the height of the entire score by counting the pages

    # set scene rectangle
    io['gui'].print_scene.setSceneRect(0, 0, scene_width, scene_height) # TODO: check if it looks ok

    def pre_calculate(io):
        
        #--------------------------------------------------------------------------------------------------------------------------------------
        # DOC structure:
        # the events are the literal dicts of the json score file like:
        # {"tag": "note6", "pitch": 56, "time": 1024.0, "duration": 256.0, "hand": "r", "staff": 1, "attached": "."}
        # so the DOC list is a structured list of pages and lines within that page and events within that line.
        # below a detailed description of the structure.
        DOC = [
            { # page1
                'left_over_space': 100, # the space thats leftover on the page if we write all lines with the reserved margins
                0:{ # line1
                    'staff_widths': [120, 80, 0, 0], # this list gives the staff_width for each staff, if zero the staff is off
                    'start_tick': 0, # the tick where the line starts
                    'end_tick': 4096, # the tick where the line ends
                    'system_width': 200, # the width of the entire line including all 4 staffs and margins
                    'events': [
                        {"tag": "note6", "pitch": 56, "time": 1024.0, "duration": 256.0, "hand": "r", "staff": 1, "attached": "."}, # event1
                        # event2...
                        # event3...
                        # etc
                    ]
                },
                # line2...1:{}
                # line3...2:{}
                # etc...
            },
            # page2...
            # page3...
            # etc
        ]
        #--------------------------------------------------------------------------------------------------------------------------------------

        # the doc we need to fill
        DOC = []

        # data to collect
        page_spacing = []
        staff_widths = []
        
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

        '''
        first we add all types of events:
            - barlines with numbering
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
        line_widths = []
        for lb, line in zip(linebreaks, DOC):

            staff1_width = 0
            staff2_width = 0
            staff3_width = 0
            staff4_width = 0

            # get the highest and lowest pitch of every staff
            range_every_staff = range_staffs(io, line, lb)

            # calculate the width of every staff
            for idx, res in enumerate(range_every_staff):
                if idx == 0:
                    staff1_width += calculate_staff_width(res[0], res[1]) * draw_scale
                elif idx == 1:
                    staff2_width += calculate_staff_width(res[0], res[1]) * draw_scale
                elif idx == 2:
                    staff3_width += calculate_staff_width(res[0], res[1]) * draw_scale
                elif idx == 3:
                    staff4_width += calculate_staff_width(res[0], res[1]) * draw_scale

            # add the margins to the staff width
            if staff1_width: staff1_width += (lb['staff1']['margins'][0] + lb['staff1']['margins'][1]) * draw_scale
            if staff2_width: staff2_width += (lb['staff2']['margins'][0] + lb['staff2']['margins'][1]) * draw_scale
            if staff3_width: staff3_width += (lb['staff3']['margins'][0] + lb['staff3']['margins'][1]) * draw_scale
            if staff4_width: staff4_width += (lb['staff4']['margins'][0] + lb['staff4']['margins'][1]) * draw_scale

            line_widths.append([staff1_width, staff2_width, staff3_width, staff4_width])
        
        print(line_widths)


        # for linebreak in io['score']['events']['linebreak']:
        #     pprint(linebreak)


        
        # print('-------------------------START-------------------------')
        # for ln in DOC:
        #     print('new line:')
        #     for evt in ln:
        #         print(evt)
        # print('--------------------------END--------------------------')
        return DOC


    def draw(io):
        
        ...

    # running the pre_calculate() and draw() functions
    DOC = pre_calculate(io)
    draw(io)

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
                self.do_eng