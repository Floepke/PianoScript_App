from imports.utils.savefilestructure import SaveFileStructureSource
import copy
from imports.utils.constants import *


class Slur:

    def __init__(self):
        self.is_new_slur = False
        self.click_pitch = None
        self.start_click_tick = 0
        self.handle = None
        self.edit_obj = None
        self.end_click_tick = None

    def tool(self, io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the slur tool'''

        # left mouse button handling:
        if event_type == 'leftclick':

            # detect if we clicked on a slur
            detect = io['editor'].detect_item(io, float(x), float(
                y), event_type='slur', return_item=False)
            if detect:
                # if we clicked on a slur, we want to edit it so we create a copy of the detected slur
                self.edit_obj = copy.deepcopy(detect)
                # self.delete_editor(io, detect)
                self.is_new_slur = False
                self.click_pitch = None
                self.start_click_tick = None
                # detect the handle and assign it
                clicked_item = io['editor'].detect_item(
                    io, float(x), float(y), event_type='slur', return_item=True)
                for t in clicked_item.data(0):
                    if '#handle' in t:
                        self.handle = t

            else:
                # we have to create a (new) slur at mouse release
                self.is_new_slur = True
                self.click_pitch = io['calc'].x2pitch_editor(x)
                self.start_click_tick = io['calc'].y2tick_editor(y, snap=True)

        elif event_type == 'leftclick+move':

            if self.edit_obj:

                if self.handle:
                    # we clicked on a handle so we need to update it's position based on the mouse position
                    
                    # check if mouse x position is not out of bounds and set to outer bounds if it's oob.
                    x = max(EDITOR_LEFT, min(x, EDITOR_RIGHT))
                    
                    # calculate the xy values for the handle
                    mouse_x = io['calc'].x2xunits_editor(x)
                    mouse_y = io['calc'].y2tick_editor(y, snap=False)
                    
                    # assign to handle
                    handle_key = 'p'+self.handle[-1]
                    self.edit_obj[handle_key]['distance_c4units'] = mouse_x
                    self.edit_obj[handle_key]['time'] = mouse_y
                    if self.handle == '#handle0':
                        self.edit_obj['time'] = mouse_y

                    # update duration of slur for properly draw the slur in the editor
                    max_time = max(self.edit_obj[key]['time'] for key in ['p0', 'p1', 'p2', 'p3'])
                    self.edit_obj['duration'] = max_time
                    
                    self.draw_editor(io, self.edit_obj)

        elif event_type == 'leftrelease':

            if self.is_new_slur:  
                # if we didn't click on an existing slur or slur handle we create a new slur
                
                # update the tick value for if we release the mouse for usage for initial slur handle positions
                self.end_click_tick = io['calc'].y2tick_editor(y, snap=True)
                
                # this function creates a initial slur
                slur = self.generate_init_slur(io)
                
                self.draw_editor(io, slur)
                
                # add new slur to the score file
                io['score']['events']['slur'].append(slur)

            else:

                # remove old slur from the file
                for sl in io['score']['events']['slur']:
                    if sl['tag'] == self.edit_obj['tag']:
                        io['score']['events']['slur'].remove(sl)
                        break

                # create copy of the edit_obj and add it to the score
                new = self.edit_obj
                io['score']['events']['slur'].append(new)

                # draw the note, redraw the editor viewport
                io['maineditor'].draw_viewport()

            self.edit_obj = None
            self.is_new_slur = False

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
            detect = io['editor'].detect_item(io, float(x), float(y), event_type='slur')
            if detect:
                # if we clicked on a note, we want to delete it
                Slur.delete_editor(io, detect)

        elif event_type == 'rightclick+move':
            ...

        elif event_type == 'rightrelease':
            ...

        elif event_type == 'move':

            ...  # io['calc'].x2xunits_editor(x)

    @staticmethod
    def delete_editor(io, slur):

        io['score']['events']['slur'].remove(slur)
        io['editor'].delete_with_tag([slur['tag']])

    def draw_editor(self, io, slur):

        # delete old slur
        io['editor'].delete_with_tag([slur['tag']])

        radius = 7.5

        # points coords
        p0_x = io['calc'].units2x_editor(slur['p0']['distance_c4units'])
        p0_y = io['calc'].tick2y_editor(slur['p0']['time'])
        p1_x = io['calc'].units2x_editor(slur['p1']['distance_c4units'])
        p1_y = io['calc'].tick2y_editor(slur['p1']['time'])
        p2_x = io['calc'].units2x_editor(slur['p2']['distance_c4units'])
        p2_y = io['calc'].tick2y_editor(slur['p2']['time'])
        p3_x = io['calc'].units2x_editor(slur['p3']['distance_c4units'])
        p3_y = io['calc'].tick2y_editor(slur['p3']['time'])

        # draw handles
        io['editor'].new_oval(p0_x - radius,
                              p0_y - radius,
                              p0_x + radius,
                              p0_y + radius,
                              fill_color='#ca375c',
                              outline_color='',
                              tag=[slur['tag'], 'slurhandle', '#handle0'])
        io['editor'].new_oval(p1_x - radius,
                              p1_y - radius,
                              p1_x + radius,
                              p1_y + radius,
                              fill_color='#ca375c',
                              outline_color='',
                              tag=[slur['tag'], 'slurhandle', '#handle1'])
        io['editor'].new_oval(p2_x - radius,
                              p2_y - radius,
                              p2_x + radius,
                              p2_y + radius,
                              fill_color='#ca375c',
                              outline_color='',
                              tag=[slur['tag'], 'slurhandle', '#handle2'])
        io['editor'].new_oval(p3_x - radius,
                              p3_y - radius,
                              p3_x + radius,
                              p3_y + radius,
                              fill_color='#ca375c',
                              outline_color='',
                              tag=[slur['tag'], 'slurhandle', '#handle3'])

        # drawing the slur
        points = io['calc'].bezier_curve((p0_x, p0_y), (p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y), resolution=25)
        num_points = len(points)
        max_width = 5  # or whatever value you want
        min_width = 1  # or whatever minimum value you want
        range_width = max_width - min_width
        for i in range(num_points - 1):
            width = ((1 - abs(num_points / 2 - i) / (num_points / 2)) * range_width) + min_width
            io['editor'].new_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                                  tag=[slur['tag'], 'slurline'],
                                  width=width)

        # drawing indication dashed line
        points = [(p0_x, p0_y), (p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)]
        io['editor'].new_line_list(points,
                                   tag=[slur['tag'], 'slurindicationline'],
                                   dash=[2, 2],
                                   color='#ca375c')

    def generate_init_slur(self, io):
        '''
            calculating the initial positions if the handles based on the start and end time i.c.w. the 
            notes in the score. if the 'click_pitch' was lower then key 40 (central c4) the slur is being 
            processed as a left hand slur for it's initial positions and if higher then c4 it's processed
            as right hand slur.
        '''

        click_pitch, start_click_tick, end_click_tick = self.click_pitch, self.start_click_tick, self.end_click_tick
        if click_pitch <= 40:
            hand = 'l'
        else:
            hand = 'r'

        # filter for note start times in the range of the start and end click time from the click_pitch hand
        notes_happening_in_slur = [note for note in io['score']['events']['note'] if
                                   note['time'] >= start_click_tick and
                                   note['time'] <= end_click_tick and
                                   note['hand'] == hand]

        if len(notes_happening_in_slur) <= 1:
            # DEFAULT INITIAL POSITION: in this case the program didn't find any logical slur position so we create a default slur handle positions.
            if hand == 'l':
                new = SaveFileStructureSource.new_slur(
                    tag='slur' + str(io['calc'].add_and_return_tag()),
                    staff=io['selected_staff'],
                    p0={
                        'time': start_click_tick,
                        # distance from c4 in STAFF_X_UNIT_EDITOR float unit's
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch-5))
                    },
                    p1={
                        'time': start_click_tick + ((end_click_tick - start_click_tick) / 4),
                        # ...
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch-10))
                    },
                    p2={
                        'time': start_click_tick + ((end_click_tick - start_click_tick) / 4 * 3),
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch-10))
                    },
                    p3={
                        'time': end_click_tick,
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch-5))
                    }
                )
            else:
                new = SaveFileStructureSource.new_slur(
                    tag='slur' + str(io['calc'].add_and_return_tag()),
                    staff=io['selected_staff'],
                    p0={
                        'time': start_click_tick,
                        # distance from c4 in STAFF_X_UNIT_EDITOR float unit's
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch+5))
                    },
                    p1={
                        'time': start_click_tick + ((end_click_tick - start_click_tick) / 4),
                        # ...
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch+10))
                    },
                    p2={
                        'time': start_click_tick + ((end_click_tick - start_click_tick) / 4 * 3),
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch+10))
                    },
                    p3={
                        'time': end_click_tick,
                        'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(click_pitch+5))
                    }
                )
            return new

        # HANDLE POSITIONS BASED ON LOGICAL DEFAULT: calculate the four points of the slur
        if hand == 'l':
            start_note = min(notes_happening_in_slur, key=lambda note: (note['time'], note['pitch']))
            end_note = max(notes_happening_in_slur, key=lambda note: (note['time'], -note['pitch']))
        else:
            start_note = min(notes_happening_in_slur, key=lambda note: (note['time'], -note['pitch']))
            end_note = max(notes_happening_in_slur, key=lambda note: (note['time'], note['pitch']))

        # create new slur obj
        if hand == 'l':
            new = SaveFileStructureSource.new_slur(
                tag='slur' + str(io['calc'].add_and_return_tag()),
                staff=io['selected_staff'],
                p0={
                    'time': start_note['time'],
                    # distance from c4 in STAFF_X_UNIT_EDITOR float units
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(start_note['pitch']-5))
                },
                p1={
                    'time': start_note['time'] + ((end_note['time'] - start_note['time']) / 4),
                    # ...
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(start_note['pitch']-10))
                },
                p2={
                    'time': start_note['time'] + ((end_note['time'] - start_note['time']) / 4 * 3),
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(start_note['pitch']-10))
                },
                p3={
                    'time': end_note['time'],
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(end_note['pitch']-5))
                }
            )
        else:
            new = SaveFileStructureSource.new_slur(
                tag='slur' + str(io['calc'].add_and_return_tag()),
                staff=io['selected_staff'],
                p0={
                    'time': start_note['time'],
                    # distance from c4 in STAFF_X_UNIT_EDITOR float unit's
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(start_note['pitch']+5))
                },
                p1={
                    'time': start_note['time'] + ((end_note['time'] - start_note['time']) / 4),
                    # ...
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(start_note['pitch']+10))
                },
                p2={
                    'time': start_note['time'] + ((end_note['time'] - start_note['time']) / 4 * 3),
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(start_note['pitch']+10))
                },
                p3={
                    'time': end_note['time'],
                    'distance_c4units': io['calc'].x2xunits_editor(io['calc'].pitch2x_editor(end_note['pitch']+5))
                }
            )

        return new
