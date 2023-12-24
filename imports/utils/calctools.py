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


        