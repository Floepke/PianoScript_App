from imports.utils.constants import *
from PySide6.QtWidgets import QMessageBox, QFileDialog
import mido, os, copy, threading
from midiutil.MidiFile import MIDIFile


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

    def load_midi(self):

        if not self.io['fileoperations'].save_check():
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self.io['root'], 'Open Midi File', '', 'Midi Files (*.mid *.MID)')

        if not file_path:
            return

        # as starting point we load the source Blueprint/template and empty the neccessary fields
        self.io['score'] = copy.deepcopy(SCORE_TEMPLATE)

        # we set the midi import propery to true
        self.io['midi_import'] = True

        # set title to name of the midi file
        self.io['score']['header']['title'] = os.path.splitext(
            os.path.basename(file_path))[0]

        # clear grid
        self.io['score']['events']['grid'] = []

        # Import the midi file and place the messages in dict
        mid = mido.MidiFile(file_path)

        tpb = mid.ticks_per_beat
        all_msg = []
        track = 0
        track_name = 'Nameless Track'
        track_hand = 'l'

        # loop for creating a list of all messages that include relative time, track number
        for tracks in mid.tracks:
            time = 0
            for msg in tracks:
                msg = msg.dict()

                # delta time to relative time
                msg['time'] += time
                time = msg['time']

                # track name
                if msg['type'] == 'track_name':
                    # asking user for input using pyside dialog
                    track_name = msg['name']
                    track_hand = self.leftorright(track, msg['name'])

                # en_of_track means we need to reset the time to zero
                if msg['type'] == 'end_of_track':
                    msg['track'] = track
                    all_msg.append(msg)
                    track += 1

                # note_off check
                if msg['type'] == 'note_on' and msg['velocity'] == 0:
                    msg['type'] = 'note_off'

                if msg['type'] == 'note_on':
                    msg['hand'] = track_hand

                if msg['type'] in ['note_on', 'note_off', 'set_tempo', 'time_signature']:
                    msg['track'] = track
                    msg['track_name'] = track_name

                    all_msg.append(msg)

        # calculate duration
        for idx, evt in enumerate(all_msg):
            if evt['type'] == 'note_on':
                for n in all_msg[idx+1:]:
                    if n['type'] == 'note_off' and evt['note'] == n['note'] and n['track'] == evt['track']:
                        evt['duration'] = n['time'] - evt['time']
                        break
            elif evt['type'] == 'time_signature':
                for idx2, t in enumerate(all_msg[idx+1:]):
                    if t['type'] == 'time_signature' or t == all_msg[-1]:
                        evt['duration'] = t['time'] - evt['time']
                        break

            # check if has property duration
            if 'duration' not in evt:
                evt['duration'] = all_msg[-1]['time'] - evt['time']

        # convert to pianoticks
        for msg in all_msg:

            msg['time'] = int(QUARTER_PIANOTICK / tpb * msg['time'])

            if msg['type'] in ['note_on', 'time_signature']:
                print(msg, msg['type'])
                msg['duration'] = int(
                    QUARTER_PIANOTICK / tpb * msg['duration'])

        # write time_signatures and notes:
        for i in all_msg:
            if i['type'] == 'time_signature':

                # create grid
                length = int(int(
                    i['numerator'] * ((QUARTER_PIANOTICK * 4) / i['denominator'])) / i['numerator'])
                msg = {
                    'tag': 'grid',
                    'amount': int(i['duration'] / length),
                    'numerator': i['numerator'],
                    'denominator': i['denominator'],
                    'grid': [],
                    'visible': True
                }

                # calculate grid ticks
                for g in range(i['numerator']):
                    msg['grid'].append(length * (g + 1))

                # add the message
                self.io['score']['events']['grid'].append(msg)

            # write notes
            elif i['type'] == 'note_on':

                note = {'time': i['time'],
                        'duration': i['duration'],
                        'pitch': i['note'] - 20,
                        'hand': i['hand'],
                        'tag': 'note',
                        'stem-visible': True,
                        'accidental': 0,
                        'staff': 0,
                        'notestop': True}

                self.io['score']['events']['note'].append(note)

        # renumber tags
        self.io['calc'].renumber_tags()

        # draw the editor
        self.io['maineditor'].redraw_editor()

        # reset the ctlz buffer
        self.io['ctlz'].reset_ctlz

    def export_midi(self, export=True):

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
                MyMIDI.addTempo(track=0, time=0, tempo=120)
                MyMIDI.addTrackName(track=0, time=0, trackName='Track 0')

            # adding the notes
            for note in Score['events']['note']:
                t = int(note['time']/256*ticks_per_quarternote)
                d = int(note['duration']/256*ticks_per_quarternote)
                c = 0
                if note['hand'] == 'r':
                    c = 1  # l or r?? first fix the midi import
                MyMIDI.addNote(track=0, channel=c, pitch=int(
                    note['pitch']+20), time=t, duration=d, volume=80, annotation=None)

            # saving the midi file
            with open(file_path, "wb") as output_file:
                MyMIDI.writeFile(output_file)

    def play_midi(self):
        self.export_midi(export=False)

        # Load the MIDI file
        mid = mido.MidiFile(os.path.expanduser('~/.pianoscript/play.mid'))

        # Get all output ports
        self.outports = [mido.open_output(name)
                         for name in mido.get_output_names()]

        # Set the playing flag to True
        self.playing = True

        # Play the MIDI file on all output ports
        def play():
            for msg in mid.play():
                # If the playing flag is False, stop playing
                if not self.playing:
                    break
                with self.lock:  # Acquire the lock before sending messages
                    for outport in self.outports:
                        outport.send(msg)

            # Close all output ports
            for outport in self.outports:
                outport.close()

        self.play_thread = threading.Thread(target=play)
        self.play_thread.start()

    def stop_midi(self):
        # Set the playing flag to False
        self.playing = False

        # Send an "All Sound Off" or "All Notes Off" message to each channel
        with self.lock:  # Acquire the lock before sending messages
            for outport in self.outports:
                for channel in range(16):  # MIDI channels are 0-15
                    all_sound_off = mido.Message(
                        'control_change', channel=channel, control=120, value=0)
                    all_notes_off = mido.Message(
                        'control_change', channel=channel, control=123, value=0)
                    outport.send(all_sound_off)
                    outport.send(all_notes_off)

        # Wait for the play thread to finish
        if self.play_thread is not None:
            self.play_thread.join()
