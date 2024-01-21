# in HARDCODE.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *
from imports.design.note import Note

class DrawEditor:
    '''The DrawEditor class handles all the drawing parts for the editor'''

    @staticmethod
    def draw_titles(io:dict):
        '''Draws the title and composer name of the score file on the topleft corner of the editor'''

        # draw title background
        io['editor'].new_rectangle(EDITOR_LEFT, EDITOR_TOP, EDITOR_RIGHT, EDITOR_MARGIN,
                                      fill_color=BACKGROUND_COLOR, 
                                      outline_color=BACKGROUND_COLOR,
                                      tag=['titlebackground'])
        
        # draw bottom background to hide the stafflines
        io['editor'].new_rectangle(EDITOR_LEFT, EDITOR_TOP, EDITOR_RIGHT, EDITOR_MARGIN,
                                      fill_color=BACKGROUND_COLOR, 
                                      outline_color=BACKGROUND_COLOR,
                                      tag=['titlebackground'])

        title = "'" + io['score']['header']['title'] + "'" + ' by composer: ' + io['score']['header']['composer']
        io['editor'].new_text(EDITOR_LEFT, 0, title, 
                              tag=['titletext'], 
                              anchor='nw', 
                              size=20, 
                              font='Courier New')

    @staticmethod
    def draw_staff(io:dict):
        '''Draws the staff'''
        
        # calculating staff length
        editor_zoom = io['score']['properties']['editor_zoom']
        staff_length = io['total_ticks'] * (editor_zoom / QUARTER_PIANOTICK)
        # get the total screen height of the pc

        x_curs = EDITOR_LEFT + EDITOR_MARGIN

        # draw the A#0 staffline
        io['editor'].new_line(x_curs,
                              EDITOR_MARGIN,
                              x_curs,
                              EDITOR_MARGIN+staff_length,
                              width=2,
                              tag=['staffline'],
                              color='#000000')
        
        x_curs += (STAFF_X_UNIT_EDITOR * 2)

        for octave in range(7): # 7 octaves

            for _ in range(2): # draw group of 2 stafflines
                if octave == 3:
                    # draw the clef (dashed line)
                    io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN+staff_length,
                        width=1,
                        tag=['staffline'],
                        dash=(6,6),
                        color='black')
                else:
                    io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN+staff_length,
                        width=1,
                        tag=['staffline'],
                        color='black')
                x_curs += STAFF_X_UNIT_EDITOR

            x_curs += STAFF_X_UNIT_EDITOR

            for _ in range(3): # draw group of 3 stafflines, traditionally they are is thicker
                io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN+staff_length,
                        width=2,
                        tag=['staffline'],
                        color='black')
                x_curs += STAFF_X_UNIT_EDITOR

            x_curs += STAFF_X_UNIT_EDITOR

    @staticmethod
    def draw_barlines_grid_timesignature_and_measurenumbers(io:dict, top, bttm):
        '''Draws the barlines, grid, timesignature and measure numbers'''
        print('---------------START DRAW BARLINES GRID TIMESIGNATURE AND MEASURENUMBERS---------------')
        # calculating dimensions
        staff_width = EDITOR_WIDTH - (EDITOR_MARGIN * 2)
        editor_zoom = io['score']['properties']['editor_zoom']

        y_cursor = EDITOR_MARGIN
        measure_numbering = 0

        io['editor'].delete_with_tag(['barline', 'timesignature', 'measurenumber', 'gridline'])

        for gr in io['score']['events']['grid']:
            print(gr)
            # draw the timesignature indicator
            io['editor'].new_text(EDITOR_LEFT + (EDITOR_MARGIN / 2), 
                                  y_cursor,
                                  str(gr['numerator']), 
                                  tag=['timesignature'], 
                                  anchor='s', 
                                  size=40, 
                                  font='Courier New')
            io['editor'].new_line(EDITOR_LEFT + EDITOR_MARGIN - (EDITOR_MARGIN / 3), 
                                  y_cursor, 
                                  EDITOR_LEFT + (EDITOR_MARGIN / 3), 
                                  y_cursor, 
                                  width=6, 
                                  tag=['timesignature'], 
                                  color='black')
            io['editor'].new_line(EDITOR_LEFT + EDITOR_MARGIN, 
                                  y_cursor, 
                                  EDITOR_LEFT + (EDITOR_MARGIN / 3), 
                                  y_cursor,
                                  width=2,
                                  tag=['timesignature'],
                                  color='black',
                                  dash=(2, 4))
            io['editor'].new_text(EDITOR_LEFT + (EDITOR_MARGIN / 2), 
                                  y_cursor, 
                                  str(gr['denominator']),
                                  tag=['timesignature'], 
                                  anchor='n', 
                                  size=40, 
                                  font='Courier New')
            
            # measure length in pianoticks
            measure_length = io['calc'].get_measure_length(gr)
            amount = gr['amount']

            for _ in range(amount):

                measure_numbering += 1
                
                if y_cursor > top-1000 and y_cursor < bttm+1000:
                
                    # draw the barline
                    io['editor'].new_line(EDITOR_LEFT + EDITOR_MARGIN,
                                        y_cursor,
                                        EDITOR_RIGHT - EDITOR_MARGIN,
                                        y_cursor,
                                        width=2,
                                        tag=['barline'],
                                        color='black')
                    
                    # draw the measure number
                    io['editor'].new_text(EDITOR_LEFT,
                                        y_cursor,
                                        str(measure_numbering),
                                        tag=['measurenumber'],
                                        anchor='nw',
                                        size=30,
                                        font='Courier New')

                    # draw the gridlines
                    for tick in gr['grid']:
                        tick *= (editor_zoom / QUARTER_PIANOTICK)
                        io['editor'].new_line(EDITOR_LEFT + EDITOR_MARGIN,
                                            y_cursor + tick,
                                            EDITOR_LEFT + EDITOR_MARGIN + staff_width,
                                            y_cursor + tick,
                                            width=0.5,
                                            tag=['gridline'],
                                            dash=(7,7),
                                            color='black')
                
                # move the y_curs
                y_cursor += measure_length * (editor_zoom / QUARTER_PIANOTICK)
                print('y_cursor', y_cursor, 'measure length', measure_length)

                # if this is the last iteration and last iteration from gr: draw the endline
                if _ == amount - 1 and gr == io['score']['events']['grid'][-1]:
                    io['editor'].new_line(EDITOR_LEFT + EDITOR_MARGIN,
                                          y_cursor,
                                          EDITOR_LEFT + EDITOR_MARGIN + staff_width,
                                          y_cursor,
                                          width=4,
                                          tag=['barline'],
                                          color='black')

    @staticmethod
    def draw_line_cursor(io, x, y):
        '''Draws the cursor'''
        # delete the old cursor
        io['editor'].delete_with_tag(['cursor'])

        # get the cursor position
        y = io['calc'].y2tick_editor(y, snap=True)
        y = io['calc'].tick2y_editor(y)

        # draw the new cursor
        io['editor'].new_line(EDITOR_LEFT, y, EDITOR_LEFT+EDITOR_MARGIN, y,
                              width=2, 
                              tag=['cursor'], 
                              color='black',
                              dash=(4,4))
        io['editor'].new_line(EDITOR_RIGHT-EDITOR_MARGIN, y, EDITOR_RIGHT, y,
                              width=2, 
                              tag=['cursor'], 
                              color='black',
                              dash=(4,4))
        

    @staticmethod
    def move_staff(io, y):
        '''moves the staff to the y position'''
        stafflines = io['editor'].find_with_tag(['staffline'])
        for staffline in stafflines:
            # TODO: fit the stafflines to the screen
            staffline.setPos(0, y-EDITOR_MARGIN-EDITOR_MARGIN)


    
    
    
    
    
    
    
    
    
    
    @staticmethod
    def add_soundingdots_and_stopsigns_to_viewport(io):
        '''updates the soundingdots and stopsings'''

        # delete the old soundingdots and stopsings
        io['editor'].delete_with_tag(['notestop', 'connectstem'])

        unit = STAFF_X_UNIT_EDITOR / 2
        color = '#000000'

        for note in io['viewport']['events']['note']:
            
            note_start = note['time']
            note_end = note['time']+note['duration']
            stopflag = True

            # add the sounding dot to the drawing queue
            def sounding_dot(time, pitch, n):
                tag = [n['tag'], note['tag'], 'soundingdot']
                dot = {
                    'tag': tag,
                    'time':time,
                    'pitch':pitch,
                }
                if not dot in io['viewport']['events']['dot']:
                    io['viewport']['events']['dot'].append(dot)

            for n in io['viewport']['events']['note']: # N == THE COMPARED NOTE TODO: change folder structure in measures
                # connect chords (if two or more notes start at the same time)
                if note['hand'] == n['hand'] and n['time'] == note['time'] and not note['tag'] == 'notecursor':
                    x1 = io['calc'].pitch2x_editor(note['pitch'])
                    x2 = io['calc'].pitch2x_editor(n['pitch'])
                    y = io['calc'].tick2y_editor(note['time'])
                    io['editor'].new_line(x1,y,x2,y,
                        tag=[n['tag'], note['tag'], 'connectstem'],
                        width=5,
                        color='black')
                
                # continuation dot:
                # there are 5 possible situations where we have to draw a continuation dot
                # if we draw one, we have also to check if this continuation dot is on the 
                # same hand as the note and if the pitch is one semitone higher or lower, 
                # so that we can draw the notehead upwards further in the code.
                comp_start = n['time']
                comp_end = n['time']+n['duration']
                # GREATER, LESS and EQUALS are defined in constants.py and applies a small treshold to the comparison
                if GREATER(comp_end, note_start) and LESS(comp_end, note_end) and note['hand'] == n['hand']:
                    sounding_dot(n['time']+n['duration'], note['pitch'], n)

                if LESS(note_end, comp_end) and GREATER(note_end, comp_start) and note['hand'] == n['hand']:
                    sounding_dot(note['time']+note['duration'], n['pitch'], n)

                if GREATER(note_start, comp_start) and LESS(note_start, comp_end) and note['hand'] == n['hand']:
                    sounding_dot(note['time'], n['pitch'], n)

                if GREATER(comp_start, note_start) and LESS(comp_start, note_end) and note['hand'] == n['hand']:
                    sounding_dot(n['time'], note['pitch'], n)

                # stop sign desicion:
                if EQUALS(comp_start, note_end) and note['hand'] == n['hand']:
                    stopflag = False
            
            # notestop sign:
            if stopflag and not note['tag'] == 'notecursor':
                x = io['calc'].pitch2x_editor(note['pitch'])
                y = io['calc'].tick2y_editor(note['time']+note['duration'])

                if io['score']['properties']['stop_sign_style'] == 'Klavarskribo':
                    # traditional stop sign:
                    io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR/2), y-(STAFF_X_UNIT_EDITOR),
                        x, y,
                        tag=[note['tag'], 'notestop'],
                        width=2,
                        color=color)
                    io['editor'].new_line(x, y,
                        x+(STAFF_X_UNIT_EDITOR/2), y-(STAFF_X_UNIT_EDITOR),
                        tag=[note['tag'], 'notestop'],
                        width=2,
                        color=color)
                elif io['score']['properties']['stop_sign_style'] == 'PianoScript':
                    # experimental stopsign:
                    points = [(x, y-(STAFF_X_UNIT_EDITOR)), (x+(STAFF_X_UNIT_EDITOR/2), y), (x-(STAFF_X_UNIT_EDITOR/2), y)]
                    io['editor'].new_polygon(points,
                        tag=[note['tag'], 'notestop'],
                        width=0,
                        fill_color=color)
                io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR), y, x+(STAFF_X_UNIT_EDITOR), y,
                    tag=[note['tag'], 'notestop'],
                    width=.75,
                    dash=[3, 3],
                    color=color)
        


















