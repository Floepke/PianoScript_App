

class DrawEditor:
    '''The DrawEditor class handles all the drawing parts for the editor'''

    @staticmethod
    def draw_title(io:dict):
        '''Draws the title of the score on the top of the editor'''

        title = '"' + io['score']['header']['title']['text'] + '"' + ' by composer: ' + io['score']['header']['composer']['text']
        io['editor'].new_text(-512, 0, title, tag='titletext', anchor='nw', size=20, font='Courier New')

    @staticmethod
    def draw_background(io:dict):
        '''Draws the background'''

        # calculate the height of the background
        total_ticks = io['calctools'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom'] # the size in pixels per quarter note
        background_height = total_ticks * (editor_zoom / io['QUARTER_PIANOTICK']) + (io['EDITOR_MARGIN'] * 2)
        
        # create the background rectangle
        io['editor'].new_rectangle(-512, 0, 512, background_height, 
                                   fill_color='#eeeeee', 
                                   outline_color='#eeeeee', 
                                   tag='background')

    @staticmethod
    def draw_staff(io:dict):
        '''Draws the staff'''
        
        # calculating dimensions
        staff_width = io['WIDTH'] - (io['EDITOR_MARGIN'] * 2)
        staff_line_unit = staff_width / 49
        total_ticks = io['calctools'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom']
        staff_length_pixels = total_ticks * (editor_zoom / io['QUARTER_PIANOTICK'])

        x_curs = -512 + io['EDITOR_MARGIN']

        # draw the A#0 staffline
        io['editor'].new_line(x_curs,
                              io['EDITOR_MARGIN'],
                              x_curs,
                              io['EDITOR_MARGIN']+staff_length_pixels,
                              width=2,
                              tag='staffline',
                              color='#000000')
        
        x_curs += staff_line_unit + staff_line_unit

        for staff in range(7):

            for _ in range(2):
                if staff == 3:
                    io['editor'].new_line(x_curs,io['EDITOR_MARGIN'],x_curs,io['EDITOR_MARGIN']+staff_length_pixels,
                        width=1,
                        tag='staffline',
                        dash=(6,6),
                        color='black')
                else:
                    io['editor'].new_line(x_curs,io['EDITOR_MARGIN'],x_curs,io['EDITOR_MARGIN']+staff_length_pixels,
                        width=1,
                        tag='staffline',
                        color='black')
                x_curs += staff_line_unit

            x_curs += staff_line_unit

            for _ in range(3):
                io['editor'].new_line(x_curs,io['EDITOR_MARGIN'],x_curs,io['EDITOR_MARGIN']+staff_length_pixels,
                        width=2,
                        tag='staffline',
                        color='black')
                x_curs += staff_line_unit

            x_curs += staff_line_unit

    @staticmethod
    def draw_barlines_grid_and_numbers(io:dict):
        '''Draws the barlines and the measure numbers'''

        # calculating dimensions
        staff_width = 1024 - (io['EDITOR_MARGIN'] * 2)
        editor_zoom = io['score']['properties']['editor-zoom']

        y_curs = io['EDITOR_MARGIN']

        for gr in io['score']['events']['grid']:
            
            measure_length = io['calctools'].get_measure_length(gr)
            amount = gr['amount']

            for _ in range(amount):
                
                # draw the barline
                io['editor'].new_line(-512 + io['EDITOR_MARGIN'],
                                      y_curs,
                                      -512 + io['EDITOR_MARGIN'] + staff_width,
                                      y_curs,
                                      width=2,
                                      tag='barline',
                                      color='black')
                
                # draw the measure number
                io['editor'].new_text(-512 + io['EDITOR_MARGIN'],
                                      y_curs,
                                      str(_ + 1),
                                      tag='barline',
                                      anchor='e',
                                      size=40,
                                      font='Courier New')

                # draw the gridlines
                for tick in gr['grid']:
                    tick *= (editor_zoom / io['QUARTER_PIANOTICK'])
                    io['editor'].new_line(-512 + io['EDITOR_MARGIN'],
                                          y_curs + tick,
                                          -512 + io['EDITOR_MARGIN'] + staff_width,
                                          y_curs + tick,
                                          width=0.5,
                                          tag='barline',
                                          dash=(7,7),
                                          color='black')
                
                # move the y_curs
                y_curs += measure_length * (editor_zoom / io['QUARTER_PIANOTICK'])

                # if this is the last iteration and last iteration from gr, draw the endline
                if _ == amount - 1 and gr == io['score']['events']['grid'][-1]:
                    io['editor'].new_line(-512 + io['EDITOR_MARGIN'],
                                          y_curs,
                                          -512 + io['EDITOR_MARGIN'] + staff_width,
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
        radius = io['EDITOR_X_UNIT'] / 2

        io['editor'].new_oval(x-radius, y-radius, x+radius, y+radius, fill_color='black', tag='note')