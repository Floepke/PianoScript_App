from imports.utils.constants import *
from PySide6.QtWidgets import QMessageBox, QFileDialog
import mido
import os
import threading
import json
import statistics
from midiutil.MidiFile import MIDIFile
from imports.utils.savefilestructure import SaveFileStructureSource



class Midi:

    def __init__(self, io):

        self.io = io

        # midi play
        self.playing = False
        self.play_thread = None
        self.outports = []
        self.lock = threading.Lock()  # Create a lock

    def leftorright(self, channel, name):

        dialog = QMessageBox()
        dialog.setWindowTitle('Which Hand?')
        dialog.setText(
            f'To which hand do you want to import?\nChannel: {channel}\nName: {name}')

        left_button = dialog.addButton('Left', QMessageBox.NoRole)
        right_button = dialog.addButton('Right', QMessageBox.YesRole)

        dialog.exec()

        if dialog.clickedButton() == left_button:
            return 'l'
        elif dialog.clickedButton() == right_button:
            return 'r'

    def load_midi(self, file_path):
        '''converts/imports a midi file from the file_path to .pianoscript'''
        
        # load the template
        path = self.io['calc'].ensure_json('~/.pianoscript/template.pianoscript', SCORE_TEMPLATE)
        with open(path, 'r') as file:
            self.io['score'] = json.load(file)
        
        # ensure the contents of the file are empty
        self.io['score']['header']['title'] = os.path.splitext(
            os.path.basename(file_path))[0]
        self.io['events'] = SaveFileStructureSource.new_events_folder()
        self.io['score']['events']['grid'] = []

        def read_midi(filepath):
            midi = mido.MidiFile(filepath)

            events = []
            
            # create dict of all events and filter only the desired types
            for i, track in enumerate(midi.tracks):
                for msg in track:
                    new = msg.dict()
                    new['track'] = i
                    events.append(new)
            filter = ['time_signature', 'set_tempo', 'end_of_track', 'track_name', 'note_on', 'note_off']
            events = [evt for evt in events if evt['type'] in filter]

            # check for every track if it contains any note. if not we delete all events from that track.
            placeholder = []
            track_names = {}
            for tracks in range(16):
                track_events = [evt for evt in events if evt['track'] == tracks]
                contains_desired = False
                for evt in track_events:
                    if evt['type'] in ['note_on', 'note_off', 'set_tempo']:
                        contains_desired = True
                        break
                if contains_desired:
                    # search for track name
                    for evt2 in track_events:
                        if evt2['type'] == 'track_name':
                            track_names[tracks] = evt2['name']
                    for evt2 in track_events:
                        placeholder.append(evt2)
            events = placeholder

            # change note_on with zero velocity to note_off.
            for evt in events:
                if evt['type'] == 'note_on':
                    if evt['velocity'] == 0:
                        evt['type'] = 'note_off'

            # delta to relative time.
            time = 0
            for evt in events:
                time += evt['time']
                evt['time'] = time
                if evt['type'] == 'end_of_track':
                    time = 0

            # convert time to pianoticks.
            ticks_per_quarter = midi.ticks_per_beat
            pianoticks_per_quarter = 256
            for evt in events:
                evt['time'] = evt['time'] * (pianoticks_per_quarter / ticks_per_quarter)

            # sort on time key
            events = sorted(events, key=lambda evt: evt['time'])

            # calculate duration of note_on, time_signature
            for idx, evt in enumerate(events):
                if evt['type'] == 'note_on':
                    for dur in events[idx+1:]:
                        if dur['type'] == 'note_off' and dur['note'] == evt['note'] or dur['type'] == 'end_of_track':
                            evt['duration'] = dur['time'] - evt['time']
                            break
                if evt['type'] == 'time_signature':
                    for idx_dur, dur in enumerate(events[idx+1:]):
                        if dur['type'] == 'time_signature' or len(events[idx+1:])-1 == idx_dur:
                            evt['duration'] = dur['time'] - evt['time']
                            break
            
            # delete note_off, we don't need it
            filter = ['note_off']
            events = [evt for evt in events if not evt['type'] in filter]

            # check for notes that have zero length and change the duration to 8 pianoticks (128th note)
            for note in events:
                if note['type'] == 'note_on':
                    if note['duration'] < 8:
                        note['duration'] = 8

            # for eye candy I like to change the name note_on to note because it's noth note on and off
            for note in events: 
                if note['type'] == 'note_on':
                    note['type'] = 'note'

            return events, track_names
        
        events, track_names = read_midi(file_path)

        # gues the hand based on the avarage pitch and track number.
        avarage_tracks = {}
        for t in range(16):
            avarage_pitch = []
            for evt in events:
                if evt['type'] == 'note' and evt['track'] == t:
                    avarage_pitch.append(evt['note'])
            avarage_pitch = statistics.mean(avarage_pitch) if avarage_pitch else None
            avarage_tracks[t] = avarage_pitch
        highest_track = max((k for k, v in avarage_tracks.items() if v is not None), key=avarage_tracks.get, default=None)

        
        # add the events to the .pianoscript file
        for evt in events:
            print(evt)
            if evt['type'] == 'note':
                hand = 'r' if highest_track == evt['track'] and not highest_track == None else 'l'
                pitch = max(1, min(88, evt['note'] - 20))
                new = SaveFileStructureSource.new_note(
                    tag = 0,
                    pitch = pitch,
                    time = evt['time'],
                    duration = evt['duration'],
                    hand = hand,
                    staff = 0,
                    track = evt['track'],
                )
                self.io['score']['events']['note'].append(new)

            elif evt['type'] == 'time_signature':
                measure_length = self.io['calc'].get_measure_length(evt)
                amount = int(evt['duration'] / measure_length)
                grid = []
                for numerator_count in range(evt['numerator']-1):
                    grid.append(measure_length / evt['numerator'] * (numerator_count+1))
                new = SaveFileStructureSource.new_grid(
                    amount = amount,
                    numerator = evt['numerator'],
                    denominator = evt['denominator'],
                    grid = grid,
                )
                self.io['score']['events']['grid'].append(new)

        # if the midi contains no time signature we add it manualy
        if not self.io['score']['events']['grid']:
            measure_length = self.io['calc'].get_measure_length({'numerator':4,'denominator':4})
            new = SaveFileStructureSource.new_grid(
                amount = int(max(events, key=lambda evt: evt['time'])['time'] / measure_length),
                numerator = 4,
                denominator = 4,
                grid = [256, 512, 768]
            )
            self.io['score']['events']['grid'].append(new)

        # add the imported midi message to the .pianoscript file
        self.io['score']['midi_data'] = events

        # renumber tags
        self.io['calc'].renumber_tags()

        # draw the editor
        self.io['maineditor'].redraw_editor()
        self.io['maineditor'].redraw_editor()

        # reset the ctlz buffer
        self.io['ctlz'].reset_ctlz

    def export_midi(self, export=True, tempo=120):

        if export:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self.io['root'], 'Save Midi File', '', 'Midi Files (*.mid *.MID)')
        else:
            file_path = os.path.expanduser('~/.pianoscript/play.mid')

            # Check if the directory for the play.mid file exists
            dir = os.path.dirname(file_path)
            if not os.path.exists(dir):
                # If the directory doesn't exist, create it
                os.makedirs(dir)

        if file_path:
            Score = self.io['score']
            # configure channels and names
            longname = {'l': 'left', 'r': 'right'}
            trackname = {}
            channel = {}
            nrchannels = 0
            for note in Score['events']['note']:
                if note['hand'] not in channel:
                    channel[note['hand']] = nrchannels
                    trackname[nrchannels] = longname[note['hand']]
                    nrchannels += 1

            # some info for the midifile
            clocks_per_tick = 24
            denominator_dict = {
                1: 0,
                2: 1,
                4: 2,
                8: 3,
                16: 4,
                32: 5,
                64: 6,
                128: 7,
                256: 8
            }
            ticks_per_quarternote = 2048

            # creating the midi file object
            MyMIDI = MIDIFile(numTracks=nrchannels,
                              removeDuplicates=True,
                              deinterleave=False,
                              adjust_origin=False,
                              file_format=1,
                              ticks_per_quarternote=ticks_per_quarternote,
                              eventtime_is_ticks=True)

            for ts in Score['events']['grid']:
                MyMIDI.addTimeSignature(track=0,
                                        time=0,
                                        numerator=int(ts['numerator']),
                                        denominator=denominator_dict[int(
                                            ts['denominator'])],
                                        clocks_per_tick=clocks_per_tick,
                                        notes_per_quarter=8)
            MyMIDI.addTempo(track=0, time=0, tempo=tempo)
            MyMIDI.addTrackName(track=0, time=0, trackName='Tempo & Left hand')
            MyMIDI.addTrackName(track=1, time=0, trackName='Right hand')

            # adding the notes
            for note in Score['events']['note'] + Score['events']['gracenote']:
                t = int(note['time']/256*ticks_per_quarternote)
                if 'duration' in note: d = int(note['duration']/256*ticks_per_quarternote)
                else: d = 32 # length for midi if gracenote
                c = 0
                if note['hand'] == 'r':
                    c = 1  # l or r?? first fix the midi import
                MyMIDI.addNote(track=0 if note['hand'] == 'l' else 1, channel=c, pitch=int(
                    note['pitch']+20), time=t, duration=d, volume=80, annotation=None)

            # saving the midi file
            with open(file_path, "wb") as output_file:
                MyMIDI.writeFile(output_file)
