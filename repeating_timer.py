#! python3.12
# coding: utf-8

""" repeating timer implementation """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2023-2023 all rights reserved'  # noqa

from threading import Timer


class RepeatTimer(Timer):
    """ the repeating timer implementation """
    def run(self):
        """
        :arg interval:  is a floating point value in seconds
        :arg function: the function that is called after each interval
        """
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
