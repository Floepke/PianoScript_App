def script_Halftime(script):

    # half time notes
    for note in script.score['events']['note']:
        note['duration'] /= 2
        note['time'] /= 2

    # half time gracenotes
    for gracenote in script.score['events']['gracenote']:
        gracenote['time'] /= 2

    # half time countlines
    for countline in script.score['events']['countline']:
        countline['time'] /= 2

    # half time beam markers
    for beam in script.score['events']['beam']:
        beam['time'] /= 2
        beam['duration'] /= 2

def script_Doubletime(script):

    # double time notes
    for note in script.score['events']['note']:
        note['duration'] *= 2
        note['time'] *= 2

    # double time gracenotes
    for gracenote in script.score['events']['gracenote']:
        gracenote['time'] *= 2

    # double time countlines
    for countline in script.score['events']['countline']:
        countline['time'] *= 2

    # double time beam markers
    for beam in script.score['events']['beam']:
        beam['time'] *= 2
        beam['duration'] *= 2