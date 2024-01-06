import re
from imports.design.note import Note
from imports.utils.savefilestructure import empty_events_folder

class Selection:

    @staticmethod
    def process(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the selection tool'''

        # right mouse button handling:
        if event_type == 'rightclick':
            # delete note cursor
            io['editor'].delete_with_tag(['notecursor'])

            # delete the previous selection
            Selection.delete_selection(io)

            # detect if we are clicking an object (tag ending on a number)
            detect = io['editor'].detect_item(io['score'], float(x), float(y), event_type='all')
            if not detect:
                # if we are not clicking an object we want to start a selection rectangle
                io['selection']['rectangle_on'] = True
                io['selection']['x1'] = x
                io['selection']['y1'] = y
                io['selection']['x2'] = x
                io['selection']['y2'] = y

                # empty the selection buffer
                io['selection']['selection_buffer'] = empty_events_folder()
                

        elif event_type in ['rightclick+move', 'scroll']:
            if io['selection']['rectangle_on']:
                # if we are in rectangle selection mode we want to update the rectangle and detect the containing objects
                Selection.draw_selection_rectangle_and_detect(io, x, y)

        
        elif event_type == 'rightrelease':
            # delete the selection rectangle
            io['editor'].delete_with_tag(['selectionrectangle'])

            selected = io['selection']['inrectangle']
            
            # write the selected objects to the selection buffer in the folder structure of ['score']['events']
            if selected is not None: 
                io['selection']['selection_buffer'] = Selection.organize_selection_add(io, selected)

            io['maineditor'].draw_viewport()

            # disable the selection rectangle
            io['selection']['rectangle_on'] = False
            io['selection']['x1'] = None
            io['selection']['y1'] = None
            io['selection']['x2'] = None
            io['selection']['y2'] = None

        io['maineditor'].draw_viewport()

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
                    if event['tag'] in io['drawn_obj']:
                        io['drawn_obj'].remove(event['tag'])

        return selection
    
    @staticmethod
    def delete_selection(io):

        io['selection']['inrectangle'] = []
        
        # delete all drawn_obj that where in the previous selection (selection_buffer)
        for event_type in io['selection']['selection_buffer'].keys():
            for event in io['selection']['selection_buffer'][event_type]:
                if event['tag'] in io['drawn_obj']:
                    io['drawn_obj'].remove(event['tag'])

    @staticmethod
    def draw_selection_rectangle_and_detect(io, x, y):
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
        
        x1, y1, x2, y2 = standardize_coordinates(io['selection']['x1'], io['selection']['y1'], io['selection']['x2'], io['selection']['y2'])

        # detect all notes in the selection rectangle
        selected = io['editor'].detect_objects_rectangle(io, 
                                                            x1, 
                                                            y1, 
                                                            x2,
                                                            y2, 
                                                            event_type='all')
        
        # add the selected notes to the rectangle detection list
        if selected is not None:
            for s in selected:
                io['selection']['inrectangle'].append(s)

        # remove duplicates from the inrectangle list
        io['selection']['inrectangle'] = list({v['tag']:v for v in io['selection']['inrectangle']}.values())

        # delete the selection rectangle
        io['editor'].delete_with_tag(['selectionrectangle'])

        # draw the selection rectangle
        io['editor'].new_rectangle(x1,
                                   y1,
                                   x2,
                                   y2,
                                   tag=['selectionrectangle'],
                                   fill_color='#f09cff60',
                                   width=1,
                                   outline_color='000000ff',
                                   dash=(6,6))
        io['editor'].tag_raise(['selectionrectangle'])

        