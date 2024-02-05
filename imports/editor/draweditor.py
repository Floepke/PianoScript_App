# in HARDCODE.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *
from imports.design.note import Note
import copy

class DrawEditor:
    '''The DrawEditor class handles all the drawing parts for the editor'''

    @staticmethod
    def draw_titles(io:dict):
        '''Draws the title and composer name of the score file on the topleft corner of the editor'''

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
        # calculating dimensions
        staff_width = EDITOR_WIDTH - (EDITOR_MARGIN * 2)
        editor_zoom = io['score']['properties']['editor_zoom']

        y_cursor = EDITOR_MARGIN
        measure_numbering = 0

        io['editor'].delete_with_tag(['barline', 'timesignature', 'measurenumber', 'gridline'])

        for gr in io['score']['events']['grid']:
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

        def continuation_dot(time, pitch, note):
            dot = {
                'time':time,
                'pitch':pitch,
                'type':'continuationdot',
                'staff':note['staff']
            }
            io['viewport']['events']['dot'].append(dot)

        def stop_sign(time, pitch, note):
            stop = {
                'time':time,
                'pitch':pitch,
                'type':'notestop',
                'staff': note['staff']
            }
            io['viewport']['events']['stop'].append(stop)

        # delete the old soundingdots and stopsings
        io['editor'].delete_with_tag(['notestop', 'connectstem'])

        unit = STAFF_X_UNIT_EDITOR / 2

        # making a list of noteon and noteoff messages like a linear midi file
        note_on_off = []
        for note in io['viewport']['events']['note']:
            evt = copy.deepcopy(note)
            evt['endtime'] = evt['time'] + evt['duration']
            note_on_off.append(copy.deepcopy(evt))
            evt = copy.deepcopy(evt)
            evt['type'] = 'noteoff'
            note_on_off.append(copy.deepcopy(evt))
        note_on_off = sorted(note_on_off, key=lambda y: y['time'] if y['type'] == 'note' else y['endtime'])  

        # we add the notestop and continuationdot events
        active_notes = []
        for idx, note in enumerate(note_on_off):
        
            if note['type'] == 'note':
                active_notes.append(note)
                for n in active_notes:
                    # continuation dots for note start:
                    if n != note:
                        if (not EQUALS(n['endtime'], note['time']) and
                            note['staff'] == n['staff'] and
                            note['hand'] == n['hand']):
                            continuation_dot(note['time'], n['pitch'], note)
                            print('!!!')
        
            elif note['type'] == 'noteoff':
                for n in active_notes:
                    if (n['duration'] == note['duration'] and 
                        n['pitch'] == note['pitch'] and 
                        n['staff'] == note['staff'] and 
                        n['hand'] == note['hand']):
                        active_notes.remove(n)
                        break

                
                for idx_n, n in enumerate(active_notes):
                    # continuation dots for note end:
                    if n != note:
                        if (not EQUALS(n['endtime'], note['endtime']) and
                            note['staff'] == n['staff'] and
                            note['hand'] == n['hand']):
                            continuation_dot(note['endtime'], n['pitch'], note)

            if note['type'] == 'noteoff':
                continue
            
            stop_flag = False

            # stop sign:
            for n in note_on_off[idx+1:]:
                if (n['type'] == 'note' and 
                    EQUALS(n['time'], note['time']+note['duration']) and 
                    n['staff'] == note['staff'] and 
                    n['hand'] == note['hand']):
                    break
                if (n['type'] == 'note' and 
                    GREATER(n['time'], note['time']+note['duration']) and 
                    n['staff'] == note['staff'] and
                    n['hand'] == note['hand']):
                    stop_flag = True
                    break
                if n == note_on_off[-1]:
                    stop_flag = True

            if stop_flag:
                stop_sign(note['time']+note['duration']-FRACTION, note['pitch'], note)

            # # connect stem
            # for n in note_on_off[idx+1:]:
            #     if (EQUALS(n['time'], note['time']) and
            #         n['staff'] == note['staff'] and
            #         n['hand'] == note['hand']):
            #         DOC.append(
            #             {
            #                 'type': 'connectstem',
            #                 'time': note['time'],
            #                 'pitch': note['pitch'],
            #                 'time2': note['time'],
            #                 'pitch2': n['pitch'],
            #                 'staff': note['staff']
            #             }
            #         )
            #     if n['time'] > note['time']:
            #         break
        


















