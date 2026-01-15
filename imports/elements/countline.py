from imports.utils.savefilestructure import SaveFileStructureSource
import copy
from imports.utils.constants import *


class CountLine:

    @staticmethod
    def tool(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the countline tool'''

        # left mouse button handling:
        if event_type == 'leftclick':
            # detect if we clicked on a note
            detect = io['editor'].detect_item(
                io, float(x), float(y), event_type='countline')

            if detect:
                CountLine.delete_editor(io, detect)
                io['edit_obj'] = copy.deepcopy(detect)
                io['edit_obj']['tag'] = 'edit_obj'
            else:
                # we have to create a (new) edit_obj:
                io['edit_obj'] = SaveFileStructureSource.new_countline(
                    tag='edit_obj',
                    time=io['calc'].y2tick_editor(y, snap=True),
                    pitch1=io['calc'].x2pitch_editor(x),
                    pitch2=io['calc'].x2pitch_editor(x),
                    staff=0
                )
                io['edit_obj']['handle'] = 'handle2'
            CountLine.draw_editor(io, io['edit_obj'])

        elif event_type == 'leftclick+move':
            # safety: if somehow the edit_obj is None, return
            if not io['edit_obj']:
                return
                
            # get the mouse position in pianoticks and pitch
            mouse_pitch = io['calc'].x2pitch_editor(x)
            mouse_time = io['calc'].y2tick_editor(y, snap=True)

            # detect handle
            handle = 'pitch1' if abs(io['edit_obj']['pitch1'] - mouse_pitch) < abs(
                io['edit_obj']['pitch2'] - mouse_pitch) else 'pitch2'

            # edit the countline
            io['edit_obj'][handle] = mouse_pitch
            io['edit_obj']['time'] = mouse_time

            # draw the note
            CountLine.draw_editor(io, io['edit_obj'])

        elif event_type == 'leftrelease':
            if io['edit_obj']:
                # delete the edit_obj
                io['editor'].delete_with_tag([io['edit_obj']['tag']])

                # delete the note from file
                for cl in io['score']['events']['countline']:
                    if cl['tag'] == io['edit_obj']['tag']:
                        io['score']['events']['countline'].remove(cl)
                        break

                # create copy of the edit_obj, give it a identical tag and add it to the score
                new = copy.deepcopy(io['edit_obj'])
                new['tag'] = 'countline' + str(io['calc'].add_and_return_tag())
                io['score']['events']['countline'].append(new)

                # draw the note, redraw the editor viewport
                io['maineditor'].draw_viewport()

                # delete the edit_obj
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
            # detect if we clicked on a note
            detect = io['editor'].detect_item(
                io, float(x), float(y), event_type='countline')

            if detect:
                CountLine.delete_editor(io, detect)

        elif event_type == 'rightclick+move':
            ...

        elif event_type == 'rightrelease':
            ...

    @staticmethod
    def draw_editor(io, countline, inselection: bool = False):

        # first delete the old countline
        io['editor'].delete_with_tag([countline['tag']])

        # update drawn object
        if countline in io['viewport']['events']['countline']:
            io['viewport']['events']['countline'].remove(countline)

        # get the x and y position of the countline
        x1 = io['calc'].pitch2x_editor(countline['pitch1'])
        x2 = io['calc'].pitch2x_editor(countline['pitch2'])
        y = io['calc'].tick2y_editor(countline['time'])

        # add the new countline
        color = '#009cff' if inselection else NOTATION_COLOR_EDITOR
        io['editor'].new_line(x1, y, x2, y,
                              tag=[countline['tag'], 'countline'],
                      color=color,
                              dash=(4, 4),
                              width=.5)

        # add handles
        io['editor'].new_rectangle(x1-5, y-5, x1+5, y+5,
                                   tag=[countline['tag'],
                                        'countline', 'handle'],
                                   fill_color='#aaaa0099',
                                   width=0)
        io['editor'].new_rectangle(x2-5, y-5, x2+5, y+5,
                                   tag=[countline['tag'],
                                        'countline', 'handle'],
                                   fill_color='#aaaa0099',
                                   width=0)

    def delete_editor(io, countline):

        # delete from file and editor
        io['score']['events']['countline'].remove(countline)
        io['editor'].delete_with_tag([countline['tag']])
        if countline in io['viewport']['events']['countline']:
            io['viewport']['events']['countline'].remove(countline)
