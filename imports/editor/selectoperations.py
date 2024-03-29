import copy
from imports.editor.selection import SaveFileStructureSource
from imports.elements.note import Note
from imports.elements.slur import Slur
from imports.elements.beam import Beam
from imports.elements.countline import CountLine
from imports.elements.arpeggio import Arpeggio
from imports.elements.gracenote import GraceNote
from imports.elements.linebreak import LineBreak
from imports.elements.trill import Trill
from imports.elements.dot import Dot


class SelectOperations:

    def __init__(self, io):

        self.io = io

        self.funcselector = {
            'note': Note,
            'slur': Slur,
            'beam': Beam,
            'countline': CountLine,
            'arpeggio': Arpeggio,
            'gracenote': GraceNote,
            'trill': Trill,
            'linebreak': LineBreak,
            'dot': Dot,
        }

    def cut(self):
        '''cuts the selected events into the clipboard'''
        self.io['selection']['copycut_buffer'] = copy.deepcopy(
            self.io['selection']['selection_buffer'])

        # delete the selected events
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                Note.delete_editor(self.io, event)

        self.io['maineditor'].update('keyedit')

        print('cut')

    def copy(self):
        '''copies the selected events into the clipboard'''
        self.io['selection']['copycut_buffer'] = copy.deepcopy(
            self.io['selection']['selection_buffer'])

        print('copy')

    def paste(self):
        '''pastes the events from the clipboard into the score'''

        first_evt = False

        # paste the events from the clipboard into the score
        for event_type in self.io['selection']['copycut_buffer'].keys():
            for event in self.io['selection']['copycut_buffer'][event_type]:
                # find lowest time value in the clipboard
                if not first_evt:
                    first_evt = min(
                        self.io['selection']['copycut_buffer'][event_type], key=lambda x: x['time'])['time']
                mouse_time = self.io['calc'].y2tick_editor(
                    self.io['mouse']['y'], snap=True)
                new = copy.deepcopy(event)
                new['time'] = new['time'] - first_evt + mouse_time
                new['tag'] = event_type + \
                    str(self.io['calc'].add_and_return_tag())
                new['staff'] = self.io['selected_staff']
                self.io['score']['events'][event_type].append(new)

        self.io['maineditor'].update('keyedit')

        print('paste')

    def delete(self):
        '''deletes the selected events'''

        # delete the selected events
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                self.funcselector[event_type].delete_editor(self.io, event)

        self.io['maineditor'].update('keyedit')

        print('delete')

    def transpose_up(self):
        '''transposes the selected events up'''

        # transpose the selected events
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                if event_type in self.io['selection']['transpose_types']:
                    event['pitch'] += 1
                    if event['pitch'] > 88:
                        event['pitch'] = 88
                    if event in self.io['viewport']['events'][event_type]:
                        self.io['viewport']['events'][event_type].remove(event)

        self.io['maineditor'].update('keyedit')

        print('transpose up')

    def transpose_down(self):
        '''transposes the selected events down'''

        # transpose the selected events
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                if event_type in self.io['selection']['transpose_types']:
                    event['pitch'] -= 1
                    if event['pitch'] < 1:
                        event['pitch'] = 1
                    if event in self.io['viewport']['events'][event_type]:
                        self.io['viewport']['events'][event_type].remove(event)

        self.io['maineditor'].update('keyedit')

        print('transpose down')

    def move_forward(self):
        '''moves the selected events forward in time'''

        # move the selected events
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                if event_type in self.io['selection']['move_types']:
                    event['time'] += self.io['snap_grid']
                    if event in self.io['viewport']['events'][event_type]:
                        self.io['viewport']['events'][event_type].remove(event)

        self.io['maineditor'].update('keyedit')

        print('move forward')

    def move_backward(self):
        '''moves the selected events backward in time'''

        # move the selected events
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                if event_type in self.io['selection']['move_types']:
                    event['time'] -= self.io['snap_grid']
                    if event in self.io['viewport']['events'][event_type]:
                        self.io['viewport']['events'][event_type].remove(event)

        self.io['maineditor'].update('keyedit')

        print('move backward')

    def hand_left(self):
        '''sets the selected events to the left hand'''

        # set the selected events to the left hand
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                if event_type in self.io['selection']['hand_types']:
                    event['hand'] = 'l'
                    if event in self.io['viewport']['events'][event_type]:
                        self.io['viewport']['events'][event_type].remove(event)

        self.io['maineditor'].update('keyedit')

        print('hand to left')

    def hand_right(self):
        '''sets the selected events to the right hand'''

        # set the selected events to the right hand
        for event_type in self.io['selection']['selection_buffer'].keys():
            for event in self.io['selection']['selection_buffer'][event_type]:
                if event_type in self.io['selection']['hand_types']:
                    event['hand'] = 'r'
                    if event in self.io['viewport']['events'][event_type]:
                        self.io['viewport']['events'][event_type].remove(event)

        self.io['maineditor'].update('keyedit')

        print('hand to right')
