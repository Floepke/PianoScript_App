#! python3.11
# coding: utf-8

""" grid data proposal """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2023-2024 all rights reserved'  # noqa

# "grid":[
#       {
#         "amount":8,
#         "numerator":5,
#         "denominator":4,
#         "grid":4,
#         "hidden": [2, 4],
#         "visible":true
#        }
#
# result:
#        1 =======    (bar)
#        2 -
#        3 -------
#        4 -
#        5 -------
#        1 =======    (bar)
# ],

from typing import Dict

from dataclasses import dataclass


# pylint: disable=too-many-instance-attributes
@dataclass
class Grid:
    """ measure definition """

    def __init__(self, **kwargs):
        """ initialize the class """

        self.nr: int = int(kwargs.get('nr', -1))
        self.start: int = int(kwargs.get('start', 1))
        self.amount: int = int(kwargs.get('amount', 1))
        self.numerator: int = int(kwargs.get('numerator', 4))
        self.denominator: int = int(kwargs.get('denominator', 4))
        self.grid: [int] = kwargs.get('grid', [])
        self.option: str = kwargs.get('option', '')
        self.visible: bool = bool(kwargs.get('visible', True))

    def to_dict(self) -> dict:
        """ convert back to dictionary """

        return {
            'nr': self.nr,
            'tag': f'grid{self.nr - 1}',
            'start': self.start,
            'amount': self.amount,
            'numerator': self.numerator,
            'denominator': self.denominator,
            'option': self.option,
            'grid': self.grid,
            'visible': self.visible
        }

    def __eq__(self, other):
        return self.nr == other.nr

    @staticmethod
    def base(denominator: int) -> int:
        """ base scales note length """

        dct = {
            1: 1024,
            2: 512,
            4: 256,
            8: 64,
            16: 32,
            32: 16,
            64: 8,
            128: 1
        }
        return dct.get(denominator, 1)
