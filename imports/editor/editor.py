from imports.editor.draweditor import DrawEditor
from imports.design.note import Note
from imports.design.slur import Slur
from imports.design.beam import Beam
from imports.design.countline import Countline
from imports.editor.selection import Selection


class Editor:
    '''The editor class handles all the editor functions'''

    def __init__(self, io):

        self.io = io
        self.toolselector = {
            'note':Note,
            'slur':Slur,
            'beam':Beam,
            'countline':Countline
        }

    def update(self, event_type: str, x: int = None, y: int = None):
        '''updates all neccesary parts of the editor'''

        # update total ticks
        self.io['total_ticks'] = self.io['calc'].get_total_score_ticks()

        # run the selected tool
        self.toolselector[self.io['tool']].tool(self.io, event_type, x, y)

        # run selection module
        Selection.process(self.io, event_type, x, y)

        # draw_viewport if scroll
        if event_type == 'refresh':
            self.draw_viewport(self.io)

        # draw the cursor
        if event_type == 'move':
            DrawEditor.draw_cursor(self.io, x, y)

        self.drawing_order()

    def draw_viewport(self, io):
        '''draw_viewportes the editor drawing viewport'''

        # clear the editor scene
        io['editor'].delete_with_tag(['midinote', 
                                      'stem', 
                                      'noteheadwhite', 
                                      'leftdotwhite', 
                                      'noteheadblack', 
                                      'leftdotblack'])
        #DrawEditor.draw_background(io)

        # draw title, background, staff, barlines, barnumbers, grid and notes
        if io['total_ticks'] != self.io['calc'].get_total_score_ticks():
            print('total ticks changed; redraw background, staff, barlines, barnumbers and grid')
            DrawEditor.draw_background(io)
            DrawEditor.draw_titles(io)
            DrawEditor.draw_staff(io)
            DrawEditor.draw_barlines_grid_timesignature_and_measurenumbers(io)

        # these drawing functions only draw in the viewport
        io['calc'].update_viewport_ticks(io)
        DrawEditor.draw_notes(io)
        
        self.drawing_order()

        # count number of items on the QGraphicScene
        print(f"number of items on scene: {len(io['editor'].canvas.items())}")

    def drawing_order(self):
        '''
            set drawing order on tags. the tags are hardcoded in the draweditor class
            they are background, staffline, titletext, barline, etc...
        '''

        drawing_order = ['background', 
                         'midinote', 
                         'staffline',
                         'titletext', 
                         'barline', 
                         'gridline', 
                         'barnumbering',
                         'stem',
                         'noteheadwhite',
                         'leftdotwhite',
                         'noteheadblack',
                         'leftdotblack',
                         'timesignature', 
                         'measurenumber',
                         'selectionrectangle',
                        ]
        self.io['editor'].tag_raise(drawing_order)

    def select_tool(self, tool):
        '''selects a tool that is selected in the tool selector'''
        self.io['tool'] = tool
        self.io['gui'].tool_label.setText(f"Tool: {tool}")
        
    