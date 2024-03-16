''' These scripts are about manipulating the pitch of the score '''

def transpose(io):
    ''' This script transposes all notes in the score by the user given semitones '''
    
    # access the score file directly:
    score = io['score']

    # ask user for input
    user_input = io['script'].ask_int('Transpose all notes by x semitones:\n (can be a negative number too)',
                                      min_value=-88, 
                                      max_value=88, 
                                      default_value=0)

    if user_input:
        # transpose all notes in the score by the users given amount
        for note in score['events']['note']:
            value = note['pitch'] + user_input
            if value < 1:
                value = 1
            elif value > 88:
                value = 88
            note['pitch'] = value