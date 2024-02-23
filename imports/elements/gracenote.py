from imports.utils.constants import *
import copy
from imports.utils.savefilestructure import SaveFileStructureSource

class GraceNote:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the grace note tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # detect if we clicked on a note
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='gracenote')
            if detect:
                # if we clicked on a note, we want to edit it so we create a copy of the note
                GraceNote.delete_editor(io, detect)
                io['edit_obj'] = copy.deepcopy(detect)
                io['edit_obj']['hand'] = io['hand']
                io['edit_obj']['staff'] = io['selected_staff']
                io['edit_obj']['tag'] = 'edit_obj'
            else:
                # we have to create a (new) edit_obj:
                io['edit_obj'] = SaveFileStructureSource.new_gracenote(
                    tag='edit_obj',
                    time=io['calc'].y2tick_editor(y, snap=True),
                    pitch=io['calc'].x2pitch_editor(x),
                    hand=io['hand'],
                    staff=io['selected_staff']
                )
                GraceNote.draw_editor(io, io['edit_obj'])
                io['editor'].delete_with_tag(['notecursor'])

        elif event_type == 'leftclick+move':
            if io['edit_obj']:
                # get the mouse position in pianoticks and pitch
                mouse_time = io['calc'].y2tick_editor(y, snap=True)
                mouse_pitch = io['calc'].x2pitch_editor(x)

                io['edit_obj']['pitch'] = mouse_pitch
                io['edit_obj']['time'] = mouse_time

                # draw the note
                GraceNote.draw_editor(io, io['edit_obj'])
        
        elif event_type == 'leftrelease':
            if io['edit_obj']:
                # delete the edit_obj
                io['editor'].delete_with_tag([io['edit_obj']['tag']])

                # create copy of the edit_obj, give it a identical tag and add it to the score
                new = copy.deepcopy(io['edit_obj'])
                new['tag'] = 'gracenote' + str(io['calc'].add_and_return_tag())
                io['score']['events']['gracenote'].append(new)

                # delete the edit_obj
                io['edit_obj'] = None

                GraceNote.draw_editor(io, new)

                # draw the note, redraw the editor viewport
                io['maineditor'].draw_viewport()

        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...

        # right mouse button handling:
        elif event_type == 'rightclick':
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='gracenote')
            if detect:
                # if we clicked on a note, we want to delete it
                GraceNote.delete_editor(io, detect)

        elif event_type == 'rightclick+move':
            ...
        
        elif event_type == 'rightrelease':
            ...

    @staticmethod
    def draw_editor(io, note, inselection=False):

        # delete old gracenote
        io['editor'].delete_with_tag([note['tag']])

        color = 'black'
        
        # draw notehead
        x = io['calc'].pitch2x_editor(note['pitch'])
        y = io['calc'].tick2y_editor(note['time'])
        unit = PITCH_UNIT
        if note['pitch'] in BLACK_KEYS:
            # draw the black notehead down
            io['editor'].new_oval(x - unit * 4,
                                y,
                                x + unit * 4,
                                y + unit * 8,
                                tag=[note['tag'], 'noteheadblack'],
                                fill_color=color,
                                outline_width=2,
                                outline_color=color)
        elif note['pitch'] in WHITE_KEYS:
            # draw the black notehead up
            io['editor'].new_oval(x - unit * 4, 
                                y,
                                x + unit * 4,
                                y + unit * 8,
                                tag=[note['tag'], 'noteheadwhite'],
                                fill_color='white',
                                outline_width=2,
                                outline_color=color)

    @staticmethod
    def delete_editor(io, note):
        # delete old gracenote
        io['editor'].delete_with_tag([note['tag']])

        # delete from score
        io['score']['events']['gracenote'].remove(note)