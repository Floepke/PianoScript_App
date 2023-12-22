import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from PySide6.QtWidgets import QToolBar, QLineEdit, QSpinBox
from PySide6.QtWidgets import QLabel, QDockWidget
from PySide6.QtGui import QScreen, QGuiApplication, QAction
from PySide6.QtGui import QKeyEvent, QColor

BACKGROUND_COLOR = QColor('#777777')

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

        # # Create a toolbar
        # toolbar = QToolBar("Toolbar", self.main)
        # self.main.addToolBar(toolbar)

        # # Create actions for the toolbar
        # action1 = QAction("Cut", triggered=self.cut)
        # action2 = QAction("Copy", triggered=self.copy)
        # action3 = QAction("Paste", triggered=self.paste)
        # toolbar.addActions([action1, action2, action3])

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.editor_view = QGraphicsView(self.editor_scene, self.main)
        self.editor_scene.addItem(QGraphicsRectItem(0, 0, 200, 1500))

        # Create the print view
        self.print_scene = QGraphicsScene(self.main)
        self.print_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.print_view = QGraphicsView(self.print_scene, self.main)

        # Create a resizable splitter
        self.splitter = QSplitter(self.main)
        self.splitter.addWidget(self.editor_view)
        self.splitter.addWidget(self.print_view)
        self.splitter.setHandleWidth(20)

        # Set up the main layout
        central_widget = QWidget(self.main)
        self.main.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.splitter)

        # Create a dockable widget
        self.dock_widget = QDockWidget("Dockable Widget", self.main)
        self.dock_widget.setStyleSheet("""
        QDockWidget {
            border: 1px solid black;
        }
        """)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        

        # Add widgets to the dockable widget
        dock_layout = QVBoxLayout()
        self.entry_box = QLineEdit("Type something")
        self.entry_box.setToolTip("Type something here")
        self.spin_box = QSpinBox()
        self.spin_box.setToolTip("Adjust the spin box")
        self.label = QLabel("Label:")
        self.label.setToolTip("This is a label")
        dock_layout.addWidget(self.entry_box)
        dock_layout.addWidget(self.spin_box)
        dock_layout.addWidget(self.label)
        self.dock_widget.setLayout(dock_layout)

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

    