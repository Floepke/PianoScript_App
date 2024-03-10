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

from os import curdir
from os.path import dirname
from os.path import join
from os.path import abspath
from os.path import isfile

from sys import argv
from sys import exit as _exit

from jsons import loads

from copy import deepcopy

import pprint

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QApplication
# pylint: enable=no-name-in-module

from imports.editor.staff_sizer_editor.staff_sizer import StaffSizer
from imports.editor.staff_sizer_editor.staff_sizer_control import PianoNotes
from imports.editor.staff_sizer_editor.staff_sizer_dialog import StaffSizerDialog
from imports.editor.staff_sizer_editor.staff_io import StaffIo

from imports.editor.grideditor.dialog_result import DialogResult


def test_0():
    """ test for the translate_note function """
    for index in range(89):
        name = PianoNotes.translate_note(piano_note=index)
        print(f'{index:<3} {name}')

    start_notes = [
        3, 8,
        15, 20,
        27, 32,
        39, 44,
        51, 56,
        63, 68,
        75
    ]
    print('--- start notes --')
    for index in start_notes:
        _, _, note = PianoNotes.translate_note(piano_note=index)
        print(f'{index:<3} {note}')

    finish_notes = [
        19, 26,
        31, 38,
        43, 50,
        55, 62,
        67, 74,
        79, 86
    ]
    print('--- finish notes --')
    for index in finish_notes:
        _, _, note = PianoNotes.translate_note(piano_note=index)
        print(f'{index:<3} {note}')

def find_file(fname: str) -> str:
    """ find a file somewhere in the folders """

    current = abspath(curdir)
    while len(current) > 4:  # as in 'C:\\x'
        result = join(current, fname)
        if isfile(result):
            return result
        current = dirname(current)

    return None

def time_calc(time: int) -> int:
    """ simplified version of the actual function """

    result = 1 + int(time / 768)
    print(f'{time:0>5} {result:0>3}')
    return result


def test_1():
    """ test the dialog with four line breaks """

    filename = find_file('example.json')
    assert filename
    with open(file=filename, mode='r', encoding='utf8') as stream:
        linebreaks = loads(stream.read())

    app = QApplication(argv)

    dialog = StaffSizerDialog(callback=test1_callback,
                              linebreaks=linebreaks,
                              time_calc=time_calc)

    layout = QGridLayout()
    layout.addWidget(dialog, 0, 0, 1, 1)

    dialog.show()

    _exit(app.exec())

def test1_callback(result: DialogResult,
                   staffs: list):
    """ callback for results  """

    print(f'{result}')

    ppr = pprint.PrettyPrinter(indent=4)

    output = ppr.pformat(staffs)
    print(output)


def test_2():
    """ test 3"""

    data = {
        'tag': 'sizer123',
        'time': 12345,
        'staff1': {
            'margins': [10, 12],
            'range': [3, 79]
        },
        'staff2': {
            'margins': [11, 13],
            'range': [8, 80]
        },
        'staff3': {
            'margins': [12, 14],
            'range': [15, 81]
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
