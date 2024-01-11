import threading, traceback

# we genereally import everything from this file for usage in the engraver, later we add the engraver specific imports here
from imports.engraver.calcdump import *
from imports.utils.constants import *

'''
    The Renderer is a really long script. I chose to write it only in functions because 
    I like to program that way. I try to program it in a steps way. First we pre_calculate() 
    then we draw(). pre_calculate() calculates a dict of events which the draw function can 
    use to draw.

    We need to first pre calculate how the music will fit on the page. Then we can draw it.
'''

def render(io, render_type='default'): # render_type = 'default' (render only the current page) | 'export' (render all pages for exporting to pdf)

    def pre_calculate(io):
        
        # page dimentions
        page_orientation = io['score']['properties']['page_orientation']
        page_margin_left = io['score']['properties']['page_margin_left']
        page_margin_right = io['score']['properties']['page_margin_right']
        page_margin_top = io['score']['properties']['page_margin_up']
        page_margin_bottom = io['score']['properties']['page_margin_down']
        draw_scale = io['score']['properties']['draw_scale']

        # calculate the page dimentions
        if page_orientation == 'portrait':
            page_width = WIDTH
            page_height = HEIGHT
        elif page_orientation == 'landscape':
            page_width = HEIGHT
            page_height = WIDTH 


    def draw(io):
        
        ...

    # running the pre_calculate() and draw() functions
    pre_calculate(io)
    draw(io)

class Engraver:
    '''This class cares for handling rendering requests and only render the relevant requests.'''
    
    def __init__(self, io):
        self.lock = threading.Lock()
        self.thread = None
        self.render_in_progress = False
        self.latest_request = False
        self.io = io

    def do_engrave(self):
        with self.lock:
            if self.render_in_progress:
                self.latest_request = True
                print("Another render request is already in progress. Ignoring the current request.")
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


