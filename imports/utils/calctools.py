from imports.utils.CONSTANT import *

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
        pitch = max(1, min(88, pitch)) # evaluate pitch to be between 1 and 88
        x = LEFT + EDITOR_MARGIN - STAFF_X_UNIT
        for n in range(21, 109): # 21 is A0, 109 is C8 (based on midi note numbers)
            x += STAFF_X_UNIT if n % 12 in [0, 5] else STAFF_X_UNIT / 2 # 12 is octave, 0 is C, 5 is F
            if pitch == n-20: break
        return x
    
    # def mouse2pitch_editor(self, event):
    #     '''converts mouse position into xy position on the editor'''
    #     return self.x2pitch_editor(event.x())
    
    # def mouse2tick_editor(self, event):
    #     '''converts mouse position into tick position on the editor'''
    #     return self.y2tick_editor(event.y())
    

        