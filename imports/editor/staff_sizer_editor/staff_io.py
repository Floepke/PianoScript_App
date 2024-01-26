#! python3.11
# coding: utf8

""" editor for the staff sizers """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from typing import Dict
from typing import List

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer

class StaffIo:
    """ input output staff sizers """

    # this is received and should be returned
    # def new_linebreak(
    #         tag: str,  # linebreak+tagnumber to make tag unique
    #         time: float,  # in linear time in pianoticks 0 to infinity
    #         staff1_lr_margins: list = [10.0, 10.0],  # list with two values: (leftmargin, rightmargin) in mm
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
    def import_staffs(data: Dict):
        """ import tag, time and staff definitions """

        tag = data.get('tag', '')
        time = data.get('time', 0.0)
        staff1 = data.get('staff1', {})
        staff2 = data.get('staff2', {})
        staff3 = data.get('staff3', {})
        staff4 = data.get('staff4', {})

        result = [
            StaffSizer.import_sizer(dct=staff1),
            StaffSizer.import_sizer(dct=staff2),
            StaffSizer.import_sizer(dct=staff3),
            StaffSizer.import_sizer(dct=staff4),
        ]

        return result

    @staticmethod
    def export_staffs(staffs: List[StaffSizer]) -> Dict:
        """ import from the program """

        result = {
            'tag': '',
            'time': 0.0,
        }

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
