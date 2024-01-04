import re
from imports.design.note import Note

class Selection:

    @staticmethod
    def process(io, event_type: str, x: int, y: int):
        '''handles the mouse handling of the selection tool'''

        # right mouse button handling:
        if event_type == 'rightclick':
            # delete note cursor
            io['editor'].delete_with_tag(['notecursor'])

            # detect if we are clicking an object (tag ending on a number)
            detect = io['editor'].detect_items(io['score'], float(x), float(y), object_type='all')
            if not detect:
                # if we are not clicking an object we want to start a selection rectangle
                io['selection']['rectangle_on'] = True
                io['selection']['x1'] = x
                io['selection']['y1'] = y
                io['selection']['x2'] = x
                io['selection']['y2'] = y

                # draw the selection rectangle
                Selection.draw_selection_rectangle(io)

                # empty the selection buffer
                io['selection']['selection_buffer'] = {
                    'note':[],
                    'ornament':[],
                    'text':[],
                    'beam':[],
                    'slur':[],
                    'pedal':[],
                    'countline':[],
                    'staffsizer':[],
                    'startrepeat':[],
                    'endrepeat':[],
                    'starthook':[],
                    'endhook':[],
                    'countline':[]
                }
                io['maineditor'].draw_viewport(io)
                

        elif event_type == 'rightclick+move':
            if io['selection']['rectangle_on']:
                # if we are in rectangle selection mode we want to update the rectangle
                io['selection']['x2'] = x
                io['selection']['y2'] = y

                # redraw the selection rectangle
                Selection.draw_selection_rectangle(io)

        
        elif event_type == 'rightrelease':
            # delete the selection rectangle
            io['editor'].delete_with_tag(['selectionrectangle'])

            # detect all notes in the selection rectangle
            selected = None
            if io['selection']['rectangle_on']:
                selected = io['editor'].detect_objects_rectangle(io['score'], 
                                                                io['selection']['x1'], 
                                                                io['selection']['y1'], 
                                                                io['selection']['x2'], 
                                                                io['selection']['y2'], 
                                                                object_type='note')
            
            # write the selected objects to the selection buffer if there are any
            if selected is not None: 
                io['selection']['selection_buffer'] = Selection.organize_selection(io, selected)

                # make the selection blue
                io['maineditor'].draw_viewport(io)

            # disable the selection rectangle
            io['selection']['rectangle_on'] = False
            io['selection']['x1'] = None
            io['selection']['y1'] = None
            io['selection']['x2'] = None
            io['selection']['y2'] = None

    @staticmethod
    def organize_selection(io, selected: list):
        
        # organize selection into a dictionary with the same structue as score['events']:
        event_types = ['note', 'slur', 'beam', 'countline']
        selection = {}
        for event_type in event_types:
            selection[event_type] = []
        
        for event_type in event_types:
            for event in selected:
                if event_type in event['tag']:
                    selection[event_type].append(event)

        return selection

    @staticmethod
    def draw_selection_rectangle(io):
        '''draws the selection rectangle'''

        # delete the selection rectangle
        io['editor'].delete_with_tag(['selectionrectangle'])

        # draw the selection rectangle
        io['editor'].new_rectangle(io['selection']['x1'],
                                   io['selection']['y1'],
                                   io['selection']['x2'],
                                   io['selection']['y2'],
                                   tag=['selectionrectangle'],
                                   fill_color='#009cff60',
                                   width=1,
                                   outline_color='000000ff',
                                   dash=(6,6))
        io['editor'].tag_raise(['selectionrectangle'])

        