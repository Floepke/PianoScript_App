import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel,
    QMenu, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon

class FileBrowser(QWidget):
    def __init__(self, io):
        super().__init__()
        self.io = io

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.current_path = os.path.expanduser("~")  # Start at home directory
        self.allowed_extensions = (".pianoscript", ".mid")

        self.clipboard_path = None
        self.clipboard_mode = None  # "cut" or "copy"

        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.open_context_menu)

        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()

        # Add ".." to go up if not at root
        parent_path = os.path.dirname(self.current_path)
        if os.path.abspath(self.current_path) != os.path.abspath(os.sep):
            up_item = QListWidgetItem("..")
            up_item.setData(Qt.UserRole, parent_path)
            up_item.setIcon(QIcon.fromTheme("go-up"))
            self.list_widget.addItem(up_item)

        # List folders
        try:
            entries = os.listdir(self.current_path)
        except Exception as e:
            self.list_widget.addItem(QListWidgetItem(f"Error: {e}"))
            return

        folders = []
        files = []
        for entry in sorted(entries, key=lambda x: x.lower()):
            full_path = os.path.join(self.current_path, entry)
            if os.path.isdir(full_path):
                folders.append((entry, full_path))
            elif os.path.isfile(full_path) and entry.lower().endswith(self.allowed_extensions):
                files.append((entry, full_path))

        for entry, full_path in folders:
            item = QListWidgetItem(entry)
            item.setData(Qt.UserRole, full_path)
            item.setIcon(QIcon.fromTheme("folder"))
            self.list_widget.addItem(item)

        for entry, full_path in files:
            item = QListWidgetItem(entry)
            item.setData(Qt.UserRole, full_path)
            item.setIcon(QIcon.fromTheme("text-x-generic"))
            self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        entry_name = item.text()
        entry_path = item.data(Qt.UserRole)
        if entry_name == "..":
            self.current_path = entry_path
            # Save the new path to settings
            self.io['settings']['browser_path'] = self.current_path
            self.refresh_list()
        elif os.path.isdir(entry_path):
            self.current_path = entry_path
            # Save the new path to settings
            self.io['settings']['browser_path'] = self.current_path
            self.refresh_list()
        elif os.path.isfile(entry_path):
            print(f"Opening file: {entry_path}")
            if entry_path.lower().endswith(".pianoscript"):
                self.io['fileoperations'].load(entry_path)
            elif entry_path.lower().endswith(".mid"):
                self.io['fileoperations'].import_midi(entry_path)

    def open_context_menu(self, position: QPoint):
        item = self.list_widget.itemAt(position)
        if not item:
            return

        entry_name = item.text()
        entry_path = item.data(Qt.UserRole)
        is_file = os.path.isfile(entry_path)
        is_folder = os.path.isdir(entry_path)
        is_up = entry_name == ".."

        menu = QMenu(self)

        if not is_up:
            cut_action = menu.addAction("Cut")
            copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        if is_file and not is_up:
            delete_action = menu.addAction("Delete")
            rename_action = menu.addAction("Rename")

        action = menu.exec(self.list_widget.mapToGlobal(position))

        if not is_up and action == cut_action:
            self.clipboard_path = entry_path
            self.clipboard_mode = "cut"
        elif not is_up and action == copy_action:
            self.clipboard_path = entry_path
            self.clipboard_mode = "copy"
        elif action == paste_action:
            self.handle_paste()
        elif is_file and not is_up and action == delete_action:
            self.handle_delete(entry_path)
        elif is_file and not is_up and action == rename_action:
            self.handle_rename(entry_path)

    def handle_paste(self):
        if not self.clipboard_path or not os.path.exists(self.clipboard_path):
            return
        basename = os.path.basename(self.clipboard_path)
        dest_path = os.path.join(self.current_path, basename)
        # Avoid overwriting
        if os.path.exists(dest_path):
            QMessageBox.warning(self, "Paste", f"File '{basename}' already exists in this folder.")
            return
        try:
            if os.path.isfile(self.clipboard_path):
                shutil.copy2(self.clipboard_path, dest_path)
                if self.clipboard_mode == "cut":
                    os.remove(self.clipboard_path)
            elif os.path.isdir(self.clipboard_path):
                shutil.copytree(self.clipboard_path, dest_path)
                if self.clipboard_mode == "cut":
                    shutil.rmtree(self.clipboard_path)
            if self.clipboard_mode == "cut":
                self.clipboard_path = None
                self.clipboard_mode = None
            self.refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Paste Error", str(e))

    def handle_delete(self, entry_path):
        reply = QMessageBox.question(
            self, "Delete File",
            f"Are you sure you want to delete '{os.path.basename(entry_path)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(entry_path)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", str(e))

    def handle_rename(self, entry_path):
        old_name = os.path.basename(entry_path)
        old_ext = os.path.splitext(old_name)[1].lower()
        new_name, ok = QInputDialog.getText(
            self, "Rename File", f"Enter new name for '{old_name}':", text=old_name
        )
        if ok and new_name and new_name != old_name:
            # Ensure extension is preserved if not provided
            if not new_name.lower().endswith(self.allowed_extensions):
                new_name += old_ext
            new_path = os.path.join(self.current_path, new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Rename", f"A file named '{new_name}' already exists.")
                return
            try:
                os.rename(entry_path, new_path)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", str(e))
    
    