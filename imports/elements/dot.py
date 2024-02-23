from imports.utils.constants import *

class Dot:

    @staticmethod
    def draw_editor(io, dot, inselection=False):
        '''draws the continuation dot in the editor'''

        # get the dot's position
        x = io['calc'].pitch2x_editor(dot['pitch'])
        y = io['calc'].tick2y_editor(dot['time'])

        print('dot')
        
        io['editor'].new_oval(x-(STAFF_X_UNIT_EDITOR/4),y+(STAFF_X_UNIT_EDITOR /4),
            x+(STAFF_X_UNIT_EDITOR/4),y+(STAFF_X_UNIT_EDITOR/4*3),
            outline_color='black',
            fill_color='#000000',
            tag=[dot['tag'], 'continuationdot'])
        
        io['editor'].new_line(x-(STAFF_X_UNIT_EDITOR), y, x+(STAFF_X_UNIT_EDITOR), y,
                tag=[dot['tag'], 'continuationdot'],
                width=.75,
                dash=[3, 3],
                color='black')