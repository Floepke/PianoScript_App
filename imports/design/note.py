from imports.utils.constants import *

class Note:
    
    @staticmethod
    def draw_editor(io, note):
        # delete the old note
        io['editor'].delete_with_tag([note['tag']])

        # get the x and y position of the note
        x = io['calc'].pitch2x_editor(note['pitch'])
        y = io['calc'].tick2y_editor(note['time'])
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
        
        # draw the left dot
        if note['hand'] == 'l' and note['pitch'] in BLACK_KEYS:
            yy = y + unit
            radius = (unit * .5) / 2
            io['editor'].new_oval(x - radius,
                                yy - radius,
                                x + radius,
                                yy + radius,
                                tag=note['tag'],
                                fill_color='white',
                                outline_width=1,
                                outline_color='white')
        elif note['hand'] == 'l' and note['pitch'] not in BLACK_KEYS:
            yy = y + unit
            radius = (unit * .5) / 2
            io['editor'].new_oval(x - radius,
                                yy - radius,
                                x + radius,
                                yy + radius,
                                tag=note['tag'],
                                fill_color=color,
                                outline_width=1,
                                outline_color=color)
            
        # draw the stem
        if note['hand'] == 'l' and note['stem_visible']:
            io['editor'].new_line(x, y, x - (unit * 5), y,
                                tag=note['tag'],
                                width=thickness,
                                color=color)
        elif note['hand'] == 'r' and note['stem_visible']:
            io['editor'].new_line(x, y, x + (unit * 5), y,
                                tag=note['tag'],
                                width=thickness,
                                color=color)
            
        # draw the midi note
        endy = io['calc'].tick2y_editor(note['time'] + note['duration'])
        io['editor'].new_rectangle(x - unit, 
                                    y,
                                    x + unit, 
                                    endy, 
                                    tag=note['tag'], 
                                    fill_color='red', 
                                    width=0,
                                    outline_color='red')
            

    @staticmethod
    def draw_engraver(io, note):
        # Code to draw the note in the engraver view
        ...
