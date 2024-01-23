#! python3.11
# coding: utf8

""" the Grid Editor dialog """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

from typing import Optional
from typing import Any
from typing import List
from typing import Dict

from copy import deepcopy

from dataclasses import dataclass

from collections import namedtuple

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QSpinBox
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QToolBar
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton

from PySide6.QtGui import QIcon
from PySide6.QtGui import QAction

from PySide6.QtCore import QSize
from PySide6.QtCore import QModelIndex
from PySide6.QtCore import Qt
# pylint: enable=no-name-in-module

from imports.editor.grideditor.dialog_result import DialogResult

from imports.editor.grideditor.grid import Grid

from imports.editor.grideditor.grid_treeview import GridTreeView

from imports.editor.grideditor.measure_view import MeasureView

from imports.editor.grideditor.lines_view import LinesView

from imports.editor.grideditor.popup import Popup


@dataclass
class GridControls:
    """ the controls used in the dialog """

    def __init__(self):
        """ initialize the class """

        self.selected_lbl: Optional[QLabel] = None
        self.spin_start: Optional[QSpinBox] = None
        self.check_visible: Optional[QCheckBox] = None
        self.spin_amount: Optional[QSpinBox] = None
        self.spin_numerator: Optional[QSpinBox] = None
        self.combo_denominator: Optional[QComboBox] = None
        self.note_lbl: Optional[QLabel] = None


class GridDialog(QDialog):
    """ the Grid editor dialog """

    def __init__(self,
                 parent,
                 grid_dct: [Grid]):
        """ initialize the class """

        super().__init__(parent)

        self.setMinimumSize(610, 410)
        self.setMaximumSize(610, 410)

        # grid.grid has changed from a number to the array of count lines
        # a way around this for the moment
        # it will be fixed in the next iteration

        self.grids = []
        for idx, dct in enumerate(deepcopy(grid_dct), 1):
            dct['nr'] = idx
            self.grids.append(Grid(**dct))

        self.nr = 0

        self.controls = GridControls()
        self.setWindowTitle('Grid definitions')
        self.check_visible: Optional[QCheckBox] = None
        self.spin_amount: Optional[QSpinBox] = None
        self.spin_numerator: Optional[QSpinBox] = None
        self.combo_denominator: Optional[QComboBox] = None
        self.tree_view: Optional[GridTreeView] = None
        self.measure_view: Optional[MeasureView] = None
        self.line_view: Optional[LinesView] = None
        self.grid: Optional[List[int]] = None

        dialog_layout = QGridLayout()

        edt_box = self.editbox()
        dialog_layout.addWidget(edt_box, 0, 0)

        self.setLayout(dialog_layout)

        dialog_icon = QIcon('icons/GridEditor.png')
        self.setWindowIcon(dialog_icon)
        self.close_callback = None

        # pylint: disable=invalid-name
        self.closeEvent = self.dialog_closes
        # pylint: enable=invalid-name

        self.dialog_result = DialogResult.CLOSE_WINDOW

        current = self.grids[self.nr]
        self.nr = current.nr
        self.start = current.start
        self.popup = None

        # when mute is True, no data should be updated
        self.mute = False

    @property
    def cur_grid(self) -> Grid:
        """ returns the current grid """

        value = Grid(
            nr=self.nr,
            start=self.start,
            visible=self.visible,
            amount=self.amount,
            numerator=self.numerator,
            grid=self.grid,
            denominator=self.denominator)
        return value

    @cur_grid.setter
    def cur_grid(self, value: Grid) -> None:
        """ set the current grid """

        self.mute = True
        self.nr = value.nr
        self.start = value.start
        self.selected = f'grid {value.nr}'
        self.visible = value.visible
        self.amount = value.amount
        self.numerator = value.numerator
        self.denominator = value.denominator
        self.grid = value.grid
        self.mute = False

    def update_measure_view(self):
        """ updates the measure view """

        self.measure_view.draw_measure(visible=self.cur_grid.visible,
                                       numerator=self.cur_grid.numerator,
                                       hidden=[])

    def editbox(self) -> QGroupBox:
        """ the grid editor box """

        edit_box = QGroupBox()
        edit_box.setMaximumSize(QSize(600, 400))
        edit_box.setMinimumSize(QSize(600, 400))

        edit_layout = QGridLayout()

        self.tree_view = GridTreeView(box=edit_box,
                                      layout=edit_layout,
                                      row=0,
                                      col=0,
                                      span=5,
                                      on_selection_changed=self._on_selection_changed)

        self._populate()

        self._lines_view(box=edit_box,
                         layout=edit_layout,
                         row=0,
                         col=5)

        self._lines_func(box=edit_box,
                         layout=edit_layout,
                         row=1,
                         col=5,
                         rowspan=1,
                         colspan=3)

        self.create_measure_view(box=edit_box,
                                 layout=edit_layout,
                                 row=0,
                                 column=6)

        self._create_toolbar(box=edit_box,
                             layout=edit_layout,
                             row=1)

        self._create_selected(box=edit_box,
                              layout=edit_layout,
                              row=2)

        self._create_start(box=edit_box,
                           layout=edit_layout,
                           row=3)

        self._create_amount(box=edit_box,
                            layout=edit_layout,
                            row=4)

        self._create_signature(box=edit_box,
                               layout=edit_layout,
                               row=5)

        self._yorn_box(box=edit_box,
                       layout=edit_layout,
                       col=5,
                       row=5,
                       colspan=3)

        # Set the column stretch for the three columns
        edit_layout.setColumnStretch(0, 0.25)
        edit_layout.setColumnStretch(1, 0.25)
        edit_layout.setColumnStretch(2, 0.25)
        edit_layout.setColumnStretch(3, 0.25)
        edit_layout.setColumnStretch(4, 0.25)
        edit_layout.setColumnStretch(5, 1.00)
        edit_layout.setColumnStretch(6, 0.25)

        return edit_box

    def create_measure_view(self,
                            box: QGroupBox,
                            layout: QGridLayout,
                            row=0,
                            column=6):
        """ create the measure view """

        assert box
        self.measure_view = MeasureView()
        layout.addWidget(self.measure_view.view, row, column)

    def _populate(self):
        """ populate the TreeView """

        start = 1
        for nr, grd in enumerate(self.grids, 1):
            grd.nr = nr
            grd.start = start
            start += grd.amount

        columns = ['Grid', 'Data']

        data = []
        for grd in self.grids:
            value = GridDialog.visible_text(grd.visible)
            dct = {
                'parent': f'grid{grd.nr}',
                'children': {
                    'start': str(grd.start),
                    'visible': value,
                    'amount': str(grd.amount),
                    'numerator': str(grd.numerator),
                    'denominator': str(grd.denominator),
                    'grid': ','.join([str(pos) for pos in grd.grid]),
                },
                'parent.readonly': True,
                'child1.readonly': True,
                'child2.readonly': True,
            }
            data.append(dct)

        self.tree_view.populate(columns=columns, data=data)

    def _on_selection_changed(self, row: int, col: int, parent: Any):
        """ the selection in the QTreeView changed """

        if parent is None:
            # a parent row was clicked, the row of the parent is given
            self.note = f'selected row {row}'
        else:
            # here, a child was clicked, now the row is the child's row
            # and the parent has a value. Now get the row of the parent
            self.note = f'selected child row {row} col {col} of parent on row {parent.row()}'
            row = parent.row()

        self.cur_grid = self.grids[row]
        self.update_measure_view()
        self._update_grids_view()

    def _create_selected(self,
                         box: QGroupBox,
                         layout: QGridLayout,
                         row: int):
        """ two labels for selected """

        lbl1 = QLabel(parent=box)
        lbl1.setText('Selected')
        lbl1.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(lbl1, row, 0)

        selected_lbl = QLabel(parent=box)
        selected_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.controls.selected_lbl = selected_lbl

        layout.addWidget(selected_lbl, row, 1)
        box.setLayout(layout)

    def _create_start(self,
                      box: QGroupBox,
                      layout: QGridLayout,
                      row: int):
        """ start of a grid """

        lbl2 = QLabel(parent=box)
        lbl2.setText('Start')
        layout.addWidget(lbl2, row, 0)

        spin_start = QSpinBox(parent=box)
        spin_start.setMinimum(1)
        spin_start.setMaximum(200)
        spin_start.setValue(0)
        spin_start.setEnabled(False)
        self.controls.spin_start = spin_start

        layout.addWidget(spin_start, row, 1)

        check_visible = QCheckBox(parent=box)
        check_visible.setText('Visible')
        check_visible.stateChanged.connect(self._visible_changed)
        layout.addWidget(check_visible, row, 2)

        self.check_visible = check_visible

    def _create_amount(self,
                       box: QGroupBox,
                       layout: QGridLayout,
                       row: int):
        """ label and spin for amount of grids """

        lbl = QLabel(parent=box)
        lbl.setText('Amount')
        layout.addWidget(lbl, row, 0)

        spin_amount = QSpinBox(parent=box)
        spin_amount.setMinimum(1)
        spin_amount.setMaximum(10000)
        spin_amount.setValue(0)
        spin_amount.valueChanged.connect(self.amount_changed)
        self.spin_amount = spin_amount

        layout.addWidget(spin_amount, row, 1)

    def _create_toolbar(self,
                        box: QGroupBox,
                        layout: QGridLayout,
                        row: int):
        """ toolbar """
        tb_layout = QGridLayout()

        toolbar = QToolBar(parent=box)
        tb_layout.addWidget(toolbar, row, 1)

        action_add = QAction('Add', self)
        action_add.setToolTip('Add same Grid')
        action_add.triggered.connect(self._on_add)
        toolbar.addAction(action_add)

        action_del = QAction('Del', self)
        action_del.setToolTip('Delete Grid')
        action_del.triggered.connect(self._on_del)
        toolbar.addAction(action_del)

        for idx in range(tb_layout.count()):
            tb_layout.itemAt(idx).setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(tb_layout, row, 0, 1, 4)

    def _on_add(self):
        """ add the same grid """

        row = self.cur_grid.nr - 1
        self.note = f'add grid after grid={row + 1}'
        self.grids.insert(row, deepcopy(self.cur_grid))
        self._renumber_grids()
        self._populate()

    def _on_del(self):
        """ delete this grid """

        row = self.cur_grid.nr - 1
        self.note = f'pop grid {row}'
        self.grids.pop(row)
        self._renumber_grids()
        self._populate()

    def _on_ok(self):
        """ the OK button was clicked """

        self.dialog_result = DialogResult.OK
        self.close()

    def _on_cancel(self):
        """ the cancel button was clicked """

        self.dialog_result = DialogResult.CANCEL
        self.close()

    def update_value(self, row: int, name: str, value: str):
        """ update the value in the model """

        self.tree_view.set_value(row=row, name=name, value=value)

    @staticmethod
    def visible_text(state: bool):
        """ convert bool to text """
        return 'visible' if state else 'blank'

    def _visible_changed(self):
        """ grid visible changed """

        value = self.visible
        idx = self.cur_grid.nr - 1
        text = GridDialog.visible_text(value)
        self.update_measure_view()

        if not self.mute:
            self.update_value(row=idx, name='visible', value=text)
            self.grids[idx].visible = value

    def _create_signature(self,
                          box: QGroupBox,
                          layout: QGridLayout,
                          row: int):
        """ label and two values """

        lbl = QLabel(parent=box)
        lbl.setText('Signature')
        layout.addWidget(lbl, row, 0)

        numerator = self._create_numerator(box=box)
        layout.addWidget(numerator, row, 1)

        denominator = self._create_denominator(box=box)
        layout.addWidget(denominator, row, 2)

    def _create_numerator(self,
                          box: QGroupBox) -> QSpinBox:
        """ create the numerator """

        spin_numerator = QSpinBox(parent=box)
        spin_numerator.setMinimum(1)
        spin_numerator.setMaximum(128)
        spin_numerator.setValue(0)
        spin_numerator.valueChanged.connect(self.signature_changed)
        self.spin_numerator = spin_numerator
        return spin_numerator

    @property
    def numerator(self) -> int:
        """ get the numerator of the signature """

        return self.spin_numerator.value()

    @numerator.setter
    def numerator(self, value: int):
        """ set the numerator of the signature """

        num_min = self.spin_numerator.minimum()
        num_max = self.spin_numerator.maximum()
        if num_min <= value <= num_max:
            self.spin_numerator.setValue(value)

    @property
    def _allowed_denominators(self) -> list:
        """ the denominator values that are allowed """

        assert self
        return [1, 2, 4, 8, 16, 32, 64, 128]

    def _create_denominator(self,
                            box: QGroupBox) -> QComboBox:
        """ denominator of the signature """

        combo_denominator = QComboBox(parent=box)
        for value in self._allowed_denominators:
            combo_denominator.addItem(str(value))

        combo_denominator.setCurrentText('4')

        combo_denominator.currentTextChanged.connect(self.signature_changed)
        self.combo_denominator = combo_denominator

        return combo_denominator

    @property
    def denominator(self) -> Optional[int]:
        """ denominator of the signature """

        value = int(self.combo_denominator.currentText())
        return value if value in self._allowed_denominators else None

    @denominator.setter
    def denominator(self, value) -> None:
        """ set the signature denominator """

        if value in self._allowed_denominators:
            self.combo_denominator.setCurrentText(str(value))

    def signature_changed(self):
        """ the signature changed """

        row = self.cur_grid.nr - 1
        num = self.spin_numerator.value()
        den = self.combo_denominator.currentText()
        self.note = f'Signature changed {num}/{den}, mute= {self.mute}'
        self.update_measure_view()
        self._update_grids_view()

        if not self.mute:
            self.update_value(row=row, name='denominator', value=den)
            self.grids[row].denominator = int(den)
            self.update_value(row=row, name='numerator', value=str(num))
            self.grids[row].numerator = int(num)

    def _yorn_box(self,
                  box: QGroupBox,
                  layout: QGridLayout,
                  row: int = 0,
                  col: int = 0,
                  rowspan:int = 1,
                  colspan:int = 1):
        """ OK or Cancel """

        yorn_layout = QGridLayout()

        ok_button = QPushButton(parent=box)
        ok_button.setText('OK')
        ok_button.clicked.connect(self._on_ok)
        yorn_layout.addWidget(ok_button, 0, 0, 1, 1)

        self.popup_check = QCheckBox(parent=box)
        self.popup_check.setText('Logging')
        self.popup_check.setChecked(False)
        self.popup_check.stateChanged.connect(self.popup_check_changed)
        yorn_layout.addWidget(self.popup_check, 0, 1, 1, 1)

        cancel_button = QPushButton(parent=box)
        cancel_button.setText('Cancel')
        cancel_button.clicked.connect(self._on_cancel)
        yorn_layout.addWidget(cancel_button, 0, 2, 1, 1)

        layout.addLayout(yorn_layout, row, col, rowspan, colspan)

    def popup_check_changed(self, state: int):
        """ show or hide the popup """

        assert state
        if self.is_popup_allowed:
            if not self.popup:
                self.create_popup()
        else:
            if self.popup:
                self.popup.close()
                self.popup = None

    @property
    def selected(self) -> str:
        """ selected grid sequence name """

        return self.controls.selected_lbl.text()

    @selected.setter
    def selected(self, value: str):
        """ set the selected grid """

        self.controls.selected_lbl.setText(value)

    @property
    def start(self) -> int:
        """ get start grid """

        return self.controls.spin_start.value()

    @start.setter
    def start(self, value: int):
        """ set start grid """

        self.controls.spin_start.setValue(value)

    @property
    def start_max(self) -> int:
        """ get maximum start+_max """

        return self.controls.spin_start.maximum()

    @start_max.setter
    def start_max(self, value: int):
        """ set maximum start+_max """

        self.controls.spin_start.setMaximum(value)

    @property
    def visible(self) -> bool:
        """ get grid is visible """

        return self.check_visible.isChecked()

    @visible.setter
    def visible(self, value: bool) -> None:
        """ set grid is visible """

        self.check_visible.setChecked(value)

    @property
    def amount(self) -> int:
        """ get maximum start+_max """

        return self.spin_amount.value()

    @amount.setter
    def amount(self, value: int):
        """ set maximum start+_max """

        self.spin_amount.setValue(value)

    @property
    def amount_max(self) -> int:
        """ get maximum start+_max """

        return self.spin_amount.maximum()

    @amount_max.setter
    def amount_max(self, value: int):
        """ set maximum start+_max """

        self.spin_amount.setMaximum(value)

    def amount_changed(self) -> None:
        """ the amount value has changed """

        amount = self.amount
        row = self.cur_grid.nr - 1
        self._renumber_grids()
        self.note = f'amount changed {self.amount}'

        if not self.mute:
            self.update_value(row=row, name='amount', value=str(amount))
            self.grids[row].amount = amount

    def _renumber_grids(self) -> None:
        """
        Renumber the grids and update their start values based on the
        current start and amount.
        This function does not take any parameters and does not return anything.
        """
        start = 1
        for row, grid in enumerate(self.grids):
            grid.start = start
            self.update_value(row=row, name='start', value=str(start))
            start += grid.amount

    def _lines_view(self,
                    box: QGroupBox,
                    layout: QGridLayout,
                    row: int,
                    col: int):
        """ grid lines view """

        self.line_view = LinesView(box=box,
                                   layout=layout,
                                   width=100,
                                   row=row,
                                   col=col,
                                   col_span=1,
                                   row_span=1,
                                   on_selection_changed=self._lines_on_selection_changed,
                                   on_value_changed=self._lines_on_value_changed)

    def _lines_on_selection_changed(self, changed: namedtuple):
        """ an item was selected """

        row, col, par, data = changed
        self.note = f'selection:     row {row} col {col} parent {par} data {data}'

    def _lines_on_value_changed(self,
                                top_left: namedtuple,
                                bottom_right: namedtuple):
        """ value in the tree changed"""

        assert bottom_right

        row, col, par, data = top_left
        self.note = f'index: row {row} col {col} parent {par} data {data}'

        if data is None:
            return

        self.cur_grid.grid[row] = int(data)
        self.update_lines()

    def update_lines(self):
        """ update the grid lines """

        value = ','.join([str(line) for line in self.cur_grid.grid])
        nr = self.cur_grid.nr - 1
        self.tree_view.set_value(row=nr, name='grid', value=value)

    def _lines_func(self,
                    box: QGroupBox,
                    layout: QGridLayout,
                    row: int,
                    col: int,
                    rowspan:int = 1,
                    colspan:int = 1):
        """ grid lines functions """

        toolbar = QToolBar(parent=box)

        action_add = QAction('Add', self)
        action_add.setToolTip('Add same line')
        action_add.triggered.connect(self._on_line_add)
        toolbar.addAction(action_add)

        action_del = QAction('Del', self)
        action_del.setToolTip('Delete line')
        action_del.triggered.connect(self._on_line_del)
        toolbar.addAction(action_del)

        action_reset = QAction('Reset', self)
        action_reset.setStatusTip('Reset to default')
        action_reset.triggered.connect(self._on_line_reset)
        toolbar.addAction(action_reset)

        layout.addWidget(toolbar, row, col, rowspan, colspan)

    def _on_line_add(self):
        """ add a line in the measure """

        self.note = 'add a line'

    def _on_line_del(self):
        """ delete a line in the measure """

        self.note = 'delete a line'

    def _on_line_reset(self):
        """ reset lines to default """

        self.note = 'reset lines to default'
        num = self.numerator
        den = self.denominator

        step = self.base.get(den, 1)
        lines = [x * step for x in range(1, num)]
        self.cur_grid.grid = lines
        self.update_lines()
        self._update_grids_view()

    def _update_grids_view(self):
        """ update the view of the grid in the measure """

        if self.mute:
            return

        lines = self.cur_grid.grid
        columns = ['Lines']
        data = [str(pos) for pos in lines]
        self.line_view.populate(columns=columns, data=data)

    def set_close_event(self, close_callback) -> None:
        """ set the callback on close """

        self.close_callback = close_callback

    def dialog_closes(self, event):
        """ this dialog closes """

        if self.popup:
            self.popup.close()

        self.do_callback()
        event.accept()

    @property
    def base(self) -> Dict:
        """ eh, the base """

        assert self  # @property and @staticmethod don't go together
        return {
            1: 1024,
            2: 512,
            4: 256,
            8: 64,
            16: 32,
            32: 16,
            64: 8,
            128: 1
        }

    def do_callback(self):
        """ execute the callback when it's implemented """

        if self.close_callback:

            # we have to restore the grid.grid to the array of count lines
            # because there is no support for count lines in the grid editor yet
            # we ar switching on all count lines

            grid_dct = []
            for item in self.grids:
                dct = item.to_dict()
                num = item.numerator
                step = self.base.get(item.denominator, 1)
                dct['grid'] = [x * step for x in range(1, num)]
                dct.pop('start', None)
                dct.pop('option', None)
                dct.pop('hidden', None)
                grid_dct.append(dct)
                print(str(dct))

            self.close_callback(result=self.dialog_result, grids=grid_dct)

    @property
    def is_popup_allowed(self):
        """Return True if popup is allowed, False if denied."""

        return self.popup_check.checkState() == Qt.CheckState.Checked

    @property
    def note(self) -> str:
        """Get the note on the note label."""

        return self.popup.text if self.popup else ''

    @note.setter
    def note(self, value: str) -> None:
        """ set the note on the note label
            :param str value: the text to be added to the label
        """

        if self.is_popup_allowed:
            if self.popup is None:
                self.create_popup()
            self.popup.append(value)

    def create_popup(self):
        """Create the popup dialog."""

        self.popup = Popup(
            message='[CLEAR]',
            result_callback=self.popup_callback
        )

    def popup_callback(self, result: DialogResult):
        """Handle the popup result."""

        assert result is not None
        self.popup = None
