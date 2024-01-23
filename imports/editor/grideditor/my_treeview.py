#! python3.11
# coding: utf8

""" the lines treeview """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2024-2024 all rights reserved'

from typing import List

from PySide6.QtWidgets import QTreeView
from PySide6.QtGui import QStandardItemModel

class MyTreeView(QTreeView):
    """ MyTreeView can restore expanded rows """

    def __init__(self, parent=None):
        """ initialize the class """
        super().__init__(parent)

        self.model = QStandardItemModel()
        self.setModel(self.model)

    def get_parent_row_indices(self):
        """ get the indices of the parent rows """

        model = self.model
        return [model.index(row, 0) for row in range(model.rowCount())]

    def get_expanded_rows(self) -> List[int]:
        """ get the expanded rows """

        indices = self.get_parent_row_indices()
        for index in indices:
            print(f'index row {index.row()} col {index.column()}')
        return [index.row() for index in indices if self.isExpanded(index)]
