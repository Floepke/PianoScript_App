#! python3.11
# coding: utf8

""" get and set mp3 tags """

__author__ = 'Sihir'
__copyright__ = '© Sihir 2023-2024 all rights reserved'

from os.path import abspath
from os.path import isfile
from os.path import splitext
from os.path import basename
from os.path import expanduser
from os.path import join

from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtCore import QRect

from imports.editor.grideditor.popup import Popup


class ShowHelp:
    """ show the help pages in .html format """

    def __init__(self):
        """ initialize the class """

        self.help_location = expanduser('~/.pianoscript/docs/help')
        self.web_view = None
        self.popup = None

    def show(self, subject: str):
        """ show subject.html """

        folder = self.help_location
        name = f'{subject}.html'
        html_file = abspath(join(folder, name))
        if not isfile(html_file):

            if self.web_view is not None:
                self.web_view.close()

            message = f'help subject not found: {subject}'
            self.popup = Popup(message=message, timeout=5)
            return

        self.web_view = QWebEngineView()
        self.web_view.close_event = self.help_closing
        self.web_view.setWindowTitle('Pianoscript Help')  # noqa
        self.web_view.setGeometry(QRect(100, 100, 1200, 800))
        self.web_view.load(QUrl.fromLocalFile(html_file))
        self.web_view.show()

    def help_closing(self, event):
        """ help window is closing """

        self.web_view = None
