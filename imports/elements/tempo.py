import copy
from imports.utils.savefilestructure import SaveFileStructureSource
from imports.utils.constants import *

class Tempo:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the tempo tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # detect if we clicked on a tempo
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='tempo')

            if detect:
                # we clicked on a tempo marker; edit the tempo using dialog
                bpm = io['script'].ask_int('Set tempo; quarter notes per minute:', min_value=1, max_value=1000, default_value=120)
                if bpm:
                    for t in io['score']['events']['tempo']:
                        if t == detect:
                            t['tempo'] = int(bpm)
            else:
                # we add a new tempo to the score and draw it
                new = SaveFileStructureSource.new_tempo(
                    tag='tempo' + str(io['calc'].add_and_return_tag()),
                    time=io['calc'].y2tick_editor(y, snap=True)
                )
                print(io['calc'].y2tick_editor(y, snap=True))
                bpm = io['script'].ask_int('Set tempo; quarter notes per minute:', min_value=1, max_value=1000, default_value=120)
                new['tempo'] = int(bpm)
                io['score']['events']['tempo'].append(new)
                Tempo.draw_editor(io, new)

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
            # detect if we clicked on a note
            detect = io['editor'].detect_item(
                io, float(x), float(y), event_type='tempo')
            # if it's locked we block the rightclick
            if detect and not detect['tag'] == 'lockedtempo':
                Tempo.delete_editor(io, detect)

        elif event_type == 'rightclick+move':
            ...

        elif event_type == 'rightrelease':
            ...

    @staticmethod
    def draw_editor(io, tempo, inselection=False):

        # delete old tempo
        io['editor'].delete_with_tag([tempo['tag']])

        y = io['calc'].tick2y_editor(tempo['time'])
        height = io['calc'].tick2y_editor(tempo['time']+128) - y

        if tempo['tag'] == 'lockedtempo':
            color = '#556677'
        else:
            color = 'blue'

        # add the new tempo
        io['editor'].new_rectangle(EDITOR_RIGHT - (EDITOR_MARGIN/2), y-height, EDITOR_RIGHT - (EDITOR_MARGIN/4), y,
                                   tag=[tempo['tag'], 'tempo'],
                                   fill_color='#00008833',
                                   outline_color=color,
                                   width=3)
        io['editor'].new_text(EDITOR_RIGHT - (EDITOR_MARGIN/4*1.5), y-(height*.5), 'T',
                              tag=[tempo['tag'], 'tempo'],
                              font='Courier New',
                              size=32,
                              color=color)
        io['editor'].new_line(EDITOR_RIGHT - EDITOR_MARGIN, y, EDITOR_RIGHT - (EDITOR_MARGIN/3), y,
                              tag=[tempo['tag'], 'tempo'],
                              color=color,
                              dash=(2, 2),
                              width=3)

    @staticmethod
    def delete_editor(io, tempo):

        # delete from file and editor
        io['score']['events']['tempo'].remove(tempo)
        io['editor'].delete_with_tag([tempo['tag']])
        if tempo in io['viewport']['events']['tempo']:
            io['viewport']['events']['tempo'].remove(tempo)
