#! python3.11
# coding: utf8

""" the Grid Editor dialog """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

from typing import Callable

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QTreeView
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QHeaderView

from PySide6.QtGui import QStandardItemModel
from PySide6.QtGui import QStandardItem

from PySide6.QtCore import Qt
# pylint: enable=no-name-in-module


class LinesView:

    def __init__(self,
                 box: QGroupBox,
                 layout: QGridLayout,
                 row: int,
                 col: int = 0,
                 width: int = 100,
                 rowspan: int = 1,
                 colspan: int = 1,
                 on_selection_changed: Callable = None):
        """ create a TreeView """

        self._on_selection_changed = on_selection_changed
        self.view = view = QTreeView(parent=box)

        view.setColumnWidth(0, width)
        view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.model = model = QStandardItemModel()
        view.setModel(model)
        view.setUniformRowHeights(True)
        self.selection_model = self.view.selectionModel()

        # load these items in the edit controls
        view.clicked.connect(self._on_tree_view_clicked)

        layout.addWidget(view, row, col, rowspan, colspan)

    def _on_tree_view_clicked(self, index):
        """ the tree was clicked changed """

        # print('on_tree_view_clicked')
        if self._on_selection_changed is not None:
            item = self.model.itemFromIndex(index)
            self._on_selection_changed(item.row(), item.column(), item.parent())

    def populate(self, columns: list, data: list):
        """ populate the view """

        view = self.view
        model = self.model
        model.clear()

        model.setHorizontalHeaderLabels(columns)

        # populate data
        for i, item in enumerate(data):
            parent = QStandardItem(str(item))
            # if item['parent.readonly']:
            #    parent.setFlags(parent.flags() ^ Qt.ItemIsEditable)
            model.appendRow(parent)
            # span container columns
            # view.setFirstColumnSpanned(i, view.rootIndex(), True)

        # Set the header to resize column 0
        header = view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

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
