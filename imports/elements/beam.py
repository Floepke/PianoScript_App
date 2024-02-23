from imports.utils.savefilestructure import SaveFileStructureSource
from imports.utils.constants import *
import copy
from PySide6.QtCore import Qt

class Beam:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the slur tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # detect if we clicked on a beam
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='beam')

            if detect:
                io['edit_obj'] = detect
            else:
                time = io['calc'].y2tick_editor(y, snap=True)
                if io['calc'].x2pitch_editor(x) >= 44:
                    hand = 'r'
                else:
                    hand = 'l'
                # we add a new beam to the score and draw it
                new = SaveFileStructureSource.new_beam(
                    tag='beam' + str(io['calc'].add_and_return_tag()),
                    time=time,
                    duration=io['snap_grid'],
                    hand=hand,
                    staff=io['selected_staff']
                )
                io['edit_obj'] = new
                Beam.draw_editor(io, io['edit_obj'])

        elif event_type == 'leftclick+move':
            if io['edit_obj']:
                mouse_time = io['calc'].y2tick_editor(y, snap=True)
                io['edit_obj']['duration'] = mouse_time - io['edit_obj']['time']
                if io['edit_obj']['duration'] < 0:
                    io['edit_obj']['duration'] = 0
                Beam.draw_editor(io, io['edit_obj'])
        
        elif event_type == 'leftrelease':
            if io['edit_obj']:
                io['score']['events']['beam'].append(copy.deepcopy(io['edit_obj']))
                Beam.draw_editor(io, io['edit_obj'])
                io['edit_obj'] = None
            


        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...

        # right mouse button handling:
        elif event_type == 'rightclick':
            # detect if we clicked on a beam
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='beam')

            if detect:
                io['score']['events']['beam'].remove(detect)
                io['editor'].delete_with_tag([detect['tag']])

        elif event_type == 'rightclick+move':
            ...
        
        elif event_type == 'rightrelease':
            ...


    def draw_editor(io, beam, inselection=False):

        # delete old beam
        io['editor'].delete_with_tag([beam['tag']])

        # xy data
        time = io['calc'].tick2y_editor(beam['time'])
        time2 = io['calc'].tick2y_editor(beam['time']+beam['duration'])

        if beam['hand'] == 'r':
            x = EDITOR_RIGHT-(EDITOR_MARGIN/3*2)
        else:
            x = EDITOR_LEFT+(EDITOR_MARGIN/3*2)

        # draw new beam
        io['editor'].new_line(x, time,
                              x, time2,
                              tag=[beam['tag'], 'beam'],
                              color='green',
                              width=12,
                              capstyle=Qt.FlatCap)
        if beam['hand'] == 'r':
            io['editor'].new_line(x, time,
                              x-(EDITOR_MARGIN/3), time,
                              tag=[beam['tag'], 'beam'],
                              color='green',
                              width=2)
            io['editor'].new_line(x, time2,
                              x-(EDITOR_MARGIN/3), time2,
                              tag=[beam['tag'], 'beam'],
                              color='green',
                              width=2)
        else:
            io['editor'].new_line(x, time,
                              x+(EDITOR_MARGIN/3), time,
                              tag=[beam['tag'], 'beam'],
                              color='green',
                              width=2)
            io['editor'].new_line(x, time2,
                              x+(EDITOR_MARGIN/3), time2,
                              tag=[beam['tag'], 'beam'],
                              color='green',
                              width=2)
        if beam['duration'] == 0:
            io['editor'].new_rectangle(x-5, time-5,
                                       x+5, time+5,
                                       tag=[beam['tag'], 'beam'],
                                       fill_color='green')
        
        

    def delete_editor(io, beam):
        
        ...


















