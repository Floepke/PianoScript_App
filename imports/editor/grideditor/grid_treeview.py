#! python3.11
# coding: utf8

""" the Grid Editor dialog """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

from typing import Callable
from typing import List

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QTreeView
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QAbstractItemView

from PySide6.QtGui import QStandardItemModel
from PySide6.QtGui import QStandardItem
from PySide6.QtCore import Qt
# pylint: enable=no-name-in-module

from imports.editor.grideditor.my_treeview import MyTreeView


class GridTreeView:

    def __init__(self,
                 box: QGroupBox,
                 layout: QGridLayout,
                 row: int,
                 col: int = 0,
                 span: int = 1,
                 on_selection_changed: Callable = None):
        """ create a TreeView """

        self._on_selection_changed = on_selection_changed
        self.view = view = MyTreeView(parent=box)
        view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        self.model = model = QStandardItemModel()
        view.setModel(model)
        view.setUniformRowHeights(True)
        self.selection_model = self.view.selectionModel()

        # load these items in the edit controls
        view.clicked.connect(self._on_tree_view_clicked)

        layout.addWidget(view, row, col, 1, span)

    def _on_tree_view_clicked(self, index):
        """ the tree was clicked changed """

        # print('on_tree_view_clicked')
        if self._on_selection_changed is not None:
            item = self.model.itemFromIndex(index)
            self._on_selection_changed(
                item.row(), item.column(), item.parent())

    def populate(self, columns: list, data: list):
        """ populate the view """

        view = self.view
        indices = view.get_parent_row_indices()
        for index in indices:
            print(f'grid index row {index.row()} col {index.column()}')

        expanded = view.get_expanded_rows()
        # print(f'expanded rows {expanded}')

        model = self.model
        model.clear()

        model.setHorizontalHeaderLabels(columns)

        # populate data
        for i, item in enumerate(data):
            parent = QStandardItem(item['parent'])
            if item['parent.readonly']:
                parent.setFlags(parent.flags() ^ Qt.ItemIsEditable)

            dct = item['children']
            for key, value in dct.items():
                child1 = QStandardItem(key)
                if item['child1.readonly']:
                    child1.setFlags(child1.flags() ^ Qt.ItemIsEditable)

                child2 = QStandardItem(value)
                if item['child2.readonly']:
                    child2.setFlags(child2.flags() ^ Qt.ItemIsEditable)

                parent.appendRow([child1, child2])
            model.appendRow(parent)
            # span container columns
            view.setFirstColumnSpanned(i, view.rootIndex(), True)

        parent_indices = view.get_parent_row_indices()
        for nr, index in enumerate(parent_indices):
            print(f'row {nr} {index.row()}')
        # view.restore_expanded_items(expanded)

    def set_value(self, row, name: str, value: str = ''):
        """ change a value in model row """

        item = self.model.item(row)
        if item is None:
            return

        for idx in range(item.rowCount()):
            child1 = item.child(idx, 0)
            child2 = item.child(idx, 1)
            if child1.text() == name:
                child2.setText(value)
                return
