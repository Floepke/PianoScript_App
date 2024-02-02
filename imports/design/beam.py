from imports.utils.savefilestructure import SaveFileStructureSource
from imports.utils.constants import *
import copy

class Beam:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the slur tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # detect if we clicked on a linebreak
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='linebreak')

            if detect:
                io['edit_obj'] = detect
            else:
                time = io['calc'].y2tick_editor(y, snap=True)
                if io['calc'].x2pitch_editor(x) >= 44:
                    hand = 'r'
                else:
                    hand = 'l'
                # we add a new linebreak to the score and draw it
                new = SaveFileStructureSource.new_beam(
                    tag='beam' + str(io['calc'].add_and_return_tag()),
                    time=time,
                    duration=0,
                    hand=hand,
                    staff=io['selected_staff']
                )
                io['score']['events']['beam'].append(new)
                Beam.draw_editor(io, new)

        elif event_type == 'leftclick+move':
            ...
        
        elif event_type == 'leftrelease':
            ...

        # middle mouse button handling:
        elif event_type == 'middleclick':
            ...

        elif event_type == 'middleclick+move':
            ...

        elif event_type == 'middlerelease':
            ...

        # right mouse button handling:
        elif event_type == 'rightclick':
            ...

        elif event_type == 'rightclick+move':
            ...
        
        elif event_type == 'rightrelease':
            ...


    def draw_editor(io, beam, inselection=False):

        # delete old beam
        io['editor'].delete_with_tag([beam['tag']])

        # xy data
        time = io['calc'].y2tick_editor(beam['time'])
        time2 = io['calc'].y2tick_editor(beam['time']+beam['duration'])

        # draw new beam
        io['editor'].new_line(100, time,
                              100, time+100,
                              tag=[beam['tag'], 'beam'],
                              color='black',
                              dash=(2,2),
                              width=3)
        
        

    def delete_editor(io, linebreak):
        
        ...


















