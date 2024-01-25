#! python3.11
# coding: utf8

""" editor for the line breaks """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from dataclasses import dataclass
# Ik denk een dialoogje wanneer je op de linebreak marker klikt met de linker
# muisknop waar de volgende eigenschapen in te stellen zijn:
# margin left(staff1-4),
# marginright(staff1-4),
# staff range toets x tot y(staff1-4)
#
# For Midi the range is from C2 (note #0) to G8 (note #127),
# middle C is note #60 (known as C3 in MIDI terminology).

from typing import Any
from typing import Optional

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QGroupBox

from PySide6.QtCore import QSize
# pylint: enable=no-name-in-module

from imports.editor.linebreakeditor.line_break import LineBreak


class LineBreakControl:
    """ controls for one linebreak """

    _note_names = ['C ', 'C#', 'D ', 'D#',
                   'E ', 'F ', 'F#', 'G ',
                   'G#', 'A ', 'A#', 'B ']

    # I won't split this up even more
    # pylint: disable=too-many-instance-attributes
    @dataclass
    class GuiData:
        """ storage for gui controls """

        def __init__(self):
            """ the GUI controls """

            self.margin_left: Optional[QSpinBox] = None
            self.margin_right: Optional[QSpinBox] = None

            self.staff_start: Optional[QSpinBox] = None
            self.start_label: Optional[QLabel] = None
            self.start_octave: Optional[QLabel] = None

            self.staff_finish: Optional[QSpinBox] = None
            self.finish_label: Optional[QLabel] = None
            self.finish_octave: Optional[QLabel] = None

    # pylint: enable=too-many-instance-attributes

    def __init__(self,
                 layout: QGridLayout,
                 row: int,
                 parent: Any,
                 has_label: bool = True):
        """ initialize the class """

        self._line_break = LineBreak(
            margin_left=10,
            margin_right=20,
            staff_start=0,
            staff_finish=127
        )

        # save a reference to the controls in this class
        self.gui_data = LineBreakControl.GuiData()

        group_margin, group_staff = self._create_group_boxes(parent=parent,
                                                             layout=layout,
                                                             row=row,
                                                             has_label=has_label)

        # --- MARGIN ---
        self._create_margin_left(parent=parent,
                                 group=group_margin)

        self._create_margin_right(parent=parent,
                                  group=group_margin)

        #  --- STAFF ---
        note_size = QSize(16, 16)

        self._create_staff_start(parent=parent,
                                 group_staff=group_staff,
                                 note_size=note_size)

        self._create_staff_finish(parent=parent,
                                  group_staff=group_staff,
                                  note_size=note_size)

        self._connect()

    @property
    def line_break(self) -> LineBreak:
        """ get the line break value """

        return self._line_break

    @line_break.setter
    def line_break(self, value: LineBreak):
        """ set the line break value """

        self._line_break = value
        self.gui_data.margin_left.setValue(value.margin_left)
        self.gui_data.margin_right.setValue(value.margin_right)
        self.gui_data.staff_start.setValue(value.staff_start)
        self.gui_data.staff_finish.setValue(value.staff_finish)

    @staticmethod
    def translate_note(midi_note: int) -> tuple:
        """ translate the number to a note name """

        octave, note = divmod(midi_note, 12)
        name = LineBreakControl._note_names[note]
        return name, octave - 2

    def _create_group_boxes(self,
                            parent: Any,
                            layout: QGridLayout,
                            row: int,
                            has_label: bool):
        """ create the group boxes for this dialog """

        label = 'Left           Right' if has_label else ''
        group_margin = QGroupBox(label, parent=parent)
        layout.addWidget(group_margin, row, 0, 1, 1)
        group_margin.setLayout(QGridLayout())

        label = 'Start                    Finish' if has_label else ''
        group_staff = QGroupBox(label, parent=parent)
        layout.addWidget(group_staff, row, 1, 1, 1)
        group_staff.setLayout(QGridLayout())

        return group_margin, group_staff

    def _create_margin_left(self,
                            parent: Any,
                            group: QGroupBox):
        """ the left margin control """

        margin_left = QSpinBox(parent=parent)
        margin_left.setMinimum(0)
        margin_left.setMaximum(1000)
        group.layout().addWidget(margin_left, 0, 0, 1, 1)

        self.gui_data.margin_left = margin_left

    def _create_margin_right(self,
                             parent: Any,
                             group: QGroupBox):
        """ the right margin control """

        margin_right = QSpinBox(parent=parent)
        margin_right.setMinimum(0)
        margin_right.setMaximum(1000)
        group.layout().addWidget(margin_right, 0, 1, 1, 1)

        self.gui_data.margin_right = margin_right

    def _create_staff_start(self,
                            parent: Any,
                            group_staff: QGroupBox,
                            note_size: QSize):
        """ create the start group """

        # default data
        start = self._line_break.staff_start
        name, octave = LineBreakControl.translate_note(start)

        #  --- START ---
        staff_start = QSpinBox(parent=parent)
        staff_start.setMinimum(0)  # C-1
        staff_start.setMaximum(127)  # G9
        staff_start.setValue(start)

        group_staff.layout().addWidget(staff_start, 0, 0, 1, 1)

        start_label = QLabel(parent=parent)
        start_label.setText(name)
        start_label.setMinimumSize(note_size)
        start_label.setMaximumSize(note_size)
        group_staff.layout().addWidget(start_label, 0, 1, 1, 1)

        start_octave = QLabel(parent=parent)
        start_octave.setText(str(octave))
        start_octave.setMinimumSize(note_size)
        start_octave.setMaximumSize(note_size)
        group_staff.layout().addWidget(start_octave, 0, 2, 1, 1)

        self.gui_data.staff_start = staff_start
        self.gui_data.start_label = start_label
        self.gui_data.start_octave = start_octave

    def _create_staff_finish(self,
                             parent: Any,
                             group_staff: QGroupBox,
                             note_size: QSize):
        """ create the finish group """

        # default data
        finish = self._line_break.staff_finish
        name, octave = LineBreakControl.translate_note(finish)

        # FINISH
        staff_finish = QSpinBox(parent=parent)
        staff_finish.setMinimum(0)  # C2
        staff_finish.setMaximum(127)  # G8
        staff_finish.setValue(finish)
        group_staff.layout().addWidget(staff_finish, 0, 3, 1, 1)

        finish_label = QLabel(parent=parent)
        finish_label.setText(name)
        finish_label.setMinimumSize(note_size)
        finish_label.setMaximumSize(note_size)
        group_staff.layout().addWidget(finish_label, 0, 4, 1, 1)

        finish_octave = QLabel(parent=parent)
        finish_octave.setText(str(octave))
        finish_octave.setMinimumSize(note_size)
        finish_octave.setMaximumSize(note_size)
        group_staff.layout().addWidget(finish_octave, 0, 5, 1, 1)

        self.gui_data.staff_finish = staff_finish
        self.gui_data.finish_label = finish_label
        self.gui_data.finish_octave = finish_octave

    def _connect(self):
        """ bypass too-many-statements """

        self.gui_data.margin_left.valueChanged.connect(self._margin_left_changed)
        self.gui_data.margin_right.valueChanged.connect(self._margin_right_changed)
        self.gui_data.staff_start.valueChanged.connect(self._staff_start_changed)
        self.gui_data.staff_finish.valueChanged.connect(self._staff_finish_changed)

    def _margin_left_changed(self, value: int):
        """ margin on the left changed """

        self._line_break.margin_left = value

    def _margin_right_changed(self, value: int):
        """ margin on the right changed """

        self._line_break.margin_right = value

    def _staff_start_changed(self, value: int):
        """ staff start changed """

        self._line_break.staff_start = value
        name, octave = LineBreakControl.translate_note(value)
        self.gui_data.start_label.setText(name)
        self.gui_data.start_octave.setText(str(octave))

    def _staff_finish_changed(self, value: int):
        """ staff start changed """

        self._line_break.staff_finish = int(value)
        name, octave = LineBreakControl.translate_note(value)
        self.gui_data.finish_label.setText(name)
        self.gui_data.finish_octave.setText(str(octave))
