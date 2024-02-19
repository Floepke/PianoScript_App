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
from imports.design.dot import Dot
import re
from imports.editor.ctlz import CtlZ
import threading
from imports.utils.constants import *
from imports.utils.savefilestructure import SaveFileStructureSource
from imports.engraver.engraver import pre_render


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
            'linebreak':LineBreak,
            'dot':Dot,
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

        if event_type in ['zoom', 'loadfile', 'keyedit', 'ctlz', 'grid_editor', 'score_options']:
            self.redraw_editor()
            if self.io['auto_engrave'] or event_type in ['score_options', 'grid_editor']:
                self.io['engraver'].do_engrave()
            if self.io['autosave']:
                try: self.io['fileoperations'].auto_save()
                except KeyError: ...

        if event_type in ['page_change']:
            self.io['engraver'].do_engrave()

        # save if there is a change in the score
        if (self.io['score'] != self.io['ctlz'].buffer[self.io['ctlz'].index] and 
            not event_type in ['zoom', 'loadfile', 'keyedit', 'ctlz', 'grid_editor', 'page_change']):
            if self.io['auto_engrave']: 
                self.io['engraver'].do_engrave()
            if self.io['autosave']:
                try: self.io['fileoperations'].auto_save()
                except KeyError: ...
        
        # draw the cursor
        if event_type == 'move' or 'move' in event_type:
            DrawEditor.draw_line_cursor(self.io, x, y)

        # add to ctlz stack (in this function we check if there is indeed a change in the score)
        self.io['ctlz'].add_ctlz()

    def draw_viewport(self):
        '''draws all events only in the viewport'''
        
        self.io['calc'].update_viewport_ticks(self.io)

        def draw_events(io):
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
                    if (tm >= top and tm <= bttm or tm + d >= top and tm + d <= bttm or tm <= top and tm + d >= bttm) and event['staff'] == io['selected_staff']:
                        return True
                else: # event has no duration
                    if tm >= top and tm <= bttm:
                        return True
                
                return False
           
            for e_type in io['viewport']['events'].keys():
                if e_type in ['grid']: # skip all events that are not time based
                    continue

                # delete duplicate events from viewport events (safety check)
                events = io['viewport']['events'][e_type]
                io['viewport']['events'][e_type] = [i for n, i in enumerate(events) if i not in events[n + 1:]]
                
                for event in io['score']['events'][e_type]:

                    if is_in_viewport(event, io['viewport']['toptick'], io['viewport']['bottomtick']):
                        # element is in viewport
                        if not event in io['viewport']['events'][e_type]:
                            # add event to viewport
                            if event in io['selection']['selection_buffer'][e_type]:
                                self.funcselector[e_type].draw_editor(io, event, inselection=True)
                            else:
                                self.funcselector[e_type].draw_editor(io, event)
                            io['viewport']['events'][e_type].append(event)
                        else:
                            # element was already drawn, do nothing
                            ...
                    else:
                        # element is outside the viewport, delete it if it was drawn
                        if event in io['viewport']['events'][e_type]:
                            io['editor'].delete_with_tag([event['tag']])
                            io['viewport']['events'][e_type].remove(event)

        #DrawEditor.add_soundingdots_and_stopsigns_to_viewport(self.io)

        draw_events(self.io)

        # draw the grid and barlines
        top_y = self.io['calc'].tick2y_editor(self.io['viewport']['toptick'])
        bottom_y = self.io['calc'].tick2y_editor(self.io['viewport']['bottomtick'])
        DrawEditor.draw_barlines_grid_timesignature_and_measurenumbers(self.io, top_y, bottom_y)

        # Move the stafflines with the viewport
        #DrawEditor.move_staff(self.io, top_y)
        
        self.drawing_order()

        self.io['gui'].editor_view.update()
        

    def drawing_order(self):
        '''
            set drawing order on tags. the tags are hardcoded in the draweditor class
            they are background, staffline, titletext, barline, etc...
        '''

        drawing_order = [
            'midinote', 
            'staffline',
            'titlebackground',
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
            'linebreak',
            'gracenote'
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
        self.io['viewport']['events'] = SaveFileStructureSource.new_events_folder_viewport()

        # draw the editor
        DrawEditor.draw_titles(self.io)
        DrawEditor.draw_staff(self.io)

        # set scene size
        height = self.io['calc'].get_total_score_ticks() / QUARTER_PIANOTICK * self.io['score']['properties']['editor_zoom'] + EDITOR_MARGIN + EDITOR_MARGIN
        self.io['gui'].editor_scene.setSceneRect(EDITOR_LEFT, EDITOR_TOP, EDITOR_WIDTH, height)
        
        # draw all events in viewport
        self.draw_viewport()

    def toggle_auto_engrave(self):
        '''toggles the autorender function'''
        if self.io['auto_engrave']:
            self.io['auto_engrave'] = False
            self.io['gui'].auto_engrave_action.setChecked(False)
        else:
            self.io['auto_engrave'] = True
            self.io['gui'].auto_engrave_action.setChecked(True)
        















