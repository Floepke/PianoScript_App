from imports.editor.draweditor import DrawEditor
from imports.design.note import Note
from imports.design.slur import Slur
from imports.design.beam import Beam
from imports.design.countline import CountLine
from imports.editor.selection import Selection
from imports.design.arpeggio import Arpeggio
from imports.design.gracenote import GraceNote
from imports.design.staffsizer import StaffSizer
from imports.design.linebreak import LineBreak
from imports.design.trill import Trill
import re
from imports.editor.ctlz import CtlZ
import threading



class Editor:
    '''The editor class handles all the editor functions'''

    def __init__(self, io):

        self.io = io
        self.funcselector = {
            'note':Note,
            'slur':Slur,
            'beam':Beam,
            'countline':CountLine,
            'arpeggio':Arpeggio,
            'gracenote':GraceNote,
            'staffsizer':StaffSizer,
            'trill':Trill,
            'linebreak':LineBreak
        }

    def update(self, event_type: str, x: int = None, y: int = None):
        '''updates all neccesary parts of the editor'''

        if 'move' in event_type:
            # write the mouse position to the io['mouse'] dict
            self.io['mouse']['x'] = x
            self.io['mouse']['y'] = y # TODO: check if this is neccessary

        # update total ticks
        self.io['total_ticks'] = self.io['calc'].get_total_score_ticks()

        # run the selected tool
        self.funcselector[self.io['tool']].tool(self.io, event_type, x, y)

        # run selection module
        Selection.process(self.io, event_type, x, y)

        # draw_viewport if one of the following events occured
        if event_type in ['resize', 'scroll']:
            self.draw_viewport()

        if event_type in ['zoom', 'loadfile', 'grid_edit']:
            self.redraw_editor()

        # draw the cursor
        if event_type == 'move' or 'move' in event_type:
            DrawEditor.draw_line_cursor(self.io, x, y)

        # TODO: check if undo update is working, currenyly it checks if the score changed since the last edit action
        if self.io['score'] != self.io['ctlz'].buffer[self.io['ctlz'].index]:
            self.io['engraver'].do_engrave()
        
        # add to ctlz stack (in this function we check if there is indeed a change in the score)
        self.io['ctlz'].add_ctlz()

    def draw_viewport(self):
        '''draws all events only in the viewport'''
        
        self.io['calc'].update_viewport_ticks(self.io)

        def draw_time_based_events_in_viewport(io):
            '''Draws all time based events of the score in the viewport'''
        
            def is_in_viewport(event, top, bttm):
                '''returns True if the event is in the viewport, False if not'''
                tm = event['time']
                try:
                    d = event['duration']
                except KeyError:
                    d = None
                
                if d: # event has a duration
                    # check if the event is in the viewports range being visible or not
                    if tm >= top and tm <= bttm or tm + d >= top and tm + d <= bttm or tm <= top and tm + d >= bttm:
                        return True
                else: # event has no duration
                    if tm >= top and tm <= bttm:
                        return True
                
                return False
           
            for e_type in io['score']['events'].keys():
                if e_type in ['grid']: # skip all events that are not time based
                    continue
                
                for idx, event in enumerate(io['score']['events'][e_type]):
                    if is_in_viewport(event, io['viewport']['toptick'], io['viewport']['bottomtick']):
                        # element is in viewport
                        if not event['tag'] in io['drawn_obj']:
                            # element was not yet drawn, draw it
                            if event in io['selection']['selection_buffer'][e_type]:
                                self.funcselector[e_type].draw_editor(io, event, inselection=True)
                            else:
                                self.funcselector[e_type].draw_editor(io, event)
                            io['drawn_obj'].append(event['tag'])
                        else:
                            # element was already drawn, do nothing
                            ...
                    else:
                        # element is outside the viewport, delete it
                        if event['tag'] in io['drawn_obj']:
                            io['editor'].delete_with_tag([event['tag']])
                            io['drawn_obj'].remove(event['tag'])

        draw_time_based_events_in_viewport(self.io)
        
        self.drawing_order()
        

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
            'soundingdot',
            'connectstem',
            'noteheadwhite',
            'leftdotwhite',
            'noteheadblack',
            'leftdotblack',
            'timesignature', 
            'measurenumber',
            'selectionrectangle',
            'notestop',
            'cursor',
            'countline',
            'handle',
            'linebreak'
        ]
        self.io['editor'].tag_raise(drawing_order)

    def select_tool(self, tool):
        '''selects a tool that is selected in the tool selector'''
        print(f"selected tool: {tool}")
        self.io['tool'] = tool
        self.io['gui'].tool_label.setText(f"Tool: {tool}")

    def redraw_editor(self):
        '''redraws the editor'''

        # clear the editor scene
        self.io['editor'].delete_all()
        self.io['drawn_obj'] = []

        # draw the editor
        DrawEditor.draw_background(self.io)
        DrawEditor.draw_titles(self.io)
        DrawEditor.draw_staff(self.io)
        DrawEditor.draw_barlines_grid_timesignature_and_measurenumbers(self.io)
        
        # draw all events in viewport
        self.draw_viewport()
        
    