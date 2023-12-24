from imports.editor.draweditor import DrawEditor

class Editor:
    '''The editor class handles all the editor functions'''

    def __init__(self, io):
        self.io = io
        
        self.redraw(self.io)

    def redraw(self, io):
        '''I want to check the performance if I draw the entire editor every time the score changes. I don't know if it will be fine, but I want to see.'''

        # clear the editor scene
        io['editor'].delete_all()

        # draw titles
        DrawEditor.draw_title(io)

        # draw the background
        DrawEditor.draw_background(io)

        # draw the staff
        DrawEditor.draw_staff(io)

        # draw barines
        ...

        # draw gridlines
        ...

        # draw notes
        ...
        
        # set drawing order on tags
        
        io['editor'].tag_raise('background')
        io['editor'].tag_raise('titletext')
        io['editor'].tag_raise('staffline')
        
    