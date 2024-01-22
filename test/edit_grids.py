#! python3.11
# coding: utf8

""" Grid Editor interface example """

__copyright__ = '© Sihir 2024-2024 all rights reserved'

from sys import exit as _exit
from sys import argv

from typing import List
from typing import Dict

# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QDialog

from PySide6.QtCore import Qt
# pylint: enable=no-name-in-module

from imports.editor.grideditor.dialog_result import DialogResult
from imports.editor.grideditor.grid_editor_dialog import GridDialog

from imports.editor.grideditor.grid import Grid


class GridInterface(QDialog):
    """ example interface """

    # start of fake pianoscript
    def __init__(self):
        """ fake initialisation """

        super().__init__()

        self.editor_dialog = None
        self.io = {'score': {'events': {'grid': self.example_grids()}}}
        self.show()
        self.lower()

    def example_grids(self) -> List[Dict]:
        """ example """

        assert self
        grids = [
            Grid(nr=1,
                 start=1,
                 amount=2,
                 numerator=4,
                 denominator=4,
                 grid=[256, 512, 768],
                 option='',
                 visible=True).to_dict(),

            Grid(nr=2,
                 start=3,
                 amount=2,
                 numerator=3,
                 denominator=4,
                 grid=[256, 512],
                 option='',
                 visible=True).to_dict(),
        ]
        return grids

    # end of fake pianoscript,

    def open_grid_dialog(self):
        """ this opens the dialog """

        grid = self.io['score']["events"]["grid"]
        self.editor_dialog = GridDialog(parent=self,
                                        grid_dct=grid)
        self.editor_dialog.setWindowFlags(Qt.Tool)
        self.editor_dialog.set_close_event(self.dialog_close_callback)
        self.editor_dialog.show()

    def dialog_close_callback(self, result: DialogResult, grids: [Grid]):
        """ the dialog has closed """

        self.io['score']["events"]["grid"] = grids
        self.editor_dialog = None

        # the following is needed to close the fake program, do not copy
        self.show()
        self.close()


# part of fake pianoscript

if __name__ == '__main__':

    app = QApplication(argv)
    itf = GridInterface()
    itf.open_grid_dialog()
    _exit(app.exec())
