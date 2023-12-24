class CalcTools:
    '''
        The CalcTools class contains all the methods that calculate basic things about the score.
        it's a separate class because I don't want to clutter the editor class with these methods.
        It are little solutions to little problems.
        Included methods:
            - get_total_score_ticks(); returns the total number of ticks in the score
    '''

    def __init__(self, io):
        self.io = io

    def get_total_score_ticks(self):
        '''Returns the total number of ticks from the score'''
        
        total_ticks = 0
        
        for gr in self.io['score']['events']['grid']:
            
            # calculate the length of one measure based on the numerator and denominator.
            numerator = gr['numerator']
            denominator = gr['denominator']
            measure_length = int(numerator * (1024 / denominator))
            amount = gr['amount']
            
            # assign to total_ticks of one grid message
            total_ticks += measure_length * amount
        
        return total_ticks
    
    @staticmethod
    def get_measure_length(grid):
        '''
            Returns the length of a measure in pianoticks. 
            argument: grid message from the score file
        '''
        return int(grid['numerator'] * (1024 / grid['denominator']))
    
    def time2y_editor(self, time):
        '''
            time2y converts pianoticks into pixels
            based on the io preferences.
        '''
        return time * (self.io['score']['properties']['editor-zoom'] / self.io['QUARTER_PIANOTICK']) + self.io['EDITOR_MARGIN']

    def pitch2x_editor(self, pitch):
        '''
            pitch2x converts pitch into pixels
            based on the io preferences.
        '''
        # check if the pitch is in the range of the editor
        if pitch < 1:
            pitch = 1
            print('pitch out of range, set to 1')
        elif pitch > 88:
            pitch = 88
            print('pitch out of range, set to 88')
        
        # calculate the x position
        notes = ['c', 'C', 'd', 'D', 'e', 'f', 'F', 'g', 'G', 'a', 'A', 'b']
        x = self.io['LEFT'] + self.io['EDITOR_MARGIN']
        for n in range(21, 109): # 21 is A0, 109 is C8
            x += (self.io['EDITOR_X_UNIT'] / 2) * (2 if notes[n % 12] in ['c', 'f'] else 1)
            if pitch == n-20: break
        return x - self.io['EDITOR_X_UNIT']
    

        