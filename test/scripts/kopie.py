#! python3.11
# coding: utf8

""" Popup window implemented for PySide6 """

__copyright__ = '© Sihir 2024-2024 all rights reserved'

from sys import exit as _exit

from os import listdir

from os.path import abspath
from os.path import expanduser
from os.path import basename
from os.path import splitext
from os.path import join
from os.path import dirname

from shutil import copy as _copy


def this() -> str:
    """ py script name """

    return basename(__file__)

def here() -> str:
    """ py script folder """

def has_ext(filename: str, wanted: str) -> bool:
    """ true when the filename has the extension """

    _, ext = splitext(filename)
    return ext.casefold() == wanted.casefold()


def main() -> int:
    """ copy the scripts to the scripting folder """

    source = dirname(__file__)
    target = expanduser('~/.pianoscript/pianoscripts')  # noqa

    for file in listdir(source):
        if has_ext(file, '.py') and (file != this()):
            source_file = abspath(join(source, file))
            target_file = abspath(join(target, file))
            _copy(source_file, target_file)
            print(target_file)
    return 0


if __name__ == '__main__':
    _exit(main())
