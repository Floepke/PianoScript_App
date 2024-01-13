'''
    In this file we dump all the calculations for the engraver.
    Like the calctools.py it stores all solutions to little 
    problems but for the engraver.
'''

def note_split_processor(io, note):
    '''
        note_split_processor splits a note message into different parts
        if the note is crossing a linebreak point. This is neccesary because
        we have to draw the note in two parts in this case.
    '''

    output = []
    n_start = note['time']
    n_end = note['time']+note['duration']

    # create list with all linebreak times
    linebreak_times = []
    for lb in io['score']['events']['linebreak']:
        linebreak_times.append(lb['time'])
    
    # check if there is a linebreak in between n_start and n_end
    nb_times = []
    for lb in linebreak_times:
        if n_start < lb < n_end:
            nb_times.append(lb)
    
    # if there is no linebreak in between n_start and n_end
    if not nb_times:
        note['type'] = 'note'
        output.append(note)
        return output
    
    # process the linebreaks
    first = True
    for nb in nb_times:
        new = dict(note)
        new['duration'] = nb - n_start
        new['time'] = n_start
        if first:
            new['type'] = 'note'
        else:
            new['type'] = 'notesplit'
        output.append(new)
        n_start = nb
        first = False

    # add the last split note
    new = dict(note)
    new['duration'] = n_end - n_start
    new['time'] = n_start
    new['type'] = 'notesplit'
    output.append(new)

    return output






















