# in HARDCODE.py you can find all constants that are used in the application along with the description.
from imports.utils.HARDCODE import *

class DrawEditor:
    '''The DrawEditor class handles all the drawing parts for the editor'''

    @staticmethod
    def draw_titles(io:dict):
        '''Draws the title and composer name of the score file on the topleft corner of the editor'''

        title = '"' + io['score']['header']['title']['text'] + '"' + ' by composer: ' + io['score']['header']['composer']['text']
        io['editor'].new_text(LEFT, 0, title, tag='titletext', anchor='nw', size=20, font='Courier New')

    @staticmethod
    def draw_background(io:dict):
        '''Draws the background'''

        # calculate the height of the background
        total_ticks = io['calctools'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom'] # the size in pixels per quarter note
        background_height = total_ticks * (editor_zoom / QUARTER_PIANOTICK) + (EDITOR_MARGIN * 2)
        
        # create the background rectangle
        io['editor'].new_rectangle(LEFT, TOP, RIGHT, background_height,
                                   fill_color='#eeeeee', 
                                   outline_color='#eeeeee', 
                                   tag='background')

    @staticmethod
    def draw_staff(io:dict):
        '''Draws the staff'''
        
        # calculating staff length
        total_ticks = io['calctools'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom']
        staff_length = total_ticks * (editor_zoom / QUARTER_PIANOTICK)

        x_curs = LEFT + EDITOR_MARGIN

        # draw the A#0 staffline
        io['editor'].new_line(x_curs,
                              EDITOR_MARGIN,
                              x_curs,
                              EDITOR_MARGIN+staff_length,
                              width=2,
                              tag='staffline',
                              color='#000000')
        
        x_curs += EDITOR_X_UNIT + EDITOR_X_UNIT

        for octave in range(7): # 7 octaves

            for _ in range(2): # draw group of 2 stafflines
                if octave == 3:
                    # draw the clef (dashed line)
                    io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN + staff_length,
                        width=1,
                        tag='staffline',
                        dash=(6,6),
                        color='black')
                else:
                    io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN + staff_length,
                        width=1,
                        tag='staffline',
                        color='black')
                x_curs += EDITOR_X_UNIT

            x_curs += EDITOR_X_UNIT

            for _ in range(3): # draw group of 3 stafflines, traditionally they are is thicker
                io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN + staff_length,
                        width=2,
                        tag='staffline',
                        color='black')
                x_curs += EDITOR_X_UNIT

            x_curs += EDITOR_X_UNIT

    @staticmethod
    def draw_barlines_grid_and_numbers(io:dict):
        '''Draws the barlines and the measure numbers'''

        # calculating dimensions
        staff_width = WIDTH - (EDITOR_MARGIN * 2)
        editor_zoom = io['score']['properties']['editor-zoom']

        y_curs = EDITOR_MARGIN

        for gr in io['score']['events']['grid']:
            
            # measure length in pianoticks
            measure_length = io['calctools'].get_measure_length(gr)
            amount = gr['amount']

            for _ in range(amount):
                
                # draw the barline
                io['editor'].new_line(LEFT + EDITOR_MARGIN,
                                      y_curs,
                                      LEFT + EDITOR_MARGIN + staff_width,
                                      y_curs,
                                      width=2,
                                      tag='barline',
                                      color='black')
                
                # draw the measure number
                io['editor'].new_text(LEFT + EDITOR_MARGIN,
                                      y_curs,
                                      str(_ + 1),
                                      tag='barline',
                                      anchor='e',
                                      size=40,
                                      font='Courier New')

                # draw the gridlines
                for tick in gr['grid']:
                    tick *= (editor_zoom / QUARTER_PIANOTICK)
                    io['editor'].new_line(LEFT + EDITOR_MARGIN,
                                          y_curs + tick,
                                          LEFT + EDITOR_MARGIN + staff_width,
                                          y_curs + tick,
                                          width=0.5,
                                          tag='barline',
                                          dash=(7,7),
                                          color='black')
                
                # move the y_curs
                y_curs += measure_length * (editor_zoom / QUARTER_PIANOTICK)

                # if this is the last iteration and last iteration from gr: draw the endline
                if _ == amount - 1 and gr == io['score']['events']['grid'][-1]:
                    io['editor'].new_line(LEFT + EDITOR_MARGIN,
                                          y_curs,
                                          LEFT + EDITOR_MARGIN + staff_width,
                                          y_curs,
                                          width=4,
                                          tag='barline',
                                          color='black')
    
    @staticmethod
    def draw_notes(io):
        '''Draws the notes of the score'''

        # get the xy position of a note
        x = io['calctools'].pitch2x_editor(20)
        y = io['calctools'].time2y_editor(1024)

        # draw the note
        radius = EDITOR_X_UNIT / 2
        io['editor'].new_oval(x-radius, y-radius, x+radius, y+radius, fill_color='black', tag='note')