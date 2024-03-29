from imports.utils.savefilestructure import SaveFileStructureSource
from imports.utils.constants import *
import copy


class LineBreak:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the line break tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # detect if we clicked on a linebreak
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='linebreak')

            if detect:
                io['edit_obj'] = detect
            else:
                # we add a new linebreak to the score and draw it
                new = SaveFileStructureSource.new_linebreak(
                    tag='linebreak' + str(io['calc'].add_and_return_tag()),
                    time=io['calc'].y2tick_editor(y, snap=True)
                )
                io['score']['events']['linebreak'].append(new)
                LineBreak.draw_editor(io, new)

        elif event_type == 'leftclick+move':
            if io['edit_obj']:
                time = io['calc'].y2tick_editor(y, snap=True)
                io['edit_obj']['time'] = time
                LineBreak.draw_editor(io, io['edit_obj'])
                for lb in io['score']['events']['linebreak']:
                    if lb['tag'] == io['edit_obj']['tag']:
                        lb = copy.deepcopy(io['edit_obj'])
                        break

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
                io, float(x), float(y), event_type='linebreak')
            # if it's locked we block the rightclick
            if detect and not detect['tag'] == 'lockedlinebreak':
                LineBreak.delete_editor(io, detect)

        elif event_type == 'rightclick+move':
            ...

        elif event_type == 'rightrelease':
            ...

    def draw_editor(io, linebreak, inselection=False):

        # delete old linebreak
        io['editor'].delete_with_tag([linebreak['tag']])

        y = io['calc'].tick2y_editor(linebreak['time'])
        height = io['calc'].tick2y_editor(linebreak['time']+128) - y

        if linebreak['tag'] == 'lockedlinebreak':
            color = '#556677'
        else:
            color = 'blue'

        # add the new linebreak
        io['editor'].new_rectangle(EDITOR_RIGHT - (EDITOR_MARGIN/2), y, EDITOR_RIGHT - (EDITOR_MARGIN/4), y+height,
                                   tag=[linebreak['tag'], 'linebreak'],
                                   fill_color='#00008833',
                                   outline_color=color,
                                   width=3)
        io['editor'].new_text(EDITOR_RIGHT - (EDITOR_MARGIN/4*1.5), y+(height*.5), 'B',
                              tag=[linebreak['tag'], 'linebreak'],
                              font='Courier New',
                              size=32,
                              color=color)
        io['editor'].new_line(EDITOR_RIGHT - EDITOR_MARGIN, y, EDITOR_RIGHT - (EDITOR_MARGIN/3), y,
                              tag=[linebreak['tag'], 'linebreak'],
                              color=color,
                              dash=(2, 2),
                              width=3)

    def delete_editor(io, linebreak):

        # delete from file and editor
        io['score']['events']['linebreak'].remove(linebreak)
        io['editor'].delete_with_tag([linebreak['tag']])
        if linebreak in io['viewport']['events']['linebreak']:
            io['viewport']['events']['linebreak'].remove(linebreak)
