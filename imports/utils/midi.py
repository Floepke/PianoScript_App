from imports.utils.constants import *
from PySide6.QtWidgets import QMessageBox, QFileDialog
import mido, os


class Midi:

    def __init__(self, io):
        
        self.io = io

    def leftorright(self, channel, name):

        dialog = QMessageBox()
        dialog.setWindowTitle('Which Hand?')
        dialog.setText(f'To which hand do you want to import?\nChannel: {channel}\nName: {name}')
        
        left_button = dialog.addButton('Left', QMessageBox.NoRole)
        right_button = dialog.addButton('Right', QMessageBox.YesRole)
        
        dialog.exec()
        
        if dialog.clickedButton() == left_button:
            return 'l'
        elif dialog.clickedButton() == right_button:
            return 'r'

    def load_midi(self):

        # if not self.io['fileoperations'].save_check():
        #     return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName()
        
        if file_path:

            # as starting point we load the source Blueprint/template and empty the neccessary fields
            self.io['score'] = SCORE_TEMPLATE
            self.io['score']['events']['grid'] = []

            # we set the midi import propery to true
            self.io['midi_import'] = True

            # set title to name of the midi file
            self.io['score']['header']['title']['text'] = os.path.splitext(os.path.basename(file_path))[0]

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
            
            # convert to pianoticks
            for msg in all_msg:

                msg['time'] = int(QUARTER_PIANOTICK / tpb * msg['time'])
                
                if msg['type'] in ['note_on', 'time_signature']:
                    msg['duration'] = int(QUARTER_PIANOTICK / tpb * msg['duration'])

            for i in all_msg:
                if i['type'] != 'note_off':
                    print(i)

            # ask user for choose hand for tracks
            ...

            # write time_signatures and notes:
            for i in all_msg:
                if i['type'] == 'time_signature':
                    msg = {
                        'tag':'grid',
                        'amount':int(i['duration'] / int(i['numerator'] * ((QUARTER_PIANOTICK * 4) / i['denominator']))),
                        'numerator':i['numerator'],
                        'denominator':i['denominator'],
                        'grid':[],
                        'visible':True
                    }

                    # calculate grid ticks
                    length = int(int(i['numerator'] * ((QUARTER_PIANOTICK * 4) / i['denominator'])) / i['numerator'])
                    for g in range(i['numerator']):
                        msg['grid'].append(length*(g+1))
                    
                    # add the message
                    self.io['score']['events']['grid'].append(msg)

                # write notes
                if i['type'] == 'note_on':

                    note = {'time': i['time'],
                            'duration': i['duration'],
                            'pitch': i['note'] - 20, 
                            'hand': i['hand'], 
                            'tag':'note',
                            'stem_visible':True,
                            'accidental':0,
                            'staff':0,
                            'notestop':True}
                    
                    self.io['score']['events']['note'].append(note)

            # renumber tags
            self.io['calc'].renumber_tags()

            # draw the editor
            self.io['maineditor'].update('loadfile')

            # reset the ctlz buffer
            self.io['ctlz'].reset_ctlz