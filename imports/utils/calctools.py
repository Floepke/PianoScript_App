from imports.utils.constants import *

class CalcTools:
    '''
        The CalcTools class contains all the methods that calculate basic things about the score.
        it's a separate class because I don't want to clutter the editor class with these methods.
        It are little solutions to little problems.
        Included methods:
            - get_total_score_ticks(); returns the total number of ticks in the score
            - get_measure_length(grid); returns the length of a measure in pianoticks based on the grid message from the score file

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

    def pitch2x_editor(self, pitch):
        '''converts pitch into x position on the editor'''
        
        # evaluate pitch (between 1 and 88) and create initial x position 
        pitch = max(1, min(88, pitch))
        x = LEFT + EDITOR_MARGIN - STAFF_X_UNIT_EDITOR
        
        # 21 is A0, 109 is C8 (based on midi note numbers); 12 is octave, 0 is C, 5 is F
        for n in range(21, 109):
            x += STAFF_X_UNIT_EDITOR if n % 12 in [0, 5] else STAFF_X_UNIT_EDITOR / 2
            if pitch == n-20:
                break
        
        return x
    
    def x2pitch_editor(self, x):
        '''converts x position on the editor into pitch'''
        
        # make a list of all base x positions
        x_positions = []
        for n in range(88):
            x_positions.append(self.pitch2x_editor(n+1))

        # find the closest base x position
        closest_x = min(x_positions, key=lambda y:abs(y-x))
        closest_x_index = x_positions.index(closest_x)
        return closest_x_index + 1
    
    def y2tick_editor(self, y):
        '''converts y position on the editor into pianoticks'''
        snap_grid = self.io['snap_grid']
        return int((y - EDITOR_MARGIN) * (QUARTER_PIANOTICK / self.io['score']['properties']['editor-zoom']) / snap_grid) * snap_grid

    
    def create_new_tag_number(self):
        '''returns the tag of an element'''
        tag = self.io['new_tag']
        self.io['new_tag'] += 1
        return tag
    
    def renumber_tags(self):
        '''
            This function takes the score and
            renumbers the event tags starting
            from zero again. It's needed if we
            load a new or existing project.
        '''
        for k in self.io['score']['events'].keys(): # loop through all event types
            for obj in self.io['score']['events'][k]: # loop through all objects of one event type
                if not 'tag' in obj: continue # to skip any event that doesn't have a tag
                if obj['tag'] == 'linebreak': continue # to ensure that only the first linebreak doesn't get a new tag
                obj['tag'] = f"{k}{self.io['new_tag']}"
                if k in self.io['selection']['copy_types']:
                    obj['tag'] = '#'+obj['tag']
                self.io['new_tag'] += 1
        