from imports.utils.constants import *

class Note:
    
    @staticmethod
    def draw_editor(io, note):
        # delete the old note
        io['editor'].delete_with_tag(note['tag'])

        # get the x and y position of the note
        x = io['calctools'].pitch2x_editor(note['pitch'])
        y = io['calctools'].tick2y_editor(note['time'])
        print(x, y)

        # set colors
        if note['tag'] == 'notecursor':
            color = 'blue' # TODO: set color depending on settings
        else:
            color = 'black' # TODO: set color depending on settings

        # draw the notehead
        unit = STAFF_X_UNIT_EDITOR / 2
        thickness = 5
        if note['pitch'] in BLACK_KEYS:
            io['editor'].new_oval(x - unit,
                                y,
                                x + unit,
                                y + unit * 2,
                                tag=note['tag'],
                                fill_color=color,
                                outline_width=thickness,
                                outline_color=color)
        else:
            io['editor'].new_oval(x - unit,
                                y,
                                x + unit,
                                y + unit * 2,
                                tag=note['tag'],
                                fill_color='white',
                                outline_width=thickness,
                                outline_color=color)
            
        # draw the stem
        if note['hand'] == 'l':
            io['editor'].new_line(x, y, x - (unit * 5), y,
                                tag=note['tag'],
                                width=thickness,
                                color=color)
        else:
            io['editor'].new_line(x, y, x + (unit * 5), y,
                                tag=note['tag'],
                                width=thickness,
                                color=color)

    @staticmethod
    def draw_engraver(io, note):
        # Code to draw the note in the engraver view
        ...
