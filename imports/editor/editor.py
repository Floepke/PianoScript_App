from imports.editor.draweditor import DrawEditor
from imports.design.note import Note
from imports.design.slur import Slur
from imports.design.beam import Beam
from imports.design.countline import CountLine
from imports.editor.selection import Selection
from imports.design.arpeggio import Arpeggio
from imports.design.gracenote import GraceNote
from imports.design.staffsizer import StaffSizer
from imports.design.trill import Trill



class Editor:
    '''The editor class handles all the editor functions'''

    def __init__(self, io):

        self.io = io
        self.toolselector = {
            'note':Note,
            'slur':Slur,
            'beam':Beam,
            'count line':CountLine,
            'arpeggio':Arpeggio,
            'grace note':GraceNote,
            'staff sizer':StaffSizer,
            'trill':Trill,
        }

    def update(self, event_type: str, x: int = None, y: int = None):
        '''updates all neccesary parts of the editor'''

        # update total ticks
        self.io['total_ticks'] = self.io['calc'].get_total_score_ticks()

        # run the selected tool
        self.toolselector[self.io['tool']].tool(self.io, event_type, x, y)

        # run selection module
        Selection.process(self.io, event_type, x, y)

        # draw_viewport if one of the following events occured
        if event_type in ['resize', 'scroll']:
            self.draw_viewport(self.io)

        if event_type in ['zoom', 'loadfile', 'grid_edit']:
            self.redraw_editor(self.io)
            self.draw_viewport(self.io)

        # draw the cursor
        if event_type == 'move':
            DrawEditor.draw_line_cursor(self.io, x, y)

        self.drawing_order()

    def draw_viewport(self, io):
        '''draws all events only in the viewport'''

        # clear the editor scene
        io['editor'].delete_with_tag(['midinote', 
                                      'noteheadwhite', 
                                      'leftdotwhite', 
                                      'noteheadblack', 
                                      'leftdotblack',
                                      'soundingdot',
                                      'stem',
                                      'connectstem',
                                      'notestop'])
        
        io['calc'].update_viewport_ticks(io)

        # these drawing functions only draw in the viewport
        DrawEditor.draw_notes(io)
        
        self.drawing_order()

        # count number of items on the QGraphicScene
        print(f"number of items on scene: {len(io['editor'].canvas.items())}")

    def drawing_order(self):
        '''
            set drawing order on tags. the tags are hardcoded in the draweditor class
            they are background, staffline, titletext, barline, etc...
        '''

        drawing_order = [
            'background', 
            'midinote', 
            'staffline',
            'titletext', 
            'barline', 
            'gridline', 
            'barnumbering',
            'stem',
            'connectstem',
            'noteheadwhite',
            'leftdotwhite',
            'noteheadblack',
            'leftdotblack',
            'timesignature', 
            'measurenumber',
            'selectionrectangle',
            'soundingdot',
            'notestop',
            'cursor'
        ]
        self.io['editor'].tag_raise(drawing_order)

    def select_tool(self, tool):
        '''selects a tool that is selected in the tool selector'''
        print(f"selected tool: {tool}")
        self.io['tool'] = tool
        self.io['gui'].tool_label.setText(f"Tool: {tool}")

    def redraw_editor(self, io):
        '''redraws the editor'''

        # clear the editor scene
        io['editor'].delete_all()

        # draw the editor
        DrawEditor.draw_background(io)
        DrawEditor.draw_titles(io)
        DrawEditor.draw_staff(io)
        print(io['score']['properties']['editor-zoom'])
        DrawEditor.draw_barlines_grid_timesignature_and_measurenumbers(io)
        
        # events
        DrawEditor.draw_notes(io)

        self.drawing_order()

    def draw_non_viewport(self, io):
        '''draws all events outside the viewport'''

        # clear the editor scene
        io['editor'].delete_all()
        
    