#! python3.11
# coding: utf8

""" editor for the line breaks """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from typing import Dict
from typing import List

from dataclasses import dataclass


@dataclass
class StaffSizer:
    """ controls for one linebreak """

    def __init__(self, **kwargs):
        """ initialize the class """

        self.margin_left = kwargs.get('margin_left', 0)
        self.margin_right = kwargs.get('margin_right', 0)
        self.staff_start = kwargs.get('staff_start', 0)
        self.staff_finish = kwargs.get('staff_finish', 127)
        self.staff_auto = kwargs.get('staff_auto', True)

    @classmethod
    def import_sizer(cls, dct: Dict):
        """ import from the program """

        margin_left, margin_right = dct.get('margins', [0, 0])
        value = dct.get('range', None)

        if isinstance(value, List):
            staff_auto = False
            staff_start, staff_finish = tuple(value)
        else:
            staff_start = 0
            staff_finish = 88
            staff_auto = True

        return StaffSizer(margin_left=margin_left,
                          margin_right=margin_right,
                          staff_start=staff_start,
                          staff_finish=staff_finish,
                          staff_auto=staff_auto)

    def export_sizer(self) -> Dict:
        """ convert to dictionary """

        if self.staff_auto:
            staff_range = 'auto'
        else:
            staff_range = [self.staff_start, self.staff_finish]

        return {
            'margins': [self.margin_left, self.margin_right],
            'range': staff_range
        }
