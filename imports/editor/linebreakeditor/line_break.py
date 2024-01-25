#! python3.11
# coding: utf8

""" editor for the line breaks """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from typing import Dict

from dataclasses import dataclass

# Ik denk een dialoogje wanneer je op de linebreak marker klikt met de linker
# muisknop waar de volgende eigenschapen in te stellen zijn:
# margin left (staff1-4),
# margin right(staff1-4),
# staff range toets x tot y(staff1-4)

@dataclass
class LineBreak:
    """ controls for one linebreak """

    def __init__(self, **kwargs):
        """ initialize the class """

        self.margin_left = kwargs.get('margin_left', 0)
        self.margin_right = kwargs.get('margin_right', 0)
        self.staff_start = kwargs.get('staff_start', 0)
        self.staff_finish = kwargs.get('staff_finish', 0)

    def to_dict(self) -> Dict:
        """ convert to dictionary """

        return {'margin_left': self.margin_left,
                'margin_right': self.margin_right,
                'staff_start': self.staff_start,
                'staff_finish': self.staff_finish}
