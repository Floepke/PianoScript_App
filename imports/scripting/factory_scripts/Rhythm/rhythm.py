'''These scripts are about changing the rhythm of the score.'''


def script_halftime(script):

    # multiply all notes in the score
    for note in script.score['events']['note']:
        note['time'] /= 2
        note['duration'] /= 2
    for gracenote in script.score['events']['gracenote']:
        gracenote['time'] /= 2

def script_doubletime(script):

    # divide all notes in the score
    for note in script.score['events']['note']:
        note['time'] *= 2
        note['duration'] *= 2
    for gracenote in script.score['events']['gracenote']:
        gracenote['time'] *= 2