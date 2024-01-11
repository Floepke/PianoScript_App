import datetime

class Score:
    
    def __init__(self):

        self.header = self.Header()

        self.properties = self.Properties()

    class Header:

        def __init__(self):
            
            self.title = 'Untitled'
            self.composer = 'Pianoscript'
            self.copyright = 'Copyright (C) 2024, Pianoscript. All rights reserved.'
            self.app_name = 'pianoscript'
            self.app_version = 1.0
            self.timestamp = datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S')
            self.genre = ''
            self.comment = ''

    class Properties:

        def __init__(self):
            
            # layout:
            self.page_width = 210
            self.page_height = 297
            self.page_margin_left = 10
            self.page_margin_right = 10
            self.page_margin_up = 10
            self.page_margin_down = 10
            self.draw_scale = 1
            self.header_height = 10
            self.footer_height = 10
            self.color_right_midinote = '#c8c8c8'
            self.color_left_midinote = '#c8c8c8'
            self.editor_zoom = 80
            self.threelinescale = 1.
            self.black_note_rule = ['AlwaysUp', 'AlwaysDown', 'OnlyChordUp', 'AlwaysDownExceptCollisions', 'AlwaysUpExceptCollisions'][2]
            self.stop_sign_style = ['PianoScript', 'Klavarskribo'][0]

            # onoff:
            self.minipiano = True
            self.staff_onoff = True
            self.stem_onoff = True
            self.beam_onoff = True
            self.note_onoff = True
            self.midinote_onoff = True
            self.notestop_onoff = True
            self.pagenumbering_onoff = True
            self.barlines_onoff = True
            self.basegrid_onoff = True
            self.countline_onoff = True
            self.measurenumbering_onoff = True
            self.accidental_onoff = True
            self.leftdot_onoff = True
            self.soundingdotonoff = True

            # staffs
            self.staffs = {
                    '1':{
                        'onoff':True,
                        'staff-number':0,
                        'staff-scale':1.0
                    },
                    '2':{
                        'onoff':False,
                        'staff-number':1,
                        'staff-scale':1.0
                    },
                    '3':{
                        'onoff':False,
                        'staff-number':2,
                        'staff-scale':1.0
                    },
                    '4':{
                        'onoff':False,
                        'name':'Staff 4',
                        'staff-number':3,
                        'staff-scale':1.0
                    }
                }
        
