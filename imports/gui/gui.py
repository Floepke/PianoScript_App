# in CONSTANT.py you can find all constants that are used in the application along with the description.
from imports.utils.CONSTANT import *

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QToolButton
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget
from PySide6.QtWidgets import QToolBar, QLineEdit, QSpinBox
from PySide6.QtWidgets import QLabel, QDockWidget
from PySide6.QtGui import QAction
from PySide6.QtGui import QColor
from imports.gui.graphicsview import GraphicsView
from imports.utils.fileoprations import FileOperations

BACKGROUND_COLOR = QColor('#eeeeee')

class Gui():
    def __init__(self, main):
        self.main = main
        
        # Set window properties
        self.main.setWindowTitle("PianoScript")
        self.main.setGeometry(100, 100, 800, 600)

        # Create the status bar
        self.statusbar = self.main.statusBar()
        self.statusbar.showMessage(STATUSBAR_DEFAULT_TEXT)

        #start menu--------------------------------------------------------------------

        # Create a toolbar
        self.toolbar = QToolBar(self.main)
        self.main.addToolBar(self.toolbar)

        # Create a QMenu
        self.file_menu = QMenu("File", self.main)

        # Add actions to the QMenu
        self.new_action = QAction("New", self.main)
        self.file_menu.addAction(self.new_action)

        self.load_action = QAction("Load", self.main)
        self.file_menu.addAction(self.load_action)

        self.save_action = QAction("Save", self.main)
        self.file_menu.addAction(self.save_action)

        self.saveas_action = QAction("Save As", self.main)
        self.file_menu.addAction(self.saveas_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction("Exit", self.main)
        self.file_menu.addAction(self.exit_action)

        # Create a QToolButton
        self.file_button = QToolButton(self.main)
        self.file_button.setText("File")
        self.file_button.setMenu(self.file_menu)
        self.file_button.setPopupMode(QToolButton.InstantPopup)

        # Add the QToolButton to the QToolBar
        self.toolbar.addWidget(self.file_button)

        #end menu--------------------------------------------------------------------

        # Create the editor view
        self.editor_scene = QGraphicsScene(self.main)
        self.editor_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.editor_view = GraphicsView(self.editor_scene, self.main)

        # Create the print view
        self.print_scene = QGraphicsScene(self.main)
        self.print_scene.setBackgroundBrush(BACKGROUND_COLOR)
        self.print_view = GraphicsView(self.print_scene, self.main)

        # Create a resizable splitter
        self.splitter = QSplitter(self.main)
        self.splitter.addWidget(self.editor_view)
        self.splitter.addWidget(self.print_view)
        self.splitter.setHandleWidth(20)

        # Set the initial sizes of the widgets in the splitter
        self.splitter.setSizes([1000, self.splitter.width()])

        # Set up the main layout
        self.central_widget = QWidget(self.main)
        self.main.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.splitter)

        # Create a dockable widget
        self.dock_widget = QDockWidget("Tool box", self.main)
        self.dock_widget.setStyleSheet("""QDockWidget {border: 1px solid black;}""")
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.main.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        

        # Add widgets to the dockable widget
        self.dock_layout = QVBoxLayout()
        self.entry_box = QLineEdit("Type something")
        self.entry_box.setToolTip("Type something here")
        self.spin_box = QSpinBox()
        self.spin_box.setToolTip("Adjust the spin box")
        self.label = QLabel("Label:")
        self.label.setToolTip("This is a label")
        self.dock_layout.addWidget(self.entry_box)
        self.dock_layout.addWidget(self.spin_box)
        self.dock_layout.addWidget(self.label)
        self.dock_widget.setLayout(self.dock_layout)

    def show(self):
        self.main.show()

    