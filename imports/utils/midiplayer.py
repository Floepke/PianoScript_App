import mido
import threading
import os

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
        self.thread = threading.Thread(target=self._play_midi_thread)
        self.thread.start()

    def _play_midi_thread(self):
        self.io['midi'].export_midi(export=False, tempo=120)
        mid = mido.MidiFile(self.path)
        for msg in mid.play():
            if self.stop.is_set():
                self._send_panic()
                break
            for port in mido.get_output_names():
                with mido.open_output(port) as output:
                    output.send(msg)

    def stop_midi(self):
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

