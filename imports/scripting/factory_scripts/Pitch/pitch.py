''' These scripts are about manipulating the pitch of the score '''
# TODO: these scripts are not working

def script_transpose_from_to_measure(io):
    ''' This script transposes all notes in the score by the user given semitones '''

    # get score
    score = io['score']

    # get amount of measures in the file
    grids = io['score']['events']['grid']
    measure_amount = 0
    for gr in grids:
        for i in range(gr['amount']):
            measure_amount += 1

    # ask user for input
    from_ = io['script'].ask_int(
        'Select from measure ...', min_value=1, max_value=measure_amount, default_value=1)
    to_ = io['script'].ask_int(
        'to measure ...', min_value=from_, max_value=measure_amount, default_value=from_)
    transpose = io['script'].ask_int('Transpose all notes by x semitones:\n (can be a negative number too)',
                                     min_value=-88,
                                     max_value=88,
                                     default_value=0)

    # get barline times
    barline_times = io['calc'].get_barline_ticks()
    barline_times.append(io['total_ticks'])

    if from_ and to_ and transpose:
        # transpose all notes in the score by the users given amount
        for note in score['events']['note']:
            if note['time'] >= barline_times[from_-1] and note['time'] < barline_times[to_]:
                value = note['pitch'] + transpose
                if value < 1:
                    value = 1
                elif value > 88:
                    value = 88
                note['pitch'] = value
    else:
        io['script'].info(
            'The script didn\'t get enough input. Nothing happened.')


def script_transpose_all(io):
    ''' This script transposes all notes in the score by the user given semitones '''

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


def script_mirror_pitch(io):
    ''' This script mirrors all pitch values in the score '''

    score = io['score']

    # get highest and lowest pitch in the score
    highest = 0
    lowest = 88
    for note in io['score']['events']['note']:
        if note['pitch'] > highest:
            highest = note['pitch']
        if note['pitch'] < lowest:
            lowest = note['pitch']

    # mirror all notes in the score
    for note in io['score']['events']['note']:
        note['pitch'] = highest - note['pitch'] + lowest
    for gracenote in io['score']['events']['gracenote']:
        gracenote['pitch'] = highest - gracenote['pitch'] + lowest

def script_remap_all_occurrences_of_pitch_x(script):

    remap = script.ask_int('Remap note ...:\n(integer 1-88)',
                                      min_value=1,
                                      max_value=88,
                                      default_value=40)
    if not remap: return
    remapped = script.ask_int('... to note:\n(integer 1-88)',
                                      min_value=1,
                                      max_value=88,
                                      default_value=40)
    if not remapped: return
    
    # remap the notes
    for r in script.score['events']['note']:
        if r['pitch'] == remap:
            r['pitch'] = remapped
    # remap the gracenotes
    for r in script.score['events']['gracenote']:
        if r['pitch'] == remap:
            r['pitch'] = remapped
