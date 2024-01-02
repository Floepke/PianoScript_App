'''
    This file contains all the hard-coded values used in the program.
    All values are capitalized and separated by underscores to indicate 
    that they are constants.
'''
# the default text of the statusbar.
STATUSBAR_DEFAULT_TEXT = 'Ready to write music :D'

# a pianotick is a float representing the length of a note.
# a quarter pianotick is 256 pianoticks so an eighth pianotick is 128 pianoticks and so on.
QUARTER_PIANOTICK = 256.0

# the 'blueprint' for a score; it's the fallback score if no score is loaded and a reference for the developer.
# if we write a property in the blueprint that is not in the score, it will be added to the score by the
# FixScore() class based on this blueprint.
import datetime
SCORE_TEMPLATE = {
    'header':{
        'title':{
            'text':'Untitled',
            'x-offset':0,
            'y-offset':0,
            'visible':True
        },
        'composer':{
            'text':'PianoScript',
            'x-offset':0,
            'y-offset':0,
            'visible':True
        },
        'copyright':{
            'text':'\u00a9 PianoScript 2023',
            'x-offset':0,
            'y-offset':0,
            'visible':True
        },
        'app-name':'pianoscript',
        'app-version':1.0,
        'timestamp':datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S'),
        'genre':'',
        'comment':''
    },
    'properties':{
        'page-width':210,
        'page-height':297,
        'page-margin-left':10,
        'page-margin-right':10,
        'page-margin-up':10,
        'page-margin-down':10,
        'draw-scale':1,
        'header-height':10,
        'footer-height':10,
        'minipiano':True,
        'engraver':'pianoscript vertical',
        'color-right-hand-midinote':'#c8c8c8',
        'color-left-hand-midinote':'#c8c8c8',
        'editor-zoom':180, # size in pixels per quarter note
        'staffonoff':True,
        'stemonoff':True,
        'beamonoff':True,
        'noteonoff':True,
        'midinoteonoff':True,
        'notestoponoff':True,
        'pagenumberingonoff':True,
        'barlinesonoff':True,
        'basegridonoff':True,
        'countlineonoff':True,
        'measurenumberingonoff':True,
        'accidentalonoff':True,
        'staff':[
            {
                'onoff':True,
                'name':'Staff 1',
                'staff-number':0,
                'staff-scale':1.0
            },
            {
                'onoff':False,
                'name':'Staff 2',
                'staff-number':1,
                'staff-scale':1.0
            },
            {
                'onoff':False,
                'name':'Staff 3',
                'staff-number':2,
                'staff-scale':1.0
            },
            {
                'onoff':False,
                'name':'Staff 4',
                'staff-number':3,
                'staff-scale':1.0
            }
        ],
        'soundingdotonoff':True,
        'black-note-style':'PianoScript',
        'threelinescale':1,
        'stop-sign-style':'PianoScript',
        'leftdotonoff':True
    },
    'events':{
        'grid':[
            {
        'tag':'grid',
        'amount':105,
        'numerator':3,
        'denominator':8,
        'grid':[128, 256], # a list of ticks relative to the start of every measure. every tick is a gridline
        'visible':True
      }
    ],
    'note':[],
    'countline':[],
    'staffsizer':[],
    'startrepeat':[],
    'endrepeat':[],
    'starthook':[],
    'endhook':[]
  }
}

# # the test template to test any new functionality
# SCORE_TEMPLATE = {
#     'header':{
#         'title':{
#             'text':'Untitled',
#             'x-offset':0,
#             'y-offset':0,
#             'visible':True
#         },
#         'composer':{
#             'text':'PianoScript',
#             'x-offset':0,
#             'y-offset':0,
#             'visible':True
#         },
#         'copyright':{
#             'text':'\u00a9 PianoScript 2023',
#             'x-offset':0,
#             'y-offset':0,
#             'visible':True
#         },
#         'app-name':'pianoscript',
#         'app-version':1.0,
#         'timestamp':datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S'),
#         'genre':'',
#         'comment':''
#     },
#     'properties':{
#         'page-width':210,
#         'page-height':297,
#         'page-margin-left':10,
#         'page-margin-right':10,
#         'page-margin-up':10,
#         'page-margin-down':10,
#         'draw-scale':1,
#         'header-height':10,
#         'footer-height':10,
#         'minipiano':True,
#         'engraver':'pianoscript vertical',
#         'color-right-hand-midinote':'#c8c8c8',
#         'color-left-hand-midinote':'#c8c8c8',
#         'editor-zoom':80, # size in pixels per quarter note
#         'staffonoff':True,
#         'stemonoff':True,
#         'beamonoff':True,
#         'noteonoff':True,
#         'midinoteonoff':True,
#         'notestoponoff':True,
#         'pagenumberingonoff':True,
#         'barlinesonoff':True,
#         'basegridonoff':True,
#         'countlineonoff':True,
#         'measurenumberingonoff':True,
#         'accidentalonoff':True,
#         'staff':[
#             {
#                 'onoff':True,
#                 'name':'Staff 1',
#                 'staff-number':0,
#                 'staff-scale':1.0
#             },
#             {
#                 'onoff':False,
#                 'name':'Staff 2',
#                 'staff-number':1,
#                 'staff-scale':1.0
#             },
#             {
#                 'onoff':False,
#                 'name':'Staff 3',
#                 'staff-number':2,
#                 'staff-scale':1.0
#             },
#             {
#                 'onoff':False,
#                 'name':'Staff 4',
#                 'staff-number':3,
#                 'staff-scale':1.0
#             }
#         ],
#         'soundingdotonoff':True,
#         'black-note-style':'PianoScript',
#         'threelinescale':1,
#         'stop-sign-style':'PianoScript',
#         'leftdotonoff':True
#     },
#     'events':{
#         'grid':[
#             {
#         'tag':'grid',
#         'amount':16,
#         'numerator':4,
#         'denominator':4,
#         'grid':[256, 512, 768], # a list of ticks relative to the start of the measure. every tick is a gridline
#         'visible':True
#       }
#     ],
#     'note':[
#         {
#         'tag':'#note2',
#         'time':0.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note3',
#         'time':0.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note4',
#         'time':0.0,
#         'duration':256.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note5',
#         'time':256.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 384.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note6',
#         'time':256.0,
#         'duration':256.0,
#         'pitch':42,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 384.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note7',
#         'time':256.0,
#         'duration':128.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note8',
#         'time':384.0,
#         'duration':128.0,
#         'pitch':45,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note9',
#         'time':512.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 704.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note10',
#         'time':512.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 704.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note11',
#         'time':768.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 896.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note12',
#         'time':768.0,
#         'duration':256.0,
#         'pitch':42,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 896.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note13',
#         'time':512.0,
#         'duration':192.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note14',
#         'time':704.0,
#         'duration':64.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note15',
#         'time':768.0,
#         'duration':128.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note16',
#         'time':896.0,
#         'duration':128.0,
#         'pitch':45,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note17',
#         'time':1024.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note18',
#         'time':1024.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note19',
#         'time':1024.0,
#         'duration':256.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note20',
#         'time':1280.0,
#         'duration':128.0,
#         'pitch':48,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note21',
#         'time':1408.0,
#         'duration':128.0,
#         'pitch':45,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note22',
#         'time':1536.0,
#         'duration':512.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1792.0 1920.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note23',
#         'time':1280.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1408.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note24',
#         'time':1280.0,
#         'duration':256.0,
#         'pitch':42,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1408.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note25',
#         'time':1536.0,
#         'duration':384.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1792.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note26',
#         'time':1536.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note27',
#         'time':1792.0,
#         'duration':256.0,
#         'pitch':45,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1920.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note28',
#         'time':0.0,
#         'duration':512.0,
#         'pitch':28,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 256.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note29',
#         'time':0.0,
#         'duration':256.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note30',
#         'time':256.0,
#         'duration':256.0,
#         'pitch':36,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note31',
#         'time':512.0,
#         'duration':512.0,
#         'pitch':28,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 768.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note32',
#         'time':512.0,
#         'duration':256.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note33',
#         'time':768.0,
#         'duration':256.0,
#         'pitch':36,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note34',
#         'time':1024.0,
#         'duration':512.0,
#         'pitch':28,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1280.0 1408.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note35',
#         'time':1024.0,
#         'duration':256.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note36',
#         'time':1536.0,
#         'duration':256.0,
#         'pitch':28,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1664.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note37',
#         'time':1280.0,
#         'duration':128.0,
#         'pitch':33,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note38',
#         'time':1408.0,
#         'duration':128.0,
#         'pitch':36,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note39',
#         'time':1536.0,
#         'duration':128.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note40',
#         'time':1664.0,
#         'duration':128.0,
#         'pitch':31,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note41',
#         'time':1792.0,
#         'duration':128.0,
#         'pitch':36,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note42',
#         'time':1920.0,
#         'duration':128.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note43',
#         'time':1920.0,
#         'duration':128.0,
#         'pitch':39,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note44',
#         'time':1792.0,
#         'duration':256.0,
#         'pitch':30,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 1920.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note45',
#         'time':2048.0,
#         'duration':256.0,
#         'pitch':52,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2176.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note46',
#         'time':2304.0,
#         'duration':128.0,
#         'pitch':52,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note47',
#         'time':2432.0,
#         'duration':128.0,
#         'pitch':54,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note48',
#         'time':2560.0,
#         'duration':256.0,
#         'pitch':55,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2688.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note49',
#         'time':2816.0,
#         'duration':256.0,
#         'pitch':52,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2944.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note50',
#         'time':3072.0,
#         'duration':256.0,
#         'pitch':50,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 3200.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note51',
#         'time':2048.0,
#         'duration':128.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note52',
#         'time':2176.0,
#         'duration':128.0,
#         'pitch':50,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note53',
#         'time':2304.0,
#         'duration':256.0,
#         'pitch':48,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2432.0 2432.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note54',
#         'time':2048.0,
#         'duration':384.0,
#         'pitch':40,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2176.0 2304.0 2304.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note56',
#         'time':2944.0,
#         'duration':128.0,
#         'pitch':48,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note57',
#         'time':3072.0,
#         'duration':128.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note58',
#         'time':3200.0,
#         'duration':128.0,
#         'pitch':45,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note59',
#         'time':3328.0,
#         'duration':128.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note60',
#         'time':3712.0,
#         'duration':128.0,
#         'pitch':42,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note61',
#         'time':3840.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':True
#       },
#       {
#         'tag':'#note62',
#         'time':2048.0,
#         'duration':256.0,
#         'pitch':31,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note63',
#         'time':2304.0,
#         'duration':256.0,
#         'pitch':33,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2432.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note64',
#         'time':2560.0,
#         'duration':256.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note65',
#         'time':2816.0,
#         'duration':256.0,
#         'pitch':36,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note66',
#         'time':3072.0,
#         'duration':512.0,
#         'pitch':38,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 3328.0 3456.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note67',
#         'time':3584.0,
#         'duration':384.0,
#         'pitch':31,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note68',
#         'time':3968.0,
#         'duration':128.0,
#         'pitch':30,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':True
#       },
#       {
#         'tag':'#note69',
#         'time':2048.0,
#         'duration':256.0,
#         'pitch':35,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note70',
#         'time':2304.0,
#         'duration':128.0,
#         'pitch':36,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note71',
#         'time':2432.0,
#         'duration':384.0,
#         'pitch':38,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2560.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note73',
#         'time':2816.0,
#         'duration':256.0,
#         'pitch':40,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note74',
#         'time':3072.0,
#         'duration':256.0,
#         'pitch':42,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note75',
#         'time':3328.0,
#         'duration':128.0,
#         'pitch':40,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note76',
#         'time':3456.0,
#         'duration':128.0,
#         'pitch':42,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note77',
#         'time':3584.0,
#         'duration':512.0,
#         'pitch':38,
#         'hand':'l',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 3968.0',
#         'end-of-note':True
#       },
#       {
#         'tag':'#note78',
#         'time':2560.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2688.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note79',
#         'time':2816.0,
#         'duration':256.0,
#         'pitch':43,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2944.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note81',
#         'time':3456.0,
#         'duration':256.0,
#         'pitch':45,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 3584.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note82',
#         'time':3328.0,
#         'duration':256.0,
#         'pitch':48,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 3456.0',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note83',
#         'time':3584.0,
#         'duration':512.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 3712.0 3840.0',
#         'end-of-note':True
#       },
#       {
#         'tag':'#note84',
#         'time':2432.0,
#         'duration':128.0,
#         'pitch':42,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note85',
#         'time':2560.0,
#         'duration':128.0,
#         'pitch':47,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':'',
#         'end-of-note':False
#       },
#       {
#         'tag':'#note86',
#         'time':2688.0,
#         'duration':256.0,
#         'pitch':50,
#         'hand':'r',
#         'stem_visible':True,
#         'accidental':0,
#         'staff':0,
#         'notestop':True,
#         'type':'note',
#         'continuation_dot':' 2816.0 2816.0',
#         'end-of-note':False
#       }
#     ],
#     'ornament':[],
#     'text':[],
#     'beam':[],
#     'bpm':[],
#     'slur':[],
#     'pedal':[],
#     'linebreak':[
#       {
#         'tag':'linebreak',
#         'time':0,
#         'margin-staff1-left':10,
#         'margin-staff1-right':10,
#         'margin-staff2-left':10,
#         'margin-staff2-right':10,
#         'margin-staff3-left':10,
#         'margin-staff3-right':10,
#         'margin-staff4-left':10,
#         'margin-staff4-right':10
#       }
#     ],
#     'countline':[],
#     'staffsizer':[],
#     'startrepeat':[],
#     'endrepeat':[],
#     'starthook':[],
#     'endhook':[]
#   }
# }

# the black keys of a piano keyboard as a list of integers starting from 1 and ending at 88
BLACK_KEYS = [2, 5, 7, 10, 12, 14, 17, 19, 22, 24, 26, 29, 31, 34, 36, 38, 41, 43, 46,
         48, 50, 53, 55, 58, 60, 62, 65, 67, 70, 72, 74, 77, 79, 82, 84, 86]

# the white keys of a piano keyboard as a list of integers starting from 1 and ending at 88
WHITE_KEYS = [1, 3, 4, 6, 8, 9, 11, 13, 15, 16, 18, 20, 21, 23, 25, 27,
         28, 30, 32, 33, 35, 37, 39, 40, 42, 44, 45, 47, 49,
         51, 52, 54, 56, 57, 59, 61, 63, 64, 66, 68, 69,
         71, 73, 75, 76, 78, 80, 81, 83, 85, 87, 88]


# ----------editor and printview dimensions for easy calculations (all pixel values get's scaled by the QGraphicView)----------

# the width of the QGraphicView
WIDTH = 1024

# the margin of the QGraphicView
EDITOR_MARGIN = WIDTH / 6

# the height of the QGraphicView (only used in the printview)
import math
HEIGHT = WIDTH * math.sqrt(2)

# the right side position of the QGraphicView
RIGHT = WIDTH / 2

# the left side position of the QGraphicView
LEFT = -RIGHT

# the top side position of the QGraphicView
TOP = 0

# the bottom side position of the QGraphicView (only used in the printview)
BOTTOM = HEIGHT

# the x unit is the distance between (for example) the c# and d# stafflines.
# 49 is the sum of units of a full piano keyboard if we count the units from key 2 to 87,
# which are the outer sides of the staff in the editor.
STAFF_X_UNIT_EDITOR = (WIDTH - (EDITOR_MARGIN * 2)) / 49

# ----------------------------------------------------------------------------------------------------------------------------



