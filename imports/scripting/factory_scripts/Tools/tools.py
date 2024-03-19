# TODO: scripts not working and change the creation of the linebreak

def script_add_quick_linebreaks(script):
    """
    Adds linebreaks to the score at intervals specified by the user.

    The user can input one or more integers. Each integer represents the number of measures 
    before a linebreak is added. The last integer is applied repeatedly until the end of the score.
    """

    intervals = script.ask_str('Enter the one or more intervals in which the linebreaks should be added.\nExample:"2 3 5" will place 2 measures in the first line, 3 in the second \nand 5 in the third and so on. 5 will be applied till the end of the score.')
    if intervals: 
        overwrite = script.ask_yesno('Overwrite existing linebreaks?')
    else:
        return

    if intervals and overwrite:
        
        if overwrite:
            # delete any existing linebreak except the lockedlinebreak
            script.score['events']['linebreak'] = []
            script.add_linebreak(0, tag='lockedlinebreak')
            
            
        # evaluate if the input is valid
        for interval in intervals.split(' '):
            try:
                interval = int(interval)
                if interval < 1:
                    script.error('The script only accepts integers greater than 0 as input. E.g. "2 3 5". Script aborted.')
                    return
            except:
                script.error('The script only accepts integers seperated by space as input. E.g. "2 3 5". Script aborted.')
                return
        
        # convert the input to a list
        intervals = [int(interval) for interval in intervals.split(' ')]

        # get the barline ticks
        barline_times = script.get_barline_ticks()
        score_ticks = script.get_score_ticks()
        barline_times.append(score_ticks)

        time = 0
        interval_index = 0

        while time <= score_ticks:
            # Use the current interval to index into barline_times
            interval = intervals[interval_index]
            time += barline_times[interval]
            print('time', time)

            if time >= score_ticks:
                break

            # add a linebreak
            script.add_linebreak(time)

            # Move to the next interval, or stay at the last one if we've reached the end of the list
            if interval_index < len(intervals) - 1:
                interval_index += 1


def script_switch_hands(io):

    for note in io['score']['events']['note']:

        if note['hand'] == 'l':
            note['hand'] = 'r'
        else:
            note['hand'] = 'l'  