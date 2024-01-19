'''
    This file contains all the hard-coded values used in the program.
    All values are capitalized and separated by underscores to indicate 
    that they are constants.
'''
# the background color of the editor and print view
BACKGROUND_COLOR = '#fee'

# the default text of the statusbar.
STATUSBAR_DEFAULT_TEXT = 'Ready to write music :D'

# a pianotick is a float representing the length of a note.
# a quarter pianotick is 256 pianoticks so an eighth pianotick is 128 pianoticks and so on.
QUARTER_PIANOTICK = 256.0

# fraction is a really small value for if we need to offset a value for a small fraction
FRACTION = 0.0000001

# the 'blueprint' for a score; it's the fallback score if no score is loaded and a reference for the developer.
# if we write a property in the blueprint that is not in the score, it will be added to the score by the
# FixScore() class based on this blueprint. TODO: Create a FixScore class
import datetime
from imports.utils.savefilestructure import SaveFileStructureSource
SCORE_TEMPLATE = {
    'header':{
        'title':'Untitled',
        'composer':'PianoScript',
        'copyright':'Copyright (C) 2024, Pianoscript. All rights reserved.',
        'app_name':'pianoscript',
        'app_version':1.0,
        'timestamp':datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S'),
        'genre':'',
        'comment':''
    },
    'properties':{
        'page_width':210, # all measurements are in millimeters
        'page_height':297,
        'page_margin_left':10,
        'page_margin_right':10,
        'page_margin_up':10,
        'page_margin_down':10,
        'draw_scale':1,
        'header_height':10,
        'footer_height':10,
        'color_right_midinote':'#c8c8c8',
        'color_left_midinote':'#c8c8c8',
        'editor_zoom':80, # size in pixels per quarter note
        'black_note_rule':[
            'AlwaysUp', 
            'AlwaysDown', 
            'OnlyChordUp', 
            'AlwaysDownExceptCollisions', 
            'AlwaysUpExceptCollisions'
            ][2],
        'threeline_scale':1,
        'stop_sign_style':['PianoScript', 'Klavarskribo'][0],
        'continuation_dot_style':['PianoScript', 'Klavarskribo'][1],
        
        'staff_onoff':True,
        'minipiano_onoff':True,
        'stem_onoff':True,
        'beam_onoff':True,
        'note_onoff':True,
        'midinote_onoff':True,
        'notestop_onoff':True,
        'page_numbering_onoff':True,
        'barlines_onoff':True,
        'basegrid_onoff':True,
        'countline_onoff':True,
        'measure_numbering_onoff':True,
        'accidental_onoff':True,
        'soundingdot_onoff':True,
        'leftdot_onoff':True,
        'staffs':(
            {
                'onoff':True,
                'name':'Staff 1',
                'staff_scale':1.0
            },
            {
                'onoff':False,
                'name':'Staff 2',
                'staff_scale':1.0
            },
            {
                'onoff':False,
                'name':'Staff 3',
                'staff_scale':1.0
            },
            {
                'onoff':False,
                'name':'Staff 4',
                'staff_scale':1.0
            }
        )
    },
    'events':{
        'grid':[
            {
        'tag':'grid',
        'amount':8,
        'numerator':4,
        'denominator':4,
        'grid':[256, 512, 768], # a list of ticks relative to the start of every measure. every tick is a gridline
        'visible':True
      }
    ],
    'note':[],
    'countline':[],
    'linebreak':[
        SaveFileStructureSource.new_linebreak('lockedlinebreak', 0)
    ],
    'staffsizer':[],
    'startrepeat':[],
    'endrepeat':[],
    'starthook':[],
    'endhook':[],
    'dot':[],
    'stop':[],
  }
}

# the black keys of a piano keyboard as a list of integers starting from 1 and ending at 88
BLACK_KEYS = [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46,
         48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]

# the white keys of a piano keyboard as a list of integers starting from 1 and ending at 88
WHITE_KEYS = [1, 3, 4, 6, 8, 9, 11, 13, 15, 16, 18, 20, 21, 23, 25, 27,
         28, 30, 32, 33, 35, 37, 39, 40, 42, 44, 45, 47, 49,
         51, 52, 54, 56, 57, 59, 61, 63, 64, 66, 68, 69,
         71, 73, 75, 76, 78, 80, 81, 83, 85, 87, 88]

# in the comparison of equals, this is the treshold for the difference between two floats that is used in the code to deside
# if two floats are equal or not. If the difference between two floats is smaller than this treshold, the floats are considered equal.
EQUALS_TRESHOLD = 7
def EQUALS(a, b):
    return abs(a - b) < EQUALS_TRESHOLD
def LESS(a, b):
    return a < b - EQUALS_TRESHOLD
def GREATER(a, b):
    return a > b + EQUALS_TRESHOLD


# ----------editor and printview dimensions for easy calculations (all pixel values get's scaled by the QGraphicView)----------

# the width of the QGraphicView
EDITOR_WIDTH = 1024

# the margin of the QGraphicView
EDITOR_MARGIN = EDITOR_WIDTH / 6

# the right side position of the QGraphicView
EDITOR_RIGHT = EDITOR_WIDTH / 2

# the left side position of the QGraphicView
EDITOR_LEFT = -EDITOR_RIGHT

# the top side position of the QGraphicView
EDITOR_TOP = 0

# the x unit is the distance between (for example) the c# and d# stafflines.
# 49 is the sum of units of a full piano keyboard if we count the units from key 2 to 87,
# which are the outer sides of the staff in the editor.
STAFF_X_UNIT_EDITOR = (EDITOR_WIDTH - (EDITOR_MARGIN * 2)) / 49

# ----------------------------------------------------------------------------------------------------------------------------

# this is the staff x unit but in relation to mm. So the size in mm of the distance 
# between the c# and d# stafflines (if the draw_scale is set to 1.0).
PITCH_UNIT = 1