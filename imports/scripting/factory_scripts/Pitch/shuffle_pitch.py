

def script_Shuffle_pitch_from_selected_notes(script):

    selected_notes = script.selected()['note']
    score = script.score

    # gather pitch
    pitch = []
    for note in selected_notes:
        pitch.append(note['pitch'])

    # shuffle
    import random
    random.shuffle(pitch)

    # apply shuffled
    idx_shuffle = 0
    for note in score['events']['note']:
        if note in selected_notes:
            note['pitch'] = pitch[idx_shuffle]
            idx_shuffle += 1
