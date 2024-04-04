#! python3.12
# coding: utf-8`

""" pygame music player interface """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2024-2024 all rights reserved'  # noqa

from os.path import basename

from PySide6.QtWidgets import QApplication

from player_window import PlayerWindow

from player import Player


class MainClass:
    """ ... """

    def __init__(self):
        """ initialize the class """

        self.app = QApplication()
        self.wnd = PlayerWindow(closing=self.closing)
        self.player = Player(finished=self.finish, progress=self.progress)

    def play(self, filename: str):
        """ load and play the MIDI file """

        self.wnd.set_text(basename(filename))
        self.player.load(filename=filename)

    def progress(self, value: int):
        """ receive progress """

        self.wnd.set_progress(progress=value)

    def finish(self):
        """ music has finished """

        self.player.close()
        self.wnd.set_text('finished')
        self.wnd.set_progress(0.0)

    def closing(self):
        """ window is closing """

        self.player.close()

    def run(self) -> int:
        """ run the window """

        return self.app.exec()

