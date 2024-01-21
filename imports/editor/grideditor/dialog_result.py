#! python3.11
# coding: utf8

""" get and set mp3 tags """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from enum import Enum
from enum import auto


class DialogResult(Enum):
    """ enumeration for closing the window"""
    CLOSE_WINDOW = auto()
    OK = auto()
    CANCEL = auto()
    ESCAPE = auto()
    EXPIRED = auto()
    ENTER = auto()
    ALL = auto()
    NONE = auto()

    @classmethod
    def get(cls, value: str):
        """ translate the enum or string back to enum """
        dct = {}
        for key in DialogResult:
            dct[key] = key
            dct[str(key)] = key
            dct[key.name] = key
        return dct.get(value, None)
