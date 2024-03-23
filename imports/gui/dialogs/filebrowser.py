import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QHeaderView, QPushButton, QFileDialog
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import QSortFilterProxyModel


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
        self.model = QFileSystemModel()
        self.model.setRootPath(self.folder_path)

        # Create the proxy model
        self.proxy_model = FolderSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        # Set the name filters to only display .mid and .pianoscript files
        self.model.setNameFilters(["*.mid", "*.pianoscript"])
        self.model.setNameFilterDisables(False)  # This line makes the model hide files that don't match the name filters

        # Set the model for the QTreeView
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(self.folder_path)))

        # Sort the model
        self.proxy_model.sort(0, Qt.AscendingOrder)

        # Set the column width to fit the contents
        self.tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # Create the button to select a custom path
        self.select_path_button = QPushButton("Select Path", self)
        layout.addWidget(self.select_path_button)

    def select_custom_path(self, path=None):
        if path == None:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.Directory)
            path = dialog.getExistingDirectory(self, "Select Custom Path")
            if path:
                self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(path)))
        else:
            self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(path)))
        self.io['settings']['browser_path'] = path
        self.model.directoryLoaded.emit(path)
    
    def refresh_browser(self, path):
        self.tree_view.setRootIndex(self.model.index(path))


class FolderSortFilterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_file_info = self.sourceModel().fileInfo(left)
        right_file_info = self.sourceModel().fileInfo(right)

        if left_file_info.isDir() and not right_file_info.isDir():
            return True
        if not left_file_info.isDir() and right_file_info.isDir():
            return False

        return super().lessThan(left, right)