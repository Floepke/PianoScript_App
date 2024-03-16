'''These scripts are about changing the rhythm of the score.'''


def multiply_rhythm_by_2(io):

    # access the score file directly:
    score = io['score']

    # multiply all notes in the score
    for note in score['events']['note']:
        note['time'] *= 2
        note['duration'] *= 2

def divide_rhythm_by_2(io):

    # access the score file directly:
    score = io['score']

    # divide all notes in the score
    for note in score['events']['note']:
        note['time'] /= 2
        note['duration'] /= 2