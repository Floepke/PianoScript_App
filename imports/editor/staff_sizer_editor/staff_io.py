#! python3.11
# coding: utf8

""" editor for the staff sizers """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from typing import Dict
from typing import List
from typing import Optional
from typing import Callable
from typing import cast

from dataclasses import dataclass

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer
from imports.editor.staff_sizer_editor.my_exception import MyException


class StaffIo:
    """ input output staff sizers """

    # this is received and should be returned
    # def new_linebreak(
    #         tag: str,  # linebreak+tagnumber to make tag unique
    #         time: float,  # in linear time in pianoticks 0 to infinity
    #         staff1_lr_margins: list = [10.0, 10.0],  # two values: [left, right] in mm
    #         staff2_lr_margins: list = [10.0, 10.0],  # ...
    #         staff3_lr_margins: list = [10.0, 10.0],
    #         staff4_lr_margins: list = [10.0, 10.0],
    #         staff1_range: list or str = 'auto',
    #         # list with two values: (lowestnote, highestnote) or string 'auto'
    #         staff2_range: list or str = 'auto',  # ...
    #         staff3_range: list or str = 'auto',
    #         staff4_range: list or str = 'auto'
    # ):
    #     '''The linebreak event structure.'''
    #     return {
    #         'tag': tag,
    #         'time': time,
    #         'staff1': {
    #             'margins': staff1_lr_margins,
    #             'range': staff1_range
    #         },
    #         'staff2': {
    #             'margins': staff2_lr_margins,
    #             'range': staff2_range
    #         },
    #         'staff3': {
    #             'margins': staff3_lr_margins,
    #             'range': staff3_range
    #         },
    #         'staff4': {
    #             'margins': staff4_lr_margins,
    #             'range': staff4_range
    #         }
    #     }

    @staticmethod
    def export_staffs(staffs: List[StaffSizer]) -> Dict:
        """ import from the program """

        result = {}
        if staffs:
            result['tag'] = ''
            result['time'] = 0.0

        for idx, staff in enumerate(staffs, 1):

            staff_margin = [staff.margin_left, staff.margin_right]
            if staff.staff_auto:
                staff_range = 'auto'
            else:
                staff_range = [staff.staff_start, staff.staff_finish]
            result[f'staff{idx}'] = {
                'margin': staff_margin,
                'range': staff_range
            }

        return result


@dataclass
class LineBreak:
    """ the linebreak contains four staff_sizers and a timestamp """

    def __init__(self, **kwargs):
        """ initialize the class """

        self.tag = kwargs.get('tag', None)
        self.time = kwargs.get('time', 0)
        self.measure_nr = kwargs.get('measure_nr', 0)
        self.staffs = kwargs.get('staffs', cast(Optional[List], None))


class LineBreakImport:
    """ importing line breaks """

    @staticmethod
    def importer(data: list, time_calc: Callable) -> List[LineBreak]:
        """ initialize all line breaks """

        result = []
        for brk_data in data:
            staff1 = brk_data.get('staff1', None)
            staff2 = brk_data.get('staff2', None)
            staff3 = brk_data.get('staff3', None)
            staff4 = brk_data.get('staff4', None)
            staffs = [
                StaffSizer.import_sizer(dct=staff1),
                StaffSizer.import_sizer(dct=staff2),
                StaffSizer.import_sizer(dct=staff3),
                StaffSizer.import_sizer(dct=staff4),
            ]

            tag = brk_data.get('tag', '')
            time = brk_data.get('time', 0.0)
            measure_nr = time_calc(time)
            brk = LineBreak( tag=tag,
                             time=time,
                             measure_nr=measure_nr,
                             staffs=staffs)
            result.append(brk)

        result.sort(key=lambda elem: elem.measure_nr, reverse=False)
        return result

