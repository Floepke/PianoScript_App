from imports.utils.constants import *

class Note:
    
    @staticmethod
    def draw_editor(io, note):
        # get the x and y position of the note
        x = io['calctools'].pitch2x_editor(note['pitch'])
        y = io['calctools'].tick2y_editor(note['time'])
        print(x, y)

        # draw the notehead
        unit = STAFF_X_UNIT_EDITOR / 2
        thickness = 5
        if note['pitch'] in BLACK_KEYS:
            io['editor'].new_oval(x - unit,
                                y,
                                x + unit,
                                y + unit * 2,
                                tag='note',
                                fill_color='black',
                                outline_width=thickness)
        else:
            io['editor'].new_oval(x - unit,
                                y,
                                x + unit,
                                y + unit * 2,
                                tag='note',
                                fill_color='white',
                                outline_width=thickness)
            
        # draw the stem
        if note['hand'] == 'l':
            io['editor'].new_line(x, y, x - (unit * 5), y,
                                tag='stem',
                                width=thickness,
                                color='black')
        else:
            io['editor'].new_line(x, y, x + (unit * 5), y,
                                tag='stem',
                                width=thickness,
                                color='black')

    @staticmethod
    def draw_engraver(io, note):
        # Code to draw the note in the engraver view
        ...
