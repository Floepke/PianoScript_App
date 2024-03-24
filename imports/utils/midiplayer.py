import mido
import threading
import os
import time
from PySide6.QtWidgets import QInputDialog

class MidiPlayer:
    def __init__(self, io):
        self.path = os.path.expanduser('~/.pianoscript/play.mid')
        self.thread = None
        self.stop = threading.Event()

        # connect the play and stop buttons
        self.io = io
        self.io['gui'].toolbar.play_button.clicked.connect(self.play_midi)
        self.io['gui'].toolbar.stop_button.clicked.connect(self.stop_midi)

    def play_midi(self):
        if self.thread is not None and self.thread.is_alive():
            return  # skip starting a new thread if the previous one is still running

        self.set_midi_port()  # set the MIDI port

        self.thread = threading.Thread(target=self._play_midi_thread)
        self.thread.start()

    def _play_midi_thread(self):
        self.io['midi'].export_midi(export=False, tempo=120)
        mid = mido.MidiFile(self.path)
        for msg in mid:
            if self.stop.wait(msg.time):  # non-blocking sleep
                self._send_panic()
                break
            if not msg.is_meta and not msg.type == 'sysex':
                with mido.open_output(self.io['settings']['midi_port']) as output:
                    output.send(msg)

    def stop_midi(self):
        self._send_panic()  # send the panic message immediately
        self.stop.set()
        if self.thread is not None:
            self.thread.join()
        self.stop.clear()

    def _send_panic(self):
        for port in mido.get_output_names():
            with mido.open_output(port) as output:
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

