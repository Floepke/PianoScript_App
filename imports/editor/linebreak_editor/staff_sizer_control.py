#! python3.11
# coding: utf8

""" editor for the staff sizer """

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

from typing import Any
from typing import List
from typing import Optional

from functools import partial

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QRadioButton
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QHBoxLayout

from PySide6.QtCore import QSize
# pylint: enable=no-name-in-module

from imports.editor.linebreak_editor.staff_sizer import StaffSizer
from imports.editor.linebreak_editor.pianonotes import PianoNotes
from imports.editor.linebreak_editor.keyboard_view import KeyboardView

class StaffSizerControl:
    """ controls for one linebreak """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    def  __init__(self,
                 layout: QHBoxLayout,
                 row: int,
                 column: int,
                 parent: Any,
                 keyboard: KeyboardView):
        """ initialize the class """

        self._staff_index = 0
        self._staff_sizers: [
            StaffSizer(margin_left=0,
                       margin_right=0,
                       staff_auto=True,
                       staff_start=4,
                       staff_finish=87)
        ]

        self._keyboard = keyboard

        self._radios, staff_group = self._create_radio(
            parent=parent,
            layout=layout,
            row=row,
            col=column)

        row = 1

        left_group = QGroupBox('Margin')
        left_group.setLayout(QGridLayout())
        staff_group.layout().addWidget(left_group,
                                       row,
                                       column,
                                       1,
                                       1)

        # --- MARGIN ---
        label_blank = QLabel()
        label_blank.setText(' ')
        label_blank.setMaximumHeight(18)
        left_group.layout().addWidget(label_blank,
                                      row,
                                      column,
                                      1,
                                      1)

        self._margin_left = self._create_margin_left(
            parent=parent,
            layout=left_group.layout(),
            row=row + 1,
            col=column)

        self._margin_right = self._create_margin_right(
            parent=parent,
            layout=left_group.layout(),
            row=row + 2,
            col=column)

        right_group = QGroupBox('Range')
        right_group.setLayout(QGridLayout())
        staff_group.layout().addWidget(right_group,
                                       row,
                                       column + 1,
                                       1,
                                       1)

        #  --- STAFF ---
        note_size = QSize(16, 16)
        self._staff_auto = self._create_staff_auto(
            parent=parent,
            layout=right_group.layout(),
            row=0,
            col=column)

        self._staff_start = self._create_staff_start(
            parent=parent,
            layout=right_group.layout(),
            note_size=note_size,
            row=1,
            col=column)

        self._staff_finish = self._create_staff_finish(
            parent=parent,
            layout=right_group.layout(),
            note_size=note_size,
            row=2,
            col=column)

        self._connect()

    @property
    def _staff_sizer(self) -> StaffSizer:
        """ get the staff sizer values """

        assert self._staff_sizers
        assert self._staff_index is not None
        return self._staff_sizers[self._staff_index]

    @_staff_sizer.setter
    def _staff_sizer(self, value: StaffSizer):
        """ set the staff sizer values """

        assert value is not None
        assert self._staff_index is not None
        self.staff_sizers[self._staff_index] = value

        self._margin_left.setValue(value.margin_left)
        self._margin_right.setValue(value.margin_right)

        self._staff_auto.setChecked(value.staff_auto)

        _, _, start = PianoNotes.translate_note(value.staff_start)
        self._staff_start.setCurrentText(start)

        _, _, finish = PianoNotes.translate_note(value.staff_finish)
        self._staff_finish.setCurrentText(finish)

        self._staff_start.setEnabled(not value.staff_auto)
        self._staff_finish.setEnabled(not value.staff_auto)

    @property
    def staff_sizers(self) -> List[StaffSizer]:  # noqa
        """ get all staff_sizers """

        return self._staff_sizers  # noqa

    @staff_sizers.setter
    def staff_sizers(self, value: List[StaffSizer]):  # noqa
        """ set all staff_sizers and activate 0"""

        self._staff_sizers = value  # noqa
        self._staff_sizer = value[self._staff_index]

    def _create_margin_left(self,
                            parent: Any,
                            layout: QGridLayout,
                            row: int,
                            col: int) -> QSpinBox:
        """ the left margin control """

        assert self
        label = QLabel()
        label.setText('Left')
        layout.addWidget(label, row, col, 1, 1)

        margin_left = QSpinBox(parent=parent)
        margin_left.setMinimum(0)
        margin_left.setMaximum(1000)
        margin_left.setMinimumWidth(50)
        margin_left.setMaximumWidth(50)
        layout.addWidget(margin_left, row, col + 1, 1, 1)
        return margin_left

    def _create_margin_right(self,
                             parent: Any,
                             layout: QGridLayout,
                             row: int,
                             col: int) -> QSpinBox:
        """ the right margin control """

        assert self
        label = QLabel()
        label.setText('Right')
        layout.addWidget(label, row, col, 1, 1)

        margin_right = QSpinBox(parent=parent)
        margin_right.setMinimumWidth(50)
        margin_right.setMaximumWidth(50)
        margin_right.setMinimum(0)
        margin_right.setMaximum(1000)
        layout.addWidget(margin_right, row, col + 1, 1, 1)
        return margin_right

    def _create_staff_auto(self,
                           parent: Any,
                           layout: QGridLayout,
                           row: int,
                           col: int) -> QCheckBox:
        """ checkbox for auto """

        assert self
        lbl_auto = QLabel()
        lbl_auto.setText('Auto')
        layout.addWidget(lbl_auto, row, col, 1, 1)

        check_auto = QCheckBox(parent=parent)
        check_size = QSize(32, 16)
        check_auto.setMinimumSize(check_size)
        check_auto.setMaximumSize(check_size)

        layout.addWidget(check_auto, row, col + 1, 1, 1)
        return check_auto

    def _create_staff_start(self, **kwargs) -> tuple:
        """ create the start group """

        assert self
        layout = kwargs.get('layout', Optional[QGridLayout])
        # note_size = kwargs.get('note_size', Optional[QSize])
        row = kwargs.get('row', 0)
        col = kwargs.get('col', 0)
        parent = kwargs.get('parent', None)

        lbl_start = QLabel()
        lbl_start.setText('Min')
        layout.addWidget(lbl_start, row, col, 1, 1)

        staff_start = QComboBox(parent=parent)
        staff_start.setEditable(False)
        staff_start.setMaximumWidth(50)
        staff_start.setMinimumWidth(50)

        for number in PianoNotes.start_notes():
            _, _, note = PianoNotes.translate_note(number)
            staff_start.addItem(note)
        layout.addWidget(staff_start, row, col + 1, 1, 1)
        return staff_start

    def _create_staff_finish(self, **kwargs) -> tuple:
        """ create the finish group """

        assert self
        layout = kwargs.get('layout', Optional[QGridLayout])
        # note_size = kwargs.get('note_size', Optional[QSize])
        row = kwargs.get('row', 0)
        col = kwargs.get('col', 0)
        parent = kwargs.get('parent', None)

        lbl_start = QLabel()
        lbl_start.setText('Max')
        layout.addWidget(lbl_start, row, col, 1, 1)

        # FINISH
        staff_finish = QComboBox(parent=parent)
        staff_finish.setEditable(False)
        staff_finish.setMaximumWidth(50)
        staff_finish.setMinimumWidth(50)

        for number in PianoNotes.finish_notes():
            _, _, note = PianoNotes.translate_note(number)
            staff_finish.addItem(note)
        layout.addWidget(staff_finish, row, col + 1, 1, 1)
        return staff_finish

    def _create_radio(self,
                      layout: QGridLayout,
                      parent: Any,
                      row: int,
                      col: int) -> tuple:
        """ the radio buttons for selecting the staff sizer """

        staff_group = QGroupBox('Staff')
        layout.addWidget(staff_group, 1)
        staff_group.setLayout(QGridLayout())

        radio_layout = QGridLayout()
        staff_group.layout().addLayout(radio_layout, 0, 0, 1, 4)

        lbl_meas_tick = QLabel('Measure:Tick')
        radio_layout.addWidget(lbl_meas_tick, 0, 0, 1, 2)
        lbl_measure = QLabel('')
        lbl_measure.setMinimumWidth(150)
        lbl_measure.setMaximumWidth(150)
        radio_layout.addWidget(lbl_measure, 0, 2, 1, 2)
        self.lbl_measure = lbl_measure

        inner_radio = QGridLayout()
        radio_layout.addLayout(inner_radio, 1, 0, 1, 4)

        radio_1 = QRadioButton('1', parent=parent)
        radio_1.setChecked(True)
        inner_radio.addWidget(radio_1, 0, 0, 1, 1)

        radio_2 = QRadioButton('2', parent=parent)
        radio_2.setChecked(False)
        inner_radio.addWidget(radio_2, 0, 1, 1, 1)

        radio_3 = QRadioButton('3', parent=parent)
        radio_3.setChecked(False)
        inner_radio.addWidget(radio_3, 0, 2, 1, 1)

        radio_4 = QRadioButton('4', parent=parent)
        radio_4.setChecked(False)
        inner_radio.addWidget(radio_4, 0, 3, 1, 1)

        return [radio_1, radio_2, radio_3, radio_4], staff_group

    def _connect(self):
        """ bypass too-many-statements """

        # save a reference to the controls in this class
        self._margin_left.valueChanged.connect(self._margin_left_changed)
        self._margin_right.valueChanged.connect(self._margin_right_changed)
        self._staff_auto.stateChanged.connect(self._staff_auto_changed)
        self._staff_start.currentIndexChanged.connect(self._staff_start_index_changed)
        self._staff_finish.currentIndexChanged.connect(self._staff_finish_index_changed)

        for idx, radio in enumerate(self._radios, 0):
            radio.clicked.connect(partial(self._radio_changed, idx))

    def set_measure_nr(self, measure: int, tick: int):
        """ the measure number for this linebreak """

        self.lbl_measure.setText(f'{measure}:{round(tick, 1)}')

    def _margin_left_changed(self, value: int):
        """ margin on the left changed """

        self._staff_sizer.margin_left = value

    def _margin_right_changed(self, value: int):
        """ margin on the right changed """

        self._staff_sizer.margin_right = value

    def _staff_auto_changed(self, state: int):
        """ auto checkbox changed """

        auto = state == 2
        self._staff_sizer.staff_auto = auto
        self._staff_start.setEnabled(not auto)
        self._staff_finish.setEnabled(not auto)

        start = self._staff_sizer.staff_start
        start = self._keyboard.valid_start(start)
        self._staff_sizer.staff_start = start
        self.handle_start(start)

        finish = self._staff_sizer.staff_finish
        finish = self._keyboard.valid_finish(finish)
        self._staff_sizer.staff_finish = finish
        self.handle_finish(finish)

    def _staff_start_index_changed(self, index: int):
        """ index of the staff_start has changed """

        assert index is not None
        value = self._staff_start.currentText()
        start = PianoNotes.revert_translation(value)
        self.handle_start(value=start)

    def handle_start(self, value: int):
        """ the value of start has changed """

        self._staff_sizer.staff_start = value
        index = self._staff_index
        self._staff_sizers[index] = self._staff_sizer

        auto = self._staff_sizer.staff_auto
        if auto:
            value = -1
        self._keyboard.start(value=value, auto=auto)

    def _staff_finish_index_changed(self, index: int):
        """ index of the staff_finish has changed """

        assert index is not None
        value = self._staff_finish.currentText()
        finish = PianoNotes.revert_translation(value)
        self.handle_finish(finish)

    def handle_finish(self, value):
        """ the value of the finish has changed """

        self._staff_sizer.staff_finish = value
        index = self._staff_index
        self._staff_sizers[index] = self._staff_sizer

        auto = self._staff_sizer.staff_auto
        if auto:
            value = -1
        self._keyboard.finish(value=value, auto=auto)

    def _radio_changed(self, idx: int):
        """ one of the radio buttons was changed """

        self._staff_index = idx
        self._staff_sizer = self._staff_sizers[idx]
        self.handle_start(self._staff_sizer.staff_start)
        self.handle_finish(self._staff_sizer.staff_finish)
