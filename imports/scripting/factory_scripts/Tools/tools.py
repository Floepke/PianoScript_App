

def script_Remap_hands_from_track_number(script):

    tracks = [] # tuples (track number, track name)
    for tr in script.score['midi_data']:
        if tr['type'] == 'track_name':
            tracks.append((tr['track'], tr['name']))
    
    if tracks: choosed, index = script.ask_list(f'''Choose which track you want to remap:''', [f'track number: {track[0]}; track name: {track[1]}' for track in tracks])
    else: 
        script.info('This .pianoscript file was not imported from midi and therefore it cannot be remapped from track number. Script aborted.')
        return

    track_number = tracks[index][0]
    track_name = tracks[index][1]

    remap_to, _ = script.ask_list(f'''Choose to set "track {track_number}; {track_name}" to left or right hand:''', ['left', 'right'])
    remap_to = remap_to[0]

    for note in script.score['events']['note']:
        if note['track'] == track_number:
            note['hand'] = remap_to

def script_Add_quick_linebreaks(script):

    user_input = script.ask_str('''
                                Enter a list of integers that represent the grouping of
                                the measures. 
                                
                                Example: "4 3 5 4" will place 4 measures in 
                                the first line, 2 in the second etc... 
                                
                                The last number groups 
                                until the end of the document. 
                                
                                You can also group the entire 
                                file by entering "4" into groups of 4.''')
    
    if not user_input:
        script.info('No user input. Aborting.')
        return

    try:
        user_input = [int(n) for n in user_input.split()]
    except ValueError:
        script.error('Please enter only integers Try again. Aborting.')
        return
    
    print(user_input)

