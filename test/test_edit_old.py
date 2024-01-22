#! python3.11
# coding: utf-8

""" grid editor proposal """

__author__ = 'Sihir'  # noqa
__copyright__ = '© Sihir 2023-2023 all rights reserved'  # noqa

from sys import exit as _exit
from sys import argv

from os.path import isfile

from typing import Optional
from typing import Callable

from tkinter import Tk
from tkinter import Toplevel
from tkinter import Button

from json import dumps
from json import loads

from imports.editor.grideditor.grid import Grid

from grid_io import GridIo

from imports.editor.grideditor.grid_editor_dialog import GridDialog

from blueprint import BluePrint
from blueprint import Score


def grids_name() -> str:
    """ the data file name """

    return 'data.json'


def blue_name() -> str:
    """ the blueprint file """

    return 'blue.json'


def prepare(clear: bool) -> str:
    """ test read and write """

    filename = grids_name()
    if not isfile(filename) or clear:
        source = [Grid(amount=11, hidden=[]),
                  Grid(amount=22, hidden=[2]),
                  Grid(amount=33, hidden=[2, 4])
        GridIo.write(source, filename)
    return filename


class TkWindow:
    """ simulates the main window or pianoscript """

    def __init__(self, master: Tk,
                 data: GridList,
                 on_save: Callable):
        """ initialize the class """

        self.data = data
        self.master = master
        self.master.title('Test Grid')
        self.master.attributes('-toolwindow', True)
        self.toplevel = None
        self.gr_edit = None
        self.on_save = on_save

        self.button = Button(text='Grid Editor',
                             width=10,
                             command=self.grid_editor)
        self.button.grid(row=0,
                         column=0,
                         padx=4,
                         pady=4)

    def grid_editor(self):
        """ show the grid editor """

        self.toplevel = Toplevel(self.master)
        self.gr_edit = Gredit(master=self.toplevel,
                              grids=self.data,
                              on_close=self.on_close)

    def on_close(self):
        """ when the window closes """

        grids = self.gr_edit.result
        if self.on_save:
            self.on_save(grids)


class MainWindow:
    """ simulate the main window """
    FILE = 1
    BLUEPRINT = 2

    def __init__(self):
        """ initialize this class """

        self.mode = MainWindow.FILE
        clear = False  # read the file when it it exists

        for arg in argv[1:]:

            match arg:
                case '-b':
                    self.mode = MainWindow.BLUEPRINT
                case '-c':
                    clear = True

        self.root = Tk()

        source = prepare(clear=clear)

        self._filename = source
        grids: Optional[GridList] = None

        match self.mode:

            case MainWindow.FILE:
                grids = GridIo.read(source)

            case MainWindow.BLUEPRINT:
                name = blue_name()
                if not isfile(name):
                    with open(file=name, mode='w', encoding='utf-8') as stream:
                        stream.write(dumps(BluePrint))

                with open(file=name, mode='r', encoding='utf-8') as stream:
                    blue = loads(stream.read())
                    assert blue

                grids = GridList()
                for item in blue["events"]["grid"]:
                    grids.append(index=item['grid'], grid=Grid(dct=item))

        self.piano_window = TkWindow(master=self.root,
                                     data=grids,
                                     on_save=self.on_save)

        self.root.mainloop()

    def _destroy(self):
        self.root.destroy()

    def on_save(self, *args):
        """  save the grids """

        grids, *_ = args
        grid_list = GridList()
        for item in grids:
            grid_list.append(grid=Grid(dct=item))

        match self.mode:

            case MainWindow.FILE:
                if self._filename is None:
                    return

                GridIo.write(grid_list, self._filename)

            case MainWindow.BLUEPRINT:

                blue = Score
                blue_grids = []
                for grid in grids.lst:
                    new = grid.__dict__
                    blue_grids.append(new)

                Score["events"]["grid"] = blue_grids
                contents = dumps(blue)

                with open(file=blue_name(), mode='w', encoding='utf-8') as stream:
                    stream.write(contents)


def main() -> int:
    """ main function """

    _ = MainWindow()
    return 0


if __name__ == '__main__':
    _exit(main())
