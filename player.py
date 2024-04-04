#! python3.12
# coding: utf-8`

""" music player interface """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2024-2024 all rights reserved'  # noqa

from typing import Callable

from pymixer import PyMixer

from repeating_timer import RepeatTimer


class Player:
    """ a simple player for MIDI """

    def __init__(self, finished: Callable, progress: Callable):
        """ initialize the class """

        self.filename = None
        self.progress = progress
        self.player = PyMixer(finished=finished)
        self.timer = RepeatTimer(interval=1.0, function=self.update)
        self.timer.start()

    def load(self, filename: str):
        """ load a MIDI file """

        self.filename = filename
        duration = self.duration(filename=filename)
        self.player.load(track=filename, duration=duration, progress=0)

    def play(self):
        """ play the loaded MIDI file """

        self.player.play()

    @property
    def busy(self) -> int:
        """ done when busy == 0 """

        return self.player.busy

    def pause(self):
        """ pause the player """

        self.player.pause()

    def unpause(self):
        """ resume playing """

        self.player.unpause()

    def update(self):
        """ ... """

        if self.progress:
            self.progress(self.player.get_progress())

    @staticmethod
    def duration(filename: str) -> int:
        """ get the length of the file in seconds """

        # to do: get the duration of the MIDI file in seconds
        seconds = 0
        return seconds

    def close(self):
        """ stop the timer """

        self.timer.cancel()
