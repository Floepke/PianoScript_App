import re
from imports.elements.note import Note
from imports.utils.savefilestructure import SaveFileStructureSource


class Selection:

    @staticmethod
    def process(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the selection tool'''

        # start rectangle selection with left+shift or right click
        if event_type == 'leftclick+shift' or event_type == 'rightclick':
            # delete note cursor
            io['editor'].delete_with_tag(['notecursor'])

            # delete the previous selection
            Selection.delete_selection(io)
            # detect if we are clicking an object (tag ending on a number)
            detect = io['editor'].detect_item(
                io, float(x), float(y), event_type='all')
            if not detect:
                # if we are not clicking an object we want to start a selection rectangle
                io['selection']['rectangle_on'] = True
                io['selection']['x1'] = x
                io['selection']['y1'] = y
                io['selection']['x2'] = x
                io['selection']['y2'] = y

                # empty the selection buffer
                io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()

        elif event_type in ['leftclick+shift+move', 'rightclick+move', 'scroll']:
            if io['selection']['rectangle_on'] and not io['shiftmode_flag']:
                # if we are in rectangle selection mode we want to update the rectangle and detect the containing objects
                Selection.draw_selection_rectangle(io, x, y)

        elif event_type in ['leftrelease', 'rightrelease']:
            # delete the selection rectangle
            io['editor'].delete_with_tag(['selectionrectangle'])

            Selection.detect_selection(io)

            io['maineditor'].draw_viewport()

            # disable the selection rectangle
            io['selection']['rectangle_on'] = False
            io['selection']['x1'] = 0
            io['selection']['y1'] = 0
            io['selection']['x2'] = 0
            io['selection']['y2'] = 0

        # io['maineditor'].draw_viewport()

    @staticmethod
    def organize_selection_add(io, selected):

        # organize selection into a dictionary with the same structure as score['events']:
        selection = {}
        for event_type in io['selection']['copy_types']:
            selection[event_type] = []
        for event_type in io['selection']['copy_types']:
            for event in selected:
                if event_type in event['tag']:
                    selection[event_type].append(event)
                    if event in io['viewport']['events'][event_type]:
                        io['viewport']['events'][event_type].remove(event)

        return selection

    @staticmethod
    def delete_selection(io):

        io['selection']['inrectangle'] = []

        # delete all drawn_obj that where in the previous selection (selection_buffer)
        for event_type in io['selection']['selection_buffer'].keys():
            for event in io['selection']['selection_buffer'][event_type]:
                if event in io['viewport']['events'][event_type]:
                    io['viewport']['events'][event_type].remove(event)

    @staticmethod
    def draw_selection_rectangle(io, x, y):
        '''draws the selection rectangle and detects all objects in the rectangle'''

        # if we are in rectangle selection mode we want to update the rectangle
        io['selection']['x2'] = x
        io['selection']['y2'] = y

        def standardize_coordinates(x1, y1, x2, y2):
            top_left_x = min(x1, x2)
            top_left_y = min(y1, y2)
            bottom_right_x = max(x1, x2)
            bottom_right_y = max(y1, y2)
            return top_left_x, top_left_y, bottom_right_x, bottom_right_y

        x1, y1, x2, y2 = standardize_coordinates(
            io['selection']['x1'], io['selection']['y1'], io['selection']['x2'], io['selection']['y2'])

        # delete the selection rectangle
        io['editor'].delete_with_tag(['selectionrectangle'])

        # draw the selection rectangle
        io['editor'].new_rectangle(x1,
                                   y1,
                                   x2,
                                   y2,
                                   tag=['selectionrectangle'],
                                   fill_color='',
                                   width=4,
                                   outline_color='ff0000ff',
                                   dash=(2, 2))
        io['editor'].tag_raise(['selectionrectangle'])

    @staticmethod
    def detect_selection(io):
        '''detects and stores objects inside the selection rectangle'''

        def standardize_coordinates(x1, y1, x2, y2):
            top_left_x = min(x1, x2)
            top_left_y = min(y1, y2)
            bottom_right_x = max(x1, x2)
            bottom_right_y = max(y1, y2)
            return top_left_x, top_left_y, bottom_right_x, bottom_right_y

        x1, y1, x2, y2 = standardize_coordinates(
            io['selection']['x1'], io['selection']['y1'], io['selection']['x2'], io['selection']['y2'])

        # clear the current buffer
        io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()

        # detect any score objects within the rectangle via scene items
        detected = io['editor'].detect_objects_rectangle(io, x1, y1, x2, y2, event_type='all') or []

        for obj in detected:
            # determine event type from tag prefix and configured copy_types
            evt_type = None
            for t in io['selection']['copy_types']:
                if t in obj['tag']:
                    evt_type = t
                    break
            if not evt_type:
                continue

            # filter by selected staff if the object has a staff attribute
            if 'staff' in obj and obj['staff'] != io['selected_staff']:
                continue

            # add to selection buffer and force redraw by removing from viewport cache
            io['selection']['selection_buffer'][evt_type].append(obj)
            if obj in io['viewport']['events'][evt_type]:
                io['viewport']['events'][evt_type].remove(obj)

        # mark selection as active if anything was added
        io['selection']['active'] = any(len(v) > 0 for v in io['selection']['selection_buffer'].values())

    @staticmethod
    def select_all(io):
        '''Select all notes in the project and color visible ones blue.'''

        # clear previous selection visuals and buffer
        Selection.delete_selection(io)
        io['selection']['selection_buffer'] = SaveFileStructureSource.new_events_folder()
        io['selection']['active'] = True

        # add all notes to the selection buffer
        for note in io['score']['events']['note']:
            io['selection']['selection_buffer']['note'].append(note)
            # force redraw in selection color by removing existing viewport entries
            if note in io['viewport']['events']['note']:
                io['viewport']['events']['note'].remove(note)

        # update the viewport to reflect selection color
        io['maineditor'].draw_viewport()
