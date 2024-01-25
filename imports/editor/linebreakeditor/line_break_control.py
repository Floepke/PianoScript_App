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

from typing import Optional
from typing import Any

from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QGroupBox

from PySide6.QtCore import QSize

from imports.editor.linebreakeditor.line_break import LineBreak


class LineBreakControl:
    """ controls for one linebreak """

    _note_names = ['C ', 'C#', 'D ', 'D#', 'E ', 'F ', 'F#', 'G ', 'G#', 'A ', 'A#', 'B ']

    def __init__(self,
                 layout: QGridLayout,
                 row: int,
                 span: int,
                 parent: Any):
        """ initialize the class """

        self._line_break = LineBreak(left_margin=0,
                                     right_margin=0,
                                     staff_start=0,
                                     staff_finish=127)

        # --- MARGIN ---
        group_margin = QGroupBox('Left           Right', parent=parent)
        layout.addWidget(group_margin, row, 0, 1, 1)
        group_margin.setLayout(QGridLayout())

        self.margin_left = margin_left = QSpinBox(parent=parent)
        margin_left.setMinimum(0)
        margin_left.setMaximum(1000)
        group_margin.layout().addWidget(margin_left, 0, 0, 1, 1)

        self.margin_right = margin_right = QSpinBox(parent=parent)
        margin_right.setMinimum(0)
        margin_right.setMaximum(1000)
        group_margin.layout().addWidget(margin_right, 0, 1, 1, 1)

        #  --- STAFF ---
        group_staff = QGroupBox('Start                    Finish', parent=parent)
        layout.addWidget(group_staff, row, 1, 1, 1)
        group_staff.setLayout(QGridLayout())

        #  --- START ---
        self.staff_start = staff_start = QSpinBox(parent=parent)
        staff_start.setMinimum(0)  # C-1
        staff_start.setMaximum(127)  # G9
        group_staff.layout().addWidget(staff_start, 0, 0, 1, 1)

        self.start_label = label4 = QLabel(parent=parent)
        name, octave = LineBreakControl.translate_note(0)
        label4.setText(name)
        note_size = QSize(12, 16)
        label4.setMinimumSize(note_size)
        label4.setMaximumSize(note_size)
        group_staff.layout().addWidget(label4, 0, 1, 1, 1)

        self.start_octave = label5 = QLabel(parent=parent)
        label5.setText(str(octave))
        label5.setMinimumSize(note_size)
        label5.setMaximumSize(note_size)
        group_staff.layout().addWidget(label5, 0, 2, 1, 1)

        self.staff_finish = staff_finish = QSpinBox(parent=parent)
        staff_finish.setMinimum(0)  # C2
        staff_finish.setMaximum(127)  # G8
        staff_finish.setValue(127)
        group_staff.layout().addWidget(staff_finish, 0, 3, 1, 1)

        name, octave = LineBreakControl.translate_note(127)
        self.finish_label = label7 = QLabel(parent=parent)
        label7.setText(name)
        label7.setMinimumSize(note_size)
        label7.setMaximumSize(note_size)
        group_staff.layout().addWidget(label7, 0, 4, 1, 1)

        self.finish_octave = label8 = QLabel(parent=parent)
        label8.setText(str(octave))
        label8.setMinimumSize(note_size)
        label8.setMaximumSize(note_size)
        group_staff.layout().addWidget(label8, 0, 7, 1, 1)

        margin_left.valueChanged.connect(self._margin_left_changed)
        margin_right.valueChanged.connect(self._margin_right_changed)
        staff_start.valueChanged.connect(self._staff_start_changed)
        staff_finish.valueChanged.connect(self._staff_finish_changed)

    @property
    def line_break(self) -> LineBreak:
        """ get the line break value """

        return self._line_break

    @line_break.setter
    def line_break(self, value: LineBreak):
        """ set the line break value """

        self._line_break = value
        self.margin_left.setValue(value.margin_left)
        self.margin_right.setValue(value.margin_right)
        self.staff_start.setValue(value.staff_start)
        self.staff_finish.setValue(value.staff_finish)

    @staticmethod
    def translate_note(midi_note: int) -> tuple:
        """ translate the number to a note name """

        octave, note = divmod(midi_note, 12)
        name = LineBreakControl._note_names[note]
        return name, octave - 2

    def _margin_left_changed(self, value: float):
        """ margin on the left changed """

        self._line_break.left_margin = int(value)

    def _margin_right_changed(self, value: float):
        """ margin on the right changed """

        self._line_break.right_margin = int(value)

    def _staff_start_changed(self, value: int):
        """ staff start changed """

        self._line_break.staff_start = value
        name, octave = LineBreakControl.translate_note(value)
        self.start_label.setText(name)
        self.start_octave.setText(str(octave))

    def _staff_finish_changed(self, value: int):
        """ staff start changed """

        self._line_break.staff_finish = int(value)
        name, octave = LineBreakControl.translate_note(value)
        self.finish_label.setText(name)
        self.finish_octave.setText(str(octave))
