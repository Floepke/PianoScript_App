#! python3.11
# coding: utf8

""" editor for the line breaks """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

# Ik denk een dialoogje wanneer je op de linebreak marker klikt met de linker
# muisknop waar de volgende eigenschapen in te stellen zijn:
# margin left(staff1-4),
# marginright(staff1-4),
# staff range toets x tot y(staff1-4)
#
# For Midi the range is from C2 (note #0) to G8 (note #127),
# middle C is note #60 (known as C3 in MIDI terminology).

from sys import argv
from sys import exit as _exit

from copy import deepcopy

import pprint

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QApplication
# pylint: enable=no-name-in-module

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer
from imports.editor.staff_sizer_editor.staff_sizer_control import StaffSizerControl
from imports.editor.staff_sizer_editor.staff_sizer_dialog import StaffSizerDialog
from imports.editor.staff_sizer_editor.staff_io import StaffIo

from imports.editor.grideditor.dialog_result import DialogResult


def test_0():
    """ test for the translate_note function """
    for index in range(128):
        name = StaffSizerControl.translate_note(midi_note=index)
        print(f'{index:<3} {name}')


def test_1():
    """ test the dialog with four line breaks """

    app = QApplication(argv)
    lbrk = StaffSizerDialog(callback=test1_callback)

    sizer = StaffSizer(margin_left=10,
                       margin_right=12,
                       staff_start=48,
                       staff_finish=79,
                       staff_auto=False)

    sizers = [deepcopy(sizer),
              deepcopy(sizer),
              deepcopy(sizer),
              deepcopy(sizer)]

    sizers[0].margin_left = 10
    sizers[1].margin_left = 20
    sizers[2].margin_left = 30
    sizers[3].margin_left = 40
    sizers[3].staff_auto = True

    lbrk.staff_sizers = sizers
    layout = QGridLayout()
    layout.addWidget(lbrk, 0, 0, 1, 1)
    lbrk.show()

    _exit(app.exec())


def test1_callback(result: DialogResult,
                   staffs: [StaffSizer]):
    """ callback for results  """

    print(f'{result}')
    output = StaffIo.export_staffs(staffs=staffs)

    ppr = pprint.PrettyPrinter(indent=4)
    ppr.pprint(output)


def test_2():
    """ test 3"""

    data = {
        'tag': 'sizer123',
        'time': 12345,
        'staff1': {
            'margins': [10, 12],
            'range': [48, 79]
        },
        'staff2': {
            'margins': [11, 13],
            'range': [49, 80]
        },
        'staff3': {
            'margins': [12, 14],
            'range': [50, 81]
        },
        'staff4': {
            'margins': [13, 15],
            'range': 'auto'
        }
    }

    input = StaffIo.import_staffs(data=data)
    output = StaffIo.export_staffs(staffs=input)

    ppr = pprint.PrettyPrinter(indent=4)

    print('input:')
    for item in input:
        ppr.pprint(item.__dict__)

    print('output:')
    ppr.pprint(output)


def main() -> int:
    """ main test function """

    if len(argv) < 2:
        test_0()
        return 0

    for arg in argv[1:]:
        match int(arg):
            case 0:
                test_0()
            case 1:
                test_1()
            case 2:
                test_2()

    return 0


if __name__ == '__main__':
    _exit(main())
