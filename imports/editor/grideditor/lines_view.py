#! python3.11
# coding: utf8

""" the lines treeview """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

from typing import Callable

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QTreeView
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QHeaderView

from PySide6.QtCore import QModelIndex
from PySide6.QtCore import Qt

from PySide6.QtGui import QStandardItemModel
from PySide6.QtGui import QStandardItem
# pylint: enable=no-name-in-module

from imports.editor.grideditor.my_treeview import MyTreeView


class LinesView:

    def __init__(self,
                 box: QGroupBox,
                 layout: QGridLayout,
                 row: int,
                 col: int = 0,
                 width: int = 100,
                 row_span: int = 1,
                 col_span: int = 1,
                 on_selection_changed: Callable = None,
                 on_value_changed: Callable = None):
        """ create a TreeView """

        self._on_selection_changed = on_selection_changed
        self._on_value_changed = on_value_changed
        self.mute = False

        self.view = view = MyTreeView(parent=box)

        view.setColumnWidth(0, width)
        view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.model = model = QStandardItemModel()
        view.setModel(model)
        view.setUniformRowHeights(True)
        self.selection_model = self.view.selectionModel()

        # load these items in the edit controls
        view.clicked.connect(self._on_tree_view_clicked)
        model.dataChanged.connect(self._on_data_changed)

        layout.addWidget(view, row, col, row_span, col_span)

    def get_item(self, index: QModelIndex) -> tuple:
        """ convert index to item """

        item = self.model.itemFromIndex(index)
        return item.row(), item.column(), item.parent(), item.data(Qt.DisplayRole)

    def _on_data_changed(self, top_left_index: QModelIndex, bottom_right_index: QModelIndex):
        """ some items changed """

        if self._on_value_changed and not self.mute:
            self._on_value_changed(top_left=self.get_item(top_left_index),
                                   bottom_right=self.get_item(bottom_right_index))

    def _on_tree_view_clicked(self, index):
        """ the tree was clicked changed """

        # print('on_tree_view_clicked')
        if self._on_selection_changed is not None:
            self._on_selection_changed(changed=self.get_item(index))

    def populate(self, columns: list, data: list):
        """ populate the view """

        self.mute = True
        view = self.view

        model = self.model

        model.clear()

        model.setHorizontalHeaderLabels(columns)

        # populate data
        for i, item in enumerate(data):
            parent = QStandardItem(str(item))
            model.appendRow(parent)

        self.mute = False

        # Set the header to resize column 0
        header = view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        # Set the column 0 to resize to its contents
        view.resizeColumnToContents(0)

    def set_value(self, row, value: str = ''):
        """ change a value in model row """

        item = self.model.item(0)
        try:
            child = item.child(row, 0)
            child.setText(value)
        except:
            pass
