#! python3.11
# coding: utf-8

""" grid data proposal """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2023-2023 all rights reserved'  # noqa

# "grid":[
#       {
#         "start": 1,
#         "amount":8,
#         "numerator":4,
#         "denominator":4,
#         "grid":4, ?
#         "visible":true
#        }
# ],

from typing import List

from jsons import dumps
from jsons import loads

from imports.editor.grideditor.grid import Grid


class GridIo:
    """ read and write the GridList """

    @staticmethod
    def write(glist: List[Grid], filename: str):
        """ write to file """
        with open(file=filename, mode='w', encoding='utf-8') as stream:
            stream.write(dumps(glist))

    @staticmethod
    def read(filename: str) -> List[Grid]:
        """ read from file """

        with open(file=filename, mode='r', encoding='utf-8') as stream:
            lst = loads(stream.read())

        return [Grid(**item) for item in lst]
