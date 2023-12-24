'''
    This file contains all the hard-coded values used in the program.
    All values are capitalized and separated by underscores to indicate 
    that they are constants.
'''

# a pianotick is a float representing the length of a note.
# a quarter pianotick is 256 pianoticks so an eighth pianotick is 128 pianoticks and so on.
QUARTER_PIANOTICK = 256.0

# the 'blueprint' for a score; it's the fallback score if no score is loaded and a reference for the developer.
# if we write a property in the blueprint that is not in the score, it will be added to the score by the
# FixScore() class based on this blueprint.
import datetime
SCORE_TEMPLATE = {
    "header":{
        "title":{
            "text":"Untitled",
            "x-offset":0,
            "y-offset":0,
            "visible":True
        },
        "composer":{
            "text":"PianoScript",
            "x-offset":0,
            "y-offset":0,
            "visible":True
        },
        "copyright":{
            "text":"\u00a9 PianoScript 2023",
            "x-offset":0,
            "y-offset":0,
            "visible":True
        },
        "app-name":"pianoscript",
        "app-version":1.0,
        "timestamp":datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S"),
        "genre":"",
        "comment":""
    },
    "properties":{
        "page-width":210,
        "page-height":297,
        "page-margin-left":10,
        "page-margin-right":10,
        "page-margin-up":10,
        "page-margin-down":10,
        "draw-scale":1,
        "header-height":10,
        "footer-height":10,
        "minipiano":True,
        "engraver":"pianoscript vertical",
        "color-right-hand-midinote":"#c8c8c8",
        "color-left-hand-midinote":"#c8c8c8",
        "editor-zoom":80, # size in pixels per quarter note
        "staffonoff":True,
        "stemonoff":True,
        "beamonoff":True,
        "noteonoff":True,
        "midinoteonoff":True,
        "notestoponoff":True,
        "pagenumberingonoff":True,
        "barlinesonoff":True,
        "basegridonoff":True,
        "countlineonoff":True,
        "measurenumberingonoff":True,
        "accidentalonoff":True,
        "staff":[
            {
                "onoff":True,
                "name":"Staff 1",
                "staff-number":0,
                "staff-scale":1.0
            },
            {
                "onoff":False,
                "name":"Staff 2",
                "staff-number":1,
                "staff-scale":1.0
            },
            {
                "onoff":False,
                "name":"Staff 3",
                "staff-number":2,
                "staff-scale":1.0
            },
            {
                "onoff":False,
                "name":"Staff 4",
                "staff-number":3,
                "staff-scale":1.0
            }
        ],
        "soundingdotonoff":True,
        "black-note-style":"PianoScript",
        "threelinescale":1,
        "stop-sign-style":"PianoScript",
        "leftdotonoff":True
    },
    "events":{
        "grid":[
            {
        "tag":"grid",
        "amount":16,
        "numerator":4,
        "denominator":4,
        "grid":4, # a list of ticks relative to the start of the measure. every tick is a gridline
        "visible":True
      }
    ],
    "note":[],
    "ornament":[],
    "text":[],
    "beam":[],
    "bpm":[],
    "slur":[],
    "pedal":[],
    "linebreak":[
      {
        "tag":"linebreak",
        "time":0,
        "margin-staff1-left":10,
        "margin-staff1-right":10,
        "margin-staff2-left":10,
        "margin-staff2-right":10,
        "margin-staff3-left":10,
        "margin-staff3-right":10,
        "margin-staff4-left":10,
        "margin-staff4-right":10
      }
    ],
    "countline":[],
    "staffsizer":[],
    "startrepeat":[],
    "endrepeat":[],
    "starthook":[],
    "endhook":[]
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

EDITOR_MARGIN = 150 # pixels