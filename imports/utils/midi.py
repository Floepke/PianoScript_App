from imports.utils.constants import *
from PySide6.QtWidgets import QMessageBox, QFileDialog
import mido
import os
import threading
import json
import statistics
import copy
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

    def import_midi(self, file_path):
        '''converts/imports a midi file from the file_path to .pianoscript'''

        # load the template:
        path = self.io['calc'].ensure_json(
            '~/.pianoscript/template.pianoscript', SCORE_TEMPLATE)
        with open(path, 'r') as file:
            self.io['score'] = json.load(file)

        # ensure the contents of the file are empty:
        self.io['score']['header']['title'] = os.path.splitext(
            os.path.basename(file_path))[0]
        self.io['events'] = SaveFileStructureSource.new_events_folder()
        self.io['score']['events']['grid'] = []
        self.io['score']['events']['linebreak'] = []

        def import_midi(filepath):
            midi = mido.MidiFile(filepath)

            tracks = {}

            def prepare_midi(midi):

                def track_to_linear_ticks(track):
                    absolute_time = 0
                    for msg in track:
                        absolute_time += msg.time
                        msg.time = absolute_time
                    return track

                # create dict of all events and filter only the desired types
                for i, track in enumerate(midi.tracks):
                    track = track_to_linear_ticks(track)
                    track_ = []
                    for msg in track:
                        new = msg.dict()
                        new['track'] = i
                        # make notes with zero velocity note_off type
                        if new['type'] == 'note_on' and new['velocity'] == 0:
                            new['type'] = 'note_off'
                        track_.append(new)
                    tracks[i] = track_

                for track in tracks.keys():
                    filter = ['time_signature', 'set_tempo',
                              'end_of_track', 'track_name', 'note_on', 'note_off']
                    tracks[track] = [evt for evt in tracks[track] if evt['type'] in filter]

                return tracks

            # step 1: read the midi and create a list of msg that have linear time values and are sorted on the time key from low to high
            all_events = prepare_midi(midi)
            all_events = [msg for track in all_events.values() for msg in track]
            message_priority = {'note_off': 1, 'note_on': 2,
                                'time_signature': 3, 'end_of_track': 4}
            all_events.sort(key=lambda msg: (
                msg['time'], message_priority.get(msg['type'], 5)))

            # step 2: convert the miditicks to pianoticks
            ticks_per_quarter = midi.ticks_per_beat
            for evt in all_events:
                evt['time'] = evt['time'] * (QUARTER_PIANOTICK / ticks_per_quarter)

            # step 3: calculate the duration of note_on and time_signature events
            for idx, evt in enumerate(all_events):
                if evt['type'] == 'note_on':
                    for dur in all_events[idx+1:]:
                        if (dur['type'] == 'note_off' and dur['note'] == evt['note'] and dur['track'] == evt['track']) or (dur == all_events[-1]):
                            evt['duration'] = dur['time'] - evt['time']
                            if evt['duration'] <= 0:
                                evt['duration'] = 128
                            break
                if evt['type'] == 'time_signature':
                    for idx_dur, dur in enumerate(all_events[idx+1:]):
                        if dur['type'] == 'time_signature' or dur == all_events[-1]:
                            evt['duration'] = dur['time'] - evt['time']
                            break

            return all_events

        events = import_midi(file_path)

        # gues the hand based on the avarage pitch and track number.
        average_tracks = {}
        for t in range(16):
            average_pitch = []
            for evt in events:
                if evt['type'] == 'note_on' and evt['track'] == t:
                    average_pitch.append(evt['note'])
            average_pitch = statistics.mean(
                average_pitch) if average_pitch else None
            average_tracks[t] = average_pitch
        highest_track = max((k for k, v in average_tracks.items(
        ) if v is not None), key=lambda k: average_tracks[k], default=None)

        # add the events to the .pianoscript file
        for evt in events:
            if evt['type'] == 'note_on':
                hand = 'r' if highest_track == evt['track'] and not highest_track == None else 'l'
                pitch = max(1, min(88, evt['note'] - 20))
                new = SaveFileStructureSource.new_note(
                    tag=0,  # test if this couses no errors in the editor
                    pitch=pitch,
                    time=evt['time'],
                    duration=evt['duration'],
                    hand=hand,
                    staff=0,
                    track=evt['track'],
                )
                self.io['score']['events']['note'].append(new)

            elif evt['type'] == 'time_signature':
                measure_length = self.io['calc'].get_measure_length(evt)
                amount = int(evt['duration'] / measure_length)
                grid = []
                for numerator_count in range(evt['numerator']-1):
                    grid.append(measure_length /
                                evt['numerator'] * (numerator_count+1))
                new = SaveFileStructureSource.new_grid(
                    amount=amount,
                    numerator=evt['numerator'],
                    denominator=evt['denominator'],
                    grid=grid,
                )
                self.io['score']['events']['grid'].append(new)

        # if the midi contains no time signature we add it manualy
        if not self.io['score']['events']['grid']:
            measure_length = self.io['calc'].get_measure_length(
                {'numerator': 4, 'denominator': 4})
            new = SaveFileStructureSource.new_grid(
                amount=int(max(events, key=lambda evt: evt['time'])[
                           'time'] / measure_length) + 1,
                numerator=4,
                denominator=4,
                grid=[256, 512, 768]
            )
            self.io['score']['events']['grid'].append(new)

        # automatically insert linebreaks every 5 measures
        barline_ticks = self.io['calc'].get_barline_ticks()[5::5]
        barline_ticks = list(set(barline_ticks))
        try: barline_ticks.remove(0)
        except: ...
        new = SaveFileStructureSource.new_linebreak(
            tag='lockedlinebreak',
            time=0
        )
        self.io['score']['events']['linebreak'].append(new)
        for bl in barline_ticks:
            new = SaveFileStructureSource.new_linebreak(
                tag='linebreak' + str(self.io['calc'].add_and_return_tag()),
                time=bl
            )
            self.io['score']['events']['linebreak'].append(new)

        # add the imported midi message to the .pianoscript file
        self.io['score']['midi_data'] = events

        # renumber tags
        self.io['calc'].renumber_tags()

        # draw the editor
        self.io['maineditor'].redraw_editor()

        # reset the ctlz buffer
        self.io['ctlz'].reset_ctlz

    def export_midi(self, export=True, tempo=120):

        if export:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(parent=self.io['root'], 
                                                     caption='Save Midi File', 
                                                     dir='', 
                                                     filter='Midi Files (*.mid *.MID)')
        else:
            return
        
        if not file_path:
            return

        Score = copy.deepcopy(self.io['score'])

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
        MyMIDI = MIDIFile(numTracks=2,
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
        for note in Score['events']['note']: # NOTE: add gracenote
            time = int(note['time'] / 256 * ticks_per_quarternote)
            duration = int(note['duration'] / 256 * ticks_per_quarternote)
            MyMIDI.addNote(track=0 if note['hand'] == 'l' else 1, 
                            channel=0, 
                            pitch=int(note['pitch']+20), 
                            time=time, 
                            duration=duration, 
                            volume=80, 
                            annotation=None)
            
        for t in Score['events']['tempo']:
            t['time'] = int(t['time'] / 256 * ticks_per_quarternote)
            MyMIDI.addTempo(track=0, time=t['time'], tempo=t['tempo'])

        # saving the midi file
        with open(file_path, "wb") as output_file:
            MyMIDI.writeFile(output_file)

    def play_midi(self, tempo=80, trigger_inside_note=True, from_playhead=False):

        file_path = os.path.expanduser(path='~/.pianoscript/play.mid')
        # Check if the directory for the play.mid file exists
        dir = os.path.dirname(file_path)
        if not os.path.exists(path=dir):
            # If the directory doesn't exist, create it
            os.makedirs(name=dir)

        score = copy.deepcopy(self.io['score'])

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
        MyMIDI = MIDIFile(numTracks=2,
                            removeDuplicates=True,
                            deinterleave=False,
                            adjust_origin=False,
                            file_format=1,
                            ticks_per_quarternote=ticks_per_quarternote,
                            eventtime_is_ticks=True)

        for ts in score['events']['grid']:
            MyMIDI.addTimeSignature(track=0,
                                    time=0,
                                    numerator=int(ts['numerator']),
                                    denominator=denominator_dict[int(
                                        ts['denominator'])],
                                    clocks_per_tick=clocks_per_tick,
                                    notes_per_quarter=8)
        MyMIDI.addTempo(track=0, time=0, tempo=tempo)
        MyMIDI.addTrackName(track=0, time=0, trackName='PianoScript Play')
        
        # writing the notes and gracenotes
        for note in score['events']['note'] + score['events']['gracenote']:
            if not 'duration' in note:
                _, d = Midi.get_tsig_from_time(self.io, note['time'])
                duration = self.io['calc'].get_measure_length({'numerator': 1, 'denominator': d}) / d
                note['duration'] = duration
                
            if not from_playhead:
                # default midi export/normal
                time = int(note['time'] / 256 * ticks_per_quarternote)
                duration = int(note['duration'] / 256 * ticks_per_quarternote)
                MyMIDI.addNote(track=0 if note['hand'] == 'l' else 1, 
                                channel=0, 
                                pitch=int(note['pitch']+20), 
                                time=time, 
                                duration=duration, 
                                volume=80, 
                                annotation=None)
            else:
                # generate midi from the playhead position
                playhead = self.io['playhead']
                if note['time'] < playhead and note['time'] + note['duration'] > playhead and trigger_inside_note:
                    difference = playhead - note['time']
                    note['time'] = playhead
                    note['duration'] -= difference
                
                if not from_playhead:
                    playhead = 0

                if note['time'] >= playhead:
                    if from_playhead:
                        time = int((note['time'] - playhead) / 256 * ticks_per_quarternote)
                    else:
                        time = int(note['time'] / 256 * ticks_per_quarternote)
                    duration = int(note['duration'] / 256 * ticks_per_quarternote)
                    MyMIDI.addNote(track=0 if note['hand'] == 'l' else 1, 
                                    channel=0, 
                                    pitch=int(note['pitch']+20), 
                                    time=time, 
                                    duration=duration, 
                                    volume=80, 
                                    annotation=None)
        
        # writing tempo changes:
        for t in score['events']['tempo']:
            if not from_playhead:
                # default midi export/normal
                    t['time'] = int(t['time'] / 256 * ticks_per_quarternote)
                    MyMIDI.addTempo(track=0, time=t['time'], tempo=t['tempo'])
            else:
                # generate midi from the playhead position
                playhead = self.io['playhead']
                if t['time'] < playhead and trigger_inside_note:
                    t['time'] = playhead
                
                if not from_playhead:
                    playhead = 0

                if t['time'] >= playhead:
                    if from_playhead:
                        time = int((t['time'] - playhead) / 256 * ticks_per_quarternote)
                    else:
                        time = int(t['time'] / 256 * ticks_per_quarternote)
                    MyMIDI.addTempo(track=0, time=time, tempo=t['tempo'])

        # saving the midi file
        with open(file_path, "wb") as output_file:
            MyMIDI.writeFile(output_file)

    @staticmethod
    def get_tsig_from_time(io, time=0):
        
        grid = copy.deepcopy(io['score']['events']['grid'])

        # add time to time signature
        timer = 0
        for gr in grid:
            gr['time'] = timer
            m_length = io['calc'].get_measure_length(gr)
            timer += m_length * gr['amount']

        for idx, gr in enumerate(grid):
            try: 
                gr['duration'] = grid[idx+1]['time'] - gr['time']
            except IndexError: 
                gr['duration'] = grid[-1]['time'] + timer - gr['time']
        
        for gr in grid:
            if time >= gr['time'] and time < gr['duration']:
                return gr['numerator'], gr['denominator']

        return 0, 0
