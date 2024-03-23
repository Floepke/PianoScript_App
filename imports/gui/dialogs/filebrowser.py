import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QHeaderView, QPushButton, QFileDialog
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QColor


class FileBrowser(QWidget):
    def __init__(self, io):
        super().__init__()
        self.io = io

        # Set up the layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Create the QTreeView
        self.tree_view = QTreeView(self)
        layout.addWidget(self.tree_view)

        # Set the root directory for the file tree
        self.folder_path = "pianoscriptfiles"

        # Create the file system model
        model = QFileSystemModel()
        model.setRootPath(self.folder_path)

        # Set the model for the QTreeView
        self.tree_view.setModel(model)
        self.tree_view.setRootIndex(model.index(self.folder_path))

        # Set the column width to fit the contents
        self.tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # Create the button to select a custom path
        self.select_path_button = QPushButton("Select Path", self)
        layout.addWidget(self.select_path_button)

        # Connect the button to the file dialog
        self.select_path_button.clicked.connect(lambda: self.select_custom_path(None))

        # Set the alternate row colors
        self.tree_view.setAlternatingRowColors(True)

    def select_custom_path(self, path=None):
        if path == None:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.Directory)
            path = dialog.getExistingDirectory(self, "Select Custom Path")
            if path:
                model = self.tree_view.model()
                self.tree_view.setRootIndex(model.index(path))
        else:
            model = self.tree_view.model()
            self.tree_view.setRootIndex(model.index(path))
        self.io['settings']['browser_path'] = path
