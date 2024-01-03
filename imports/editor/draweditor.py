# in HARDCODE.py you can find all constants that are used in the application along with the description.
from imports.utils.constants import *
from imports.design.note import Note

class DrawEditor:
    '''The DrawEditor class handles all the drawing parts for the editor'''

    @staticmethod
    def draw_titles(io:dict):
        '''Draws the title and composer name of the score file on the topleft corner of the editor'''

        title = "'" + io['score']['header']['title']['text'] + "'" + ' by composer: ' + io['score']['header']['composer']['text']
        io['editor'].new_text(LEFT, 0, title, 
                              tag=['titletext'], 
                              anchor='nw', 
                              size=20, 
                              font='Courier New')

    @staticmethod
    def draw_background(io:dict):
        '''Draws the background'''

        # calculate the height of the background
        total_ticks = io['calc'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom'] # the size in pixels per quarter note
        background_height = total_ticks * (editor_zoom / QUARTER_PIANOTICK) + (EDITOR_MARGIN * 2)
        
        # create the background rectangle
        io['editor'].new_rectangle(LEFT, TOP, RIGHT, background_height,
                                   fill_color='#eeeeeeff', 
                                   outline_color='#eeeeeeff',
                                   tag=['background'])

    @staticmethod
    def draw_staff(io:dict):
        '''Draws the staff'''
        
        # calculating staff length
        total_ticks = io['calc'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom']
        staff_length = total_ticks * (editor_zoom / QUARTER_PIANOTICK)

        x_curs = LEFT + EDITOR_MARGIN

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
                    io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN + staff_length,
                        width=1,
                        tag=['staffline'],
                        dash=(6,6),
                        color='black')
                else:
                    io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN + staff_length,
                        width=1,
                        tag=['staffline'],
                        color='black')
                x_curs += STAFF_X_UNIT_EDITOR

            x_curs += STAFF_X_UNIT_EDITOR

            for _ in range(3): # draw group of 3 stafflines, traditionally they are is thicker
                io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN + staff_length,
                        width=2,
                        tag=['staffline'],
                        color='black')
                x_curs += STAFF_X_UNIT_EDITOR

            x_curs += STAFF_X_UNIT_EDITOR

    @staticmethod
    def draw_barlines_grid_timesignature_and_measurenumbers(io:dict):
        '''Draws the barlines, grid, timesignature and measure numbers'''

        # calculating dimensions
        staff_width = WIDTH - (EDITOR_MARGIN * 2)
        editor_zoom = io['score']['properties']['editor-zoom']

        y_cursor = EDITOR_MARGIN
        measure_numbering = 0

        for gr in io['score']['events']['grid']:

            # draw the timesignature indicator
            io['editor'].new_text(LEFT + (EDITOR_MARGIN / 2), y_cursor,
                                  str(gr['numerator']), 
                                  tag=['timesignature'], 
                                  anchor='s', 
                                  size=40, 
                                  font='Courier New')
            io['editor'].new_line(LEFT + EDITOR_MARGIN - (EDITOR_MARGIN / 3), y_cursor, LEFT + (EDITOR_MARGIN / 3), y_cursor, 
                                  width=6, 
                                  tag=['timesignature'], 
                                  color='black')
            io['editor'].new_line(LEFT + EDITOR_MARGIN, y_cursor, LEFT + (EDITOR_MARGIN / 3), y_cursor,
                                  width=2,
                                  tag=['timesignature'],
                                  color='black',
                                  dash=(2, 4))
            io['editor'].new_text(LEFT + (EDITOR_MARGIN / 2), y_cursor, str(gr['denominator']),
                                  tag=['timesignature'], 
                                  anchor='n', 
                                  size=40, 
                                  font='Courier New')
            
            # measure length in pianoticks
            measure_length = io['calc'].get_measure_length(gr)
            amount = gr['amount']

            for _ in range(amount):
                
                # draw the barline
                io['editor'].new_line(LEFT + EDITOR_MARGIN,
                                      y_cursor,
                                      RIGHT - EDITOR_MARGIN,
                                      y_cursor,
                                      width=2,
                                      tag=['barline'],
                                      color='black')
                
                # draw the measure number
                measure_numbering += 1
                io['editor'].new_text(LEFT,
                                      y_cursor,
                                      str(measure_numbering),
                                      tag=['barline'],
                                      anchor='nw',
                                      size=30,
                                      font='Courier New')

                # draw the gridlines
                for tick in gr['grid']:
                    tick *= (editor_zoom / QUARTER_PIANOTICK)
                    io['editor'].new_line(LEFT + EDITOR_MARGIN,
                                          y_cursor + tick,
                                          LEFT + EDITOR_MARGIN + staff_width,
                                          y_cursor + tick,
                                          width=0.5,
                                          tag=['barline'],
                                          dash=(7,7),
                                          color='black')
                
                # move the y_curs
                y_cursor += measure_length * (editor_zoom / QUARTER_PIANOTICK)

                # if this is the last iteration and last iteration from gr: draw the endline
                if _ == amount - 1 and gr == io['score']['events']['grid'][-1]:
                    io['editor'].new_line(LEFT + EDITOR_MARGIN,
                                          y_cursor,
                                          LEFT + EDITOR_MARGIN + staff_width,
                                          y_cursor,
                                          width=4,
                                          tag=['barline'],
                                          color='black')
    
    @staticmethod
    def draw_notes(io):
        '''Draws the notes of the score'''
        for note in io['score']['events']['note']:
            # if the note is in the current viewport, draw it
            if note['time'] >= io['viewport']['toptick'] and note['time'] <= io['viewport']['bottomtick'] or note['time'] + note['duration'] >= io['viewport']['toptick'] and note['time'] + note['duration'] <= io['viewport']['bottomtick']:
                if note in io['selection']['selection_buffer']['note']:
                    Note.draw_editor(io, note, inselection=True)
                else:
                    Note.draw_editor(io, note)


    @staticmethod
    def draw_cursor(io, x, y):
        '''Draws the cursor'''
        # delete the old cursor
        io['editor'].delete_with_tag(['cursor'])

        # get the cursor position
        print(y)
        y = io['calc'].y2tick_editor(y, snap=True)
        y = io['calc'].tick2y_editor(y)

        # draw the new cursor
        io['editor'].new_line(LEFT, y, LEFT+EDITOR_MARGIN, y,
                              width=2, 
                              tag=['cursor'], 
                              color='black',
                              dash=(4,4))
        io['editor'].new_line(RIGHT-EDITOR_MARGIN, y, RIGHT, y,
                              width=2, 
                              tag=['cursor'], 
                              color='black',
                              dash=(4,4))
        
        print('cursor drawn')