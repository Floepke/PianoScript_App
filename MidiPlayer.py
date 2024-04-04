#! python3.12
# coding: utf-8`

""" pygame music player interface """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2024-2024 all rights reserved'  # noqa

from sys import argv
from sys import exit as _exit

from os.path import abspath

from main_class import MainClass


def main() -> int:
    """ main function """

    filename = None
    it_arg = iter(argv[1:])
    for arg in it_arg:
        match arg:
            case '-m':
                filename = abspath(next(it_arg, None))

    main_class = MainClass()

    if filename is not None:
        main_class.play(filename=filename)

    return main_class.run()


if __name__ == '__main__':
    _exit(main())