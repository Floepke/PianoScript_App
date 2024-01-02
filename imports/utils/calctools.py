from imports.utils.constants import *

class CalcTools:
    '''
        The CalcTools class contains all the methods that calculate basic things about the score.
        it's a separate class because I don't want to clutter the editor class with these methods.
        It are little solutions to little problems.
        Included methods:
            - get_total_score_ticks(); returns the total number of ticks in the score
            - get_measure_length(grid); returns the length of a measure in pianoticks based on the grid message from the score file
            - tick2y_editor(time); converts pianoticks into y position on the editor
            - pitch2x_editor(pitch); converts pitch into x position on the editor
            - x2pitch_editor(x); converts x position on the editor into pitch
            - y2tick_editor(y); converts y position on the editor into pianoticks
            - add_and_return_tag(); creates a new tag number and returns it
            - renumber_tags(); renumbers the event tags starting from zero again. It's needed if we load a new or existing project.
    '''

    def __init__(self, io):
        self.io = io

    def get_total_score_ticks(self):
        '''returns the total number of ticks from the entire score'''

        total_ticks = 0

        for gr in self.io['score']['events']['grid']:
            
            # calculate the length of one measure based on the numerator and denominator.
            numerator = gr['numerator']
            denominator = gr['denominator']
            measure_length = int(numerator * ((QUARTER_PIANOTICK * 4) / denominator))
            amount = gr['amount']
            
            # assign to total_ticks of one grid message
            total_ticks += measure_length * amount
        
        return total_ticks
    
    @staticmethod
    def get_measure_length(grid):
        '''
            returns the length of a measure in pianoticks 
            based on the grid message from the score file
        '''
        return int(grid['numerator'] * (1024 / grid['denominator']))
    
    def tick2y_editor(self, time):
        '''converts pianoticks into y position on the editor'''
        return time * (self.io['score']['properties']['editor-zoom'] / QUARTER_PIANOTICK) + EDITOR_MARGIN

    @staticmethod
    def pitch2x_editor(pitch):
        '''converts pitch into x position on the editor'''
        
        # evaluate pitch (between 1 and 88) and create initial x position 
        pitch = max(1, min(88, pitch))
        x = LEFT + EDITOR_MARGIN - STAFF_X_UNIT_EDITOR
        
        # 21 is A0, 109 is C8 (based on midi note numbers); 12 is octave, 0 is C, 5 is F
        for n in range(1, 89):
            x += STAFF_X_UNIT_EDITOR if n % 12 in [4, 9] else STAFF_X_UNIT_EDITOR / 2
            if pitch == n:
                break
        
        return x
    
    @staticmethod
    def x2pitch_editor(x):
        '''converts x position on the editor into pitch'''

        # make a list of all x key center positions
        x_positions = []
        x_pos = LEFT + EDITOR_MARGIN - STAFF_X_UNIT_EDITOR
        for n in range(1, 89):
            x_pos += STAFF_X_UNIT_EDITOR if n % 12 in [4, 9] else STAFF_X_UNIT_EDITOR / 2
            x_positions.append(x_pos)

        # find the closest mouse x position based from the x_positions list
        closest_x = min(x_positions, key=lambda y:abs(y-x))
        closest_x_index = x_positions.index(closest_x)
        return closest_x_index + 1
    
    def y2tick_editor(self, y, snap=False):
        '''converts y position on the editor into pianoticks'''
        editor_zoom = self.io['score']['properties']['editor-zoom']
        y = (y - EDITOR_MARGIN) * (QUARTER_PIANOTICK / editor_zoom)
        if y < 0: y = 0
        
        if snap:
            # Snap to grid
            grid_size = self.io['snap_grid']
            y = round(y / grid_size) * grid_size

        return y
    
    def add_and_return_tag(self):
        '''creates a new tag number and returns it'''
        tag = self.io['new_tag']
        self.io['new_tag'] += 1
        return tag
    
    def renumber_tags(self): # TODO: this function is not used yet and needs review
        '''
            This function takes the score and
            renumbers the event tags starting
            from zero again. It's needed if we
            load a new or existing project.
        '''
        for k in self.io['score']['events'].keys(): # loop through all event types
            for obj in self.io['score']['events'][k]: # loop through all objects of one event type
                if not 'tag' in obj: continue # to skip any event that doesn't have a tag
                if obj['tag'] == 'linebreak': continue # to prevent that only the first linebreak doesn't get deleted later in the program
                obj['tag'] = f"{k}{self.io['new_tag']}"
                if k in self.io['selection']['copy_types']:
                    obj['tag'] = '#'+obj['tag']
                self.io['new_tag'] += 1

    @staticmethod
    def update_viewport_ticks(io):
        '''updates the viewport toptick and bottomtick based on the scroll position of the editor'''
        scale_factor = io['gui'].editor_view.transform().m11()
        px_scene_height = io['gui'].editor_scene.sceneRect().height()
        ticks_scene_height = (px_scene_height / (QUARTER_PIANOTICK / io['score']['properties']['editor-zoom'])) * scale_factor
        px_view_height = io['gui'].editor_view.height()
        tick_view_height = (px_view_height * (QUARTER_PIANOTICK / io['score']['properties']['editor-zoom'])) / scale_factor
        tick_editor_margin = io['calc'].y2tick_editor(EDITOR_MARGIN + EDITOR_MARGIN)
        # calculate the toptick and bottomtick
        toptick = (io['gui'].editor_view.verticalScrollBar().value() * (px_scene_height / ticks_scene_height))
        bottomtick = toptick + tick_view_height
        # update the viewport toptick and bottomtick
        io['viewport']['toptick'] = toptick - tick_editor_margin
        io['viewport']['bottomtick'] = bottomtick# + tick_editor_margin

    # process grid selector
    def process_grid(self):
        
        # get values
        listbox = int(self.io['gui'].length_listbox.currentItem().text())
        divide = self.io['gui'].divide_spin_box.value()
        multiply = int(self.io['gui'].multiply_spin_box.value())
        length_dict = {
            '1': 1024,
            '2': 512,
            '4': 256,
            '8': 128,
            '16': 64,
            '32': 32,
            '64': 16,
            '128': 8
        }
        print(f"listbox: {listbox}, divide: {divide}, multiply: {multiply}")
        self.io['snap_grid'] = length_dict[str(listbox)] / divide * multiply
        print(f"listbox: {listbox}, divide: {divide}, multiply: {multiply}")

    
        