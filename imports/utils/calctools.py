from imports.utils.HARDCODE import *

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
    
    def time2y_editor(self, time):
        '''converts pianoticks into y position on the editor'''
        return time * (self.io['score']['properties']['editor-zoom'] / QUARTER_PIANOTICK) + EDITOR_MARGIN

    def pitch2x_editor(self, pitch):
        '''converts pitch into x position on the editor'''
        
        # check if the pitch is in the range of the editor (1-88)
        pitch = max(1, min(88, pitch))
        
        # calculate the x position
        notes = ['c', 'C', 'd', 'D', 'e', 'f', 'F', 'g', 'G', 'a', 'A', 'b']
        x = LEFT + EDITOR_MARGIN
        for n in range(21, 109): # 21 is A0, 109 is C8; based on midi note numbers
            x += (EDITOR_X_UNIT / 2) * (2 if notes[n % 12] in ['c', 'f'] else 1)
            if pitch == n-20: break
        return x - EDITOR_X_UNIT
    

        