import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from PySide6.QtWidgets import QToolBar, QLineEdit, QSpinBox
from PySide6.QtWidgets import QLabel, QDockWidget
from PySide6.QtGui import QScreen

class Gui():
    '''
        This class builds the main graphical 
        user interface.
    '''

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
        file_menu.addAction("Open")
        file_menu.addAction("Save")
        file_menu.addAction("Exit", self.main.close)

        # Create a toolbar
        toolbar = QToolBar("Toolbar", self.main)
        self.main.addToolBar(toolbar)

        # Create actions for the toolbar
        action1 = toolbar.addAction("Cut")
        action2 = toolbar.addAction("Copy")
        action3 = toolbar.addAction("Paste")

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(Qt.white)  # Set the background color to white
        self.editor_view = QGraphicsView(self.editor_scene, self.main)
        self.editor_scene.addItem(QGraphicsRectItem(0, 0, 200, 1500))

        # Create the print view
        print_scene = QGraphicsScene(self.main)
        print_scene.setBackgroundBrush(Qt.white)  # Set the background color to white
        print_view = QGraphicsView(print_scene, self.main)

        # Create a resizable splitter
        splitter = QSplitter(self.main)
        splitter.addWidget(self.editor_view)
        splitter.addWidget(print_view)

        # Set the handle width of the splitter
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
        entry_box = QLineEdit("Type something", dock_widget)
        spin_box = QSpinBox(dock_widget)
        label = QLabel("Label:", dock_widget)

        # Set widgets as the dock widget's widget
        dock_widget.setWidget(QWidget())
        dock_widget.widget().setLayout(QVBoxLayout())
        dock_widget.widget().layout().addWidget(entry_box)
        dock_widget.widget().layout().addWidget(spin_box)
        dock_widget.widget().layout().addWidget(label)

    def show(self):
        self.main.show()