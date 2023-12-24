from ..utils.HARDCODE import QUARTER_PIANOTICK, EDITOR_MARGIN

class DrawEditor:
    '''The DrawEditor class handles all the drawing parts for the editor'''

    def draw_title(io):
        '''Draws the title of the score on the top of the editor'''

        # first delete old title
        io['editor'].delete_with_tag('titletext')

        title = '"' + io['score']['header']['title']['text'] + '"' + ' by composer: ' + io['score']['header']['composer']['text']
        io['editor'].new_text(-512, 0, title, tag='titletext', anchor='nw', size=20, font='Courier New')

    def draw_background(io):
        '''Draws the background'''

        # first delete old background
        io['editor'].delete_with_tag('background')

        # calculate the height of the background
        total_ticks = io['calctools'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom'] # the size in pixels per quarter note
        background_height = total_ticks * (editor_zoom / QUARTER_PIANOTICK) + (EDITOR_MARGIN * 2)
        
        # create the background rectangle
        io['editor'].new_rectangle(-512, 0, 512, background_height, 
                                   fill_color='#eeeeee', 
                                   outline_color='black', 
                                   tag='background')

    def draw_staff(io):
        '''Draws the staff'''

        # first delete old stafflines
        io['editor'].delete_with_tag('staffline')
        
        # calculating dimensions
        staff_width = 1024 - (EDITOR_MARGIN * 2)
        staff_line_unit = staff_width / 49
        total_ticks = io['calctools'].get_total_score_ticks()
        editor_zoom = io['score']['properties']['editor-zoom']
        staff_length_pixels = total_ticks * (editor_zoom / QUARTER_PIANOTICK)

        x_curs = -512 + EDITOR_MARGIN

        # draw the A#0 staffline
        io['editor'].new_line(x_curs, EDITOR_MARGIN, x_curs, EDITOR_MARGIN+staff_length_pixels,
                                width=2,
                                tag='staffline',
                                color='#000000')
        
        x_curs += staff_line_unit + staff_line_unit

        for staff in range(7):

            for _ in range(2):
                if staff == 3:
                    io['editor'].new_line(x_curs,EDITOR_MARGIN,x_curs,EDITOR_MARGIN+staff_length_pixels,
                        width=1,
                        tag='staffline',
                        dash=(6,6),
                        color='black')
                else:
                    io['editor'].new_line(x_curs,EDITOR_MARGIN,x_curs,EDITOR_MARGIN+staff_length_pixels,
                        width=1,
                        tag='staffline',
                        color='black')
                x_curs += staff_line_unit

            x_curs += staff_line_unit

            for _ in range(3):
                io['editor'].new_line(x_curs,EDITOR_MARGIN,x_curs,EDITOR_MARGIN+staff_length_pixels,
                        width=2,
                        tag='staffline',
                        color='black')
                x_curs += staff_line_unit

            x_curs += staff_line_unit