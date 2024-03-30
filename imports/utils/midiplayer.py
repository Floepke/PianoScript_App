import mido
import threading
import os
import time
from PySide6.QtWidgets import QInputDialog
from PySide6.QtGui import QShortcut, QKeySequence

class MidiPlayer:
    def __init__(self, io):
        self.path = os.path.expanduser('~/.pianoscript/play.mid')
        self.thread = None
        self.stop = threading.Event()
        self.from_playhead = False
        self.ready2play = True

        # connect the play and stop buttons
        self.io = io
        self.io['gui'].toolbar.play_button.clicked.connect(self.play_midi)
        self.io['gui'].toolbar.stop_button.clicked.connect(self.stop_midi)
        self.io['gui'].set_midi_out_port_action.triggered.connect(lambda: self.set_midi_port(set=True))
        prev_page_shortcut = QShortcut(QKeySequence("Space"), self.io['root'])
        prev_page_shortcut.activated.connect(self.player_switch)

    def play_midi(self, from_playhead=False):
        if self.thread is not None and self.thread.is_alive():
            self.stop_midi()
            if self.thread is not None:
                self.thread.join()

        self.set_midi_port()

        self.from_playhead = from_playhead

        self.thread = threading.Thread(target=self._play_midi_thread)
        self.thread.start()

    def stop_midi(self):
        self._send_panic()  # send the panic message immediately
        self.stop.set()
        if self.thread is not None:
            self.thread.join()
        self.stop.clear()
    
    def _play_midi_thread(self):
        self.io['midi'].play_midi(from_playhead=self.from_playhead)
        mid = mido.MidiFile(self.path)
        outport = mido.open_output(self.io['settings']['midi_port'])
        for msg in mid:
            if self.stop.wait(msg.time):  # non-blocking sleep
                self._send_panic()
                break
            if not msg.is_meta and not msg.type == 'sysex':
                    outport.send(msg)
        self.ready2play = True

    def _send_panic(self):
        with mido.open_output(self.io['settings']['midi_port']) as output:
            for channel in range(2):
                for note in range(20, 108):
                    off_msg = mido.Message('note_off', note=note, velocity=0, channel=channel)
                    output.send(off_msg)

    def set_midi_port(self, set=False):
        midi_port = self.io['settings']['midi_port'] if not set else None
        available_ports = mido.get_output_names()

        if midi_port is None or midi_port not in available_ports:
            # If the specified port is not available, prompt the user to select a port
            midi_port, ok = QInputDialog.getItem(self.io['root'], "Select MIDI Port", "Available MIDI Ports:", available_ports, 0, False)
            if ok and midi_port:
                self.io['settings']['midi_port'] = midi_port
            else:
                # If the user cancels the dialog or doesn't select a port, raise an exception
                raise Exception("No MIDI port selected")

        # Set the MIDI port
        self.midi_port = midi_port

    def player_switch(self):

        if self.ready2play:
            self.play_midi(from_playhead=True)
            self.ready2play = False
        else:
            self.ready2play = True
            self.stop_midi()

