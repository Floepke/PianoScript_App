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
                bpm = io['script'].ask_int('Set tempo; quarter notes per minute:', min_value=1, max_value=1000, default_value=detect['tempo'])
                if bpm:
                    for t in io['score']['events']['tempo']:
                        if t == detect:
                            t['tempo'] = int(bpm)
                            Tempo.draw_editor(io, detect)
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

        y1 = io['calc'].tick2y_editor(tempo['time'])
        y2 = io['calc'].tick2y_editor(tempo['time']+256)
        height = io['calc'].tick2y_editor(tempo['time']+128) - y1

        if tempo['tag'] == 'lockedtempo':
            color = '#556677'
        else:
            color = 'white'

        # add the new tempo
        io['editor'].new_rectangle(EDITOR_RIGHT - (EDITOR_MARGIN/4*3), y1, EDITOR_RIGHT - (EDITOR_MARGIN/4*2), y2,
                                   tag=[tempo['tag'], 'tempo'],
                                   fill_color='#000000',
                                   outline_color='',
                                   width=3)
        io['editor'].new_text(EDITOR_RIGHT - (EDITOR_MARGIN/4*2.65), y1+((y2-y1)/2), text=str(tempo['tempo']),
                              tag=[tempo['tag'], 'tempo'],
                              font='Edwin',
                              size=32,
                              color=color,
                              angle=90,
                              anchor='c')
        io['editor'].new_line(EDITOR_RIGHT - EDITOR_MARGIN, y1, EDITOR_RIGHT - (EDITOR_MARGIN/4*3), y1,
                              tag=[tempo['tag'], 'tempo'],
                              color='#000000',
                              dash=(2, 2),
                              width=3)

    @staticmethod
    def delete_editor(io, tempo):

        # delete from file and editor
        io['score']['events']['tempo'].remove(tempo)
        io['editor'].delete_with_tag([tempo['tag']])
        if tempo in io['viewport']['events']['tempo']:
            io['viewport']['events']['tempo'].remove(tempo)
