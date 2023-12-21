import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from PySide6.QtWidgets import QToolBar, QLineEdit, QSpinBox
from PySide6.QtWidgets import QLabel, QDockWidget
from PySide6.QtGui import QScreen, QGuiApplication, QAction
from PySide6.QtGui import QKeyEvent

BACKGROUND_COLOR = Qt.white

class Gui():
    def __init__(self, main):
        self.main = main

        # Set window properties
        self.main.setWindowTitle("PianoScript")
        self.main.setGeometry(100, 100, 800, 600)

        # Create the status bar
        statusbar = self.main.statusBar()
        statusbar.showMessage("Ready")

        # Create the file menu
        menubar = self.main.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(QAction("Open", triggered=self.open_file))
        file_menu.addAction(QAction("Save", triggered=self.save_file))
        file_menu.addAction(QAction("Exit", triggered=self.main.close))

        # Create a toolbar
        toolbar = QToolBar("Toolbar", self.main)
        self.main.addToolBar(toolbar)

        # Create actions for the toolbar
        action1 = QAction("Cut", triggered=self.cut)
        action2 = QAction("Copy", triggered=self.copy)
        action3 = QAction("Paste", triggered=self.paste)
        toolbar.addActions([action1, action2, action3])

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.editor_view = QGraphicsView(self.editor_scene, self.main)
        self.editor_scene.addItem(QGraphicsRectItem(0, 0, 200, 1500))

        # Create the print view
        print_scene = QGraphicsScene(self.main)
        print_scene.setBackgroundBrush(BACKGROUND_COLOR)
        print_view = QGraphicsView(print_scene, self.main)

        # Create a resizable splitter
        splitter = QSplitter(self.main)
        splitter.addWidget(self.editor_view)
        splitter.addWidget(print_view)
        splitter.setHandleWidth(20)

        # Set up the main layout
        central_widget = QWidget(self.main)
        self.main.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)

        # Create a dockable widget
        dock_widget = QDockWidget("Dockable Widget", self.main)
        dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

        # Add widgets to the dockable widget
        dock_layout = QVBoxLayout()
        entry_box = QLineEdit("Type something")
        entry_box.setToolTip("Type something here")
        spin_box = QSpinBox()
        spin_box.setToolTip("Adjust the spin box")
        label = QLabel("Label:")
        label.setToolTip("This is a label")
        dock_layout.addWidget(entry_box)
        dock_layout.addWidget(spin_box)
        dock_layout.addWidget(label)
        dock_widget.setLayout(dock_layout)

    def show(self):
        self.main.show()

    def open_file(self):
        pass  # Implement file opening logic here

    def save_file(self):
        pass  # Implement file saving logic here

    def cut(self):
        pass  # Implement cut logic here

    def copy(self):
        pass  # Implement copy logic here

    def paste(self):
        pass  # Implement paste logic here

    