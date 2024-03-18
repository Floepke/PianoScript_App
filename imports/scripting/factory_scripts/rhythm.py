'''These scripts are about changing the rhythm of the score.'''


def halftime(io):

    # access the score file directly:
    score = io['score']

    # multiply all notes in the score
    for note in score['events']['note']:
        note['time'] /= 2
        note['duration'] /= 2
    for gracenote in score['events']['gracenote']:
        gracenote['time'] /= 2

def doubletime(io):

    # access the score file directly:
    score = io['score']

    # divide all notes in the score
    for note in score['events']['note']:
        note['time'] *= 2
        note['duration'] *= 2
    for gracenote in score['events']['gracenote']:
        gracenote['time'] *= 2