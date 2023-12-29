from imports.editor.draweditor import DrawEditor
from imports.editor.tool.tool_note import tool_note

class Editor:
    '''The editor class handles all the editor functions'''

    def __init__(self, io):

        self.io = io

    def update_editor(self, event_type: str, x: int = None, y: int = None):
        '''updates all neccesary parts of the editor'''

        # run the selected tool
        eval('tool_' + self.io['tool'] + f'(self.io, event_type, x, y)')

    def redraw(self, io):
        '''I want to check the performance if I draw the entire editor every time the score changes. I don't know if it will be fine, but I want to see.'''

        # clear the editor scene
        io['editor'].delete_all()

        # draw title, background, staff, barlines, barnumbers, grid and notes
        DrawEditor.draw_titles(io)
        DrawEditor.draw_background(io)
        DrawEditor.draw_staff(io)
        DrawEditor.draw_barlines_grid_timesignature_and_measurenumbers(io)
        DrawEditor.draw_notes(io) # TODO in progress

    def update_drawing_order(self, io):
        '''
            set drawing order on tags. the tags are hardcoded in the draweditor class
            they are in order background, staffline, titletext, barline, etc...
        '''

        drawing_order = ['background', 'staffline', 'titletext', 
                         'barline', 'gridline', 'barnumbering', 
                         'note', 'stem', 'leftdot', 'notecursor', 
                         'timesignature', 'measurenumber']
        for t in drawing_order:
            io['editor'].tag_raise(t)
        
    