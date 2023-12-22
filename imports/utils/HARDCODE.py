'''
    This file contains all the hard-coded values used in the program.
    All values are capitalized and separated by underscores to indicate 
    that they are constants.
'''

# a pianotick is a float representing the length of a note.
# a quarter pianotick is 256 pianoticks so an eighth pianotick is 128 pianoticks and so on.
QUARTER_PIANOTICK = 256.0

# the 'blueprint' for a score; it's the fallback score if no score is loaded and a reference for the developer.
# if we write a property in the blueprint that is not in the score, it will be added to the score by the FixScore() class.
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
        "date":"30-09-2023",
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
        "printview-width(procents-froms-creen)":33,
        "editor-x-zoom":35,
        "editor-y-zoom":80,
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
        "amount":4,
        "numerator":4,
        "denominator":4,
        "grid":4,
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